#!/usr/bin/env python3
"""Test script to debug embedding issues by testing the exact same text as curl."""

import logging
import requests
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_curl_text():
    """Test embedding with the exact same text that works via curl."""
    try:
        # Test with the exact same text that works via curl
        text = "This is a longer test document that might be similar to what the PDF processing is trying to embed. It contains multiple sentences and should test the embedding generation properly."
        
        url = "http://localhost:11434/api/embeddings"
        payload = {
            "model": "nomic-embed-text",
            "prompt": text
        }
        
        print(f"Testing with text: {text[:100]}...")
        
        response = requests.post(url, json=payload, timeout=60)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success! Generated embedding with {len(data['embedding'])} dimensions")
        else:
            print(f"Error: {response.status_code} - {response.text}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_curl_text()