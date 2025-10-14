#!/usr/bin/env python3
"""Test script to debug embedding issues with progressive text lengths."""

import logging
import requests
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_progressive_text():
    """Test embedding with progressively longer text."""
    try:
        # Get the first chunk text from the PDF
        from pdf_processor import PDFProcessor
        from pathlib import Path
        
        pdf_path = Path("../paper_juanita.pdf")
        processor = PDFProcessor()
        chunks = processor.process_pdf(pdf_path)
        
        if not chunks:
            print("No chunks found!")
            return
            
        first_chunk_text = chunks[0]["text"]
        print(f"Original text length: {len(first_chunk_text)} characters")
        
        # Test with progressively longer portions
        test_lengths = [100, 500, 1000, 2000, 3000, len(first_chunk_text)]
        
        for length in test_lengths:
            test_text = first_chunk_text[:length]
            print(f"\nTesting with {len(test_text)} characters...")
            
            url = "http://localhost:11434/api/embeddings"
            payload = {
                "model": "nomic-embed-text",
                "prompt": test_text
            }
            
            try:
                response = requests.post(url, json=payload, timeout=60)
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Success! Generated embedding with {len(data['embedding'])} dimensions")
                else:
                    print(f"❌ Error: {response.status_code} - {response.text[:200]}")
                    break
            except Exception as e:
                print(f"❌ Exception: {e}")
                break
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_progressive_text()