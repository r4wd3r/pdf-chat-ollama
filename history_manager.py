"""Chat history management with persistent storage."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from config import HISTORY_DB_PATH

logger = logging.getLogger(__name__)


class HistoryManager:
    """Manages chat history persistence and retrieval."""

    def __init__(self) -> None:
        """Initialize the history manager."""
        self.history_file = HISTORY_DB_PATH
        self._ensure_history_file_exists()

    def _ensure_history_file_exists(self) -> None:
        """Ensure the history file exists with proper structure."""
        if not self.history_file.exists():
            self._save_history({"sessions": []})

    def _load_history(self) -> Dict:
        """Load chat history from file.

        Returns:
            Dictionary containing chat history data.
        """
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to load history: {e}. Creating new history.")
            return {"sessions": []}

    def _save_history(self, history_data: Dict) -> None:
        """Save chat history to file.

        Args:
            history_data: Dictionary containing chat history data.
        """
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save history: {e}")
            raise

    def create_session(self, session_name: Optional[str] = None) -> str:
        """Create a new chat session.

        Args:
            session_name: Optional name for the session.

        Returns:
            Session ID.
        """
        history = self._load_history()
        
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        if session_name:
            session_id = f"{session_id}_{session_name}"
        
        new_session = {
            "id": session_id,
            "name": session_name or f"Session {session_id}",
            "created_at": datetime.now().isoformat(),
            "messages": []
        }
        
        history["sessions"].append(new_session)
        self._save_history(history)
        
        logger.info(f"Created new session: {session_id}")
        return session_id

    def add_message(
        self, 
        session_id: str, 
        role: str, 
        content: str, 
        sources: Optional[List[Dict]] = None
    ) -> None:
        """Add a message to a chat session.

        Args:
            session_id: ID of the session.
            role: Role of the message sender ('user' or 'assistant').
            content: Message content.
            sources: Optional list of source documents used.
        """
        history = self._load_history()
        
        # Find the session
        session = None
        for s in history["sessions"]:
            if s["id"] == session_id:
                session = s
                break
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "sources": sources or []
        }
        
        session["messages"].append(message)
        session["updated_at"] = datetime.now().isoformat()
        
        self._save_history(history)
        logger.debug(f"Added {role} message to session {session_id}")

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get a specific chat session.

        Args:
            session_id: ID of the session to retrieve.

        Returns:
            Session data or None if not found.
        """
        history = self._load_history()
        
        for session in history["sessions"]:
            if session["id"] == session_id:
                return session
        
        return None

    def get_all_sessions(self) -> List[Dict]:
        """Get all chat sessions.

        Returns:
            List of all sessions sorted by creation date (newest first).
        """
        history = self._load_history()
        
        # Sort by creation date (newest first)
        sessions = sorted(
            history["sessions"], 
            key=lambda x: x.get("created_at", ""), 
            reverse=True
        )
        
        return sessions

    def get_recent_sessions(self, limit: int = 10) -> List[Dict]:
        """Get recent chat sessions.

        Args:
            limit: Maximum number of sessions to return.

        Returns:
            List of recent sessions.
        """
        sessions = self.get_all_sessions()
        return sessions[:limit]

    def delete_session(self, session_id: str) -> bool:
        """Delete a chat session.

        Args:
            session_id: ID of the session to delete.

        Returns:
            True if session was deleted, False if not found.
        """
        history = self._load_history()
        
        original_count = len(history["sessions"])
        history["sessions"] = [
            s for s in history["sessions"] 
            if s["id"] != session_id
        ]
        
        if len(history["sessions"]) < original_count:
            self._save_history(history)
            logger.info(f"Deleted session: {session_id}")
            return True
        
        return False

    def clear_all_history(self) -> None:
        """Clear all chat history."""
        self._save_history({"sessions": []})
        logger.info("Cleared all chat history")

    def get_session_summary(self, session_id: str) -> Optional[Dict]:
        """Get a summary of a chat session.

        Args:
            session_id: ID of the session.

        Returns:
            Session summary or None if not found.
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        messages = session.get("messages", [])
        user_messages = [m for m in messages if m["role"] == "user"]
        assistant_messages = [m for m in messages if m["role"] == "assistant"]
        
        return {
            "id": session["id"],
            "name": session["name"],
            "created_at": session["created_at"],
            "updated_at": session.get("updated_at"),
            "total_messages": len(messages),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "last_message": messages[-1] if messages else None
        }

    def export_session(self, session_id: str, file_path: Path) -> bool:
        """Export a session to a JSON file.

        Args:
            session_id: ID of the session to export.
            file_path: Path to save the exported session.

        Returns:
            True if export was successful, False otherwise.
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(session, f, indent=2, ensure_ascii=False)
            logger.info(f"Exported session {session_id} to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export session: {e}")
            return False

    def import_session(self, file_path: Path) -> Optional[str]:
        """Import a session from a JSON file.

        Args:
            file_path: Path to the session file to import.

        Returns:
            Session ID if import was successful, None otherwise.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Validate session data
            if not all(key in session_data for key in ["id", "name", "created_at", "messages"]):
                logger.error("Invalid session data format")
                return None
            
            history = self._load_history()
            
            # Check if session already exists
            for existing_session in history["sessions"]:
                if existing_session["id"] == session_data["id"]:
                    logger.warning(f"Session {session_data['id']} already exists")
                    return None
            
            history["sessions"].append(session_data)
            self._save_history(history)
            
            logger.info(f"Imported session: {session_data['id']}")
            return session_data["id"]
            
        except Exception as e:
            logger.error(f"Failed to import session: {e}")
            return None
