"""
Knowledge retriever for the AAOIFI Standards Enhancement System.

This module provides functionality for retrieving external knowledge
to support the pipeline.
"""

from typing import Dict, Any, List, Optional
import logging
import os
from datetime import datetime

from langchain_community.utilities import SerpAPIWrapper
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from pipeline.models.models import KnowledgeRequest, KnowledgeResponse

class KnowledgeRetriever:
    """
    Component responsible for retrieving external knowledge.
    
    This component:
    - Queries trusted sources like AAOIFI, scholarly work, or Fiqh databases
    - Fetches authoritative references when needed by other agents
    - Reformats and structures the knowledge for easy consumption
    """
    
    def __init__(
        self,
        model_name: str = "gpt-4-turbo",
        temperature: float = 0.2,
    ):
        """
        Initialize the knowledge retriever.
        
        Args:
            model_name: The name of the OpenAI model to use
            temperature: The temperature for the model
        """
        self.logger = logging.getLogger("knowledge_retriever")
        
        # Initialize the SerpAPI wrapper
        try:
            serpapi_key = os.environ.get("SERPAPI_API_KEY")
            if not serpapi_key:
                self.logger.warning("SERPAPI_API_KEY not found in environment variables")
                self.search_engine = None
            else:
                self.search_engine = SerpAPIWrapper()
        except Exception as e:
            self.logger.error(f"Error initializing SerpAPI: {e}")
            self.search_engine = None
        
        # Initialize the LLM
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature
        )
        
        # Define the summarization prompt
        self.summarization_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a knowledge specialist for AAOIFI (Accounting and Auditing Organization for Islamic Financial Institutions) standards. Your task is to summarize and structure the information provided from external sources to help with the enhancement of AAOIFI standards.

The information you're summarizing relates to Islamic financial principles, Shariah compliance, and AAOIFI standards. Please structure your summary in a clear, concise manner, focusing on:

1. Key concepts and principles
2. Relevant Shariah rulings or opinions
3. AAOIFI's official position (if available)
4. Different scholarly viewpoints (if applicable)
5. Practical implications for Islamic financial institutions

Make your summary comprehensive but focused on the specific query provided.
"""),
            ("human", """Context: {context}

Query: {query}

Search Results:
{search_results}

Please provide a structured summary of this information that would be helpful for enhancing AAOIFI standards.
""")
        ])
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a knowledge request and update the state.
        
        Args:
            state: The current state with a knowledge request
            
        Returns:
            The updated state with a knowledge response
        """
        self.logger.info("Processing knowledge request")
        
        # Extract the knowledge request
        knowledge_request = state.get("knowledge_request")
        if not knowledge_request:
            self.logger.error("No knowledge request found in state")
            return state
        
        # Ensure the knowledge request is in the right format
        if not isinstance(knowledge_request, KnowledgeRequest):
            try:
                knowledge_request = KnowledgeRequest(**knowledge_request)
            except Exception as e:
                self.logger.error(f"Error converting knowledge request: {e}")
                return state
        
        # Process the knowledge request
        knowledge_response = self._process_request(knowledge_request)
        
        # Remove the current knowledge request
        state.pop("knowledge_request", None)
        
        # Add the knowledge response to the state
        state["knowledge_responses"].append(knowledge_response)
        
        self.logger.info(f"Completed knowledge request for {knowledge_request.requester}")
        
        return state
    
    def _search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for information using SerpAPI.
        
        Args:
            query: The query to search for
            num_results: The number of results to return
            
        Returns:
            A list of search results
        """
        if not self.search_engine:
            self.logger.warning("Search engine not available")
            return [{"title": "Search engine not available", "snippet": "Please configure SerpAPI", "link": ""}]
        
        try:
            # Append AAOIFI to the query to get more relevant results
            search_query = f"AAOIFI {query} Islamic finance Shariah"
            
            # Run the search
            results = self.search_engine.results(search_query)
            
            # Extract the organic results
            organic_results = results.get("organic_results", [])
            
            # Format the results
            formatted_results = []
            for result in organic_results[:num_results]:
                formatted_results.append({
                    "title": result.get("title", ""),
                    "snippet": result.get("snippet", ""),
                    "link": result.get("link", "")
                })
            
            return formatted_results
        except Exception as e:
            self.logger.error(f"Error during search: {e}")
            return [{"title": "Search error", "snippet": str(e), "link": ""}]
    
    def _process_request(self, request: KnowledgeRequest) -> KnowledgeResponse:
        """
        Process a knowledge request.
        
        Args:
            request: The knowledge request to process
            
        Returns:
            A knowledge response
        """
        # Search for information
        search_results = self._search(request.query)
        
        # Format the search results
        formatted_results = ""
        for i, result in enumerate(search_results):
            formatted_results += f"Result {i+1}:\n"
            formatted_results += f"Title: {result['title']}\n"
            formatted_results += f"Snippet: {result['snippet']}\n"
            formatted_results += f"Link: {result['link']}\n\n"
        
        # Summarize the search results
        if search_results:
            # Format the prompt
            formatted_prompt = self.summarization_prompt.format(
                context=request.context,
                query=request.query,
                search_results=formatted_results
            )
            
            # Get the response from the LLM
            response = self.llm.invoke(formatted_prompt)
            
            # Create the knowledge response
            knowledge_response = KnowledgeResponse(
                requester=request.requester,
                query=request.query,
                content=response.content,
                sources=search_results,
                timestamp=datetime.now()
            )
        else:
            # Create an empty knowledge response
            knowledge_response = KnowledgeResponse(
                requester=request.requester,
                query=request.query,
                content="No information found for this query.",
                sources=[],
                timestamp=datetime.now()
            )
        
        return knowledge_response
