"""
Knowledge retrieval tool for the AAOIFI Standards Enhancement System.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from pipeline.models.models import KnowledgeRequest

# Change from dataclass to Pydantic model to be consistent
class KnowledgeResponse(BaseModel):
    """Class for knowledge response data."""
    content: str
    source: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        arbitrary_types_allowed = True

class KnowledgeRetrievalTool:
    """
    Tool for retrieving knowledge from external sources.
    
    This tool:
    - Takes a query and context
    - Searches for relevant information
    - Returns a structured response
    """
    
    def __init__(self, llm: ChatOpenAI):
        """
        Initialize the knowledge retrieval tool.
        
        Args:
            llm: The language model to use
        """
        self.logger = logging.getLogger("tools.knowledge_retrieval")
        self.llm = llm
        
        # Create a prompt template for knowledge retrieval
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a knowledgeable assistant specializing in Islamic finance and AAOIFI standards.
            
Your task is to provide accurate, relevant information in response to queries about Islamic finance principles, 
Shariah compliance, AAOIFI standards, and related topics.

When responding:
1. Focus on factual information from authoritative sources
2. Cite your sources when possible
3. If you're uncertain, acknowledge the limits of your knowledge
4. Structure your response in a clear, organized manner
5. Do not paraphrase or synthesize facts — quote the original when possible
6. Include citations (title + source link)
7. Prioritize authoritative sources: AAOIFI.org, Islamic Finance Gateway, IFSB, academic journals, known Muftis' fatawa ressources from the internet

Context about the request: {context}
"""),
            ("human", "{query}")
        ])
    
    def retrieve(self, request: KnowledgeRequest) -> KnowledgeResponse:
        """
        Retrieve knowledge based on the request.
        
        Args:
            request: The knowledge request
            
        Returns:
            A knowledge response
        """
        self.logger.info(f"Retrieving knowledge for query: {request.query}")
        
        # Record start time for audit
        start_time = datetime.now()
        
        # Format the prompt
        formatted_prompt = self.prompt.format(
            query=request.query,
            context=request.context
        )
        
        # Get the response from the LLM
        self.logger.debug(f"Sending prompt to LLM: {formatted_prompt}")
        
        result = None
        error = None
        
        try:
            response = self.llm.invoke(formatted_prompt)
            content = response.content
            
            self.logger.info(f"Received response from LLM, length: {len(content)}")
            
            # Create the knowledge response
            result = KnowledgeResponse(
                content=content,
                source="LLM-generated content",
                timestamp=datetime.now()
            )
            
            # Record tool usage details for the requester's audit
            retrieval_details = {
                "tool": "knowledge_retrieval",
                "timestamp": datetime.now().isoformat(),
                "query": request.query,
                "context": request.context,
                "result_summary": content[:100] + "..." if len(content) > 100 else content,
                "source": "LLM-generated content",
                "processing_time": (datetime.now() - start_time).total_seconds()
            }
            
            # Add the details to the response for the requester's audit
            if not hasattr(result, "audit_details"):
                result.audit_details = retrieval_details
            
            return result
        except Exception as e:
            self.logger.error(f"Error retrieving knowledge: {str(e)}")
            error = str(e)
            
            # Return a fallback response
            result = KnowledgeResponse(
                content=f"Error retrieving knowledge: {str(e)}",
                source="Error",
                timestamp=datetime.now()
            )
            
            # Record error details for the requester's audit
            retrieval_details = {
                "tool": "knowledge_retrieval",
                "timestamp": datetime.now().isoformat(),
                "query": request.query,
                "context": request.context,
                "error": str(e),
                "processing_time": (datetime.now() - start_time).total_seconds()
            }
            
            # Add the details to the response for the requester's audit
            if not hasattr(result, "audit_details"):
                result.audit_details = retrieval_details
            
            return result
