"""
Sovereign AI Math Tools

Mathematical operation tools with proper floating-point handling.
Includes advanced equation solving using SymPy and Z3 for Diophantine equations.
"""
from typing import Dict, Any, List, Union, Optional
from decimal import Decimal, ROUND_HALF_UP
import re


def add(a: float, b: float) -> Dict[str, Any]:
    """
    Add two numbers.
    
    Args:
        a: First number
        b: Second number
    
    Returns:
        Dictionary with result and expression
    """
    result = a + b
    return {
        'operation': 'add',
        'input_a': a,
        'input_b': b,
        'result': result,
        'expression': f"{a} + {b} = {result}"
    }


def subtract(a: float, b: float, verbose: bool = False) -> Dict[str, Any]:
    """
    Subtract b from a.
    
    Uses Decimal for precise arithmetic to avoid floating-point errors.
    
    Args:
        a: Minuend
        b: Subtrahend
        verbose: If True, return detailed steps
        
    Returns:
        Dictionary with result and optionally steps
    """
    # Use Decimal for precise calculation
    a_dec = Decimal(str(a))
    b_dec = Decimal(str(b))
    result = a_dec - b_dec
    result_float = float(result)
    
    if verbose:
        return {
            'operation': 'subtract',
            'input_a': a,
            'input_b': b,
            'result': result_float,
            'expression': f"{a} - {b} = {result_float}",
            'steps': [
                f"จัดหลักทศนิยม: {a} และ {b}",
                f"คำนวณ: {a} - {b}",
                f"ผลลัพธ์: {result_float}"
            ]
        }
    
    return {
        'operation': 'subtract',
        'input_a': a,
        'input_b': b,
        'result': result_float,
        'expression': f"{a} - {b} = {result_float}"
    }


def multiply(a: float, b: float) -> Dict[str, Any]:
    """
    Multiply two numbers.
    
    Args:
        a: First number
        b: Second number
    
    Returns:
        Dictionary with result and expression
    """
    result = a * b
    return {
        'operation': 'multiply',
        'input_a': a,
        'input_b': b,
        'result': result,
        'expression': f"{a} * {b} = {result}"
    }


def divide(a: float, b: float) -> Dict[str, Any]:
    """
    Divide a by b.
    
    Args:
        a: Dividend
        b: Divisor
    
    Returns:
        Dictionary with result and expression
    
    Raises:
        ZeroDivisionError: If b is zero
    """
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    result = a / b
    return {
        'operation': 'divide',
        'input_a': a,
        'input_b': b,
        'result': result,
        'expression': f"{a} / {b} = {result}"
    }


