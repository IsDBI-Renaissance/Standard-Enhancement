"""
Test script for the AAOIFI Standards Enhancement System.
This file contains tests for various components and end-to-end workflow.
"""

import os
import sys
import json
import logging
import argparse
import tempfile
import requests
import unittest
from unittest.mock import patch, MagicMock

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('test')

# Import system components
from pipeline.orchestrator import AAOIFIOrchestrator
from utils.gemini_client import GeminiClient
from utils.rag_system import RAGSystem
from utils.pdf_processor import PDFProcessor

# Sample text for testing
SAMPLE_STANDARD = """
# AAOIFI Standard on Murabaha

## Introduction
This standard aims to establish Shariah rules for Murabaha transactions conducted by Islamic financial institutions.

## Scope
This standard applies to Islamic financial institutions (IFIs) engaging in Murabaha transactions, regardless of their names.

## Definitions
**Murabaha**: A sale in which the seller discloses the cost of the commodity and adds a markup (profit).
**Commodity**: Any tangible or intangible asset that can be sold.
**Islamic Financial Institution (IFI)**: An institution that offers Shariah-compliant financial services.

## Shariah Requirements

### Basic Requirements
1. The IFI must own the commodity before selling it to the customer.
2. The IFI must have actual or constructive possession of the commodity before selling it.
3. The cost and markup must be clearly stated to the customer.

### Prohibited Practices
1. Selling a commodity before acquiring ownership and possession.
2. Charging late payment fees that accrue as income to the IFI.
3. Rollover of debt into a new Murabaha transaction.
4. Using interest-based benchmarks without appropriate measures.

## Accounting Treatment
The commodity should be recorded at cost in the IFI's books. Upon sale, the cost is expensed, and the markup is recognized as income over the payment period.

## Examples

### Example 1: Basic Murabaha
A customer requests the IFI to purchase a machine for $10,000 and agrees to buy it for $11,000 to be paid in installments.

### Example 2: Currency Murabaha
The IFI purchases a commodity for $10,000 and sells it for £7,700 to be paid after three months.

## Effective Date
This standard is effective from January 1, 2023.
"""

class TestAAOIFIEnhancementSystem(unittest.TestCase):
    """Test cases for the AAOIFI Standards Enhancement System."""
    
    def setUp(self):
        """Set up test environment."""
        # Use the temp directory for test outputs
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a direct path to the data directory for testing RAG
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Create a mock Gemini client for testing
        self.gemini_client = MagicMock(spec=GeminiClient)
        self.gemini_client.get_completion_text.return_value = "Enhanced text"
        self.gemini_client.format_prompt.return_value = "Formatted prompt"
        
        # Initialize orchestrator with mock client
        self.orchestrator = AAOIFIOrchestrator(
            max_retries=2,
            default_quality_score=70,
            llm_client=self.gemini_client,
            use_rag=True,
            rag_data_dir=self.data_dir
        )
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove any test files created
        for root, dirs, files in os.walk(self.temp_dir, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        os.rmdir(self.temp_dir)
    
    def test_gemini_client_initialization(self):
        """Test GeminiClient initialization."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
            client = GeminiClient()
            self.assertEqual(client.model_name, "gemini-1.5-pro")
    
    def test_orchestrator_initialization(self):
        """Test orchestrator initialization."""
        self.assertEqual(self.orchestrator.max_retries, 2)
        self.assertEqual(self.orchestrator.default_quality_score, 70)
    
    def test_rag_integration(self):
        """Test RAG integration."""
        # Create a simple PDF for testing RAG
        try:
            from reportlab.pdfgen import canvas
            pdf_path = os.path.join(self.data_dir, "test_doc.pdf")
            c = canvas.Canvas(pdf_path)
            c.drawString(100, 750, "This is a test document for RAG integration.")
            c.drawString(100, 730, "It contains information about AAOIFI standards.")
            c.save()
            
            # Test PDF processor
            pdf_processor = PDFProcessor(self.data_dir)
            chunks = pdf_processor.process_all_documents(chunk_size=100)
            
            self.assertTrue(len(chunks) > 0)
            self.assertEqual(chunks[0]["source"], "test_doc.pdf")
            
            # Test RAG system with integration
            with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
                rag_system = RAGSystem(self.gemini_client, self.data_dir)
                results = rag_system.retrieve("AAOIFI standards", top_k=1)
                
                # Should at least return one result from our test PDF
                self.assertTrue(len(results) > 0)
                
        except ImportError:
            logger.warning("reportlab not installed, skipping PDF creation test")
    
    @patch('utils.gemini_client.GeminiClient.get_completion_text')
    def test_standard_enhancement_pipeline(self, mock_get_completion):
        """Test the full standard enhancement pipeline."""
        # Mock responses for different stages
        mock_get_completion.side_effect = [
            # Parsing response
            json.dumps({
                "title": "AAOIFI Standard on Murabaha",
                "sections": [{"content": "Test content"}],
                "definitions": {"Murabaha": "Test definition"}
            }),
            # Review response
            "This is a review of the standard.",
            # Enhancement response
            "This is an enhanced standard.",
            # Quality assessment responses (for each stage)
            json.dumps({"overall_score": 85}),
            json.dumps({"overall_score": 90}),
            # Validation response
            "This is a validation of the standard.",
            json.dumps({"overall_score": 95})
        ]
        
        # Process the standard
        result = self.orchestrator.process(SAMPLE_STANDARD)
        
        # Check expected outputs
        self.assertIn("final_output", result)
        self.assertIn("audit_trail", result)
        self.assertIn("quality_scores", result)
    
    def test_flask_server(self):
        """Test Flask server API."""
        # Skip if running in CI/CD environment
        if os.environ.get('CI') == 'true':
            self.skipTest("Skipping server test in CI environment")
        
        # Try to connect to a running server
        try:
            # Health check
            response = requests.get('http://localhost:8000/')
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data['status'], 'healthy')
            
            # Enhancement request (just test the endpoint, not the actual processing)
            # This assumes a server is actually running
            try:
                response = requests.post(
                    'http://localhost:8000/enhance',
                    json={"standard_text": "Test standard"}
                )
                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertIn('enhanced_standard', data)
                self.assertIn('audit_trail', data)
            except requests.RequestException:
                logger.warning("Enhancement endpoint test failed, server might not be processing requests")
                
        except requests.ConnectionError:
            logger.warning("Flask server not running, skipping API tests")
            self.skipTest("Flask server not running")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run tests for AAOIFI Standards Enhancement System')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    verbosity = 2 if args.verbose else 1
    unittest.main(argv=[sys.argv[0]], verbosity=verbosity)
