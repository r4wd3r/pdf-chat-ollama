#!/usr/bin/env python3
"""Test script to debug embedding issues with small batches."""

import logging
from pathlib import Path
from pdf_processor import PDFProcessor
from vector_store import VectorStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_small_batch():
    """Test PDF processing with small batches."""
    try:
        pdf_path = Path("../paper_juanita.pdf")
        print(f"Testing PDF processing with: {pdf_path}")
        
        if not pdf_path.exists():
            print("PDF file not found!")
            return
        
        # Process PDF
        processor = PDFProcessor()
        chunks = processor.process_pdf(pdf_path)
        print(f"Generated {len(chunks)} chunks")
        
        # Test with just the first 3 chunks
        test_chunks = chunks[:3]
        print(f"Testing with first {len(test_chunks)} chunks")
        
        # Test vector store addition
        print("Testing vector store addition...")
        vs = VectorStore()
        vs.add_documents(test_chunks)
        print("Successfully added test chunks to vector store!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_small_batch()