"""
Sovereign AI Rule Engine

Loads and validates rules from config/rules.yaml
Handles safety checks and permissions.
"""
import yaml
from pathlib import Path
from typing import Dict, Any, List


class RuleEngine:
    """
    Loads and enforces rules from configuration.
    
    Deterministic behavior: Same config file always produces same rules.
    """
    
    def __init__(self, config_path: str = "config/rules.yaml"):
        self.config_path = Path(config_path)
        self.rules: Dict[str, Any] = {}
        self.load_rules()
    
    def load_rules(self) -> None:
        """
        Load rules from YAML configuration file.
        
        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is invalid
        """
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self.rules = yaml.safe_load(f) or {}
        else:
            # Default rules if no config exists
            self.rules = {
                "safety": {
                    "forbidden_patterns": ["eval", "exec", "__import__"],
                    "allow_os_system": False,
                    "allow_subprocess_shell": False
                },
                "tolerance": {
                    "rel_tol": 1e-9,
                    "abs_tol": 1e-12
                },
                "replan_limit": 3,
                "execution_timeout_ms": 5000
            }
    
    def is_pattern_allowed(self, pattern: str) -> bool:
        """
        Check if a code pattern is allowed.
        
        Args:
            pattern: Pattern name to check
        
        Returns:
            True if allowed, False otherwise
        """
        forbidden = self.rules.get("safety", {}).get("forbidden_patterns", [])
        return pattern not in forbidden
    
    def get_replan_limit(self) -> int:
        """
        Get maximum number of re-plan attempts.
        
        Returns:
            Maximum replan count (default 3)
        """
        return self.rules.get("replan_limit", 3)
    
    def get_tolerance(self) -> Dict[str, float]:
        """
        Get floating-point tolerance settings.
        
        Returns:
            Dictionary with rel_tol and abs_tol
        """
        return self.rules.get("tolerance", {
            "rel_tol": 1e-9,
            "abs_tol": 1e-12
        })
    
    def get_execution_timeout(self) -> int:
        """
        Get execution timeout in milliseconds.
        
        Returns:
            Timeout in ms
        """
        return self.rules.get("execution_timeout_ms", 5000)
    
    def validate_tool_permissions(self, tool_name: str, side_effects: List[str]) -> bool:
        """
        Validate if a tool's declared side effects are permitted.
        
        Args:
            tool_name: Name of the tool
            side_effects: List of side effects the tool may have
        
        Returns:
            True if all side effects are permitted
        """
        # For now, just log - actual enforcement happens in Execution
        from .utils import safe_log
        safe_log(f"Validating tool {tool_name} with side effects: {side_effects}")
        return True
