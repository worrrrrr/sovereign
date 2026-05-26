"""
Sovereign AI Core Utils

Utility functions for deterministic operations, especially floating-point comparisons.
"""
import math
from typing import Union

Number = Union[int, float]


def approx_eq(a: Number, b: Number, rel_tol: float = 1e-9, abs_tol: float = 1e-12) -> bool:
    """
    Compare two numbers with tolerance for floating-point errors.
    
    This function uses math.isclose() to handle floating-point comparison safely.
    
    Args:
        a: First number
        b: Second number
        rel_tol: Relative tolerance (default 1e-9)
        abs_tol: Absolute tolerance (default 1e-12)
    
    Returns:
        True if numbers are approximately equal, False otherwise
    
    Deterministic behavior: Given same inputs, always returns same result.
    """
    return math.isclose(a, b, rel_tol=rel_tol, abs_tol=abs_tol)


def approx(value: Number) -> "Approximate":
    """
    Create an Approximate object for fluent assertion-style comparisons.
    
    Usage:
        assert approx(0.1 + 0.2) == 0.3  # True
    
    Args:
        value: The computed value to compare
    
    Returns:
        Approximate object for comparison
    """
    return Approximate(value)


class Approximate:
    """
    Wrapper class for approximate equality comparisons.
    
    Enables syntax like: assert approx(0.1 + 0.2) == 0.3
    """
    
    def __init__(self, value: Number, rel_tol: float = 1e-9, abs_tol: float = 1e-12):
        self.value = value
        self.rel_tol = rel_tol
        self.abs_tol = abs_tol
    
    def __eq__(self, other: Number) -> bool:
        """Check if other is approximately equal to self.value"""
        return approx_eq(self.value, other, self.rel_tol, self.abs_tol)
    
    def __repr__(self) -> str:
        return f"approx({self.value})"


def safe_log(message: str, level: str = "INFO") -> None:
    """
    Log a message with timestamp and level.
    
    Args:
        message: Message to log
        level: Log level (INFO, WARNING, ERROR, DEBUG)
    """
    from datetime import datetime
    timestamp = datetime.now().isoformat()
    print(f"[{timestamp}] [{level}] {message}")
