"""
Utility for interacting with Google's Gemini API.
"""
import os
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class GeminiClient:
    """Client for interacting with Google's Gemini API."""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
            
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
        self.temperature = float(os.getenv("TEMPERATURE", 0.7))
        self.max_output_tokens = int(os.getenv("MAX_OUTPUT_TOKENS", 2048))
        self.top_p = float(os.getenv("TOP_P", 0.9))
        self.top_k = int(os.getenv("TOP_K", 40))
        
        # Initialize Gemini client
        genai.configure(api_key=self.api_key)
        
        # Set up generation config
        self.generation_config = {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "max_output_tokens": self.max_output_tokens,
        }
        
        # Initialize the model
        self.model = genai.GenerativeModel(model_name=self.model_name)
        
    def get_completion(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Get completion from Gemini API.
        
        Args:
            prompt: The prompt to complete
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            API response
        """
        try:
            # Update generation config with any provided overrides
            generation_config = self.generation_config.copy()
            if "temperature" in kwargs:
                generation_config["temperature"] = kwargs.pop("temperature")
            if "max_output_tokens" in kwargs:
                generation_config["max_output_tokens"] = kwargs.pop("max_output_tokens")
            if "top_p" in kwargs:
                generation_config["top_p"] = kwargs.pop("top_p")
            if "top_k" in kwargs:
                generation_config["top_k"] = kwargs.pop("top_k")
            
            # Call the Gemini API
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config,
                **kwargs
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}")
            raise
    
    def extract_text(self, response: Any) -> str:
        """
        Extract the generated text from a Gemini API response.
        
        Args:
            response: API response from Gemini
            
        Returns:
            Generated text
        """
        try:
            return response.text
        except (AttributeError, IndexError, KeyError) as e:
            logger.error(f"Error extracting text from Gemini API response: {str(e)}")
            return ""
            
    def get_completion_text(self, prompt: str, **kwargs) -> str:
        """
        Get completion and extract text in one call.
        
        Args:
            prompt: The prompt to complete
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            Generated text
        """
        response = self.get_completion(prompt, **kwargs)
        return self.extract_text(response)
        
    def format_prompt(self, system_message: str, user_message: str) -> str:
        """
        Format prompt for Gemini models.
        
        Args:
            system_message: System message/instructions
            user_message: User's input message
            
        Returns:
            Formatted prompt string suitable for Gemini models
        """
        # For Gemini, we can simply combine the system and user messages
        return f"{system_message}\n\n{user_message}"
