"""PDF Chat with Ollama - Chat with your PDF documents using local AI.

This package provides a CLI application for uploading PDF documents and chatting
with them using Ollama's local AI models. It uses ChromaDB for vector storage
and semantic search to provide intelligent answers based on your documents.
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .chat_engine import ChatEngine
from .config import APP_NAME, Config
from .history_manager import HistoryManager
from .pdf_processor import PDFProcessor
from .vector_store import VectorStore

__all__ = [
    "ChatEngine",
    "Config",
    "HistoryManager", 
    "PDFProcessor",
    "VectorStore",
    "APP_NAME",
    "__version__",
]
