"""
Sovereign AI Tool Registry

Centralized library for tool discovery, versioning, and metadata.
All tools must be registered with schema and side effects declaration.
"""
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass, field
import inspect


@dataclass
class ToolSchema:
    """
    Schema definition for a tool.
    
    Attributes:
        name: Unique tool identifier
        version: Semantic version string
        input_schema: Expected input parameter schema
        output_schema: Expected output schema
        side_effects: List of side effects (e.g., 'read_fs', 'write_fs', 'network')
        timeout_ms: Maximum execution time in milliseconds
        execution_type: Type of execution ('python_function', 'subprocess', 'api')
    """
    name: str
    version: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    side_effects: List[str] = field(default_factory=list)
    timeout_ms: int = 5000
    execution_type: str = 'python_function'


class ToolRegistry:
    """
    Central registry for all available tools.
    
    Deterministic behavior: Tools are registered explicitly, no dynamic discovery.
    """
    
    _instance: Optional['ToolRegistry'] = None
    _tools: Dict[str, Dict[str, Any]] = {}
    
    def __new__(cls) -> 'ToolRegistry':
        """Singleton pattern to ensure single registry instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register(
        self,
        name: str,
        func: Callable,
        version: str = "1.0.0",
        input_schema: Optional[Dict[str, Any]] = None,
        output_schema: Optional[Dict[str, Any]] = None,
        side_effects: Optional[List[str]] = None,
        timeout_ms: int = 5000
    ) -> None:
        """
        Register a tool in the registry.
        
        Args:
            name: Unique tool name
            func: The actual function to execute
            version: Version string
            input_schema: Schema describing expected inputs
            output_schema: Schema describing expected outputs
            side_effects: List of side effects
            timeout_ms: Execution timeout
        
        Raises:
            ValueError: If tool already exists or missing required fields
        """
        if name in self._tools:
            raise ValueError(f"Tool '{name}' already registered")
        
        # Infer schemas from function signature if not provided
        if input_schema is None:
            input_schema = self._infer_input_schema(func)
        
        if output_schema is None:
            output_schema = {'type': 'any'}
        
        if side_effects is None:
            side_effects = []
        
        schema = ToolSchema(
            name=name,
            version=version,
            input_schema=input_schema,
            output_schema=output_schema,
            side_effects=side_effects,
            timeout_ms=timeout_ms
        )
        
        self._tools[name] = {
            'schema': schema,
            'func': func
        }
    
    def _infer_input_schema(self, func: Callable) -> Dict[str, Any]:
        """Infer input schema from function signature."""
        sig = inspect.signature(func)
        params = {}
        for param_name, param in sig.parameters.items():
            param_type = param.annotation if param.annotation != inspect.Parameter.empty else Any
            params[param_name] = {
                'type': param_type.__name__ if hasattr(param_type, '__name__') else str(param_type),
                'required': param.default == inspect.Parameter.empty
            }
        return {'parameters': params}
    
    def lookup(self, task_type: str) -> List[Dict[str, Any]]:
        """
        Find tools suitable for a task type.
        
        Args:
            task_type: Type of task to find tools for
        
        Returns:
            List of tool info dictionaries
        """
        # Simple mapping from task_type to tool names
        task_tool_map = {
            'arithmetic': ['subtract', 'add', 'multiply', 'divide'],
            'file_operation': ['read_file', 'write_file', 'delete_file'],
            'count_rows': ['csv_reader', 'filter', 'count']
        }
        
        tool_names = task_tool_map.get(task_type, [])
        results = []
        for name in tool_names:
            if name in self._tools:
                results.append({
                    'name': name,
                    'schema': self._tools[name]['schema'],
                    'func': self._tools[name]['func']
                })
        return results
    
    def get_tool(self, name: str) -> Callable:
        """
        Get a tool function by name.
        
        Args:
            name: Tool name
        
        Returns:
            The tool function
        
        Raises:
            KeyError: If tool not found
        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found")
        return self._tools[name]['func']
    
    def get_schema(self, name: str) -> ToolSchema:
        """
        Get a tool's schema by name.
        
        Args:
            name: Tool name
        
        Returns:
            ToolSchema object
        
        Raises:
            KeyError: If tool not found
        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found")
        return self._tools[name]['schema']
    
    def validate_input(self, tool_name: str, input_data: Dict[str, Any]) -> bool:
        """
        Validate input against tool's schema.
        
        Args:
            tool_name: Name of the tool
            input_data: Input data to validate
        
        Returns:
            True if valid, False otherwise
        """
        if tool_name not in self._tools:
            return False
        
        # Basic validation - check required parameters
        schema = self._tools[tool_name]['schema'].input_schema
        params = schema.get('parameters', {})
        
        for param_name, param_info in params.items():
            if param_info.get('required', False) and param_name not in input_data:
                return False
        
        return True
    
    def list_tools(self) -> List[str]:
        """
        List all registered tool names.
        
        Returns:
            List of tool names
        """
        return list(self._tools.keys())
    
    def unregister(self, name: str) -> None:
        """
        Remove a tool from the registry.
        
        Args:
            name: Tool name to remove
        """
        if name in self._tools:
            del self._tools[name]