def solve_diophantine_z3(equation_str: str) -> Dict[str, Any]:
    """
    แก้สมการจำนวนเต็ม (Diophantine Equation) โดยใช้ Z3 Solver
    รองรับสมการในรูปแบบ f(x) = k^2 หรือสมการที่มีเงื่อนไขจำนวนเต็ม
    """
    try:
        from z3 import Solver, Int, sat, set_param
        
        # ตั้งค่า Z3
        set_param('smt.arith.nl.round_robin', True)
        
        # สร้างตัวแปร
        x = Int('x')
        k = Int('k')
        
        # Parse สมการอย่างง่าย (รองรับกรณี x^2 + bx + c = k^2)
        # หมายเหตุ: ใน production ควรมี parser ที่ซับซ้อนกว่านี้
        lhs_expr = None
        
        # ตรวจสอบรูปแบบสมการ
        if '=' in equation_str:
            left, right = equation_str.split('=', 1)
            left = left.strip()
            right = right.strip()
            
            # Hardcode parsing สำหรับตัวอย่าง x^2 + 19x - 92 = k^2
            # สามารถขยายเพิ่มได้สำหรับรูปแบบอื่น
            if 'x^2' in left and 'k^2' in right:
                # แยกสัมประสิทธิ์
                # รูปแบบ: ax^2 + bx + c
                import re
                # ลบช่องว่าง
                left = left.replace(' ', '')
                
                # หา a (สัมประสิทธิ์ x^2)
                match_a = re.search(r'(-?\d*)x\^2', left)
                a = 1 # default
                if match_a:
                    grp = match_a.group(1)
                    if grp == '' or grp == '+': a = 1
                    elif grp == '-': a = -1
                    else: a = int(grp)
                
                # หา b (สัมประสิทธิ์ x)
                match_b = re.search(r'([+-]?\d*)x(?!\^)', left)
                b = 0
                if match_b:
                    b_str = match_b.group(1)
                    if b_str == '' or b_str == '+': b = 1
                    elif b_str == '-': b = -1
                    else: b = int(b_str)
                
                # หา c (ค่าคงที่)
                # ใช้ regex หาตัวเลขสุดท้ายที่เป็นค่าคงที่
                match_c = re.search(r'([+-]\d+)$', left)
                c = 0
                if match_c:
                    c = int(match_c.group(1))
                
                # สร้าง constraint: ax^2 + bx + c = k^2
                lhs = a*x*x + b*x + c
                constraint = (lhs == k*k)
                
                s = Solver()
                s.add(constraint)
                
                solutions = set()
                
                # วนลูปหาคำตอบทั้งหมด
                while s.check() == sat and len(solutions) < 100:
                    m = s.model()
                    val_x = m[x].as_long()
                    val_k = m[k].as_long()
                    
                    solutions.add((val_x, abs(val_k))) # เก็บ k เป็นบวกเพื่อไม่ให้นับซ้ำ
                    
                    # Block คำตอบเดิม
                    s.add(x != val_x)
                
                if not solutions:
                    return {
                        'success': True,
                        'solutions': [],
                        'method': 'z3_diophantine',
                        'steps': 'ไม่พบคำตอบจำนวนเต็มในช่วงการค้นหา',
                        'raw_input': equation_str
                    }
                
                # จัดเรียงและตรวจสอบ
                sorted_solutions = sorted(list(solutions), key=lambda item: item[0])
                
                steps = [f"สมการ: {equation_str}", f"วิธีแก้: ใช้ Z3 SMT Solver หาคำตอบจำนวนเต็ม"]
                processed_solutions = []
                
                for vx, vk in sorted_solutions:
                    # Double check ด้วย Python
                    check_val = a*vx*vx + b*vx + c
                    is_correct = (check_val == vk*vk)
                    status = "✅" if is_correct else "❌"
                    step_detail = f"{status} x = {vx}, k = ±{vk} (ตรวจสอบ: {a}*({vx})² + {b}*({vx}) + {c} = {check_val} = {vk}²)"
                    steps.append(step_detail)
                    processed_solutions.append({'x': vx, 'k': vk})
                
                return {
                    'success': True,
                    'solutions': processed_solutions,
                    'method': 'z3_diophantine',
                    'steps': '\n'.join(steps),
                    'raw_input': equation_str
                }
            else:
                # กรณีอื่นๆ ที่ยังไม่ได้ implement
                return {
                    'success': False,
                    'error': 'รูปแบบสมการนี้ยังไม่รองรับในโหมด Diophantine (รองรับเฉพาะ x^2+bx+c=k^2)',
                    'raw_input': equation_str
                }
        else:
            return {
                'success': False,
                'error': 'สมการต้องมีเครื่องหมาย =',
                'raw_input': equation_str
            }
            
    except ImportError:
        return {
            'success': False,
            'error': 'Z3 not installed. Please install with: pip install z3-solver',
            'raw_input': equation_str
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Z3 solver failed: {str(e)}',
            'raw_input': equation_str
        }


