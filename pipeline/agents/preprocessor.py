"""
Preprocessor agent for the AAOIFI Standards Enhancement System.
"""

from typing import Dict, Any, Optional, List
import logging
import re

from langchain.llms.base import BaseLLM
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from pipeline.agents.base_agent import BaseAgent
from pipeline.models.models import KnowledgeRequest

class PreprocessorOutput(BaseModel):
    """
    Output from the preprocessor agent.
    """
    
    preprocessed_text: str = Field(
        description="The preprocessed text of the standard"
    )
    quality_score: int = Field(
        description="The quality score for the preprocessing (0-100)"
    )
    notes: str = Field(
        description="Notes about the preprocessing"
    )
    missing_elements: List[str] = Field(
        default_factory=list,
        description="List of elements that are missing from the standard"
    )
    needs_knowledge: bool = Field(
        False,
        description="Whether external knowledge is needed"
    )
    knowledge_query: Optional[str] = Field(
        None,
        description="The query to use for knowledge retrieval"
    )

class Preprocessor(BaseAgent):
    """
    Agent responsible for preprocessing the AAOIFI standard.
    
    This agent:
    - Parses and structures the input
    - Flags missing content or structure
    - Can request Knowledge Retrieval if gaps are found
    """
    
    def __init__(self, llm: BaseLLM):
        """
        Initialize the preprocessor agent.
        
        Args:
            llm: The language model to use
        """
        super().__init__(
            llm=llm,
            name="preprocessor",
            stage_description="Parses and structures the input standard",
        )
        
        self.parser = PydanticOutputParser(pydantic_object=PreprocessorOutput)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a specialized AI assistant that preprocesses AAOIFI (Accounting and Auditing Organization for Islamic Financial Institutions) standards. Your task is to parse and structure the input text to prepare it for review and enhancement.

AAOIFI standards are comprehensive documents that provide guidance on Shariah-compliant accounting, auditing, governance, ethics, and Shariah standards for Islamic financial institutions. Your job is to:

1. Identify and structure the different sections of the standard (e.g., introduction, scope, definitions, requirements, examples, etc.)
2. Flag any missing content or structure that should be present in a well-formed AAOIFI standard
3. Ensure all Arabic terms are properly transliterated and explained
4. Check for any obvious formatting or structural issues

If you find that the input is missing critical information that could be obtained from external sources, indicate this in your response.

Output should be in the following format:

```
Preprocessed text: (The structured version of the input text)
Quality score: (A score from 0-100 indicating the quality of the preprocessing)
Notes: (Notes about the preprocessing process, including any issues found)
Missing elements: (List any elements that are missing from the standard)
Needs knowledge: (true/false - whether external knowledge is needed)
Knowledge query: (If needs_knowledge is true, provide a specific query for retrieving the necessary information)
```

Be thorough but concise in your preprocessing.

{format_instructions}
"""),
            ("human", "Here is the AAOIFI standard to preprocess:\n\n{standard_text}")
        ])
        
        self.prompt = self.prompt.partial(
            format_instructions=self.parser.get_format_instructions()
        )
    
    def _should_request_knowledge(self, state: Dict[str, Any]) -> bool:
        """
        Determine whether the preprocessor should request external knowledge.
        
        Args:
            state: The current state
            
        Returns:
            True if knowledge should be requested, False otherwise
        """
        # If we've already processed the state, check if we need knowledge
        if hasattr(self, "_output") and self._output.needs_knowledge:
            return True
        
        return False
    
    def _create_knowledge_request(self, state: Dict[str, Any]) -> KnowledgeRequest:
        """
        Create a knowledge request for the preprocessor.
        
        Args:
            state: The current state
            
        Returns:
            A knowledge request
        """
        # Explicitly create with current timestamp to avoid validation errors
        from datetime import datetime
        
        return KnowledgeRequest(
            requester=self.name,
            query=self._output.knowledge_query or "",
            context=f"Preprocessing AAOIFI standard. Missing elements: {', '.join(self._output.missing_elements)}",
            timestamp=datetime.now(),  # Explicitly set the timestamp
            additional_params={}
        )
    
    def _process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the state.
        
        Args:
            state: The current state
            
        Returns:
            The updated state
        """
        # Format the prompt with the standard text
        formatted_prompt = self.prompt.format(standard_text=state["standard_text"])
        
        # Get the response from the LLM
        response = self.llm.invoke(formatted_prompt)
        
        # Parse the response
        try:
            self._output = self.parser.parse(response.content)
        except Exception as e:
            self.logger.error(f"Error parsing response: {e}")
            self.logger.error(f"Response content: {response.content}")
            
            # Create a fallback output
            self._output = PreprocessorOutput(
                preprocessed_text=state["standard_text"],
                quality_score=0,
                notes=f"Error parsing response: {e}",
                missing_elements=["Unable to process standard"],
                needs_knowledge=False,
            )
        
        # Check if we need knowledge
        if self._should_request_knowledge(state):
            self.logger.info("Preprocessor requesting knowledge")
            
            # Create a knowledge request
            knowledge_request = self._create_knowledge_request(state)
            
            # Add the knowledge request to the state
            state["knowledge_request"] = knowledge_request
            state["knowledge_requests"].append(knowledge_request)
            
            # Return the state with the knowledge request
            return {
                "knowledge_request": knowledge_request,
                "quality_scores": {
                    **state["quality_scores"],
                    "preprocessor": self._output.quality_score
                },
                "notes": self._output.notes
            }
        
        # Return the updated state
        return {
            "preprocessed_text": self._output.preprocessed_text,
            "quality_scores": {
                **state["quality_scores"],
                "preprocessor": self._output.quality_score
            },
            "notes": self._output.notes
        }
