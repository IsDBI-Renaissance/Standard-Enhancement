"""
Main entry point for the AAOIFI Standards Enhancement System.
This file orchestrates the entire pipeline and provides the CLI interface.
"""

import os
import argparse
import logging
import sys
from dotenv import load_dotenv

from pipeline.orchestrator import AAOIFIOrchestrator

# Load environment variables
load_dotenv()

def setup_logging(debug_level):
    """Configure logging based on the debug level."""
    log_level = logging.INFO
    if debug_level >= 1:
        log_level = logging.DEBUG
        
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    
    # Set specific module log levels
    if debug_level >= 2:
        # Enable more verbose logging for specific components
        logging.getLogger('pipeline').setLevel(logging.DEBUG)
        logging.getLogger('agent').setLevel(logging.DEBUG)
    
    return logging.getLogger('main')

def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="AAOIFI Standards Enhancement System"
    )
    parser.add_argument(
        "--input", 
        type=str, 
        required=True, 
        help="Path to the AAOIFI standard text file to analyze"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output",
        help="Output directory for enhanced standard and reports"
    )
    parser.add_argument(
        "--debug", 
        action="count", 
        default=0,
        help="Enable debug mode (use multiple times for more verbosity)"
    )
    parser.add_argument(
        "--max-retries", 
        type=int, 
        default=5,
        help="Maximum number of retries before giving up (default: 5)"
    )
    parser.add_argument(
        "--default-quality", 
        type=int, 
        default=60,
        help="Default quality score to use when parsing fails (default: 60)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.debug)
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    # Check if input file exists
    if not os.path.exists(args.input):
        logger.error(f"Error: Input file {args.input} does not exist")
        return 1
    
    # Read input file
    with open(args.input, 'r', encoding='utf-8') as f:
        standard_text = f.read()
    
    logger.info(f"Processing standard from {args.input}")
    if args.debug > 0:
        logger.debug(f"Input text length: {len(standard_text)} characters")
        logger.debug(f"First 100 characters: {standard_text[:100]}...")
    
    # Initialize the orchestrator with the configured parameters
    orchestrator = AAOIFIOrchestrator(
        max_retries=args.max_retries,
        default_quality_score=args.default_quality
    )
    
    # Process the standard
    try:
        result = orchestrator.process(standard_text)
        
        # Save the result
        output_path = os.path.join(args.output, "enhanced_standard.md")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result["final_output"])
        
        # Save the audit trail
        audit_path = os.path.join(args.output, "audit_trail.md")
        with open(audit_path, 'w', encoding='utf-8') as f:
            f.write(result["audit_trail"])
        
        # Save quality scores report if debug mode is enabled
        if args.debug > 0:
            quality_path = os.path.join(args.output, "quality_scores.md")
            with open(quality_path, 'w', encoding='utf-8') as f:
                f.write("# Quality Scores Report\n\n")
                for stage, score in result.get("quality_scores", {}).items():
                    f.write(f"## {stage.capitalize()}\n\n")
                    f.write(f"Score: {score}\n\n")
            logger.info(f"Quality scores saved to {quality_path}")
        
        logger.info(f"Enhanced standard saved to {output_path}")
        logger.info(f"Audit trail saved to {audit_path}")
        
    except Exception as e:
        logger.error(f"Error processing standard: {str(e)}", exc_info=args.debug > 0)
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
