"""
FastAPI server for the AAOIFI Standards Enhancement System.
This file provides a REST API interface to the standard enhancement pipeline.
"""

import os
import logging
import uvicorn
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from pipeline.orchestrator import AAOIFIOrchestrator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('server')

# Initialize FastAPI app
app = FastAPI(
    title="AAOIFI Standards Enhancement API",
    description="API for enhancing AAOIFI standards through a multi-agent pipeline",
    version="1.0.0"
)

# Define request and response models
class EnhancementRequest(BaseModel):
    standard_text: str = Field(..., description="The AAOIFI standard text to analyze")
    max_retries: Optional[int] = Field(5, description="Maximum number of retries before giving up")
    default_quality: Optional[int] = Field(60, description="Default quality score to use when parsing fails")

class EnhancementResponse(BaseModel):
    enhanced_standard: str = Field(..., description="The enhanced standard text")
    audit_trail: str = Field(..., description="Audit trail of the enhancement process")

# Initialize the orchestrator at server startup
orchestrator = None

@app.on_event("startup")
async def startup_event():
    global orchestrator
    logger.info("Initializing AAOIFI Standards Enhancement orchestrator")
    orchestrator = AAOIFIOrchestrator(
        max_retries=5,
        default_quality_score=60
    )
    logger.info("Server startup complete")

@app.post("/enhance", response_model=EnhancementResponse)
async def enhance_standard(request: EnhancementRequest = Body(...)):
    """
    Enhance an AAOIFI standard by processing it through the multi-agent pipeline.
    
    The process includes:
    1. Preprocessing the standard text
    2. Reviewing the preprocessed text
    3. Enhancing the reviewed text
    4. Validating the enhanced text
    
    Returns the enhanced standard text and an audit trail of the process.
    """
    global orchestrator
    
    if not orchestrator:
        logger.error("Orchestrator not initialized")
        raise HTTPException(status_code=500, detail="Server not properly initialized")
    
    if not request.standard_text:
        logger.error("No standard text provided")
        raise HTTPException(status_code=400, detail="Standard text cannot be empty")
    
    logger.info("Received enhancement request")
    logger.info(f"Input text length: {len(request.standard_text)} characters")
    
    # Update orchestrator configuration if provided in the request
    if request.max_retries is not None and request.max_retries != orchestrator.max_retries:
        orchestrator.max_retries = request.max_retries
    
    if request.default_quality is not None and request.default_quality != orchestrator.default_quality_score:
        orchestrator.default_quality_score = request.default_quality
    
    try:
        # Process the standard text
        result = orchestrator.process(request.standard_text)
        
        # Prepare the response
        response = EnhancementResponse(
            enhanced_standard=result["final_output"],
            audit_trail=result["audit_trail"]
        )
        
        logger.info("Enhancement completed successfully")
        return response
    
    except Exception as e:
        logger.error(f"Error enhancing standard: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing standard: {str(e)}")

@app.get("/")
async def health_check():
    """
    Health check endpoint to verify that the server is running.
    """
    return {"status": "healthy", "service": "AAOIFI Standards Enhancement API"}

if __name__ == "__main__":
    # Run the server with uvicorn when this file is executed directly
    uvicorn.run("server:app", host="localhost", port=8000, reload=True)
