"""
Orchestrator module for the AAOIFI Standards Enhancement System.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import re
# Update import to use langchain_openai instead of langchain_community
from langchain_openai import ChatOpenAI

from pipeline.agents.preprocessor import Preprocessor
from pipeline.agents.reviewer import Reviewer
from pipeline.agents.enhancer import Enhancer
from pipeline.agents.validator import Validator
# Temporarily comment out the knowledge retrieval tool until we create it
from pipeline.tools.knowledge_retrieval import KnowledgeRetrievalTool

class AAOIFIOrchestrator:
    """
    Orchestrator for the AAOIFI Standards Enhancement System.
    
    The orchestrator:
    - Manages the flow between the various agents
    - Maintains a persistent context
    - Makes decisions based on quality scores
    """
    
    def __init__(
        self, 
        llm_model_name: str = "gpt-4",
        max_retries: int = 5,
        default_quality_score: int = 60,
        quality_threshold: int = 50
    ):
        """
        Initialize the orchestrator.
        
        Args:
            llm_model_name: The name of the LLM model to use
            max_retries: Maximum number of retries for each stage before giving up
            default_quality_score: Default quality score to use when parsing fails
            quality_threshold: Minimum quality score required to proceed to the next stage
        """
        self.logger = logging.getLogger("pipeline.orchestrator")
        self.llm = ChatOpenAI(model_name=llm_model_name, temperature=0.7)
        
        # Set configuration parameters
        self.max_retries = max_retries
        self.default_quality_score = default_quality_score
        self.quality_threshold = quality_threshold
        
        # Set environment variables for agents to use
        import os
        os.environ["DEFAULT_QUALITY_SCORE"] = str(default_quality_score)
        
        # Initialize the agents
        self.preprocessor = Preprocessor(llm=self.llm)
        self.reviewer = Reviewer(llm=self.llm)
        self.enhancer = Enhancer(llm=self.llm)
        self.validator = Validator(llm=self.llm)
        
        # Initialize the knowledge retrieval tool
        self.knowledge_retrieval = KnowledgeRetrievalTool(llm=self.llm)
        
        self.retry_counts = {
            "preprocessor": 0,
            "reviewer": 0,
            "enhancer": 0,
            "validator": 0
        }
        
    def _initialize_state(self, standard_text: str) -> Dict[str, Any]:
        """
        Initialize the state for the pipeline.
        
        Args:
            standard_text: The text of the standard to process
            
        Returns:
            The initial state
        """
        from datetime import datetime
        import uuid
        
        return {
            "standard_text": standard_text,
            "preprocessed_text": "",
            "reviewed_text": "",
            "enhanced_text": "",
            "validated_text": "",
            "final_output": "",
            "quality_scores": {},
            "knowledge_requests": [],
            "knowledge_request": None,
            "knowledge_response": None,
            "notes": "",
            "audit_trail": "",
            "timestamp": datetime.now(),  # Add timestamp for when processing started
            "session_id": str(uuid.uuid4()),  # Add unique session ID
            "tool_usage": {},  # Track tool usage throughout the pipeline
        }
    
    def _handle_knowledge_request(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a knowledge request.
        
        Args:
            state: The current state
            
        Returns:
            The updated state
        """
        # Check if there's a knowledge request in the state
        if state.get("knowledge_request"):
            self.logger.info(f"Knowledge request detected but knowledge retrieval is not implemented yet")
            self.logger.info(f"Clearing knowledge request and continuing")
            
            # Update the state with a placeholder response
            state["knowledge_response"] = {"content": "Knowledge retrieval not implemented yet"}
            
            # Clear the knowledge request
            state["knowledge_request"] = None
        
        return state
    
    def _update_audit_trail(self, state: Dict[str, Any], stage: str, message: str, audit_entry: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Update the audit trail in the state with detailed information.
        
        Args:
            state: The current state
            stage: The stage to add to the audit trail
            message: The message to add to the audit trail
            audit_entry: Optional detailed audit entry from the agent
            
        Returns:
            The updated state
        """
        # Build the basic audit entry
        markdown_entry = f"## {stage.capitalize()}\n\n"
        
        # Add timestamp
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        markdown_entry += f"**Timestamp:** {timestamp}\n\n"
        
        # Add the basic message
        markdown_entry += f"{message}\n\n"
        
        # Add quality score if available
        if "quality_scores" in state and stage.lower() in state["quality_scores"]:
            markdown_entry += f"**Quality score:** {state['quality_scores'][stage.lower()]}\n\n"
        
        # Add detailed audit information if available
        if audit_entry:
            # Add processing timeline
            if "start_time" in audit_entry and "end_time" in audit_entry:
                markdown_entry += f"**Processing time:** {audit_entry['start_time']} to {audit_entry['end_time']}\n\n"
            
            # Add justification if available
            if "justification" in audit_entry and audit_entry["justification"]:
                markdown_entry += f"### Justification\n\n{audit_entry['justification']}\n\n"
            
            # Add processing steps if available
            if "processing_steps" in audit_entry and audit_entry["processing_steps"]:
                markdown_entry += f"### Processing Steps\n\n"
                for i, step in enumerate(audit_entry["processing_steps"], 1):
                    markdown_entry += f"{i}. **{step['step']}** ({step['timestamp']}): {step['description']}\n"
                    if "success" in step and not step["success"]:
                        markdown_entry += f"   - Error: {step.get('error', 'Unknown error')}\n"
                markdown_entry += "\n"
            
            # Add tools used if available
            if "tools_used" in audit_entry and audit_entry["tools_used"]:
                markdown_entry += f"### Tools Used\n\n"
                for i, tool in enumerate(audit_entry["tools_used"], 1):
                    markdown_entry += f"{i}. **{tool['tool']}** ({tool['timestamp']})\n"
                    markdown_entry += f"   - Reason: {tool['reason']}\n"
                    if "query" in tool and tool["query"]:
                        markdown_entry += f"   - Query: {tool['query']}\n"
                    if "result" in tool and tool["result"]:
                        markdown_entry += f"   - Result: {tool['result']}\n"
                markdown_entry += "\n"
            
            # Add improvements if available
            if "improvements" in audit_entry and audit_entry["improvements"]:
                markdown_entry += f"### Improvements Made\n\n"
                for i, improvement in enumerate(audit_entry["improvements"], 1):
                    markdown_entry += f"{i}. {improvement}\n"
                markdown_entry += "\n"
            
            # Add recommendations if available
            if "recommendations" in audit_entry and audit_entry["recommendations"]:
                markdown_entry += f"### Recommendations\n\n"
                for i, recommendation in enumerate(audit_entry["recommendations"], 1):
                    markdown_entry += f"{i}. {recommendation}\n"
                markdown_entry += "\n"
        
        # Append the entry to the audit trail
        state["audit_trail"] += markdown_entry
        
        return state
    
    def _count_sections(self, text: str) -> int:
        """
        Count the number of sections in a text.
        
        Args:
            text: The text to analyze
            
        Returns:
            The number of sections
        """
        section_headers = re.findall(r'^([A-Za-z0-9\s]+)$', text, re.MULTILINE)
        section_headers = [h for h in section_headers if 2 < len(h) < 50]
        return len(section_headers)
    
    def process(self, standard_text: str) -> Dict[str, Any]:
        """
        Process a standard.
        
        Args:
            standard_text: The text of the standard to process
            
        Returns:
            The result of the processing
        """
        state = self._initialize_state(standard_text)
        
        self.logger.info("Starting AAOIFI standard enhancement process")
        
        state["audit_trail"] = "# AAOIFI Standard Enhancement Audit Trail\n\n"
        state["audit_trail"] += "## Process Summary\n\n"
        state["audit_trail"] += f"- **Start time**: {state.get('timestamp', 'Not recorded')}\n"
        state["audit_trail"] += f"- **Input length**: {len(standard_text)} characters\n"
        state["audit_trail"] += "- **Pipeline stages**: Preprocessor → Reviewer → Enhancer → Validator\n\n"
        state["audit_trail"] += "---\n\n"
        
        current_stage = "preprocessor"
        
        while True:
            if current_stage != "preprocessor":
                self.retry_counts["preprocessor"] = 0
            
            self.retry_counts[current_stage] += 1
            if self.retry_counts[current_stage] > self.max_retries:
                error_msg = f"Maximum retries ({self.max_retries}) reached for {current_stage}. Using default quality score."
                self.logger.warning(error_msg)
                
                if "quality_scores" not in state:
                    state["quality_scores"] = {}
                    
                state["quality_scores"][current_stage] = self.default_quality_score
                
                state = self._update_audit_trail(
                    state, 
                    current_stage, 
                    f"{error_msg} Setting quality score to {self.default_quality_score}."
                )
                
                if current_stage == "preprocessor" and not state.get("preprocessed_text"):
                    self.logger.warning("Forced creation of preprocessed text using original text")
                    state["preprocessed_text"] = standard_text
            
            if current_stage == "preprocessor":
                self.logger.info("Running preprocessor agent")
                
                preprocessor_result = self.preprocessor._process(state)
                
                state.update(preprocessor_result)
                
                quality_score = state["quality_scores"].get("preprocessor", 0)
                self.logger.info(f"Completed preprocessor agent with quality score {quality_score}")
                
                state = self._update_audit_trail(
                    state, 
                    "Preprocessor", 
                    f"Preprocessed text length: {len(state.get('preprocessed_text', ''))}\n\nNotes: {state.get('notes', 'No notes.')}",
                    preprocessor_result.get("audit_entry")
                )
                
                if state.get("knowledge_request"):
                    state = self._handle_knowledge_request(state)
                    continue
                
                if quality_score < self.quality_threshold and self.retry_counts["preprocessor"] <= self.max_retries:
                    self.logger.info(f"Preprocessor quality score {quality_score} is below threshold {self.quality_threshold}, retrying")
                    continue
                
                current_stage = "reviewer"
                
            elif current_stage == "reviewer":
                self.logger.info("Running reviewer agent")
                
                reviewer_result = self.reviewer._process(state)
                
                state.update(reviewer_result)
                
                quality_score = state["quality_scores"].get("reviewer", 0)
                self.logger.info(f"Completed reviewer agent with quality score {quality_score}")
                
                state = self._update_audit_trail(
                    state, 
                    "Reviewer", 
                    f"Review notes: {state.get('notes', 'No notes.')}",
                    reviewer_result.get("audit_entry")
                )
                
                if state.get("knowledge_request"):
                    state = self._handle_knowledge_request(state)
                    continue
                
                if quality_score < self.quality_threshold:
                    self.logger.info(f"Reviewer quality score {quality_score} is below threshold {self.quality_threshold}, restarting from preprocessor")
                    current_stage = "preprocessor"
                    continue
                
                current_stage = "enhancer"
                
            elif current_stage == "enhancer":
                self.logger.info("Running enhancer agent")
                
                enhancer_result = self.enhancer._process(state)
                
                state.update(enhancer_result)
                
                quality_score = state["quality_scores"].get("enhancer", 0)
                self.logger.info(f"Completed enhancer agent with quality score {quality_score}")
                
                state = self._update_audit_trail(
                    state, 
                    "Enhancer", 
                    f"Enhanced text length: {len(state.get('enhanced_text', ''))}\n\nNotes: {state.get('notes', 'No notes.')}",
                    enhancer_result.get("audit_entry")
                )
                
                if state.get("knowledge_request"):
                    state = self._handle_knowledge_request(state)
                    continue
                
                if quality_score < self.quality_threshold:
                    self.logger.info(f"Enhancer quality score {quality_score} is below threshold {self.quality_threshold}, restarting from reviewer")
                    current_stage = "reviewer"
                    continue
                
                current_stage = "validator"
                
            elif current_stage == "validator":
                self.logger.info("Running validator agent")
                
                validator_result = self.validator._process(state)
                
                state.update(validator_result)
                
                quality_score = state["quality_scores"].get("validator", 0)
                self.logger.info(f"Completed validator agent with quality score {quality_score}")
                
                state = self._update_audit_trail(
                    state, 
                    "Validator", 
                    f"Validation notes: {state.get('notes', 'No notes.')}",
                    validator_result.get("audit_entry")
                )
                
                if state.get("knowledge_request"):
                    state = self._handle_knowledge_request(state)
                    continue
                
                if quality_score < self.quality_threshold:
                    self.logger.info(f"Validator quality score {quality_score} is below threshold {self.quality_threshold}, restarting from enhancer")
                    current_stage = "enhancer"
                    continue
                
                state["final_output"] = state.get("validated_text", state.get("enhanced_text", state.get("reviewed_text", state.get("preprocessed_text", standard_text))))
                break
        
        final_summary = "## Final Process Summary\n\n"
        final_summary += f"- **Completion time**: {datetime.now()}\n"
        
        if "quality_scores" in state and state["quality_scores"]:
            scores = state["quality_scores"].values()
            avg_score = sum(scores) / len(scores)
            final_summary += f"- **Average quality score**: {avg_score:.1f}/100\n"
        
        if "timestamp" in state:
            duration = (datetime.now() - state["timestamp"]).total_seconds()
            final_summary += f"- **Total processing time**: {duration:.1f} seconds\n"
        
        if "final_output" in state:
            final_summary += f"- **Final output length**: {len(state['final_output'])} characters\n"
        
        state["audit_trail"] += final_summary
        
        self.logger.info("Completed AAOIFI standard enhancement process")
        
        return state
