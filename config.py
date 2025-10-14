"""Configuration constants for PDF Chat application."""

import os
from pathlib import Path

# Application settings
APP_NAME = "pdf-chat-ollama"
DATA_DIR = Path.home() / f".{APP_NAME}"
VECTOR_DB_PATH = DATA_DIR / "chroma_db"
HISTORY_DB_PATH = DATA_DIR / "chat_history.json"

# Ollama settings
OLLAMA_BASE_URL = "http://localhost:11434"
CHAT_MODEL = "mixtral"
EMBEDDING_MODEL = "nomic-embed-text"

# Text processing settings
CHUNK_SIZE = 1000  # tokens
CHUNK_OVERLAP = 128  # tokens
MAX_CONTEXT_CHUNKS = 5

# Chat settings
SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on the provided PDF documents. 
Always cite your sources by mentioning the document name and page number when possible.
If you cannot find relevant information in the provided context, say so clearly.
Be concise but thorough in your responses."""

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)
