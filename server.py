"""
Flask server for the AAOIFI Standards Enhancement System.
This file provides a REST API interface to the standard enhancement pipeline.
"""

import os
import logging
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify
from dotenv import load_dotenv

from pipeline.orchestrator import AAOIFIOrchestrator
from utils.gemini_client import GeminiClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('server')

# Initialize Gemini client and orchestrator at startup
def initialize_orchestrator():
    """Initialize the orchestrator."""
    logger.info("Initializing AAOIFI Standards Enhancement orchestrator")
    
    try:
        # Initialize Gemini client
        gemini_client = GeminiClient()
        logger.info(f"Initialized Gemini client with model: {gemini_client.model_name}")
        
        # Initialize the orchestrator with RAG enabled by default
        orchestrator = AAOIFIOrchestrator(
            max_retries=5,
            default_quality_score=60,
            llm_client=gemini_client,
            use_rag=True,
            rag_data_dir="data"
        )
        
        logger.info("Orchestrator initialization complete")
        
        # Check if RAG is available
        if hasattr(orchestrator.llm_service, 'has_rag'):
            logger.info(f"RAG system available: {orchestrator.llm_service.has_rag}")
        else:
            logger.warning("RAG system not available")
            
        return orchestrator
    except Exception as e:
        logger.error(f"Error initializing orchestrator: {str(e)}", exc_info=True)
        raise

# Initialize Flask app
app = Flask(__name__)

# Initialize the orchestrator at module load time
orchestrator = initialize_orchestrator()

@app.route('/enhance', methods=['POST'])
def enhance_standard():
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
        return jsonify({"error": "Server not properly initialized"}), 500
    
    # Get request data
    data = request.get_json()
    
    if not data or 'standard_text' not in data:
        logger.error("No standard text provided")
        return jsonify({"error": "Standard text cannot be empty"}), 400
    
    standard_text = data['standard_text']
    max_retries = data.get('max_retries', orchestrator.max_retries)
    default_quality = data.get('default_quality', orchestrator.default_quality_score)
    
    logger.info("Received enhancement request")
    logger.info(f"Input text length: {len(standard_text)} characters")
    
    # Update orchestrator configuration if provided in the request
    if max_retries != orchestrator.max_retries:
        orchestrator.max_retries = max_retries
    
    if default_quality != orchestrator.default_quality_score:
        orchestrator.default_quality_score = default_quality
    
    try:
        # Process the standard text
        result = orchestrator.process(standard_text)
        
        # Prepare the response
        response = {
            "enhanced_standard": result["final_output"],
            "audit_trail": result["audit_trail"]
        }
        
        logger.info("Enhancement completed successfully")
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error enhancing standard: {str(e)}", exc_info=True)
        return jsonify({"error": f"Error processing standard: {str(e)}"}), 500

@app.route('/', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify that the server is running.
    """
    rag_status = "enabled"
    if orchestrator and hasattr(orchestrator.llm_service, 'has_rag'):
        rag_status = "active" if orchestrator.llm_service.has_rag else "disabled"
    
    return jsonify({
        "status": "healthy", 
        "service": "AAOIFI Standards Enhancement API",
        "rag": rag_status
    })

if __name__ == "__main__":
    # Set port from environment variable or default to 8000
    port = int(os.getenv("PORT", 8000))
    
    # Run the Flask app with debug enabled in development
    debug_mode = os.getenv("FLASK_ENV", "production") == "development"
    
    # Run the server
    logger.info(f"Starting server on port {port}, debug mode: {debug_mode}")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
