"""
Validator agent for the AAOIFI Standards Enhancement System.
"""

from typing import Dict, Any, Optional, List
import logging

from langchain.llms.base import BaseLLM
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from pipeline.agents.base_agent import BaseAgent
from pipeline.models.models import KnowledgeRequest

class ValidatorOutput(BaseModel):
    """
    Output from the validator agent.
    """
    
    validated_text: str = Field(
        description="The validated text of the standard"
    )
    quality_score: int = Field(
        description="The quality score for the validation (0-100)"
    )
    notes: str = Field(
        description="Notes about the validation process"
    )
    validation_checks: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of validation checks performed"
    )
    needs_knowledge: bool = Field(
        False,
        description="Whether external knowledge is needed"
    )
    knowledge_query: Optional[str] = Field(
        None,
        description="The query to use for knowledge retrieval"
    )
    final_output: Optional[str] = Field(
        None,
        description="The final output text if validation is successful"
    )

class Validator(BaseAgent):
    """
    Agent responsible for validating the enhanced AAOIFI standard.
    
    This agent:
    - Performs a final QA check before output
    - Checks structure, compliance, language, and logic
    - Ensures the standard is coherent, complete, and compliant
    - Can request Knowledge Retrieval for final verification
    """
    
    def __init__(self, llm: BaseLLM):
        """
        Initialize the validator agent.
        
        Args:
            llm: The language model to use
        """
        super().__init__(
            llm=llm,
            name="validator",
            stage_description="Performs final QA check before output",
        )
        
        self.parser = PydanticOutputParser(pydantic_object=ValidatorOutput)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a specialized AI assistant that validates AAOIFI (Accounting and Auditing Organization for Islamic Financial Institutions) standards. Your task is to perform a final quality assurance check to ensure the standard is coherent, complete, and compliant before it is finalized.

AAOIFI standards are comprehensive documents that provide guidance on Shariah-compliant accounting, auditing, governance, ethics, and Shariah standards for Islamic financial institutions. Your job is to:

1. Verify that the standard is structurally sound and follows AAOIFI's format
2. Ensure that the standard is internally consistent and free of contradictions
3. Check that all Arabic terms are properly transliterated and explained
4. Verify that the standard is Shariah-compliant
5. Perform a final language and grammar check
6. Ensure that all necessary components of the standard are present

If you need to verify any information with external sources, indicate this in your response.

Output should be in the following format:

```
Validated text: (The validated version of the standard)
Quality score: (A score from 0-100 indicating the quality of the validation)
Notes: (Notes about the validation process)
Validation checks: (List of validation checks performed, each with a name, result, and comments)
Needs knowledge: (true/false - whether external knowledge is needed)
Knowledge query: (If needs_knowledge is true, provide a specific query for retrieving the necessary information)
Final output: (If quality score >= 50, provide the final version of the standard)
```

Be thorough in your validation. The standard will only be finalized if the quality score is 50 or higher.

{format_instructions}
"""),
            ("human", "Here is the enhanced AAOIFI standard to validate:\n\n{enhanced_text}")
        ])
        
        self.prompt = self.prompt.partial(
            format_instructions=self.parser.get_format_instructions()
        )
    
    def _should_request_knowledge(self, state: Dict[str, Any]) -> bool:
        """
        Determine whether the validator should request external knowledge.
        
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
        Create a knowledge request for the validator.
        
        Args:
            state: The current state
            
        Returns:
            A knowledge request
        """
        validation_issues = []
        for check in self._output.validation_checks:
            if check.get("result") == "failed":
                validation_issues.append(f"{check.get('name')}: {check.get('comments')}")
        
        return KnowledgeRequest(
            requester=self.name,
            query=self._output.knowledge_query or "",
            context=f"Validating AAOIFI standard. Validation issues: {'; '.join(validation_issues)}",
            timestamp=None,  # This will be set by the base model
        )
    
    def _process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the state.
        
        Args:
            state: The current state
            
        Returns:
            The updated state
        """
        # Format the prompt with the enhanced text
        formatted_prompt = self.prompt.format(enhanced_text=state["enhanced_text"])
        
        # Get the response from the LLM
        response = self.llm.invoke(formatted_prompt)
        
        # Parse the response
        try:
            self._output = self.parser.parse(response.content)
        except Exception as e:
            self.logger.error(f"Error parsing response: {e}")
            self.logger.error(f"Response content: {response.content}")
            
            # Create a fallback output
            self._output = ValidatorOutput(
                validated_text=state["enhanced_text"],
                quality_score=0,
                notes=f"Error parsing response: {e}",
                validation_checks=[{"name": "Parsing", "result": "failed", "comments": str(e)}],
                needs_knowledge=False,
                final_output=None,
            )
        
        # Check if we need knowledge
        if self._should_request_knowledge(state):
            self.logger.info("Validator requesting knowledge")
            
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
                    "validator": self._output.quality_score
                },
                "notes": self._output.notes
            }
        
        # Return the updated state
        result = {
            "validated_text": self._output.validated_text,
            "quality_scores": {
                **state["quality_scores"],
                "validator": self._output.quality_score
            },
            "notes": self._output.notes
        }
        
        # If validation is successful, add the final output
        if self._output.quality_score >= 50 and self._output.final_output:
            result["final_output"] = self._output.final_output
        
        return result
