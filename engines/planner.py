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
            'logic_equation': {
                'tools': ['logic'],
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
        
        # Handle logic/equation solving from AdvancedLogicEngine (Thai language support)
        # ต้องตรวจสอบก่อน algebraic equations เพราะอาจมี pattern ซ้อนกัน
        if task.task_type == 'logic_equation' or params.get('requires_logic_solver'):
            equation_text = params.get('equation', params.get('raw_text', ''))
            if not equation_text:
                equation_text = params.get('original_input', '')
            
            return ExecutionPlan(
                is_valid=True,
                steps=[
                    PlanStep(
                        tool_name='logic',
                        action='solve_equation',
                        parameters={'text': equation_text},
                        description=f"Solve equation/logic: {equation_text}"
                    )
                ],
                task_type=task.task_type,
                intent_id=task.intent_id,
                metadata={'reasoning_type': 'equation_or_logic'}
            )
        
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
            
            # Check nested 'params' key (from IntentParser)
            if not numbers and 'params' in params:
                nested_params = params['params']
                if 'num1' in nested_params and 'num2' in nested_params:
                    numbers = [nested_params['num1'], nested_params['num2']]
                    operator = nested_params.get('operator', '+')
                elif 'numbers' in nested_params:
                    numbers = nested_params['numbers']
                    operator = nested_params.get('operator', '+')
            
            # Fallback to direct num1/num2 in params
            if not numbers and 'num1' in params and 'num2' in params:
                numbers = [params['num1'], params['num2']]
            
            # Get operator (try nested first, then direct)
            if 'params' in params and 'operator' in params['params']:
                operator = params['params']['operator']
            else:
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
        
        # Handle entertainment/joke requests
        if task.task_type == 'entertainment':
            return ExecutionPlan(
                is_valid=True,
                steps=[
                    PlanStep(
                        tool_name='tell_joke',
                        action='tell_joke',
                        parameters={},
                        description="Tell a random joke"
                    )
                ],
                task_type=task.task_type,
                intent_id=task.intent_id,
                metadata={'response_type': 'entertainment'}
            )
        
        # Handle advice/warning requests
        if task.task_type == 'advice_handling':
            advice_text = params.get('raw_text', params.get('original_input', ''))
            return ExecutionPlan(
                is_valid=True,
                steps=[],
                task_type=task.task_type,
                intent_id=task.intent_id,
                metadata={
                    'response_type': 'advice',
                    'intent_type': params.get('intent_type'),
                    'advice_context': advice_text
                }
            )
        
        # Handle financial/payment advice
        if task.task_type == 'financial_advice':
            amount = params.get('amount')
            # Try to extract amount from different possible keys
            if not amount:
                nested_params = params.get('params', {})
                amount = nested_params.get('amount')
            if not amount:
                amount = params.get('value', 0)
            
            if amount and amount > 0:
                return ExecutionPlan(
                    is_valid=True,
                    steps=[
                        PlanStep(
                            tool_name='suggest_payment',
                            action='suggest_payment',
                            parameters={'amount': float(amount), 'currency': 'THB'},
                            description=f"Suggest payment method for {amount} THB"
                        )
                    ],
                    task_type=task.task_type,
                    intent_id=task.intent_id,
                    metadata={'response_type': 'financial_advice', 'amount': amount}
                )
            else:
                return ExecutionPlan(
                    is_valid=False,
                    error_message="No amount specified for payment advice",
                    task_type=task.task_type,
                    intent_id=task.intent_id
                )
        
        # Handle social/emotional responses (no tool needed, just response generation)
        if task.task_type == 'social_response':
            return ExecutionPlan(
                is_valid=True,
                steps=[],
                task_type=task.task_type,
                intent_id=task.intent_id,
                metadata={'response_type': 'social', 'intent_type': params.get('intent_type')}
            )
        
        # Handle system test/noise (acknowledge and move on)
        if task.task_type == 'system_test':
            return ExecutionPlan(
                is_valid=True,
                steps=[],
                task_type=task.task_type,
                intent_id=task.intent_id,
                metadata={'response_type': 'system_ack'}
            )
        
        # Handle command execution (route to appropriate tool based on core_action)
        if task.task_type == 'command_execution':
            core_action = params.get('core_action')
            if core_action:
                # Map core actions to tools (future enhancement)
                return ExecutionPlan(
                    is_valid=False,
                    error_message=f"Command action '{core_action}' not yet implemented",
                    task_type=task.task_type,
                    intent_id=task.intent_id
                )
            else:
                return ExecutionPlan(
                    is_valid=False,
                    error_message="No core action specified for command",
                    task_type=task.task_type,
                    intent_id=task.intent_id
                )
        
        # Handle knowledge queries (future: route to knowledge base)
        if task.task_type == 'knowledge_query':
            # For now, return a mock response for general inquiries
            query_text = params.get('query', params.get('raw_text', ''))
            # If still empty, use the original_input from parameters
            if not query_text:
                query_text = params.get('original_input', 'คำถามทั่วไป')
            return ExecutionPlan(
                is_valid=True,
                steps=[
                    PlanStep(
                        tool_name='knowledge',
                        action='query_general',
                        parameters={'query': query_text},
                        description=f"ตอบคำถามทั่วไป: {query_text}"
                    )
                ],
                task_type=task.task_type,
                intent_id=task.intent_id,
                metadata={'response_type': 'knowledge_mock'}
            )
        
        # Handle logic reasoning / syllogism (e.g., "All X are Y, A is X, is A Y?")
        if task.task_type == 'logic_proof':
            premises = params.get('premises', [])
            conclusion = params.get('conclusion', '')
            if not premises:
                return ExecutionPlan(
                    is_valid=False,
                    error_message="No premises provided for logic reasoning",
                    task_type=task.task_type,
                    intent_id=task.intent_id
                )
            
            return ExecutionPlan(
                is_valid=True,
                steps=[
                    PlanStep(
                        tool_name='symbolic_reasoner',
                        action='evaluate_syllogism',
                        parameters={'premises': premises, 'conclusion': conclusion},
                        description=f"Evaluate logic: {premises} => {conclusion}"
                    )
                ],
                task_type=task.task_type,
                intent_id=task.intent_id,
                metadata={'reasoning_type': 'syllogism'}
            )
        
        # Handle logic/equation solving from AdvancedLogicEngine
        if task.task_type == 'logic_equation' or params.get('requires_logic_solver'):
            equation_text = params.get('equation', params.get('raw_text', ''))
            if not equation_text:
                equation_text = params.get('original_input', '')
            
            return ExecutionPlan(
                is_valid=True,
                steps=[
                    PlanStep(
                        tool_name='logic',
                        action='solve_equation',
                        parameters={'text': equation_text},
                        description=f"Solve equation/logic: {equation_text}"
                    )
                ],
                task_type=task.task_type,
                intent_id=task.intent_id,
                metadata={'reasoning_type': 'equation_or_logic'}
            )
        
        # Default fallback
        return ExecutionPlan(
            is_valid=False,
            error_message=f"No plan available for task type: {task.task_type}",
            task_type=task.task_type,
            intent_id=task.intent_id
        )
