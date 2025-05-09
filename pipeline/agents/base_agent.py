"""
Base agent for the AAOIFI Standards Enhancement System.
"""

import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from langchain_openai import ChatOpenAI

class BaseAgent(ABC):
    """
    Base class for all agents in the AAOIFI Standards Enhancement System.
    
    All agents should inherit from this class and implement the _process method.
    """
    
    def __init__(
        self, 
        llm: ChatOpenAI,
        name: str,
        stage_description: str
    ):
        """
        Initialize the base agent.
        
        Args:
            llm: The language model to use
            name: The name of the agent
            stage_description: A description of the agent's stage in the pipeline
        """
        self.llm = llm
        self.name = name
        self.stage_description = stage_description
        self.logger = logging.getLogger(f"agent.{name}")
    
    @abstractmethod
    def _process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the state.
        
        Args:
            state: The current state
            
        Returns:
            The updated state
        """
        pass
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make the agent callable.
        
        Args:
            state: The current state
            
        Returns:
            The updated state
        """
        return self._process(state)
