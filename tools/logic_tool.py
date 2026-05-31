"""
Logic Tool - ใช้ AdvancedLogicEngine ในการแก้สมการและโจทย์ตรรกะ
"""
from typing import Dict, Any, Optional
from tools.registry import global_registry
from engines.logic_engine import AdvancedLogicEngine

# Initialize engine
_logic_engine = AdvancedLogicEngine()

def _solve_equation_wrapper(text: str) -> Dict[str, Any]:
    """Wrapper function สำหรับลงทะเบียนใน registry"""
    return LogicTool.solve_equation(text)

# ลงทะเบียน tool กับ registry
global_registry.register(
    name='logic',
    func=_solve_equation_wrapper,
    description='Solve equations and logic problems (Thai language support)',
    category='reasoning',
    actions={
        'solve_equation': _solve_equation_wrapper
    }
)

class LogicTool:
    """Tool สำหรับแก้สมการและโจทย์ตรรกะ"""
    
    @staticmethod
    def solve_equation(text: str) -> Dict[str, Any]:
        """
        แก้สมการหรือโจทย์ตรรกะจากข้อความ
        
        Args:
            text: ข้อความสมการหรือโจทย์ (เช่น "แก้สมการ x + 5 = 10" หรือ "A มากกว่า B อยู่ 5, A+B=15")
        
        Returns:
            Dictionary ที่มี status, solution, และ steps
        """
        result = _logic_engine.execute(text)
        
        if result['status'] == 'success':
            return {
                'success': True,
                'solution': result['data'].get('solution'),
                'steps': result['data'].get('steps', ''),
                'message': result['message'],
                'type': result['data'].get('type', 'unknown')
            }
        else:
            return {
                'success': False,
                'error': result['message']
            }
