#!/usr/bin/env python3
"""Test script to debug embedding issues with simple text."""

import logging
from vector_store import VectorStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_simple_text():
    """Test embedding with simple text."""
    try:
        # Test with simple text first
        simple_text = "This is a simple test document for embedding generation."
        print(f"Testing with simple text: {simple_text}")
        
        vs = VectorStore()
        embedding = vs._get_embedding(simple_text)
        print(f"Success! Generated embedding with {len(embedding)} dimensions")
        
        # Test with slightly longer text
        longer_text = "This is a longer test document that contains multiple sentences. It should test the embedding generation with more content. The text includes various words and phrases to ensure proper processing."
        print(f"\nTesting with longer text: {longer_text[:100]}...")
        
        embedding2 = vs._get_embedding(longer_text)
        print(f"Success! Generated embedding with {len(embedding2)} dimensions")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_text()