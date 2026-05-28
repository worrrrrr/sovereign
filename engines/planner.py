"""
Sovereign AI Planner Engine

Creates execution plans from classified tasks.
Routes tasks to appropriate tools based on task type and constraints.
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from engines.perception import Task


@dataclass
class PlanStep:
    """Single step in an execution plan."""
    tool_name: str
    action: str
    parameters: Dict[str, Any]
    description: str = ""


@dataclass
class ExecutionPlan:
    """Complete execution plan for a task."""
    is_valid: bool
    steps: List[PlanStep] = field(default_factory=list)
    task_type: str = ""
    intent_id: str = ""
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class PlannerEngine:
    """
    Creates execution plans from Tasks.
    Determines which tools to use and in what order.
    """
    
    def __init__(self):
        self.tool_registry = self._build_tool_registry()
    
    def _build_tool_registry(self) -> Dict[str, Dict[str, Any]]:
        """Build registry of available tools and their capabilities."""
        return {
            'arithmetic': {
                'tools': ['math'],
                'actions': {
                    '+': 'add',
                    '-': 'subtract',
                    '*': 'multiply',
                    '/': 'divide'
                }
            },
            'algebraic_equation': {
                'tools': ['math'],
                'actions': {
                    'solve': 'solve_equation'
                }
            },
            'greeting': {
                'tools': [],
                'actions': {}
            },
            'time_query': {
                'tools': ['system'],
                'actions': {
                    'get_time': 'get_current_time'
                }
            },
            'joke_request': {
                'tools': ['entertainment'],
                'actions': {
                    'tell_joke': 'get_joke'
                }
            }
        }
    
    def create_plan(self, task: Task) -> ExecutionPlan:
        """
        Create an execution plan from a classified task.
        
        Args:
            task: Task object from Perception Engine
        
        Returns:
            ExecutionPlan object with steps to execute
        """
        params = task.parameters
        constraints = task.constraints
        
        # Handle algebraic equations (e.g., "2**x = x**6")
        if constraints.get('requires_symbolic_solver') or params.get('equation_type') == 'algebraic':
            equation = params.get('equation', params.get('raw_equation', ''))
            if not equation:
                return ExecutionPlan(
                    is_valid=False,
                    error_message="No equation provided to solve",
                    task_type=task.task_type,
                    intent_id=task.intent_id
                )
            
            return ExecutionPlan(
                is_valid=True,
                steps=[
                    PlanStep(
                        tool_name='math',
                        action='solve_equation',
                        parameters={'equation_str': equation},
                        description=f"Solve equation: {equation}"
                    )
                ],
                task_type=task.task_type,
                intent_id=task.intent_id,
                metadata={'equation_type': 'algebraic'}
            )
        
        # Handle simple arithmetic
        if task.task_type == 'arithmetic':
            # Try to get numbers from different possible keys
            numbers = params.get('numbers', [])
            if not numbers and 'num1' in params and 'num2' in params:
                numbers = [params['num1'], params['num2']]
            
            operator = params.get('operator', '+')
            
            if len(numbers) < 2:
                return ExecutionPlan(
                    is_valid=False,
                    error_message="Need at least two numbers for arithmetic operation",
                    task_type=task.task_type,
                    intent_id=task.intent_id
                )
            
            action_name = self.tool_registry.get('arithmetic', {}).get('actions', {}).get(operator)
            if not action_name:
                action_name = 'add'  # Default fallback
            
            expression = f"{numbers[0]} {operator} {numbers[1]}"
            
            return ExecutionPlan(
                is_valid=True,
                steps=[
                    PlanStep(
                        tool_name='math',
                        action=action_name,
                        parameters={'a': numbers[0], 'b': numbers[1]},
                        description=f"Calculate {expression}"
                    )
                ],
                task_type=task.task_type,
                intent_id=task.intent_id,
                metadata={'expression': expression}
            )
        
        # Handle greetings
        if task.task_type == 'greeting':
            return ExecutionPlan(
                is_valid=True,
                steps=[],
                task_type=task.task_type,
                intent_id=task.intent_id,
                metadata={'response_type': 'greeting'}
            )
        
        # Default fallback
        return ExecutionPlan(
            is_valid=False,
            error_message=f"No plan available for task type: {task.task_type}",
            task_type=task.task_type,
            intent_id=task.intent_id
        )
