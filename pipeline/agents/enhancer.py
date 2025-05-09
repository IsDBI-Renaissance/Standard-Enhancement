"""
Enhancer agent for the AAOIFI Standards Enhancement System.
"""

import logging
import re
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from pydantic import BaseModel, Field

from pipeline.agents.base_agent import BaseAgent
from pipeline.models.models import KnowledgeRequest, AuditEntry

class EnhancerOutput(BaseModel):
    """
    Output from the enhancer agent.
    """
    
    enhanced_text: str = Field(
        description="The enhanced text of the standard"
    )
    quality_score: int = Field(
        description="The quality score for the enhancement (0-100)"
    )
    notes: str = Field(
        description="Notes about the enhancement"
    )
    improvements: List[str] = Field(
        default_factory=list,
        description="List of improvements made to the standard"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="List of recommendations for further enhancement"
    )
    needs_knowledge: bool = Field(
        False,
        description="Whether external knowledge is needed"
    )
    knowledge_query: Optional[str] = Field(
        None,
        description="The query to use for knowledge retrieval"
    )

class Enhancer(BaseAgent):
    """
    Agent responsible for enhancing the AAOIFI standard.
    
    This agent:
    - Improves language and clarity
    - Enhances structure and formatting
    - Makes recommendations for further improvement
    """
    
    def __init__(self, llm: ChatOpenAI):
        """
        Initialize the enhancer agent.
        
        Args:
            llm: The language model to use
        """
        super().__init__(
            llm=llm,
            name="enhancer",
            stage_description="Improves the standard for clarity, completeness, and compliance",
        )
        
        self.parser = PydanticOutputParser(pydantic_object=EnhancerOutput)
        self.fixing_parser = OutputFixingParser.from_llm(parser=self.parser, llm=llm)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a specialized AI assistant that enhances AAOIFI (Accounting and Auditing Organization for Islamic Financial Institutions) standards. Your task is to improve the language, clarity, and completeness of the standard.

Your enhancements should focus on:
1. Improving clarity and readability
2. Adding any missing elements
3. Ensuring consistency in terminology and formatting
4. Maintaining strict Shariah compliance
5. Relevant use cases in Islamic finance
6. Applicable jurisprudence (Fiqh) references
7. Other AAOIFI standards for cross-referencing

IMPORTANT: You MUST return a valid JSON object with the following fields:
- enhanced_text: The enhanced version of the standard
- quality_score: A score from 0-100 indicating the quality of the enhancement (MUST be a number)
- notes: Notes about the enhancement process
- improvements: Array of improvements made to the standard
- recommendations: Array of recommendations for further enhancement
- needs_knowledge: Boolean indicating whether external knowledge is needed
- knowledge_query: If needs_knowledge is true, provide a specific query

Remember that your output needs to be parseable as JSON.

