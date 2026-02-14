"""
Text-to-Speech service for AI Voice Tutor Mode
Uses gTTS (Google Text-to-Speech) for lightweight audio generation
"""
import os
import logging
from typing import Optional
from gtts import gTTS
from pathlib import Path

logger = logging.getLogger(__name__)

# Audio storage directory
AUDIO_DIR = Path("static/audio")


class TTSService:
    """Service for generating audio from text responses"""
    
    def __init__(self):
        """Initialize TTS service and ensure audio directory exists"""
        AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"TTS Service initialized. Audio directory: {AUDIO_DIR}")
    
    async def generate_audio(
        self, 
        text: str, 
        message_id: str,
        language: str = 'en'
    ) -> Optional[str]:
        """
        Generate audio file from text
        
        Args:
            text: Text content to convert to speech
            message_id: Unique identifier for the message (for filename)
            language: Language code (default: 'en')
            
        Returns:
            URL path to audio file, or None if generation fails
        """
        try:
            # Sanitize message_id for filename
            safe_id = "".join(c for c in message_id if c.isalnum() or c in ('-', '_'))
            filename = f"response_{safe_id}.mp3"
            filepath = AUDIO_DIR / filename
            
            # Remove existing file if present
            if filepath.exists():
                filepath.unlink()
            
            # Clean text for TTS (remove markdown formatting)
            clean_text = self._clean_text_for_tts(text)
            
            # Limit text length (gTTS has limits, ~5000 chars is safe)
            if len(clean_text) > 5000:
                clean_text = clean_text[:5000] + "..."
                logger.warning(f"Text truncated to 5000 chars for audio generation")
            
            # Generate audio using gTTS
            logger.info(f"Generating audio for message {message_id} ({len(clean_text)} chars)")
            tts = gTTS(text=clean_text, lang=language, slow=False)
            tts.save(str(filepath))
            
            # Return URL path
            audio_url = f"/static/audio/{filename}"
            logger.info(f"Audio generated successfully: {audio_url}")
            return audio_url
            
        except Exception as e:
            logger.error(f"Failed to generate audio for message {message_id}: {e}")
            return None
    
    def _clean_text_for_tts(self, text: str) -> str:
        """
        Clean text for better TTS output
        - Remove markdown formatting
        - Remove LaTeX formulas
        - Remove special characters
        """
        import re
        
        # Remove markdown headers
        text = re.sub(r'#+\s+', '', text)
        
        # Remove markdown bold/italic
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        
        # Remove LaTeX formulas (replace with "equation")
        text = re.sub(r'\$\$(.+?)\$\$', 'equation', text, flags=re.DOTALL)
        text = re.sub(r'\$(.+?)\$', 'equation', text)
        
        # Remove markdown code blocks
        text = re.sub(r'```[\s\S]*?```', 'code example', text)
        text = re.sub(r'`(.+?)`', r'\1', text)
        
        # Remove bullet points
        text = re.sub(r'^\s*[-*]\s+', '', text, flags=re.MULTILINE)
        
        # Remove numbered lists
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
        
        # Clean up multiple newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove URLs
        text = re.sub(r'https?://\S+', 'link', text)
        
        return text.strip()
    
    def delete_audio(self, message_id: str) -> bool:
        """
        Delete audio file for a message
        
        Args:
            message_id: Message identifier
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            safe_id = "".join(c for c in message_id if c.isalnum() or c in ('-', '_'))
            filename = f"response_{safe_id}.mp3"
            filepath = AUDIO_DIR / filename
            
            if filepath.exists():
                filepath.unlink()
                logger.info(f"Deleted audio file: {filename}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete audio for message {message_id}: {e}")
            return False
    
    def cleanup_old_audio(self, max_files: int = 100):
        """
        Clean up old audio files to prevent storage bloat
        Keeps only the most recent max_files
        
        Args:
            max_files: Maximum number of audio files to keep
        """
        try:
            audio_files = sorted(
                AUDIO_DIR.glob("response_*.mp3"),
                key=lambda f: f.stat().st_mtime,
                reverse=True
            )
            
            # Delete older files
            for old_file in audio_files[max_files:]:
                old_file.unlink()
                logger.info(f"Cleaned up old audio: {old_file.name}")
                
            if len(audio_files) > max_files:
                logger.info(f"Cleaned up {len(audio_files) - max_files} old audio files")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old audio files: {e}")


# Global instance
tts_service = TTSService()
