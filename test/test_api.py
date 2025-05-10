"""
Test script for the AAOIFI Standards Enhancement API.
This script sends a test request to the FastAPI server.
"""

import requests
import json
import sys

def test_enhance_api():
    """Test the enhance endpoint of the API."""
    # Sample standard text for testing
    sample_text = """
# AAOIFI Standard on Murabaha

## Introduction

This standard aims to outline the principles and rules for Murabaha transactions in Islamic financial institutions.

## Definition

Murabaha is a sales contract where the seller discloses the cost of the commodity and adds a profit margin.

## Rules

1. The seller must own the asset before selling it.
2. The price and profit margin must be clearly disclosed.
3. The asset must be physically or constructively possessed by the seller.
4. The sale must be immediate and not future-based.

## Accounting Treatment

Financial institutions must record Murabaha transactions according to AAOIFI accounting standards.
    """
    
    # API endpoint
    url = "http://localhost:8000/enhance"
    
    # Request payload
    payload = {
        "standard_text": sample_text,
        "max_retries": 2,  # Lower for quicker test
        "default_quality": 60
    }
    
    print("Sending request to the API...")
    
    try:
        # Send the request
        response = requests.post(url, json=payload, timeout=300)  # Increased timeout to 5 minutes
        
        # Check the response
        if response.status_code == 200:
            result = response.json()
            
            # Print summary of results
            print("\nAPI request successful!")
            print(f"Enhanced standard length: {len(result['enhanced_standard'])}")
            print(f"Audit trail length: {len(result['audit_trail'])}")
            
            # Save the results to files for examination
            with open("test_enhanced_standard.md", "w", encoding="utf-8") as f:
                f.write(result["enhanced_standard"])
            
            with open("test_audit_trail.md", "w", encoding="utf-8") as f:
                f.write(result["audit_trail"])
            
            print("\nResults saved to:")
            print("- test_enhanced_standard.md")
            print("- test_audit_trail.md")
            
            return True
        else:
            print(f"\nError: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"\nError connecting to the API: {str(e)}")
        return False

if __name__ == "__main__":
    print("AAOIFI Standards Enhancement API Test")
    print("=====================================")
    
    success = test_enhance_api()
    
    sys.exit(0 if success else 1)
