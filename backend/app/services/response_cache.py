"""
LLM Response Cache Service
Caches LLM responses to avoid regenerating identical content
"""
import hashlib
import pickle
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class ResponseCache:
    """Cache for LLM responses based on hash(question + context)"""
    
    def __init__(self):
        self.cache_path = Path("storage/response_cache.pkl")
        self._cache = None
        self.max_age_days = 30  # Cache expires after 30 days
    
    @property
    def cache(self) -> dict:
        """Lazy load cache from disk"""
        if self._cache is None:
            self._cache = self._load_cache()
        return self._cache
    
    def _load_cache(self) -> dict:
        """Load cache from disk"""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, 'rb') as f:
                    cache_data = pickle.load(f)
                    logger.info(f"[Response Cache] Loaded {len(cache_data)} cached responses")
                    return cache_data
            except Exception as e:
                logger.error(f"Failed to load response cache: {e}")
        
        return {}
    
    def _save_cache(self):
        """Save cache to disk"""
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.cache_path, 'wb') as f:
                pickle.dump(self._cache, f)
        except Exception as e:
            logger.error(f"Failed to save response cache: {e}")
    
    def _generate_key(self, question: str, context: str = "") -> str:
        """Generate cache key from question + context"""
        combined = f"{question.lower().strip()}:{context[:500]}"  # First 500 chars of context
        return hashlib.md5(combined.encode()).hexdigest()
    
    def get(self, question: str, context: str = "") -> Optional[str]:
        """
        Get cached response if exists and not expired
        
        Args:
            question: User question
            context: Additional context
            
        Returns:
            Cached response or None
        """
        cache_key = self._generate_key(question, context)
        
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            timestamp = entry.get('timestamp')
            
            # Check if cache entry is still valid
            if timestamp:
                age = datetime.now() - timestamp
                if age < timedelta(days=self.max_age_days):
                    logger.info(f"[Response Cache] HIT - {cache_key[:8]}")
                    return entry['response']
                else:
                    # Expired, remove it
                    logger.info(f"[Response Cache] EXPIRED - {cache_key[:8]}")
                    del self.cache[cache_key]
        
        logger.info(f"[Response Cache] MISS - {cache_key[:8]}")
        return None
    
    def set(self, question: str, response: str, context: str = ""):
        """
        Store response in cache
        
        Args:
            question: User question
            response: LLM response
            context: Additional context
        """
        cache_key = self._generate_key(question, context)
        
        self.cache[cache_key] = {
            'response': response,
            'timestamp': datetime.now(),
            'question': question[:200]  # Store truncated question for debugging
        }
        
        self._save_cache()
        logger.info(f"[Response Cache] STORED - {cache_key[:8]}")
    
    def clear_expired(self):
        """Remove expired cache entries"""
        now = datetime.now()
        expired_keys = []
        
        for key, entry in self.cache.items():
            timestamp = entry.get('timestamp')
            if timestamp and (now - timestamp) > timedelta(days=self.max_age_days):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            self._save_cache()
            logger.info(f"[Response Cache] Cleared {len(expired_keys)} expired entries")
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        return {
            'total_entries': len(self.cache),
            'cache_path': str(self.cache_path)
        }


# Global instance
response_cache = ResponseCache()
