"""
Test Suite for Advanced Memory & Learning System

Tests:
1. Memory Management (consolidation, importance scoring, retrieval)
2. Feedback Learning (pattern learning from corrections)
3. Self-Correction (auto-correction, validation)
4. Performance Tracking (accuracy history, improvement suggestions)
"""
import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta
import sys
sys.path.insert(0, '/workspace')

from core.advanced_memory import (
    AdvancedMemoryManager,
    FeedbackLearningSystem,
    SelfCorrectionLoop,
    MemoryImportance,
    FeedbackType,
    initialize_learning_system
)


class TestAdvancedMemoryManager:
    """Test memory management features."""
    
    @pytest.fixture
    def memory_manager(self, tmp_path):
        """Create a fresh memory manager for each test."""
        return AdvancedMemoryManager(str(tmp_path))
    
    def test_add_memory_basic(self, memory_manager):
        """Test adding basic memory entries."""
        entry = memory_manager.add_memory(
            content="User likes Python programming",
            role="user",
            importance=MemoryImportance.HIGH
        )
        
        assert entry.content == "User likes Python programming"
        assert entry.role == "user"
        assert entry.importance == MemoryImportance.HIGH.value
        assert len(memory_manager.short_term) == 1
    
    def test_memory_consolidation_important(self, memory_manager):
        """Test that important memories are auto-consolidated."""
        entry = memory_manager.add_memory(
            content="Critical user preference",
            role="system",
            importance=MemoryImportance.CRITICAL
        )
        
        # Should be in both short-term and consolidated
        assert len(memory_manager.short_term) == 1
        assert len(memory_manager.consolidated) == 1
        assert memory_manager.consolidated[0].content == entry.content
    
    def test_memory_consolidation_batch(self, memory_manager):
        """Test batch consolidation of memories."""
        # Add several memories
        for i in range(5):
            memory_manager.add_memory(
                content=f"Memory {i}",
                role="user",
                importance=MemoryImportance.MEDIUM if i % 2 == 0 else MemoryImportance.LOW
            )
        
        # Consolidate batch
        count = memory_manager.consolidate_batch()
        
        # Should consolidate MEDIUM importance (3 memories: 0, 2, 4)
        assert count == 3
        assert len(memory_manager.consolidated) == 3
    
    def test_forget_old_memories(self, memory_manager):
        """Test forgetting old, low-importance memories."""
        # Add recent important memory
        memory_manager.add_memory(
            content="Important recent",
            role="user",
            importance=MemoryImportance.HIGH
        )
        
        # Add old trivial memory (manually set timestamp)
        old_entry = memory_manager.add_memory(
            content="Old trivial",
            role="user",
            importance=MemoryImportance.TRIVIAL
        )
        # Modify timestamp to be old
        old_time = (datetime.now() - timedelta(days=10)).isoformat()
        memory_manager.short_term[-1].timestamp = old_time
        memory_manager._save_short_term()
        
        # Forget old memories
        removed = memory_manager.forget_old_memories(days_old=7, min_importance=4)
        
        assert removed == 1
        assert len(memory_manager.short_term) == 1
        assert memory_manager.short_term[0].content == "Important recent"
    
    def test_get_relevant_memories(self, memory_manager):
        """Test retrieving relevant memories by query."""
        # Add memories with different topics
        memory_manager.add_memory(
            content="Python is great for data science",
            role="user",
            tags=["python", "programming"],
            importance=MemoryImportance.HIGH
        )
        memory_manager.add_memory(
            content="Java is good for enterprise",
            role="user",
            tags=["java", "programming"],
            importance=MemoryImportance.MEDIUM
        )
        memory_manager.consolidate_batch(force=True)
        
        # Query for Python-related memories
        relevant = memory_manager.get_relevant_memories("python programming", limit=5)
        
        assert len(relevant) >= 1
        assert "python" in relevant[0].content.lower() or "python" in relevant[0].tags
    
    def test_memory_persistence(self, tmp_path):
        """Test that memories persist across instances."""
        # Create and populate memory manager
        mm1 = AdvancedMemoryManager(str(tmp_path))
        mm1.add_memory(
            content="Persistent memory",
            role="user",
            importance=MemoryImportance.CRITICAL
        )
        
        # Create new instance (should load from disk)
        mm2 = AdvancedMemoryManager(str(tmp_path))
        
        assert len(mm2.short_term) == 1
        assert mm2.short_term[0].content == "Persistent memory"
    
    def test_memory_access_tracking(self, memory_manager):
        """Test that memory access is tracked."""
        entry = memory_manager.add_memory(
            content="Frequently accessed",
            role="user",
            importance=MemoryImportance.HIGH
        )
        memory_manager.consolidate_batch(force=True)
        
        # Access the memory multiple times
        import hashlib
        entry_hash = hashlib.md5(entry.content.encode()).hexdigest()
        
        memory_manager.access_memory(entry_hash)
        memory_manager.access_memory(entry_hash)
        
        # Find the entry in consolidated
        consolidated_entry = None
        for e in memory_manager.consolidated:
            if hashlib.md5(e.content.encode()).hexdigest() == entry_hash:
                consolidated_entry = e
                break
        
        assert consolidated_entry is not None
        assert consolidated_entry.access_count == 2


