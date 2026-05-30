"""
Sovereign AI - Advanced Memory & Learning System

Features:
1. Context-Aware Memory Consolidation
2. Memory Importance Scoring
3. Feedback-Based Learning
4. Self-Correction Loop
5. Performance Tracking
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib


class MemoryImportance(Enum):
    """Memory importance levels."""
    CRITICAL = 5      # Never forget (user preferences, core facts)
    HIGH = 4          # Long retention (important conversations)
    MEDIUM = 3        # Normal retention (general context)
    LOW = 2           # Short retention (casual chat)
    TRIVIAL = 1       # Quick forget (greetings, small talk)


class FeedbackType(Enum):
    """Types of user feedback."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    CORRECTION = "correction"
    SUGGESTION = "suggestion"


@dataclass
class MemoryEntry:
    """Enhanced memory entry with metadata."""
    content: str
    role: str
    timestamp: str
    importance: int = 3  # Default MEDIUM
    access_count: int = 0
    last_accessed: Optional[str] = None
    tags: List[str] = None
    source: str = "conversation"
    confidence: float = 1.0
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        return cls(**data)


@dataclass
class FeedbackEntry:
    """User feedback entry for learning."""
    query: str
    response: str
    feedback_type: str
    feedback_text: Optional[str]
    correct_intent: Optional[str]
    correct_response: Optional[str]
    timestamp: str
    learned: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeedbackEntry':
        return cls(**data)


