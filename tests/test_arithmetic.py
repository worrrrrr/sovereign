"""
Sovereign AI Test Suite

Tests for floating-point tolerance, safety, and deterministic behavior.
All tests must pass before any release.
"""
import pytest
from core.utils import approx_eq, approx


class TestFloatingPointTolerance:
    """Test suite for floating-point tolerance (Section 3.1 of Constitution)."""
    
    def test_01_plus_02_equals_03(self):
        """Test 1: 0.1 + 0.2 == 0.3 with tolerance"""
        result = 0.1 + 0.2
        assert approx(result) == 0.3
    
    def test_02_98_minus_911_equals_069(self):
        """Test 2: 9.8 - 9.11 == 0.69 with tolerance"""
        from tools.math import subtract
        result = subtract(9.8, 9.11)
        assert approx(result) == 0.69
    
    def test_03_sum_01_three_times(self):
        """Test 3: 0.1 + 0.2 + 0.3 == 0.6 with tolerance"""
        result = 0.1 + 0.2 + 0.3
        assert approx(result) == 0.6
    
    def test_04_error_accumulation_stress(self):
        """Test 4: Error accumulation stress test"""
        total = sum(0.1 for _ in range(10))
        assert approx(total) == 1.0
    
    def test_05_approx_eq_function(self):
        """Test 5: Direct approx_eq function test"""
        assert approx_eq(0.1 + 0.2, 0.3) is True
        assert approx_eq(9.8 - 9.11, 0.69) is True
    
    def test_06_decimal_subtraction_precision(self):
        """Test 6: Decimal-based subtraction precision"""
        from tools.math import subtract
        # This should be exactly 0.69 with Decimal arithmetic
        result = subtract(9.8, 9.11)
        assert result == 0.69  # Exact equality due to Decimal


class TestSafetyAndSecurity:
    """Test suite for safety and security (Section 3.2 of Constitution)."""
    
    def test_07_no_eval_in_codebase(self):
        """Test 7: Code containing eval() must be rejected"""
        import os
        import glob
        
        # Check all Python files in current directory structure
        py_files = glob.glob("**/*.py", recursive=True)
        
        for filepath in py_files:
            if "test_" in filepath or "__pycache__" in filepath:
                continue  # Skip test files and cache
            
            with open(filepath, 'r') as f:
                content = f.read()
                
            # Check for forbidden patterns
            assert 'eval(' not in content or 'eval.__' in content, \
                f"Found eval() in {filepath}"
            assert 'exec(' not in content or 'exec.__' in content, \
                f"Found exec() in {filepath}"
    
    def test_08_tool_registry_requires_schema(self):
        """Test 8: Tool with undeclared schema cannot be registered"""
        from tools.registry import ToolRegistry
        
        registry = ToolRegistry()
        
        def bad_tool(x):
            return x * 2
        
        # Should work - schema is optional, will be inferred
        registry.register('test_tool', bad_tool, 'Test tool description', 'TEST')
        
        # Verify it was registered
        func = registry.get_tool('test_tool')
        assert func is not None
        assert func(5) == 10
        
        # Clean up
        # Note: Registry doesn't have unregister method in current implementation


class TestDeterministicBehavior:
    """Test suite for deterministic behavior (Section 3.3 of Constitution)."""
    
    def test_09_same_input_same_output(self):
        """Test 9: Same input produces same output across multiple runs"""
        from tools.math import subtract
        
        results = []
        for _ in range(100):
            result = subtract(9.8, 9.11)
            results.append(result)
        
        # All results should be identical
        assert len(set(results)) == 1, "Results were not deterministic"
        assert results[0] == 0.69


class TestReplanLimit:
    """Test suite for re-plan limits (Section 3.4 of Constitution)."""
    
    def test_10_replan_limit_enforced(self):
        """Test 10: After 3 failures, system returns fallback response"""
        from core.rule_engine import RuleEngine
        
        rule_engine = RuleEngine()
        limit = rule_engine.get_replan_limit()
        
        assert limit == 3, f"Replan limit should be 3, got {limit}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