def solve_equation(equation_str: str, verbose: bool = False) -> Dict[str, Any]:
    """
    Solve mathematical equations using SymPy or Z3.
    Auto-detects if it's a Diophantine equation (integer solutions), system of equations, or general equation.
    
    Args:
        equation_str: Equation as string, e.g., "2**x = x**6", "x^2 + 19x - 92 = k^2", or "A + B = 15, A - B = 5"
        verbose: If True, return detailed steps
    
    Returns:
        Dictionary with solutions, steps, and metadata
    """
    import re
    
    # ขั้นตอนที่ 1: ตรวจสอบว่าเป็นระบบสมการจาก Perception Parser หรือไม่
    from core.perception import ParameterParser
    parsed_params = ParameterParser.extract_math_operands(equation_str)
    
    # ถ้าเป็นระบบสมการที่ parse ได้จากภาษาไทย
    if parsed_params and parsed_params.get('is_system'):
        equations = parsed_params.get('equations', [])
        if len(equations) >= 2:
            from tools.math_solver import solve_system_of_equations_sympy
            result = solve_system_of_equations_sympy(equations, verbose)
            result['raw_input'] = equation_str
            return result
    
    # ขั้นตอนที่ 2: Clean the input สำหรับกรณีทั่วไป
    # Remove non-mathematical text (e.g., Thai instructions like "แสดงวิธีคิด", "จงหา")
    # Keep only numbers, operators, variables, parentheses, and '='
    # Pattern to keep: digits, letters (variables), operators (+-*/^=), dots, spaces, parentheses
    cleaned_eq = re.sub(r'[^0-9a-zA-Z+\-*/^=().\s]', '', equation_str)
    if not cleaned_eq.strip():
        return {
            'success': False,
            'error': 'ไม่พบสมการคณิตศาสตร์ที่ถูกต้องในข้อความที่ป้อนเข้ามา',
            'raw_input': equation_str
        }
    
    # ตรวจสอบว่าเป็นระบบสมการหรือไม่ (มีหลายสมการคั่นด้วย comma หรือ semicolon)
    if ',' in cleaned_eq and '=' in cleaned_eq:
        # มีโอกาสเป็นระบบสมการ
        equation_parts = [eq.strip() for eq in cleaned_eq.split(',') if '=' in eq]
        if len(equation_parts) >= 2:
            from tools.math_solver import solve_system_of_equations_sympy
            result = solve_system_of_equations_sympy(equation_parts, verbose)
            result['raw_input'] = equation_str
            return result
    
    # ตรวจสอบว่าเป็นสมการ Diophantine หรือไม่ (มี k^2 หรือโจทย์หาจำนวนเต็ม)
    if 'k^2' in cleaned_eq or 'integer solution' in cleaned_eq.lower():
        # ลองใช้ Z3 ก่อน
        result = solve_diophantine_z3(cleaned_eq)
        if result['success']:
            return result
        # ถ้า Z3 ไม่สำเร็จ จะ fall back ไป SymPy (แต่อาจได้คำตอบไม่ครบ)
    
    try:
        from sympy import symbols, Eq, solve, sympify, S
        from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application, convert_xor
        
        # Define transformations to handle ^ as power and implicit multiplication (e.g., 5x -> 5*x)
        transformations = standard_transformations + (implicit_multiplication_application, convert_xor)
        
        # Parse the equation string (using cleaned version)
        if '=' in cleaned_eq:
            left, right = cleaned_eq.split('=', 1)
            left_expr = parse_expr(left.strip(), transformations=transformations)
            right_expr = parse_expr(right.strip(), transformations=transformations)
            equation = Eq(left_expr, right_expr)
        else:
            # Assume it's an expression = 0
            equation = parse_expr(cleaned_eq, transformations=transformations)
        
        # Find all symbols in the equation
        symbols_in_eq = equation.free_symbols
        if not symbols_in_eq:
            # No variables, just evaluate
            result_val = float(equation.lhs.evalf() if hasattr(equation, 'lhs') else equation.evalf())
            return {
                'success': True,
                'solutions': [result_val],
                'method': 'evaluation',
                'steps': f"ประเมินค่าโดยตรง: {cleaned_eq} = {result_val}",
                'raw_input': equation_str
            }
        
        # Use the first symbol as the variable to solve for
        variable = list(symbols_in_eq)[0]
        
        # Solve the equation
        solutions = solve(equation, variable)
        
        # Process solutions
        processed_solutions = []
        steps = []
        steps.append(f"สมการ: {equation_str}")
        steps.append(f"สมการที่ประมวลผล: {cleaned_eq}")
        steps.append(f"ตัวแปรที่พบ: {variable}")
        
        for i, sol in enumerate(solutions):
            try:
                # Try to get numerical value
                if sol.is_real:
                    num_val = complex(sol.evalf())
                    if num_val.imag == 0:
                        processed_solutions.append(float(num_val.real))
                        steps.append(f"คำตอบที่ {i+1}: {variable} ≈ {float(num_val.real):.6f}")
                    else:
                        processed_solutions.append(str(sol))
                        steps.append(f"คำตอบที่ {i+1}: {variable} = {sol} (จำนวนเชิงซ้อน)")
                else:
                    processed_solutions.append(str(sol))
                    steps.append(f"คำตอบที่ {i+1}: {variable} = {sol}")
            except Exception:
                processed_solutions.append(str(sol))
                steps.append(f"คำตอบที่ {i+1}: {variable} = {sol}")
        
        return {
            'success': True,
            'solutions': processed_solutions,
            'method': 'sympy_solve',
            'steps': '\n'.join(steps),
            'variable': str(variable),
            'raw_input': equation_str
        }
        
    except ImportError:
        return {
            'success': False,
            'error': 'SymPy not installed. Please install with: pip install sympy',
            'raw_input': equation_str
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to solve equation: {str(e)}',
            'raw_input': equation_str
        }


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



# ==============================================================================
# Register Math Tools with Global Registry
# ==============================================================================
from tools.registry import global_registry

global_registry.register(
    name="math",
    func=solve_equation,  # Default to the main solver
    description="เครื่องมือแก้สมการคณิตศาสตร์ขั้นสูง (รองรับทั้ง SymPy และ Z3)",
    category="MATHEMATICS",
    actions={
        "solve_equation": solve_equation,
        "add": add,
        "subtract": subtract,
        "multiply": multiply,
        "divide": divide,
        "count": count,
        "filter": filter_list
    }
)
