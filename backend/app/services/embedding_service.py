"""
Embedding service for vector operations
"""
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from sentence_transformers import SentenceTransformer

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and managing embeddings"""
    
    def __init__(self):
        self.model_name = settings.embedding_model
        self.vector_store_path = Path(settings.vector_store_path)
        self._model = None
        self._vector_store = None
    
    @property
    def model(self) -> SentenceTransformer:
        """Lazy load the embedding model"""
        if self._model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
        return self._model
    
    @property
    def vector_store(self) -> Dict[str, Any]:
        """Get or load the vector store"""
        if self._vector_store is None:
            self._vector_store = self._load_vector_store()
        return self._vector_store
    
    def _load_vector_store(self) -> Dict[str, Any]:
        """Load vector store from disk"""
        if self.vector_store_path.exists():
            try:
                with open(self.vector_store_path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                logger.error(f"Failed to load vector store: {e}")
        
        return {
            'embeddings': np.array([]).reshape(0, 384),  # 384 = MiniLM dimension
            'ids': [],
            'metadata': []
        }
    
    def _save_vector_store(self):
        """Save vector store to disk"""
        # Ensure directory exists
        self.vector_store_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create backup
        if self.vector_store_path.exists():
            backup_path = self.vector_store_path.with_suffix('.pkl.bak')
            self.vector_store_path.rename(backup_path)
        
        try:
            with open(self.vector_store_path, 'wb') as f:
                pickle.dump(self._vector_store, f)
        except Exception as e:
            logger.error(f"Failed to save vector store: {e}")
            raise
    
    def encode(self, texts: List[str], batch_size: int = 10) -> np.ndarray:
        """
        Encode texts to embeddings with batch processing
        
        Args:
            texts: List of text strings
            batch_size: Process this many chunks at a time to avoid memory issues
            
        Returns:
            Numpy array of embeddings
        """
        if not texts:
            return np.array([])
        
        # Process in batches to avoid memory overflow
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = self.model.encode(batch, convert_to_numpy=True, show_progress_bar=False)
            all_embeddings.append(batch_embeddings)
            logger.info(f"[Embedding] Processed batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
        
        return np.vstack(all_embeddings) if all_embeddings else np.array([])
    
    def add_documents(
        self,
        chunks: List[str],
        document_id: str,
        subject_id: str,
        filename: str
    ) -> List[str]:
        """
        Add document chunks to the vector store with batch processing
        **OPTIMIZED**: Processes in batches to prevent memory overflow
        
        Args:
            chunks: List of text chunks
            document_id: Document ID
            subject_id: Subject ID
            filename: Original filename
            
        Returns:
            List of embedding IDs
        """
        import gc
        
        if not chunks:
            return []
        
        logger.info(f"[Embedding] Starting batch embedding for {len(chunks)} chunks")
        
        # Generate embeddings in batches (10 chunks at a time)
        embeddings = self.encode(chunks, batch_size=10)
        
        # Force garbage collection after embedding
        gc.collect()
        
        # Create IDs and metadata
        ids = []
        metadata = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{document_id}_{i}"
            ids.append(chunk_id)
            metadata.append({
                'document_id': document_id,
                'subject_id': subject_id,
                'filename': filename,
                'chunk_index': i,
                'content': chunk,
                'content_preview': chunk[:200] + "..." if len(chunk) > 200 else chunk
            })
        
        # Append to vector store
        store = self.vector_store
        if len(store['embeddings']) == 0:
            store['embeddings'] = embeddings
        else:
            store['embeddings'] = np.vstack([store['embeddings'], embeddings])
        store['ids'].extend(ids)
        store['metadata'].extend(metadata)
        
        # Save updated store
        self._save_vector_store()
        
        # Clean up memory
        del embeddings
        gc.collect()
        
        logger.info(f"[Embedding] Completed - all chunks embedded and saved")
        return ids
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        subject_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents
        
        Args:
            query: Search query
            top_k: Number of results
            subject_id: Optional filter by subject
            
        Returns:
            List of matching documents with scores
        """
        store = self.vector_store
        
        if len(store['embeddings']) == 0:
            return []
        
        # Encode query
        query_embedding = self.encode([query])[0]
        
        # Filter by subject if specified
        if subject_id:
            indices = [
                i for i, m in enumerate(store['metadata'])
                if m.get('subject_id') == subject_id
            ]
            if not indices:
                return []
            embeddings = store['embeddings'][indices]
            metadata = [store['metadata'][i] for i in indices]
        else:
            embeddings = store['embeddings']
            metadata = store['metadata']
        
        # Compute cosine similarity
        similarities = np.dot(embeddings, query_embedding) / (
            np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            results.append({
                'score': float(similarities[idx]),
                'metadata': metadata[idx]
            })
        
        return results
    
    def delete_document(self, document_id: str):
        """
        Delete all chunks for a document
        
        Args:
            document_id: Document ID to delete
        """
        store = self.vector_store
        
        # Find indices to keep
        keep_indices = [
            i for i, m in enumerate(store['metadata'])
            if m.get('document_id') != document_id
        ]
        
        if len(keep_indices) == len(store['metadata']):
            return  # Nothing to delete
        
        # Filter store
        store['embeddings'] = store['embeddings'][keep_indices] if keep_indices else np.array([]).reshape(0, 384)
        store['ids'] = [store['ids'][i] for i in keep_indices]
        store['metadata'] = [store['metadata'][i] for i in keep_indices]
        
        self._save_vector_store()
    
    def get_stats(self) -> Dict[str, int]:
        """Get vector store statistics"""
        store = self.vector_store
        return {
            'total_chunks': len(store['ids']),
            'documents': len(set(m.get('document_id') for m in store['metadata']))
        }


# Global instance
embedding_service = EmbeddingService()
