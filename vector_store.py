"""Vector database operations using ChromaDB and Ollama embeddings."""

import logging
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import chromadb
import ollama
from chromadb.config import Settings

from config import VECTOR_DB_PATH, EMBEDDING_MODEL, MAX_CONTEXT_CHUNKS, OLLAMA_BASE_URL

logger = logging.getLogger(__name__)


class VectorStore:
    """Manages vector storage and retrieval using ChromaDB and Ollama embeddings."""

    def __init__(self, collection_name: str = "pdf_documents") -> None:
        """Initialize the vector store.

        Args:
            collection_name: Name of the ChromaDB collection.
        """
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self.ollama_client = ollama.Client(host=OLLAMA_BASE_URL, timeout=60.0)
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize ChromaDB client and collection."""
        try:
            # Create persistent client
            self.client = chromadb.PersistentClient(
                path=str(VECTOR_DB_PATH),
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(self.collection_name)
                logger.info(f"Loaded existing collection: {self.collection_name}")
            except Exception as e:
                # Collection doesn't exist, create it
                # This catches NotFoundError and any other exceptions
                logger.info(f"Collection not found, creating new one: {self.collection_name}")
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "PDF document chunks"}
                )
                logger.info(f"Created new collection: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {e}")
            raise

    def _get_embedding(self, text: str, max_retries: int = 3) -> List[float]:
        """Get embedding for text using Ollama.

        Args:
            text: Text to embed.
            max_retries: Maximum number of retry attempts.

        Returns:
            Embedding vector.

        Raises:
            Exception: If embedding generation fails after all retries.
        """
        import time
        import requests
        import re
        
        # Clean the text to avoid issues with special characters
        cleaned_text = self._clean_text(text)
        
        for attempt in range(max_retries):
            try:
                # Use direct HTTP request instead of ollama client
                url = f"{OLLAMA_BASE_URL}/api/embeddings"
                payload = {
                    "model": EMBEDDING_MODEL,
                    "prompt": cleaned_text
                }
                
                response = requests.post(url, json=payload, timeout=60)
                response.raise_for_status()
                
                data = response.json()
                return data["embedding"]
                
            except Exception as e:
                logger.warning(f"Embedding attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    # Wait before retrying, with exponential backoff
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to generate embedding after {max_retries} attempts: {e}")
                    raise Exception(f"Embedding generation failed: {e}")
    
    def _clean_text(self, text: str) -> str:
        """Clean text for embedding generation.
        
        Args:
            text: Raw text to clean.
            
        Returns:
            Cleaned text.
        """
        import re
        
        # Remove excessive whitespace and normalize
        text = re.sub(r'\s+', ' ', text)
        
        # Remove or replace problematic characters
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\"\']', ' ', text)
        
        # Limit text length to avoid overwhelming the API
        # Based on testing, 1000 characters seems to be the safe limit
        max_length = 1000
        if len(text) > max_length:
            text = text[:max_length]
            # Try to end at a sentence boundary
            last_period = text.rfind('.')
            if last_period > max_length * 0.8:  # If we can find a period in the last 20%
                text = text[:last_period + 1]
        
        return text.strip()

    def add_documents(self, chunks: List[Dict[str, str]]) -> None:
        """Add document chunks to the vector store.

        Args:
            chunks: List of text chunks with metadata.
        """
        if not chunks:
            logger.warning("No chunks to add to vector store")
            return

        try:
            # Prepare data for ChromaDB
            texts = [chunk["text"] for chunk in chunks]
            metadatas = [
                {
                    "filename": chunk["filename"],
                    "page_number": chunk["page_number"],
                    "filepath": chunk["filepath"],
                    "tokens": chunk.get("tokens", 0)
                }
                for chunk in chunks
            ]
            ids = [str(uuid.uuid4()) for _ in chunks]

            # Generate embeddings
            logger.info(f"Generating embeddings for {len(chunks)} chunks...")
            embeddings = []
            for i, text in enumerate(texts):
                if i % 10 == 0:
                    logger.info(f"Processing chunk {i+1}/{len(texts)}")
                embedding = self._get_embedding(text)
                embeddings.append(embedding)
                
                # Add small delay between requests to avoid overwhelming Ollama
                if i < len(texts) - 1:  # Don't delay after the last request
                    import time
                    time.sleep(0.1)  # 100ms delay

            # Add to collection
            self.collection.add(
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )

            logger.info(f"Successfully added {len(chunks)} chunks to vector store")

        except Exception as e:
            logger.error(f"Failed to add documents to vector store: {e}")
            raise

    def search_similar(
        self, 
        query: str, 
        n_results: int = MAX_CONTEXT_CHUNKS
    ) -> List[Dict[str, str]]:
        """Search for similar document chunks.

        Args:
            query: Search query.
            n_results: Number of results to return.

        Returns:
            List of similar chunks with metadata and scores.
        """
        if not query.strip():
            return []

        try:
            # Generate query embedding
            query_embedding = self._get_embedding(query)

            # Search collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )

            # Format results
            similar_chunks = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i]
                    distance = results["distances"][0][i]
                    
                    # Convert distance to similarity score (lower distance = higher similarity)
                    similarity_score = 1.0 - distance
                    
                    similar_chunks.append({
                        "text": doc,
                        "filename": metadata["filename"],
                        "page_number": metadata["page_number"],
                        "filepath": metadata["filepath"],
                        "tokens": metadata.get("tokens", 0),
                        "similarity_score": similarity_score
                    })

            logger.info(f"Found {len(similar_chunks)} similar chunks for query")
            return similar_chunks

        except Exception as e:
            logger.error(f"Failed to search vector store: {e}")
            return []

    def get_collection_stats(self) -> Dict[str, int]:
        """Get statistics about the collection.

        Returns:
            Dictionary with collection statistics.
        """
        try:
            count = self.collection.count()
            return {
                "total_chunks": count,
                "collection_name": self.collection_name
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {"total_chunks": 0, "collection_name": self.collection_name}

    def clear_collection(self) -> None:
        """Clear all documents from the collection."""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "PDF document chunks"}
            )
            logger.info(f"Cleared collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            raise

    def get_documents_by_filename(self, filename: str) -> List[Dict[str, str]]:
        """Get all chunks from a specific file.

        Args:
            filename: Name of the file to retrieve chunks for.

        Returns:
            List of chunks from the specified file.
        """
        try:
            results = self.collection.get(
                where={"filename": filename},
                include=["documents", "metadatas"]
            )

            chunks = []
            if results["documents"]:
                for i, doc in enumerate(results["documents"]):
                    metadata = results["metadatas"][i]
                    chunks.append({
                        "text": doc,
                        "filename": metadata["filename"],
                        "page_number": metadata["page_number"],
                        "filepath": metadata["filepath"],
                        "tokens": metadata.get("tokens", 0)
                    })

            return chunks

        except Exception as e:
            logger.error(f"Failed to get documents by filename: {e}")
            return []

    def delete_documents_by_filename(self, filename: str) -> int:
        """Delete all chunks from a specific file.

        Args:
            filename: Name of the file to delete chunks for.

        Returns:
            Number of chunks deleted.
        """
        try:
            # Get all IDs for the filename
            results = self.collection.get(
                where={"filename": filename},
                include=["metadatas"]
            )

            if not results["ids"]:
                return 0

            # Delete the chunks
            self.collection.delete(ids=results["ids"])
            deleted_count = len(results["ids"])
            
            logger.info(f"Deleted {deleted_count} chunks for file: {filename}")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to delete documents by filename: {e}")
            return 0
