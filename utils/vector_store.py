"""
Vector store for document retrieval.
"""
import os
import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import pickle
from datetime import datetime

logger = logging.getLogger(__name__)

class VectorStore:
    """
    Simple vector store for document retrieval.
    """
    
    def __init__(self, embedding_provider=None):
        """
        Initialize the vector store.
        
        Args:
            embedding_provider: Object that provides embeddings for text
        """
        self.documents = []
        self.embeddings = []
        self.embedding_provider = embedding_provider
        
    def add_documents(self, documents: List[Dict[str, Any]]):
        """
        Add documents to the vector store and generate embeddings.
        
        Args:
            documents: List of document chunks with text and metadata
        """
        for doc in documents:
            # Generate embedding for the document text
            embedding = self.get_embedding(doc["text"])
            
            if embedding is not None:
                self.documents.append(doc)
                self.embeddings.append(embedding)
        
        logger.info(f"Added {len(documents)} documents to the vector store")
    
    def get_embedding(self, text: str) -> np.ndarray:
        """
        Get embedding for text using the embedding provider.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as numpy array
        """
        try:
            if self.embedding_provider:
                return self.embedding_provider.get_embedding(text)
            else:
                # Fallback to simple embedding if no provider is available
                # This is just a placeholder - in practice, you'd use a proper embedding model
                # or the embedding capabilities of Gemini API
                return np.ones(768) / np.sqrt(768)  # Normalized vector of ones
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for documents similar to the query.
        
        Args:
            query: Query text
            top_k: Number of top results to return
            
        Returns:
            List of document chunks with similarity scores
        """
        if not self.documents or not self.embeddings:
            logger.warning("Vector store is empty")
            return []
        
        # Get query embedding
        query_embedding = self.get_embedding(query)
        if query_embedding is None:
            return []
        
        # Convert list of embeddings to numpy array for efficient computation
        embeddings_array = np.array(self.embeddings)
        
        # Compute cosine similarity
        similarities = np.dot(embeddings_array, query_embedding) / (
            np.linalg.norm(embeddings_array, axis=1) * np.linalg.norm(query_embedding)
        )
        
        # Get indices of top k results
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        # Return top k documents with similarity scores
        results = []
        for idx in top_indices:
            doc = self.documents[idx].copy()
            doc["similarity"] = float(similarities[idx])
            results.append(doc)
        
        return results
    
    def save(self, filepath: str):
        """
        Save the vector store to disk.
        
        Args:
            filepath: Path to save the vector store
        """
        data = {
            "documents": self.documents,
            "embeddings": self.embeddings,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        
        logger.info(f"Vector store saved to {filepath}")
    
    def load(self, filepath: str):
        """
        Load the vector store from disk.
        
        Args:
            filepath: Path to load the vector store from
        """
        if not os.path.exists(filepath):
            logger.warning(f"Vector store file {filepath} does not exist")
            return False
        
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            
            self.documents = data["documents"]
            self.embeddings = data["embeddings"]
            
            logger.info(f"Vector store loaded from {filepath} with {len(self.documents)} documents")
            return True
        except Exception as e:
            logger.error(f"Error loading vector store: {str(e)}")
            return False
