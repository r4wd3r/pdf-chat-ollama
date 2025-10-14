"""Chat engine with Ollama integration and context retrieval."""

import logging
from typing import Dict, List, Optional

import ollama

from .config import CHAT_MODEL, OLLAMA_BASE_URL, SYSTEM_PROMPT
from .history_manager import HistoryManager
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


class ChatEngine:
    """Handles chat interactions with Ollama and context retrieval."""

    def __init__(self, vector_store: VectorStore, history_manager: HistoryManager) -> None:
        """Initialize the chat engine.

        Args:
            vector_store: Vector store for document retrieval.
            history_manager: History manager for conversation persistence.
        """
        self.vector_store = vector_store
        self.history_manager = history_manager
        self.current_session_id: Optional[str] = None
        
        # Configure Ollama client - remove the incorrect initialization
        # The ollama module uses a global client that's automatically configured

    def start_session(self, session_name: Optional[str] = None) -> str:
        """Start a new chat session.

        Args:
            session_name: Optional name for the session.

        Returns:
            Session ID.
        """
        self.current_session_id = self.history_manager.create_session(session_name)
        logger.info(f"Started new chat session: {self.current_session_id}")
        return self.current_session_id

    def load_session(self, session_id: str) -> bool:
        """Load an existing chat session.

        Args:
            session_id: ID of the session to load.

        Returns:
            True if session was loaded successfully, False otherwise.
        """
        session = self.history_manager.get_session(session_id)
        if session:
            self.current_session_id = session_id
            logger.info(f"Loaded chat session: {session_id}")
            return True
        else:
            logger.warning(f"Session not found: {session_id}")
            return False

    def _format_context(self, chunks: List[Dict[str, str]]) -> str:
        """Format retrieved chunks into context for the model.

        Args:
            chunks: List of document chunks with metadata.

        Returns:
            Formatted context string.
        """
        if not chunks:
            return "No relevant documents found."

        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            source_info = f"[Source: {chunk['filename']}, Page {chunk['page_number']}]"
            context_parts.append(f"Document {i} {source_info}:\n{chunk['text']}\n")

        return "\n".join(context_parts)

    def _format_sources(self, chunks: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Format source information for history.

        Args:
            chunks: List of document chunks with metadata.

        Returns:
            List of formatted source information.
        """
        sources = []
        for chunk in chunks:
            sources.append({
                "filename": chunk["filename"],
                "page_number": chunk["page_number"],
                "similarity_score": chunk.get("similarity_score", 0.0),
                "preview": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"]
            })
        return sources

    def _build_prompt(self, user_query: str, context: str) -> str:
        """Build the complete prompt for the model.

        Args:
            user_query: User's question.
            context: Retrieved document context.

        Returns:
            Complete prompt string.
        """
        prompt = f"""{SYSTEM_PROMPT}

Based on the following documents, please answer the user's question. If the information is not available in the provided context, please say so clearly.

Documents:
{context}

Question: {user_query}

Answer:"""
        
        return prompt

    def chat(self, user_query: str) -> Dict[str, str]:
        """Process a user query and return a response.

        Args:
            user_query: User's question.

        Returns:
            Dictionary containing response and metadata.

        Raises:
            ValueError: If no session is active.
            Exception: If chat processing fails.
        """
        if not self.current_session_id:
            raise ValueError("No active chat session. Start a session first.")

        try:
            # Save user message to history
            self.history_manager.add_message(
                self.current_session_id, 
                "user", 
                user_query
            )

            # Retrieve relevant context
            logger.info(f"Searching for relevant context for query: {user_query[:50]}...")
            relevant_chunks = self.vector_store.search_similar(user_query)
            
            if not relevant_chunks:
                response_text = "I couldn't find any relevant information in the uploaded documents to answer your question."
                sources = []
            else:
                # Format context and build prompt
                context = self._format_context(relevant_chunks)
                prompt = self._build_prompt(user_query, context)
                
                # Generate response using Ollama
                logger.info("Generating response with Ollama...")
                response = ollama.chat(
                    model=CHAT_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    stream=False
                )
                
                response_text = response["message"]["content"]
                sources = self._format_sources(relevant_chunks)

            # Save assistant response to history
            self.history_manager.add_message(
                self.current_session_id,
                "assistant", 
                response_text,
                sources
            )

            return {
                "response": response_text,
                "sources": sources,
                "session_id": self.current_session_id
            }

        except Exception as e:
            logger.error(f"Chat processing failed: {e}")
            error_response = f"I encountered an error while processing your question: {str(e)}"
            
            # Save error response to history
            self.history_manager.add_message(
                self.current_session_id,
                "assistant",
                error_response
            )
            
            return {
                "response": error_response,
                "sources": [],
                "session_id": self.current_session_id,
                "error": True
            }

    def stream_chat(self, user_query: str):
        """Process a user query and stream the response.

        Args:
            user_query: User's question.

        Yields:
            Dictionary containing response chunks and metadata.

        Raises:
            ValueError: If no session is active.
            Exception: If chat processing fails.
        """
        if not self.current_session_id:
            raise ValueError("No active chat session. Start a session first.")

        try:
            # Save user message to history
            self.history_manager.add_message(
                self.current_session_id, 
                "user", 
                user_query
            )

            # Retrieve relevant context
            logger.info(f"Searching for relevant context for query: {user_query[:50]}...")
            relevant_chunks = self.vector_store.search_similar(user_query)
            
            if not relevant_chunks:
                response_text = "I couldn't find any relevant information in the uploaded documents to answer your question."
                sources = []
                
                # Save response to history
                self.history_manager.add_message(
                    self.current_session_id,
                    "assistant", 
                    response_text,
                    sources
                )
                
                yield {
                    "response": response_text,
                    "sources": sources,
                    "session_id": self.current_session_id,
                    "done": True
                }
                return

            # Format context and build prompt
            context = self._format_context(relevant_chunks)
            prompt = self._build_prompt(user_query, context)
            sources = self._format_sources(relevant_chunks)

            # Stream response using Ollama
            logger.info("Streaming response with Ollama...")
            response_text = ""
            
            stream = ollama.chat(
                model=CHAT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )

            for chunk in stream:
                if chunk["message"]["content"]:
                    response_text += chunk["message"]["content"]
                    yield {
                        "response": chunk["message"]["content"],
                        "sources": sources if chunk.get("done", False) else [],
                        "session_id": self.current_session_id,
                        "done": chunk.get("done", False)
                    }

            # Save complete response to history
            self.history_manager.add_message(
                self.current_session_id,
                "assistant", 
                response_text,
                sources
            )

        except Exception as e:
            logger.error(f"Stream chat processing failed: {e}")
            error_response = f"I encountered an error while processing your question: {str(e)}"
            
            # Save error response to history
            self.history_manager.add_message(
                self.current_session_id,
                "assistant",
                error_response
            )
            
            yield {
                "response": error_response,
                "sources": [],
                "session_id": self.current_session_id,
                "error": True,
                "done": True
            }

    def get_session_history(self) -> List[Dict]:
        """Get the current session's chat history.

        Returns:
            List of messages in the current session.
        """
        if not self.current_session_id:
            return []
        
        session = self.history_manager.get_session(self.current_session_id)
        return session.get("messages", []) if session else []

    def get_current_session_id(self) -> Optional[str]:
        """Get the current session ID.

        Returns:
            Current session ID or None if no session is active.
        """
        return self.current_session_id
