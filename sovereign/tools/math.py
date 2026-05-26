"""
Sovereign AI Math Tools

Mathematical operation tools with proper floating-point handling.
"""
from typing import Dict, Any
from decimal import Decimal, ROUND_HALF_UP


def add(a: float, b: float) -> float:
    """
    Add two numbers.
    
    Args:
        a: First number
        b: Second number
    
    Returns:
        Sum of a and b
    """
    return a + b


def subtract(a: float, b: float) -> float:
    """
    Subtract b from a.
    
    Uses Decimal for precise arithmetic to avoid floating-point errors.
    
    Args:
        a: Minuend
        b: Subtrahend
    
    Returns:
        Difference (a - b)
    """
    # Use Decimal for precise calculation
    a_dec = Decimal(str(a))
    b_dec = Decimal(str(b))
    result = a_dec - b_dec
    return float(result)


def multiply(a: float, b: float) -> float:
    """
    Multiply two numbers.
    
    Args:
        a: First number
        b: Second number
    
    Returns:
        Product of a and b
    """
    return a * b


def divide(a: float, b: float) -> float:
    """
    Divide a by b.
    
    Args:
        a: Dividend
        b: Divisor
    
    Returns:
        Quotient (a / b)
    
    Raises:
        ZeroDivisionError: If b is zero
    """
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a / b


def count(items: list) -> int:
    """
    Count the number of items in a list.
    
    Args:
        items: List of items
    
    Returns:
        Number of items
    """
    return len(items)


def filter_list(items: list, column: str, value: Any) -> list:
    """
    Filter a list of dicts by column value.
    
    Args:
        items: List of dictionaries
        column: Key to filter on
        value: Value to match
    
    Returns:
        Filtered list
    """
    return [item for item in items if item.get(column) == value]
