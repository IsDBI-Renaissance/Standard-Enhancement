"""
Utility for processing PDFs and extracting text content.
"""
import os
import logging
from typing import List, Dict, Any, Optional
import PyPDF2
import re

logger = logging.getLogger(__name__)

class PDFProcessor:
    """Class for extracting and processing text from PDF documents."""
    
    def __init__(self, pdf_directory: str):
        """
        Initialize the PDF processor.
        
        Args:
            pdf_directory: Directory containing PDF files
        """
        self.pdf_directory = pdf_directory
        self.processed_pdfs = {}
        
    def load_all_pdfs(self) -> Dict[str, str]:
        """
        Load and extract text from all PDFs in the directory.
        
        Returns:
            Dictionary mapping PDF filenames to extracted text
        """
        pdf_files = [f for f in os.listdir(self.pdf_directory) if f.lower().endswith('.pdf')]
        logger.info(f"Found {len(pdf_files)} PDF files in {self.pdf_directory}")
        
        for pdf_file in pdf_files:
            pdf_path = os.path.join(self.pdf_directory, pdf_file)
            try:
                self.processed_pdfs[pdf_file] = self.extract_text_from_pdf(pdf_path)
                logger.info(f"Successfully extracted text from {pdf_file}")
            except Exception as e:
                logger.error(f"Error extracting text from {pdf_file}: {str(e)}")
        
        return self.processed_pdfs
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text from the PDF
        """
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = []
            
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text.append(page.extract_text())
            
            return "\n".join(text)
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
        """
        Split text into chunks based on paragraphs with optional overlapping.
        
        Args:
            text: Text to chunk
            chunk_size: Maximum size of each chunk in characters
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List of dictionaries containing chunks and metadata
        """
        # Split by paragraphs (empty lines)
        paragraphs = re.split(r'\n\s*\n', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed the chunk size, save current chunk
            if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
                chunks.append({"text": current_chunk, "size": len(current_chunk)})
                # Keep overlap from the end of the current chunk
                current_chunk = current_chunk[-overlap:] if overlap > 0 else ""
            
            # Add paragraph to current chunk
            if current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph
        
        # Add the last chunk if not empty
        if current_chunk:
            chunks.append({"text": current_chunk, "size": len(current_chunk)})
        
        return chunks
    
    def process_all_documents(self, chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
        """
        Process all PDFs and create chunked documents with metadata.
        
        Args:
            chunk_size: Maximum size of each chunk in characters
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List of chunks with metadata
        """
        if not self.processed_pdfs:
            self.load_all_pdfs()
        
        all_chunks = []
        
        for pdf_file, text in self.processed_pdfs.items():
            chunks = self.chunk_text(text, chunk_size, overlap)
            
            # Add metadata to each chunk
            for i, chunk in enumerate(chunks):
                chunk["source"] = pdf_file
                chunk["chunk_id"] = f"{pdf_file}_{i}"
                all_chunks.append(chunk)
        
        logger.info(f"Created {len(all_chunks)} chunks from {len(self.processed_pdfs)} PDFs")
        return all_chunks
