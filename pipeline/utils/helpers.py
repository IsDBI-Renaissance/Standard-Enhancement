"""
Utility functions for the AAOIFI Standards Enhancement System.
"""

import re
import logging
from typing import Dict, Any, List, Optional

def format_arabic_terms(text: str) -> str:
    """
    Format Arabic terms in the text with proper transliteration and explanation.
    
    Args:
        text: The text to format
        
    Returns:
        The formatted text
    """
    # This is a simple placeholder implementation.
    # In a real system, this would be more sophisticated.
    
    # Find Arabic terms in the text (simplified approach)
    arabic_term_pattern = r'([A-Z][a-z]*(?:\s[A-Z][a-z]*)*)\s*\(([^)]*)\)'
    
    # Replace with properly formatted versions
    formatted_text = re.sub(
        arabic_term_pattern, 
        r'*\1* (\2)',
        text
    )
    
    return formatted_text

def extract_sections(text: str) -> Dict[str, str]:
    """
    Extract sections from the text.
    
    Args:
        text: The text to extract sections from
        
    Returns:
        A dictionary mapping section names to section content
    """
    # This is a simple placeholder implementation.
    # In a real system, this would be more sophisticated.
    
    # Find sections in the text
    section_pattern = r'#+\s*(.*?)\s*\n(.*?)(?=\n#+\s|$)'
    sections = {}
    
    for match in re.finditer(section_pattern, text, re.DOTALL):
        section_name = match.group(1).strip()
        section_content = match.group(2).strip()
        sections[section_name] = section_content
    
    return sections

def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate the similarity between two texts.
    
    Args:
        text1: The first text
        text2: The second text
        
    Returns:
        A similarity score between 0 and 1
    """
    # This is a simple placeholder implementation.
    # In a real system, this would use more sophisticated algorithms.
    
    # Convert to lowercase and remove punctuation
    text1 = re.sub(r'[^\w\s]', '', text1.lower())
    text2 = re.sub(r'[^\w\s]', '', text2.lower())
    
    # Split into words
    words1 = set(text1.split())
    words2 = set(text2.split())
    
    # Calculate Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    if union == 0:
        return 0.0
    
    return intersection / union

def validate_shariah_compliance(text: str) -> List[Dict[str, Any]]:
    """
    Validate Shariah compliance of the text.
    
    Args:
        text: The text to validate
        
    Returns:
        A list of validation results
    """
    # This is a placeholder implementation.
    # In a real system, this would be more sophisticated and would
    # actually check for Shariah compliance issues.
    
    results = []
    
    # Check for common Shariah compliance issues
    if "interest" in text.lower() and "prohibited" not in text.lower():
        results.append({
            "issue": "Interest (Riba) mentioned without prohibition",
            "severity": "high",
            "location": "N/A"
        })
    
    if "uncertainty" in text.lower() and "gharar" not in text.lower():
        results.append({
            "issue": "Uncertainty mentioned without reference to Gharar",
            "severity": "medium",
            "location": "N/A"
        })
    
    return results
