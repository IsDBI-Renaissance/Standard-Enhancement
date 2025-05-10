"""
Service for LLM operations using Google's Gemini API.
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from utils.gemini_client import GeminiClient
from utils.rag_system import RAGSystem

logger = logging.getLogger(__name__)

class LLMService:
    """Service for handling LLM operations with Gemini."""
    
    def __init__(
        self, 
        gemini_client: Optional[GeminiClient] = None,
        use_rag: bool = True,
        rag_data_dir: Optional[str] = "data"
    ):
        """
        Initialize LLM service.
        
        Args:
            gemini_client: Optional pre-configured Gemini client
            use_rag: Whether to use RAG system (True by default)
            rag_data_dir: Directory containing PDF documents for RAG
        """
        self.client = gemini_client or GeminiClient()
        self.has_rag = False
        
        # Initialize RAG system if enabled
        if use_rag:
            pdf_dir = rag_data_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
            if os.path.exists(pdf_dir):
                try:
                    self.rag_system = RAGSystem(self.client, pdf_dir)
                    logger.info(f"RAG system initialized with documents from {pdf_dir}")
                    self.has_rag = True
                except Exception as e:
                    logger.warning(f"Failed to initialize RAG system: {str(e)}")
            else:
                logger.warning(f"PDF directory {pdf_dir} does not exist, RAG system not initialized")
        else:
            logger.info("RAG system disabled by configuration")
        
    def enhance_text(self, text: str, criteria: Dict[str, Any]) -> str:
        """
        Enhance text according to specified criteria.
        
        Args:
            text: Text to enhance
            criteria: Enhancement criteria
            
        Returns:
            Enhanced text
        """
        system_message = """
        You are a skilled financial standards editor. Your task is to enhance the given text
        according to the specified criteria while preserving the original meaning and intent.
        Focus on clarity, precision, and consistency.
        """
        
        user_message = f"""
        Please enhance the following text according to these criteria:
        {json.dumps(criteria)}
        
        Text to enhance:
        {text}
        """
        
        # Use RAG if available
        if self.has_rag:
            logger.info("Using RAG system for text enhancement")
            
            # Get relevant chunks for logging
            query = "AAOIFI standards enhancement best practices"
            relevant_docs = self.rag_system.retrieve(query, top_k=2)
            logger.info(f"Retrieved {len(relevant_docs)} relevant document chunks for enhancement")
            
            # Include the sources in the prompt
            sources_info = "\n\nThis enhancement is informed by AAOIFI standards documentation from: "
            sources_info += ", ".join([doc['source'] for doc in relevant_docs])
            
            response = self.rag_system.generate_with_context(user_message, system_message)
            
            # Append the sources information at the end of the enhanced text
            return response + sources_info
        else:
            logger.info("RAG system not available for text enhancement")
            prompt = self.client.format_prompt(system_message, user_message)
            return self.client.get_completion_text(prompt)
        
    def analyze_quality(self, text: str, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the quality of text according to criteria.
        
        Args:
            text: Text to analyze
            criteria: Quality criteria
            
        Returns:
            Analysis results including scores and feedback
        """
        system_message = """
        You are a financial standards quality analyzer. Evaluate the given text against the 
        specified criteria and provide scores and detailed feedback.
        """
        
        user_message = f"""
        Analyze the quality of the following text according to these criteria:
        {json.dumps(criteria)}
        
        Text to analyze:
        {text}
        
        Provide your response as a JSON object with:
        1. "scores" - a dictionary mapping each criterion to a score (0-100)
        2. "overall_score" - the weighted average score
        3. "feedback" - detailed feedback for each criterion
        4. "improvements" - specific improvement recommendations
        """
        
        # Get response (using RAG if available)
        if self.has_rag:
            response = self.rag_system.generate_with_context(user_message, system_message)
        else:
            prompt = self.client.format_prompt(system_message, user_message)
            response = self.client.get_completion_text(prompt)
        
        try:
            # Extract the JSON part from the response
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
                
            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError) as e:
            logger.warning(f"Failed to parse JSON from response: {str(e)}")
            # Fallback: return basic structure
            return {
                "overall_score": 70,
                "scores": {},
                "feedback": "Failed to parse detailed feedback",
                "improvements": ["Consider manual review"]
            }
