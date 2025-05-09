"""
Models for representing data structures in the AAOIFI Standards Enhancement System.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class KnowledgeRequest(BaseModel):
    """
    A request for external knowledge.
    """
    
    requester: str = Field(
        description="The name of the agent making the request"
    )
    query: str = Field(
        description="The query to be used for knowledge retrieval"
    )
    context: Optional[str] = Field(
        None,
        description="Additional context to help with the knowledge retrieval"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="The timestamp of the request"
    )
    additional_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional parameters for the request"
    )

    class Config:
        arbitrary_types_allowed = True

class KnowledgeResponse(BaseModel):
    """
    A response from the knowledge retrieval system.
    """
    
    requester: str = Field(
        description="The name of the agent that made the request"
    )
    query: str = Field(
        description="The original query"
    )
    content: str = Field(
        description="The content retrieved from external sources"
    )
    sources: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="The sources of the retrieved content"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="The timestamp of the response"
    )

class AuditEntry(BaseModel):
    """
    An entry in the audit trail.
    """
    
    stage: str = Field(
        description="The stage of the pipeline"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="The timestamp of the entry"
    )
    quality_score: int = Field(
        description="The quality score assigned to the output"
    )
    notes: str = Field(
        description="Notes about the process"
    )
    knowledge_request: Optional[KnowledgeRequest] = Field(
        None,
        description="The knowledge request, if any"
    )
    knowledge_response: Optional[KnowledgeResponse] = Field(
        None,
        description="The knowledge response, if any"
    )

class StandardState(BaseModel):
    """
    The state of a standard as it moves through the pipeline.
    """
    
    standard_text: str = Field(
        description="The original text of the standard"
    )
    preprocessed_text: Optional[str] = Field(
        None,
        description="The preprocessed text"
    )
    reviewed_text: Optional[str] = Field(
        None,
        description="The reviewed text"
    )
    enhanced_text: Optional[str] = Field(
        None,
        description="The enhanced text"
    )
    validated_text: Optional[str] = Field(
        None,
        description="The validated text"
    )
    final_output: Optional[str] = Field(
        None,
        description="The final output text"
    )
    audit_trail: List[AuditEntry] = Field(
        default_factory=list,
        description="The audit trail of the process"
    )
    quality_scores: Dict[str, int] = Field(
        default_factory=lambda: {
            "preprocessor": 0,
            "reviewer": 0,
            "enhancer": 0,
            "validator": 0
        },
        description="The quality scores for each stage"
    )
    knowledge_requests: List[KnowledgeRequest] = Field(
        default_factory=list,
        description="The knowledge requests made during the process"
    )
    knowledge_responses: List[KnowledgeResponse] = Field(
        default_factory=list,
        description="The knowledge responses received during the process"
    )
    session_id: str = Field(
        description="The session ID"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="The timestamp of the session"
    )