class TestFeedbackLearningSystem:
    """Test feedback-based learning."""
    
    @pytest.fixture
    def learning_system(self, tmp_path):
        """Create a learning system for testing."""
        memory_manager = AdvancedMemoryManager(str(tmp_path))
        return FeedbackLearningSystem(memory_manager)
    
    def test_collect_positive_feedback(self, learning_system):
        """Test collecting positive feedback."""
        entry = learning_system.collect_feedback(
            query="What is 2+2?",
            response="2+2 equals 4",
            feedback_type=FeedbackType.POSITIVE
        )
        
        assert entry.feedback_type == "positive"
        assert len(learning_system.memory_manager.feedback_log) == 1
    
    def test_learn_from_correction(self, learning_system):
        """Test learning patterns from corrections."""
        # Simulate a correction
        learning_system.learn_from_correction(
            query="หาผลบวกของ 5 และ 3",
            correct_intent="MATH_CALCULATION"
        )
        
        # Check that patterns were learned
        assert len(learning_system.pattern_corrections) > 0
        
        # Should have learned phrases like "หาผลบวกของ"
        found_pattern = False
        for phrase, data in learning_system.pattern_corrections.items():
            if data['intent'] == 'MATH_CALCULATION':
                found_pattern = True
                assert data['count'] == 1
                break
        
        assert found_pattern
    
    def test_get_suggested_intent(self, learning_system):
        """Test getting intent suggestions based on learned patterns."""
        # Learn a pattern
        learning_system.learn_from_correction(
            query="อากาศวันนี้เป็นไง",
            correct_intent="WEATHER_QUERY"
        )
        
        # Get suggestion for similar query
        suggestion = learning_system.get_suggested_intent("อากาศวันนี้เป็นไงบ้าง")
        
        assert suggestion is not None
        intent, confidence = suggestion
        assert intent == "WEATHER_QUERY"
        assert confidence > 0
    
    def test_feedback_persistence(self, tmp_path):
        """Test that feedback persists across instances."""
        mm1 = AdvancedMemoryManager(str(tmp_path))
        ls1 = FeedbackLearningSystem(mm1)
        
        ls1.collect_feedback(
            query="Test query",
            response="Test response",
            feedback_type=FeedbackType.NEGATIVE,
            feedback_text="Incorrect answer"
        )
        
        # Create new instance
        mm2 = AdvancedMemoryManager(str(tmp_path))
        ls2 = FeedbackLearningSystem(mm2)
        
        assert len(ls2.memory_manager.feedback_log) == 1
        assert ls2.memory_manager.feedback_log[0].feedback_type == "negative"
    
    def test_analyze_feedback_trends(self, learning_system):
        """Test analyzing feedback trends."""
        # Add various feedback types
        learning_system.collect_feedback(
            query="Q1", response="A1", feedback_type=FeedbackType.POSITIVE
        )
        learning_system.collect_feedback(
            query="Q2", response="A2", feedback_type=FeedbackType.NEGATIVE,
            feedback_text="Wrong answer"
        )
        learning_system.collect_feedback(
            query="Q3", response="A3", feedback_type=FeedbackType.CORRECTION,
            correct_intent="MATH_CALCULATION"
        )
        
        trends = learning_system.analyze_feedback_trends()
        
        assert trends['total_feedback'] == 3
        assert trends['feedback_distribution']['positive'] == 1
        assert trends['feedback_distribution']['negative'] == 1
        assert trends['feedback_distribution']['correction'] == 1
        assert len(trends['common_issues']) == 2  # negative + correction


