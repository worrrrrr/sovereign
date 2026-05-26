"""
Sovereign AI Critic (Verifier) Engine

Deterministic verification of execution output.
Uses tolerance-based comparisons for floating-point results.
"""
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
import math


@dataclass
class VerificationResult:
    """
    Result of output verification.
    
    Attributes:
        status: 'pass' or 'fail'
        reason: Explanation of pass/fail
        suggested_action: What to do next ('return', 'replan', 'fallback')
    """
    status: str  # 'pass' or 'fail'
    reason: str
    suggested_action: str = 'return'


class CriticEngine:
    """
    Verifies execution output against expected constraints.
    
    Verification methods:
    - Schema validation
    - Range/type checks
    - Logical constraints
    - Floating-point tolerance checks
    
    Deterministic behavior: Same input + constraints = same result.
    """
    
    def __init__(self, rel_tol: float = 1e-9, abs_tol: float = 1e-12):
        self.rel_tol = rel_tol
        self.abs_tol = abs_tol
    
    def verify(
        self,
        output: Any,
        constraints: Dict[str, Any],
        expected_type: Optional[type] = None
    ) -> VerificationResult:
        """
        Verify output against constraints.
        
        Args:
            output: The actual output from execution
            constraints: Dictionary of constraints to check
            expected_type: Expected type of output
        
        Returns:
            VerificationResult with status and reason
        
        Deterministic: Same inputs always produce same result.
        """
        # Check type if specified
        if expected_type is not None:
            if not isinstance(output, expected_type):
                return VerificationResult(
                    status='fail',
                    reason=f"Expected type {expected_type.__name__}, got {type(output).__name__}",
                    suggested_action='replan'
                )
        
        # Check each constraint
        for constraint_type, constraint_value in constraints.items():
            result = self._check_constraint(output, constraint_type, constraint_value)
            if result.status == 'fail':
                return result
        
        # All checks passed
        return VerificationResult(
            status='pass',
            reason='All constraints satisfied',
            suggested_action='return'
        )
    
    def _check_constraint(
        self,
        output: Any,
        constraint_type: str,
        constraint_value: Any
    ) -> VerificationResult:
        """
        Check a single constraint.
        
        Args:
            output: The output value
            constraint_type: Type of constraint
            constraint_value: The constraint value/parameters
        
        Returns:
            VerificationResult
        """
        if constraint_type == 'non_negative':
            if isinstance(output, (int, float)) and output < 0:
                return VerificationResult(
                    status='fail',
                    reason='Output must be non-negative',
                    suggested_action='replan'
                )
        
        elif constraint_type == 'max_value':
            if isinstance(output, (int, float)) and output > constraint_value:
                return VerificationResult(
                    status='fail',
                    reason=f'Output exceeds maximum {constraint_value}',
                    suggested_action='replan'
                )
        
        elif constraint_type == 'min_value':
            if isinstance(output, (int, float)) and output < constraint_value:
                return VerificationResult(
                    status='fail',
                    reason=f'Output below minimum {constraint_value}',
                    suggested_action='replan'
                )
        
        elif constraint_type == 'float_tolerance':
            # Special handling for floating-point comparison
            if isinstance(constraint_value, dict):
                expected = constraint_value.get('expected')
                if expected is not None:
                    if not self._approx_eq(output, expected):
                        return VerificationResult(
                            status='fail',
                            reason=f'Output {output} not approximately equal to {expected}',
                            suggested_action='replan'
                        )
        
        elif constraint_type == 'is_integer':
            if not isinstance(output, int):
                if isinstance(output, float) and not output.is_integer():
                    return VerificationResult(
                        status='fail',
                        reason='Output must be an integer',
                        suggested_action='replan'
                    )
        
        elif constraint_type == 'custom':
            # Custom validation function
            if callable(constraint_value):
                try:
                    if not constraint_value(output):
                        return VerificationResult(
                            status='fail',
                            reason='Custom constraint failed',
                            suggested_action='replan'
                        )
                except Exception as e:
                    return VerificationResult(
                        status='fail',
                        reason=f'Custom constraint error: {str(e)}',
                        suggested_action='replan'
                    )
        
        return VerificationResult(
            status='pass',
            reason=f'Constraint {constraint_type} satisfied',
            suggested_action='return'
        )
    
    def _approx_eq(self, a: Any, b: Any) -> bool:
        """
        Check if two values are approximately equal.
        
        Uses relative and absolute tolerance for floating-point comparison.
        
        Args:
            a: First value
            b: Second value
        
        Returns:
            True if approximately equal
        """
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return math.isclose(a, b, rel_tol=self.rel_tol, abs_tol=self.abs_tol)
        return a == b
    
    def verify_arithmetic(
        self,
        result: float,
        num1: float,
        num2: float,
        operator: str
    ) -> VerificationResult:
        """
        Specialized verifier for arithmetic operations.
        
        Checks:
        - Result is a number
        - Result is within reasonable bounds
        - For subtraction: verifies with tolerance
        
        Args:
            result: The computed result
            num1: First operand
            num2: Second operand
            operator: The operation performed
        
        Returns:
            VerificationResult
        """
        # Check it's a number
        if not isinstance(result, (int, float)):
            return VerificationResult(
                status='fail',
                reason='Arithmetic result must be a number',
                suggested_action='replan'
            )
        
        # Verify based on operator
        if operator == '-':
            expected = num1 - num2
            if not self._approx_eq(result, expected):
                return VerificationResult(
                    status='fail',
                    reason=f'Subtraction result {result} != expected {expected}',
                    suggested_action='replan'
                )
        
        elif operator == '+':
            expected = num1 + num2
            if not self._approx_eq(result, expected):
                return VerificationResult(
                    status='fail',
                    reason=f'Addition result {result} != expected {expected}',
                    suggested_action='replan'
                )
        
        elif operator == '*':
            expected = num1 * num2
            if not self._approx_eq(result, expected):
                return VerificationResult(
                    status='fail',
                    reason=f'Multiplication result {result} != expected {expected}',
                    suggested_action='replan'
                )
        
        elif operator == '/':
            if num2 == 0:
                return VerificationResult(
                    status='fail',
                    reason='Division by zero',
                    suggested_action='fallback'
                )
            expected = num1 / num2
            if not self._approx_eq(result, expected):
                return VerificationResult(
                    status='fail',
                    reason=f'Division result {result} != expected {expected}',
                    suggested_action='replan'
                )
        
        return VerificationResult(
            status='pass',
            reason='Arithmetic verification passed',
            suggested_action='return'
        )
