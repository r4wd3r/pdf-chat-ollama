#!/usr/bin/env python3
"""Test script to debug embedding issues."""

import logging
from vector_store import VectorStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_embedding():
    """Test embedding generation."""
    try:
        print("Creating VectorStore...")
        vs = VectorStore()
        
        print("Testing single embedding...")
        embedding = vs._get_embedding("This is a test document.")
        print(f"Success! Generated embedding with {len(embedding)} dimensions")
        
        print("Testing document addition...")
        test_chunks = [
            {
                "text": "This is a test document chunk.",
                "filename": "test.pdf",
                "page_number": 1,
                "filepath": "/tmp/test.pdf",
                "tokens": 10
            }
        ]
        
        vs.add_documents(test_chunks)
        print("Successfully added test document!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_embedding()