class AdvancedMemoryManager:
    """
    Advanced memory management with consolidation and importance scoring.
    """
    
    def __init__(self, memory_dir: str = "data/memory"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.short_term_path = self.memory_dir / "short_session.json"
        self.long_term_path = self.memory_dir / "long_term.json"
        self.consolidated_path = self.memory_dir / "consolidated.json"
        self.feedback_path = self.memory_dir / "feedback.json"
        self.performance_path = self.memory_dir / "performance.json"
        
        # Memory stores
        self.short_term: List[MemoryEntry] = []
        self.long_term: Dict[str, MemoryEntry] = {}
        self.consolidated: List[MemoryEntry] = []
        self.feedback_log: List[FeedbackEntry] = []
        self.performance_metrics: Dict[str, Any] = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'corrections_made': 0,
            'patterns_learned': 0,
            'accuracy_history': [],
            'last_updated': datetime.now().isoformat()
        }
        
        self.load_all()
    
    def load_all(self) -> None:
        """Load all memory stores from disk."""
        if self.short_term_path.exists():
            with open(self.short_term_path, 'r') as f:
                data = json.load(f)
                self.short_term = [MemoryEntry.from_dict(e) for e in data]
        
        if self.long_term_path.exists():
            with open(self.long_term_path, 'r') as f:
                data = json.load(f)
                self.long_term = {k: MemoryEntry.from_dict(v) for k, v in data.items()}
        
        if self.consolidated_path.exists():
            with open(self.consolidated_path, 'r') as f:
                data = json.load(f)
                self.consolidated = [MemoryEntry.from_dict(e) for e in data]
        
        if self.feedback_path.exists():
            with open(self.feedback_path, 'r') as f:
                data = json.load(f)
                self.feedback_log = [FeedbackEntry.from_dict(e) for e in data]
        
        if self.performance_path.exists():
            with open(self.performance_path, 'r') as f:
                self.performance_metrics = json.load(f)
    
    def add_memory(self, content: str, role: str, 
                   importance: MemoryImportance = MemoryImportance.MEDIUM,
                   tags: List[str] = None,
                   source: str = "conversation",
                   confidence: float = 1.0) -> MemoryEntry:
        """Add a memory entry with metadata."""
        entry = MemoryEntry(
            content=content,
            role=role,
            timestamp=datetime.now().isoformat(),
            importance=importance.value,
            tags=tags or [],
            source=source,
            confidence=confidence
        )
        
        self.short_term.append(entry)
        self._save_short_term()
        
        # Auto-consolidate if important
        if importance in [MemoryImportance.CRITICAL, MemoryImportance.HIGH]:
            self.consolidate_memory(entry)
        
        return entry
    
    def consolidate_memory(self, entry: MemoryEntry) -> None:
        """Move important memories to consolidated storage."""
        # Check if already consolidated
        entry_hash = hashlib.md5(entry.content.encode()).hexdigest()
        
        for existing in self.consolidated:
            if hashlib.md5(existing.content.encode()).hexdigest() == entry_hash:
                # Update access count instead of duplicating
                existing.access_count += 1
                existing.last_accessed = datetime.now().isoformat()
                self._save_consolidated()
                return
        
        # Add new consolidated memory
        self.consolidated.append(entry)
        self._save_consolidated()
    
    def consolidate_batch(self, force: bool = False) -> int:
        """
        Consolidate memories from short-term to long-term based on importance.
        
        Args:
            force: Force consolidation of all memories
            
        Returns:
            Number of memories consolidated
        """
        consolidated_count = 0
        
        for entry in self.short_term:
            # Skip if already consolidated
            entry_hash = hashlib.md5(entry.content.encode()).hexdigest()
            already_exists = any(
                hashlib.md5(e.content.encode()).hexdigest() == entry_hash 
                for e in self.consolidated
            )
            
            if already_exists:
                continue
            
            # Consolidate if important or forced
            if force or entry.importance >= MemoryImportance.MEDIUM.value:
                self.consolidated.append(entry)
                consolidated_count += 1
        
        if consolidated_count > 0:
            self._save_consolidated()
        
        return consolidated_count
    
    def forget_old_memories(self, days_old: int = 7, min_importance: int = 3) -> int:
        """
        Remove old, low-importance memories from short-term storage.
        
        Args:
            days_old: Remove memories older than this many days
            min_importance: Don't remove memories with importance >= this value
            
        Returns:
            Number of memories removed
        """
        cutoff_date = datetime.now() - timedelta(days=days_old)
        original_count = len(self.short_term)
        
        filtered_memories = []
        for entry in self.short_term:
            entry_time = datetime.fromisoformat(entry.timestamp)
            
            # Keep if recent enough OR important enough
            if entry_time > cutoff_date or entry.importance >= min_importance:
                filtered_memories.append(entry)
        
        self.short_term = filtered_memories
        self._save_short_term()
        
        return original_count - len(self.short_term)
    
    def access_memory(self, content_hash: str) -> Optional[MemoryEntry]:
        """Record memory access and return the entry."""
        for entry in self.consolidated:
            if hashlib.md5(entry.content.encode()).hexdigest() == content_hash:
                entry.access_count += 1
                entry.last_accessed = datetime.now().isoformat()
                self._save_consolidated()
                return entry
        return None
    
    def get_relevant_memories(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        """
        Retrieve memories relevant to a query.
        Simple keyword matching (can be enhanced with embeddings).
        """
        query_words = set(query.lower().split())
        
        scored_memories = []
        for entry in self.consolidated + self.short_term:
            content_words = set(entry.content.lower().split())
            tags_set = set(t.lower() for t in entry.tags)
            
            # Calculate relevance score
            word_overlap = len(query_words & content_words)
            tag_overlap = len(query_words & tags_set) * 2  # Tags weighted higher
            
            score = (word_overlap + tag_overlap) * entry.importance
            score *= (1 + entry.access_count * 0.1)  # Boost frequently accessed
            
            if score > 0:
                scored_memories.append((score, entry))
        
        # Sort by score descending
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        
        return [entry for _, entry in scored_memories[:limit]]
    
    def _save_short_term(self) -> None:
        with open(self.short_term_path, 'w') as f:
            json.dump([e.to_dict() for e in self.short_term], f, indent=2)
    
    def _save_consolidated(self) -> None:
        with open(self.consolidated_path, 'w') as f:
            json.dump([e.to_dict() for e in self.consolidated], f, indent=2)
    
    def get_context(self) -> Dict[str, Any]:
        """Get full context including relevant memories."""
        return {
            'short_term': [e.to_dict() for e in self.short_term[-10:]],
            'consolidated_count': len(self.consolidated),
            'long_term_count': len(self.long_term),
            'performance': self.performance_metrics
        }


class FeedbackLearningSystem:
    """
    Learns from user feedback to improve system performance.
    """
    
    def __init__(self, memory_manager: AdvancedMemoryManager):
        self.memory_manager = memory_manager
        self.pattern_corrections: Dict[str, Dict[str, Any]] = {}
        self.intent_adjustments: Dict[str, float] = {}
        
        self.load_learning_data()
    
    def load_learning_data(self) -> None:
        """Load previously learned patterns."""
        learning_file = self.memory_manager.memory_dir / "learned_patterns.json"
        if learning_file.exists():
            with open(learning_file, 'r') as f:
                data = json.load(f)
                self.pattern_corrections = data.get('pattern_corrections', {})
                self.intent_adjustments = data.get('intent_adjustments', {})
    
    def save_learning_data(self) -> None:
        """Save learned patterns to disk."""
        learning_file = self.memory_manager.memory_dir / "learned_patterns.json"
        with open(learning_file, 'w') as f:
            json.dump({
                'pattern_corrections': self.pattern_corrections,
                'intent_adjustments': self.intent_adjustments,
                'last_updated': datetime.now().isoformat()
            }, f, indent=2)
    
    def collect_feedback(self, query: str, response: str, 
                        feedback_type: FeedbackType,
                        feedback_text: Optional[str] = None,
                        correct_intent: Optional[str] = None,
                        correct_response: Optional[str] = None) -> FeedbackEntry:
        """Collect user feedback for learning."""
        entry = FeedbackEntry(
            query=query,
            response=response,
            feedback_type=feedback_type.value,
            feedback_text=feedback_text,
            correct_intent=correct_intent,
            correct_response=correct_response,
            timestamp=datetime.now().isoformat()
        )
        
        self.memory_manager.feedback_log.append(entry)
        self._save_feedback()
        
        # Process feedback immediately for corrections
        if feedback_type == FeedbackType.CORRECTION and correct_intent:
            self.learn_from_correction(query, correct_intent)
        
        return entry
    
    def learn_from_correction(self, query: str, correct_intent: str) -> None:
        """Learn from a correction by adjusting patterns."""
        # Extract key phrases from query
        words = query.lower().split()
        key_phrases = []
        
        # Generate n-grams
        for n in range(1, 4):
            for i in range(len(words) - n + 1):
                phrase = ' '.join(words[i:i+n])
                if len(phrase) > 2:  # Skip very short phrases
                    key_phrases.append(phrase)
        
        # Store pattern correction
        for phrase in key_phrases:
            if phrase not in self.pattern_corrections:
                self.pattern_corrections[phrase] = {
                    'intent': correct_intent,
                    'count': 0,
                    'examples': []
                }
            
            self.pattern_corrections[phrase]['count'] += 1
            if len(self.pattern_corrections[phrase]['examples']) < 5:
                self.pattern_corrections[phrase]['examples'].append(query)
        
        self.save_learning_data()
        
        # Update performance metrics
        self.memory_manager.performance_metrics['patterns_learned'] += 1
        self._save_performance()
    
    def get_suggested_intent(self, query: str) -> Optional[Tuple[str, float]]:
        """Get suggested intent based on learned patterns."""
        words = query.lower().split()
        
        best_match = None
        best_score = 0
        
        for phrase, data in self.pattern_corrections.items():
            if phrase in query.lower():
                # Score based on phrase length and correction count
                score = len(phrase.split()) * data['count']
                if score > best_score:
                    best_score = score
                    best_match = data['intent']
        
        if best_match:
            confidence = min(1.0, best_score / 10.0)  # Normalize to 0-1
            return (best_match, confidence)
        
        return None
    
    def analyze_feedback_trends(self) -> Dict[str, Any]:
        """Analyze feedback trends for system improvement."""
        if not self.memory_manager.feedback_log:
            return {'status': 'no_feedback'}
        
        feedback_types = {}
        common_issues = []
        
        for entry in self.memory_manager.feedback_log:
            feedback_types[entry.feedback_type] = feedback_types.get(entry.feedback_type, 0) + 1
            
            if entry.feedback_type == 'negative' or entry.feedback_type == 'correction':
                common_issues.append({
                    'query': entry.query,
                    'issue': entry.feedback_text or 'No details provided'
                })
        
        return {
            'total_feedback': len(self.memory_manager.feedback_log),
            'feedback_distribution': feedback_types,
            'common_issues': common_issues[:10],  # Top 10 issues
            'learned_patterns': len(self.pattern_corrections)
        }
    
    def _save_feedback(self) -> None:
        with open(self.memory_manager.feedback_path, 'w') as f:
            json.dump([e.to_dict() for e in self.memory_manager.feedback_log], f, indent=2)
    
    def _save_performance(self) -> None:
        self.memory_manager.performance_metrics['last_updated'] = datetime.now().isoformat()
        with open(self.memory_manager.performance_path, 'w') as f:
            json.dump(self.memory_manager.performance_metrics, f, indent=2)


class SelfCorrectionLoop:
    """
    Implements self-correction mechanism for continuous improvement.
    """
    
    def __init__(self, memory_manager: AdvancedMemoryManager, 
                 feedback_system: FeedbackLearningSystem):
        self.memory_manager = memory_manager
        self.feedback_system = feedback_system
    
    def validate_response(self, query: str, response: str, 
                         intent: str) -> Tuple[bool, Optional[str]]:
        """
        Validate if a response is appropriate for the query and intent.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for empty responses
        if not response or not response.strip():
            return (False, "Empty response")
        
        # Check for contradiction patterns
        contradiction_patterns = [
            "i don't know",
            "i cannot",
            "i can't",
            "not sure",
            "unable to"
        ]
        
        response_lower = response.lower()
        if any(pattern in response_lower for pattern in contradiction_patterns):
            if intent not in ['UNKNOWN', 'CLARIFICATION_NEEDED']:
                return (False, f"Response indicates uncertainty for intent {intent}")
        
        # Check response length appropriateness
        if len(response) < 5 and intent not in ['GREETING', 'FAREWELL']:
            return (False, "Response too short for intent")
        
        return (True, None)
    
    def auto_correct(self, query: str, initial_response: str, 
                    initial_intent: str) -> Tuple[str, str, bool]:
        """
        Attempt to auto-correct a response based on learned patterns.
        
        Returns:
            Tuple of (corrected_intent, corrected_response, was_corrected)
        """
        # Check if we have learned patterns for this query
        suggestion = self.feedback_system.get_suggested_intent(query)
        
        if suggestion:
            suggested_intent, confidence = suggestion
            
            # Only auto-correct if confidence is high
            if confidence > 0.7 and suggested_intent != initial_intent:
                # Log the correction
                self.feedback_system.collect_feedback(
                    query=query,
                    response=initial_response,
                    feedback_type=FeedbackType.CORRECTION,
                    correct_intent=suggested_intent
                )
                
                self.memory_manager.performance_metrics['corrections_made'] += 1
                
                return (suggested_intent, f"[Auto-corrected] {initial_response}", True)
        
        return (initial_intent, initial_response, False)
    
    def track_performance(self, success: bool, response_time_ms: float = 0) -> None:
        """Track query performance for analytics."""
        self.memory_manager.performance_metrics['total_queries'] += 1
        
        if success:
            self.memory_manager.performance_metrics['successful_queries'] += 1
        else:
            self.memory_manager.performance_metrics['failed_queries'] += 1
        
        # Update accuracy history (keep last 100 queries)
        accuracy = (
            self.memory_manager.performance_metrics['successful_queries'] /
            self.memory_manager.performance_metrics['total_queries']
        )
        
        history = self.memory_manager.performance_metrics['accuracy_history']
        history.append(accuracy)
        if len(history) > 100:
            history.pop(0)
        
        self.memory_manager.performance_metrics['accuracy_history'] = history
        self.feedback_system._save_performance()
    
    def get_improvement_suggestions(self) -> List[Dict[str, Any]]:
        """Generate suggestions for system improvement."""
        suggestions = []
        
        # Analyze feedback trends
        trends = self.feedback_system.analyze_feedback_trends()
        
        if trends.get('status') != 'no_feedback':
            # Check for common issues
            if len(trends.get('common_issues', [])) > 0:
                suggestions.append({
                    'type': 'common_issues',
                    'priority': 'high',
                    'description': f"Found {len(trends['common_issues'])} common issues to address",
                    'issues': trends['common_issues'][:5]
                })
            
            # Check feedback distribution
            dist = trends.get('feedback_distribution', {})
            negative_count = dist.get('negative', 0) + dist.get('correction', 0)
            total = sum(dist.values())
            
            if total > 10 and negative_count / total > 0.3:
                suggestions.append({
                    'type': 'high_negative_feedback',
                    'priority': 'critical',
                    'description': f"High negative feedback rate: {negative_count/total:.1%}"
                })
        
        # Check accuracy trend
        history = self.memory_manager.performance_metrics.get('accuracy_history', [])
        if len(history) >= 10:
            recent_avg = sum(history[-10:]) / 10
            older_avg = sum(history[-20:-10]) / 10 if len(history) >= 20 else recent_avg
            
            if recent_avg < older_avg * 0.9:
                suggestions.append({
                    'type': 'declining_accuracy',
                    'priority': 'high',
                    'description': f"Accuracy declining: {older_avg:.1%} → {recent_avg:.1%}"
                })
        
        return suggestions


# Convenience function to initialize all components
def initialize_learning_system(memory_dir: str = "data/memory"):
    """Initialize the complete memory and learning system."""
    memory_manager = AdvancedMemoryManager(memory_dir)
    feedback_system = FeedbackLearningSystem(memory_manager)
    self_correction = SelfCorrectionLoop(memory_manager, feedback_system)
    
    return {
        'memory': memory_manager,
        'feedback': feedback_system,
        'self_correction': self_correction
    }