{format_instructions}
"""),
            ("human", "Here is the reviewed AAOIFI standard to enhance:\n\n{reviewed_text}")
        ])
        
        self.prompt = self.prompt.partial(
            format_instructions=self.parser.get_format_instructions()
        )
        
        # Initialize audit information
        self.audit_info = {
            "start_time": None,
            "end_time": None,
            "tools_used": [],
            "processing_steps": [],
            "justification": "",
            "improvements": [],
            "recommendations": []
        }
    
    def _extract_quality_score(self, text: str) -> int:
        """
        Extract the quality score from a text response.
        
        Args:
            text: The text to extract the quality score from
            
        Returns:
            The quality score, or 70 as a default
        """
        # Try to find "Quality score: X" pattern
        quality_match = re.search(r'Quality score:\s*(\d+)', text)
        if quality_match:
            try:
                return int(quality_match.group(1))
            except ValueError:
                pass
        
        # Default to a reasonable score to avoid infinite loops
        import os
        default_score = int(os.environ.get("DEFAULT_QUALITY_SCORE", "70"))
        self.logger.warning(f"Could not extract quality score, using default: {default_score}")
        return default_score
    
    def _extract_enhanced_text(self, text: str) -> str:
        """
        Extract the enhanced text from a text response.
        
        Args:
            text: The text to extract the enhanced text from
            
        Returns:
            The enhanced text, or the original text as a fallback
        """
        # Try to find the enhanced text between "Enhanced text:" and the next section
        enhanced_match = re.search(r'Enhanced text:\s*([\s\S]+?)(?:Quality score:|$)', text)
        if enhanced_match:
            return enhanced_match.group(1).strip()
        
        # If no match, just return the whole text
        return text.strip()
    
    def _extract_json_from_response(self, text: str) -> str:
        """
        Extract JSON content from a text that might contain markdown or other formatting.
        
        Args:
            text: The text to extract JSON from
            
        Returns:
            The extracted JSON string or the original text if no JSON found
        """
        # Try to find JSON content between triple backticks
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if json_match:
            return json_match.group(1).strip()
        
        # Try to find JSON content between curly braces
        json_match = re.search(r'(\{[\s\S]*\})', text)
        if json_match:
            return json_match.group(1).strip()
        
        return text
    
    def _parse_unstructured_response(self, response: str) -> EnhancerOutput:
        """
        Parse an unstructured response into an EnhancerOutput.
        
        Args:
            response: The unstructured response
            
        Returns:
            An EnhancerOutput object
        """
        enhanced_text = self._extract_enhanced_text(response)
        quality_score = self._extract_quality_score(response)
        
        # Extract notes if possible
        notes_match = re.search(r'Notes:\s*([\s\S]+?)(?:Improvements:|Recommendations:|Needs knowledge:|$)', response)
        notes = notes_match.group(1).strip() if notes_match else "Extracted from unstructured response"
        
        # Extract improvements if possible
        improvements = []
        improvements_match = re.search(r'Improvements:\s*(?:(\d+\.\s*[^\n]+\n)+)', response)
        if improvements_match:
            improvements_text = improvements_match.group(0)
            improvements = re.findall(r'\d+\.\s*([^\n]+)', improvements_text)
        
        # Extract recommendations if possible
        recommendations = []
        recommendations_match = re.search(r'Recommendations:\s*(?:(\d+\.\s*[^\n]+\n)+)', response)
        if recommendations_match:
            recommendations_text = recommendations_match.group(0)
            recommendations = re.findall(r'\d+\.\s*([^\n]+)', recommendations_text)
        
        # Extract needs_knowledge if possible
        needs_knowledge = False
        needs_knowledge_match = re.search(r'Needs knowledge:\s*(true|false)', response, re.IGNORECASE)
        if needs_knowledge_match:
            needs_knowledge = needs_knowledge_match.group(1).lower() == 'true'
        
        # Extract knowledge_query if possible
        knowledge_query = None
        if needs_knowledge:
            knowledge_query_match = re.search(r'Knowledge query:\s*([^\n]+)', response)
            if knowledge_query_match:
                knowledge_query = knowledge_query_match.group(1).strip()
        
        return EnhancerOutput(
            enhanced_text=enhanced_text,
            quality_score=quality_score,
            notes=notes,
            improvements=improvements,
            recommendations=recommendations,
            needs_knowledge=needs_knowledge,
            knowledge_query=knowledge_query
        )
    
    def _should_request_knowledge(self, state: Dict[str, Any]) -> bool:
        """
        Determine whether the enhancer should request external knowledge.
        
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
        Create a knowledge request for the enhancer.
        
        Args:
            state: The current state
            
        Returns:
            A knowledge request
        """
        # Record tool usage in audit info
        self.audit_info["tools_used"].append({
            "tool": "knowledge_retrieval",
            "timestamp": datetime.now().isoformat(),
            "reason": f"External knowledge needed for: {self._output.knowledge_query}",
            "query": self._output.knowledge_query or ""
        })
        
        return KnowledgeRequest(
            requester=self.name,
            query=self._output.knowledge_query or "",
            context=f"Enhancing AAOIFI standard.",
            timestamp=datetime.now()
        )
    
    def _get_audit_entry(self) -> Dict[str, Any]:
        """
        Get a detailed audit entry for the enhancer processing.
        
        Returns:
            A dictionary with detailed audit information
        """
        return {
            "stage": self.name,
            "start_time": self.audit_info["start_time"],
            "end_time": self.audit_info["end_time"],
            "quality_score": getattr(self, "_output", None) and self._output.quality_score or 0,
            "tools_used": self.audit_info["tools_used"],
            "processing_steps": self.audit_info["processing_steps"],
            "justification": self.audit_info["justification"],
            "improvements": self.audit_info["improvements"],
            "recommendations": self.audit_info["recommendations"]
        }
    
    def _process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the state.
        
        Args:
            state: The current state
            
        Returns:
            The updated state
        """
        # Reset audit info for this processing run
        self.audit_info = {
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "tools_used": [],
            "processing_steps": [],
            "justification": "",
            "improvements": [],
            "recommendations": []
        }
        
        # Record the processing step
        self.audit_info["processing_steps"].append({
            "step": "initialization",
            "timestamp": datetime.now().isoformat(),
            "description": "Enhancer agent initialized with reviewed standard text"
        })
        
        # Format the prompt with the reviewed text
        reviewed_text = state.get("reviewed_text", state.get("preprocessed_text", state.get("standard_text", "")))
        
        formatted_prompt = self.prompt.format(reviewed_text=reviewed_text)
        
        # Record the processing step
        self.audit_info["processing_steps"].append({
            "step": "prompt_creation",
            "timestamp": datetime.now().isoformat(),
            "description": "Created prompt for LLM to enhance the standard"
        })
        
        # Get the response from the LLM
        response = self.llm.invoke(formatted_prompt)
        self.logger.debug(f"Raw response: {response.content}")
        
        # Record the processing step
        self.audit_info["processing_steps"].append({
            "step": "llm_response",
            "timestamp": datetime.now().isoformat(),
            "description": "Received response from LLM"
        })
        
        # Parse the response
        parsing_method = "unknown"
        try:
            # First, try to extract JSON from the response
            json_content = self._extract_json_from_response(response.content)
            self.logger.debug(f"Extracted JSON: {json_content}")
            
            # Try standard parsing first
            try:
                self._output = self.parser.parse(json_content)
                parsing_method = "standard_parser"
                self.logger.info("Successfully parsed output with standard parser")
            except Exception as e:
                self.logger.warning(f"Standard parsing failed: {e}, trying fixing parser")
                # If regular parsing fails, try the fixing parser
                try:
                    self._output = self.fixing_parser.parse(json_content)
                    parsing_method = "fixing_parser"
                    self.logger.info("Successfully parsed output with fixing parser")
                except Exception as fix_e:
                    self.logger.warning(f"Fixing parser failed: {fix_e}, trying manual parsing")
                    # If fixing parser fails, try to parse as regular JSON
                    try:
                        json_obj = json.loads(json_content)
                        self._output = EnhancerOutput(**json_obj)
                        parsing_method = "manual_json_parsing"
                        self.logger.info("Successfully parsed output with manual JSON parsing")
                    except Exception as json_e:
                        # If all JSON parsing fails, try unstructured parsing
                        self.logger.warning(f"Manual JSON parsing failed: {json_e}, falling back to unstructured parsing")
                        self._output = self._parse_unstructured_response(response.content)
                        parsing_method = "unstructured_parsing"
                        self.logger.info("Successfully parsed output with unstructured parsing")
            
            # Record successful parsing and store relevant information
            self.audit_info["processing_steps"].append({
                "step": "parsing",
                "timestamp": datetime.now().isoformat(),
                "description": f"Successfully parsed LLM response using {parsing_method}",
                "success": True
            })
            
            # Store improvements and recommendations
            if hasattr(self._output, "improvements"):
                self.audit_info["improvements"] = self._output.improvements
            
            if hasattr(self._output, "recommendations"):
                self.audit_info["recommendations"] = self._output.recommendations
            
            # Create justification
            self.audit_info["justification"] = (
                f"The enhancer improved the standard with a quality score of {self._output.quality_score}. "
                f"The enhancements were focused on improving clarity, consistency, and completeness. "
                f"The LLM response was successfully parsed using {parsing_method}."
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing response: {e}")
            self.logger.error(f"Response content: {response.content}")
            
            # Record parsing failure
            self.audit_info["processing_steps"].append({
                "step": "parsing",
                "timestamp": datetime.now().isoformat(),
                "description": f"Failed to parse LLM response: {str(e)}",
                "success": False,
                "error": str(e)
            })
            
            # Create a fallback output
            import os
            default_score = int(os.environ.get("DEFAULT_QUALITY_SCORE", "70"))
            
            self._output = EnhancerOutput(
                enhanced_text=reviewed_text,
                quality_score=default_score,
                notes=f"Error parsing response: {e}",
                improvements=["Unable to enhance standard due to parsing error"],
                recommendations=["Review original standard manually"],
                needs_knowledge=False,
            )
            
            # Store improvements and recommendations
            self.audit_info["improvements"] = self._output.improvements
            self.audit_info["recommendations"] = self._output.recommendations
            
            # Create justification for fallback
            self.audit_info["justification"] = (
                f"The enhancer encountered an error while parsing the LLM response: {str(e)}. "
                f"A fallback quality score of {default_score} was assigned. "
                f"No enhancements were made to the original text."
            )
        
        self.logger.info(f"Enhancer quality score: {self._output.quality_score}")
        
        # Set the end time
        self.audit_info["end_time"] = datetime.now().isoformat()
        
        # Check if we need knowledge
        if self._should_request_knowledge(state):
            self.logger.info("Enhancer requesting knowledge")
            
            # Create a knowledge request
            knowledge_request = self._create_knowledge_request(state)
            
            # Add the knowledge request to the state
            state["knowledge_request"] = knowledge_request
            state["knowledge_requests"].append(knowledge_request)
            
            # Update the state with audit information
            return {
                "knowledge_request": knowledge_request,
                "quality_scores": {
                    **state["quality_scores"],
                    "enhancer": self._output.quality_score
                },
                "notes": self._output.notes,
                "audit_entry": self._get_audit_entry()
            }
        
        # Return the updated state with audit information
        return {
            "enhanced_text": self._output.enhanced_text,
            "quality_scores": {
                **state["quality_scores"],
                "enhancer": self._output.quality_score
            },
            "notes": self._output.notes,
            "audit_entry": self._get_audit_entry()
        }
