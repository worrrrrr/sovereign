"""
Sovereign AI Core Package

Core utilities and management for the Sovereign AI system.
"""
from .utils import approx_eq, approx, safe_log
from .rule_engine import RuleEngine
from .memory_manager import MemoryManager

__all__ = [
    'approx_eq',
    'approx', 
    'safe_log',
    'RuleEngine',
    'MemoryManager'
]
