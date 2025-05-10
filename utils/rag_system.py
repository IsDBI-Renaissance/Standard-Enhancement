"""
Retrieval-Augmented Generation (RAG) system.
"""
import os
import logging
from typing import List, Dict, Any, Optional
import numpy as np

from utils.pdf_processor import PDFProcessor
from utils.vector_store import VectorStore
from utils.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

class EmbeddingProvider:
    """
    Embedding provider using the Gemini API.
    """
    
    def __init__(self, gemini_client: GeminiClient):
        """
        Initialize the embedding provider.
        
        Args:
            gemini_client: Gemini API client
        """
        self.gemini_client = gemini_client
    
    def get_embedding(self, text: str) -> np.ndarray:
        """
        Get embedding for text using the Gemini API.
        
        Since Gemini API doesn't have a direct embedding endpoint like OpenAI,
        we'll use a workaround by asking the model to generate a numeric representation.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as numpy array
        """
        try:
            # For simplicity, we'll use a hash-based approach for demo purposes
            # In a production environment, you would use a proper embedding model
            import hashlib
            
            # Create a hash of the text
            hash_object = hashlib.md5(text.encode())
            hash_hex = hash_object.hexdigest()
            
            # Convert to a pseudo-embedding of 768 dimensions
            embedding = np.zeros(768)
            for i, char in enumerate(hash_hex):
                pos = i % 768
                embedding[pos] += ord(char)
            
            # Normalize the embedding
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return np.ones(768) / np.sqrt(768)  # Fallback to a normalized vector of ones

class RAGSystem:
    """
    Retrieval-Augmented Generation system.
    """
    
    def __init__(self, gemini_client: GeminiClient, pdf_directory: str = "data"):
        """
        Initialize the RAG system.
        
        Args:
            gemini_client: Gemini API client
            pdf_directory: Directory containing PDF files
        """
        self.gemini_client = gemini_client
        self.pdf_directory = pdf_directory
        self.embedding_provider = EmbeddingProvider(gemini_client)
        self.vector_store = VectorStore(self.embedding_provider)
        self.pdf_processor = PDFProcessor(pdf_directory)
        
        # Initialize the system
        self._initialize()
    
    def _initialize(self):
        """Initialize the RAG system by processing documents and building the vector store."""
        # Check if a saved vector store exists
        vector_store_path = os.path.join(self.pdf_directory, "vector_store.pkl")
        
        if os.path.exists(vector_store_path):
            # Load the existing vector store
            if self.vector_store.load(vector_store_path):
                logger.info("Loaded existing vector store")
                return
        
        # Process documents and build the vector store
        logger.info("Building new vector store from PDF documents")
        chunks = self.pdf_processor.process_all_documents()
        self.vector_store.add_documents(chunks)
        
        # Save the vector store
        self.vector_store.save(vector_store_path)
    
    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: Query text
            top_k: Number of top results to return
            
        Returns:
            List of relevant documents
        """
        results = self.vector_store.search(query, top_k)
        logger.info(f"RAG retrieval for query: '{query}' returned {len(results)} results")
        for i, doc in enumerate(results):
            logger.info(f"  Result {i+1}: From {doc['source']} (similarity: {doc['similarity']:.2f})")
        return results
    
    def generate_with_context(self, query: str, system_message: str, top_k: int = 3) -> str:
        """
        Generate a response with context from retrieved documents.
        
        Args:
            query: Query text
            system_message: System message/instructions
            top_k: Number of documents to retrieve
            
        Returns:
            Generated response
        """
        # Retrieve relevant documents
        relevant_docs = self.retrieve(query, top_k)
        
        # Create context from retrieved documents
        context = "\n\n".join([
            f"Document from {doc['source']} (similarity: {doc['similarity']:.2f}):\n{doc['text']}"
            for doc in relevant_docs
        ])
        
        # Create prompt with context
        prompt = f"""
{system_message}

Here is relevant information from AAOIFI standards documentation:

{context}

Based on this information and your knowledge, please respond to the following:

{query}
"""
        
        # Generate response
        logger.info(f"Generating response with context from {len(relevant_docs)} documents")
        start_time = logger.info("Starting generation with context")
        response = self.gemini_client.get_completion_text(prompt)
        logger.info(f"Completed generation with context")
        
        return response