class TestSelfCorrectionLoop:
    """Test self-correction mechanisms."""
    
    @pytest.fixture
    def correction_system(self, tmp_path):
        """Create a self-correction system for testing."""
        memory_manager = AdvancedMemoryManager(str(tmp_path))
        feedback_system = FeedbackLearningSystem(memory_manager)
        return SelfCorrectionLoop(memory_manager, feedback_system)
    
    def test_validate_response_valid(self, correction_system):
        """Test validating a correct response."""
        is_valid, error = correction_system.validate_response(
            query="What is Python?",
            response="Python is a programming language known for its simplicity.",
            intent="GENERAL_KNOWLEDGE"
        )
        
        assert is_valid is True
        assert error is None
    
    def test_validate_response_empty(self, correction_system):
        """Test validating an empty response."""
        is_valid, error = correction_system.validate_response(
            query="What is Python?",
            response="",
            intent="GENERAL_KNOWLEDGE"
        )
        
        assert is_valid is False
        assert error == "Empty response"
    
    def test_validate_response_uncertain(self, correction_system):
        """Test validating an uncertain response for non-unknown intent."""
        is_valid, error = correction_system.validate_response(
            query="Calculate 2+2",
            response="I don't know the answer",
            intent="MATH_CALCULATION"
        )
        
        assert is_valid is False
        assert "uncertainty" in error
    
    def test_auto_correct_with_learned_pattern(self, correction_system):
        """Test auto-correction using learned patterns."""
        # First, learn a pattern multiple times to build confidence
        for _ in range(3):
            correction_system.feedback_system.learn_from_correction(
                query="หาผลบวกของ 10 และ 20",
                correct_intent="MATH_CALCULATION"
            )
        
        # Try to auto-correct a wrong classification
        initial_intent = "UNKNOWN"
        initial_response = "I'm not sure what you're asking"
        
        corrected_intent, corrected_response, was_corrected = \
            correction_system.auto_correct(
                query="หาผลบวกของ 10 และ 20",
                initial_response=initial_response,
                initial_intent=initial_intent
            )
        
        assert was_corrected is True
        assert corrected_intent == "MATH_CALCULATION"
        assert "[Auto-corrected]" in corrected_response
    
    def test_track_performance(self, correction_system):
        """Test performance tracking."""
        # Track several queries
        for i in range(10):
            success = i < 8  # 8 successful, 2 failed
            correction_system.track_performance(success=success, response_time_ms=50)
        
        metrics = correction_system.memory_manager.performance_metrics
        
        assert metrics['total_queries'] == 10
        assert metrics['successful_queries'] == 8
        assert metrics['failed_queries'] == 2
        
        # Check accuracy history
        assert len(metrics['accuracy_history']) == 10
        assert metrics['accuracy_history'][-1] == 0.8  # 8/10
    
    def test_get_improvement_suggestions_no_issues(self, correction_system):
        """Test getting suggestions when there are no issues."""
        suggestions = correction_system.get_improvement_suggestions()
        
        # With no feedback, should return empty or minimal suggestions
        assert isinstance(suggestions, list)
    
    def test_get_improvement_suggestions_high_negative(self, correction_system):
        """Test getting suggestions when negative feedback is high."""
        # Add lots of negative feedback
        for i in range(20):
            feedback_type = FeedbackType.NEGATIVE if i < 15 else FeedbackType.POSITIVE
            correction_system.feedback_system.collect_feedback(
                query=f"Query {i}",
                response=f"Response {i}",
                feedback_type=feedback_type,
                feedback_text="Not helpful" if feedback_type == FeedbackType.NEGATIVE else None
            )
        
        suggestions = correction_system.get_improvement_suggestions()
        
        # Should suggest addressing high negative feedback
        assert len(suggestions) > 0
        assert any(s['type'] == 'high_negative_feedback' for s in suggestions)


class TestIntegration:
    """Integration tests for the complete system."""
    
    @pytest.fixture
    def full_system(self, tmp_path):
        """Initialize the complete learning system."""
        return initialize_learning_system(str(tmp_path))
    
    def test_full_workflow(self, full_system):
        """Test complete workflow: memory → feedback → learning → correction."""
        memory = full_system['memory']
        feedback = full_system['feedback']
        correction = full_system['self_correction']
        
        # 1. Add user preference to memory
        memory.add_memory(
            content="User prefers metric units",
            role="user",
            importance=MemoryImportance.CRITICAL,
            tags=["preference", "units"]
        )
        
        # 2. Simulate incorrect response and collect feedback
        feedback.collect_feedback(
            query="Convert 5 miles to kilometers",
            response="5 miles = 8046.72 meters",
            feedback_type=FeedbackType.CORRECTION,
            feedback_text="Should be in kilometers, not meters",
            correct_intent="UNIT_CONVERSION"
        )
        
        # 3. Learn from correction (multiple times to build confidence)
        for _ in range(3):
            feedback.learn_from_correction(
                query="Convert 5 miles to kilometers",
                correct_intent="UNIT_CONVERSION"
            )
        
        # 4. Auto-correct similar query
        corrected_intent, _, was_corrected = correction.auto_correct(
            query="Convert 5 miles to kilometers",
            initial_response="I'm not sure",
            initial_intent="UNKNOWN"
        )
        
        assert was_corrected is True
        assert corrected_intent == "UNIT_CONVERSION"
        
        # 5. Track performance
        correction.track_performance(success=True, response_time_ms=30)
        
        # 6. Get context
        context = memory.get_context()
        assert context['consolidated_count'] >= 1
        assert context['performance']['total_queries'] == 1
    
    def test_system_persistence(self, tmp_path):
        """Test that entire system state persists."""
        # Initialize and use system
        system1 = initialize_learning_system(str(tmp_path))
        system1['memory'].add_memory(
            content="Persistent data",
            role="system",
            importance=MemoryImportance.HIGH
        )
        system1['feedback'].collect_feedback(
            query="Test", response="Test", feedback_type=FeedbackType.POSITIVE
        )
        
        # Reinitialize (should load from disk)
        system2 = initialize_learning_system(str(tmp_path))
        
        assert len(system2['memory'].short_term) == 1
        assert len(system2['feedback'].memory_manager.feedback_log) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
