"""
Sovereign AI Memory Manager

Handles short-term and long-term memory storage.
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


class MemoryManager:
    """
    Manages conversation memory in JSON format.
    
    Deterministic behavior: Same writes produce same file content.
    """
    
    def __init__(self, memory_dir: str = "data/memory"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        self.short_term_path = self.memory_dir / "short_session.json"
        self.long_term_path = self.memory_dir / "long_term.json"
        
        self.short_term: List[Dict[str, Any]] = []
        self.long_term: Dict[str, Any] = {}
        
        self.load_memory()
    
    def load_memory(self) -> None:
        """Load memory from disk if exists."""
        if self.short_term_path.exists():
            with open(self.short_term_path, 'r') as f:
                self.short_term = json.load(f)
        
        if self.long_term_path.exists():
            with open(self.long_term_path, 'r') as f:
                self.long_term = json.load(f)
    
    def add_to_short_term(self, entry: Dict[str, Any]) -> None:
        """
        Add an entry to short-term memory.
        
        Args:
            entry: Dictionary with at least 'role' and 'content' keys
        """
        entry['timestamp'] = datetime.now().isoformat()
        self.short_term.append(entry)
        self._save_short_term()
    
    def _save_short_term(self) -> None:
        """Save short-term memory to disk."""
        with open(self.short_term_path, 'w') as f:
            json.dump(self.short_term, f, indent=2)
    
    def add_to_long_term(self, key: str, value: Any) -> None:
        """
        Add or update a long-term memory entry.
        
        Args:
            key: Unique identifier for the memory
            value: Value to store
        """
        self.long_term[key] = {
            'value': value,
            'updated_at': datetime.now().isoformat()
        }
        self._save_long_term()
    
    def _save_long_term(self) -> None:
        """Save long-term memory to disk."""
        with open(self.long_term_path, 'w') as f:
            json.dump(self.long_term, f, indent=2)
    
    def get_short_term(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve recent short-term memories.
        
        Args:
            limit: Maximum number of entries to return (None for all)
        
        Returns:
            List of memory entries
        """
        if limit is None:
            return self.short_term.copy()
        return self.short_term[-limit:]
    
    def get_long_term(self, key: Optional[str] = None) -> Any:
        """
        Retrieve long-term memory.
        
        Args:
            key: Specific key to retrieve (None for all)
        
        Returns:
            Memory value(s)
        """
        if key is None:
            return self.long_term.copy()
        return self.long_term.get(key, {}).get('value')
    
    def clear_short_term(self) -> None:
        """Clear short-term memory."""
        self.short_term = []
        self._save_short_term()
    
    def get_context(self) -> Dict[str, Any]:
        """
        Get full context for the orchestrator.
        
        Returns:
            Dictionary containing both short and long term memory
        """
        return {
            'short_term': self.get_short_term(),
            'long_term': self.get_long_term()
        }
