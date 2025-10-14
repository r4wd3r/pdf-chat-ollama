#!/usr/bin/env python3
"""Test script to debug embedding issues with specific text."""

import logging
from vector_store import VectorStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_specific_text():
    """Test embedding with specific text from the PDF."""
    try:
        # Get the first chunk text from the PDF
        from pdf_processor import PDFProcessor
        from pathlib import Path
        
        pdf_path = Path("../paper_juanita.pdf")
        processor = PDFProcessor()
        chunks = processor.process_pdf(pdf_path)
        
        if chunks:
            first_chunk_text = chunks[0]["text"]
            print(f"Testing with first chunk text:")
            print(f"Length: {len(first_chunk_text)} characters")
            print(f"First 200 chars: {first_chunk_text[:200]}")
            print()
            
            # Test embedding generation
            vs = VectorStore()
            embedding = vs._get_embedding(first_chunk_text)
            print(f"Success! Generated embedding with {len(embedding)} dimensions")
        else:
            print("No chunks found!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_specific_text()