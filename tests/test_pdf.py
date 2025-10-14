#!/usr/bin/env python3
"""Test script to debug PDF processing issues."""

import logging
from pathlib import Path
from pdf_processor import PDFProcessor
from vector_store import VectorStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_pdf_processing():
    """Test PDF processing with the actual file."""
    try:
        pdf_path = Path("../paper_juanita.pdf")
        print(f"Testing PDF processing with: {pdf_path}")
        print(f"File exists: {pdf_path.exists()}")
        
        if not pdf_path.exists():
            print("PDF file not found!")
            return
        
        # Test PDF processing
        print("Processing PDF...")
        processor = PDFProcessor()
        chunks = processor.process_pdf(pdf_path)
        print(f"Generated {len(chunks)} chunks")
        
        if chunks:
            print("First chunk preview:")
            print(f"Text: {chunks[0]['text'][:200]}...")
            print(f"Tokens: {chunks[0].get('tokens', 'N/A')}")
            print(f"Filename: {chunks[0]['filename']}")
            print(f"Page: {chunks[0]['page_number']}")
        
        # Test vector store addition
        print("\nTesting vector store addition...")
        vs = VectorStore()
        vs.add_documents(chunks)
        print("Successfully added all chunks to vector store!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_processing()