import re
from typing import Optional, Tuple, Dict, Any, List, Union
from z3 import Solver, Real, Const, sat, set_param, RealVal, simplify, And
import math
from sympy import symbols, Eq, solve as sympy_solve, parse_expr as sympy_parse

# ตั้งค่า Timeout ให้ Z3 เพื่อไม่ให้ค้างนานเกินไป (หน่วยเป็นมิลลิวินาที)
set_param('timeout', 5000)  # 5 วินาที

def solve_equation_z3(equation_str: str, verbose: bool = False) -> Dict[str, Any]:
    """
    แก้สมการคณิตศาสตร์โดยใช้ Z3 Solver และ SymPy
    รองรับสมการรูปแบบต่างๆ เช่น 3^x = x^9, 4^x = x^8, x + 5 = 10
    และระบบสมการหลายตัวแปร เช่น "A + B = 15, A - B = 5"
    """
    result = {
        "success": False,
        "solutions": [],
        "method": "z3_solver",
        "steps": [],
        "error": None
    }

    if verbose:
        result["steps"].append(f"**วิเคราะห์สมการ:** {equation_str}")

    try:
        # 1. ตรวจสอบว่าเป็นระบบสมการหรือไม่ (มีเครื่องหมายจุลภาคหรือ newline คั่น)
        equation_parts = re.split(r'[,;]\s*|\n', equation_str)
        
        # ถ้ามีมากกว่า 1 สมการ ให้ใช้ SymPy แก้ระบบสมการ
        if len(equation_parts) > 1:
            return solve_system_of_equations_sympy(equation_parts, verbose)
        
        # 2. ทำความสะอาดสมการและแปลงสัญลักษณ์ให้ Python/Z3 เข้าใจ
        # แทน '^' ด้วย '**' สำหรับยกกำลัง
        clean_eq = equation_str.replace('^', '**')
        
        # แยกฝั่งซ้ายและขวาของสมการ
        if '=' in clean_eq:
            parts = clean_eq.split('=')
            if len(parts) != 2:
                raise ValueError("สมการต้องมีเครื่องหมาย '=' เพียงหนึ่งจุด")
            lhs_str, rhs_str = parts[0].strip(), parts[1].strip()
        else:
            # ถ้าไม่มี '=' ถือว่าเป็นนิพจน์ที่ต้องการหาค่าให้เป็น 0 (เช่น x**2 - 4)
            lhs_str = clean_eq
            rhs_str = "0"

        # 2. สร้างตัวแปรใน Z3 (รองรับ x, y, z หรือตัวแปรอื่นๆ ที่พบ)
        # ค้นหาตัวแปรที่เป็นอักษรภาษาอังกฤษตัวเดียวหรือหลายตัว
        # ต้องกรองคำสงวนของ Python และฟังก์ชัน math ออก
        reserved_words = {'sin', 'cos', 'tan', 'exp', 'log', 'sqrt', 'pi', 'e', 'abs'}
        all_words = set(re.findall(r'\b[a-zA-Z]+\b', lhs_str + rhs_str))
        variables = [w for w in all_words if w not in reserved_words]
        
        # ในขั้นพื้นฐานสมมติว่าเป็นตัวแปรธรรมดา
        z3_vars = {}
        for var in variables:
            z3_vars[var] = Real(var)

        if not z3_vars:
            result["error"] = "ไม่พบตัวแปรในสมการ"
            return result

        # 3. แปลงสตริงเป็นนิพจน์ Z3 อย่างปลอดภัย
        # หมายเหตุ: eval ในที่นี้ใช้กับ context ที่ควบคุมได้เท่านั้น (เฉพาะตัวแปรที่สร้างจาก Z3)
        # เพื่อความปลอดภัยยิ่งขึ้น อาจต้องใช้ Parser แบบ Recursive Descent ใน production
        # เพิ่มฟังก์ชันคณิตศาสตร์ที่ Z3 รองรับ (หรือจะ mock ไว้ก่อน)
        local_dict = {**z3_vars, 'pi': math.pi, 'e': math.e}
        
        # แทนที่ฟังก์ชันคณิตศาสตร์ด้วย Z3 equivalents ถ้ามี
        # หมายเหตุ: Z3 ไม่รองรับ pow แบบ real exponent โดยตรงในบางกรณี
        # เราจะลอง eval ดูก่อน ถ้าไม่ได้ค่อย fallback
        
        try:
            # ใช้ ast.literal_eval หรือ sympy แทน eval เพื่อความปลอดภัย
            from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application, convert_xor
            transformations = standard_transformations + (implicit_multiplication_application, convert_xor)
            
            lhs_expr = parse_expr(lhs_str, transformations=transformations, local_dict=local_dict)
            rhs_expr = parse_expr(rhs_str, transformations=transformations, local_dict=local_dict)
        except Exception as e:
            # ถ้า parsing ล้มเหลว อาจเป็นเพราะฟังก์ชันที่ไม่รองรับ หรือ syntax
            # ลอง fallback ไปใช้ numerical method ทันที
            if verbose:
                result["steps"].append(f"**SymPy parsing ล้มเหลว: {str(e)}**")
                result["steps"].append("**เปลี่ยนไปใช้ Numerical Method ทันที**")
            return solve_equation_numerical(equation_str, verbose)

        # สร้างสมการ Z3: lhs == rhs
        z3_eq = lhs_expr == rhs_expr

        if verbose:
            result["steps"].append(f"**สร้างโมเดล Z3:** {lhs_str} = {rhs_str}")
            result["steps"].append(f"**ตัวแปรที่พบ:** {', '.join(z3_vars.keys())}")

        # 4. แก้สมการด้วย Z3 Solver
        s = Solver()
        s.add(z3_eq)

        solutions = []
        # พยายามหาคำตอบหลายๆ คำตอบ (ถ้ามี)
        # หมายเหตุ: Z3 อาจหาคำตอบได้เพียงหนึ่งคำตอบต่อรอบสำหรับสมการไม่เชิงเส้นที่ซับซ้อน
        # เราอาจต้องเพิ่ม constraint เพื่อให้หาคำตอบอื่นต่อ
        
        # รอบแรก: หาคำตอบพื้นฐาน
        if s.check() == sat:
            m = s.model()
            sol = {}
            for var_name, z3_var in z3_vars.items():
                val = m.evaluate(z3_var)
                # แปลงค่าจาก Z3 เป็น float หรือ int
                try:
                    numeric_val = float(val.as_decimal(10)) # ความละเอียด 10 หลัก
                    # ปัดเศษถ้าเป็นจำนวนเต็มใกล้เคียง
                    if abs(numeric_val - round(numeric_val)) < 1e-7:
                        numeric_val = round(numeric_val)
                    sol[var_name] = numeric_val
                except:
                    sol[var_name] = str(val)
            
            solutions.append(sol)
            
            if verbose:
                res_str = ", ".join([f"{k}={v}" for k,v in sol.items()])
                result["steps"].append(f"**พบคำตอบชุดที่ 1:** {res_str}")

            # พยายามหาคำตอบเพิ่มเติม (สำหรับสมการที่มีหลายราก)
            # เทคนิค: เพิ่มเงื่อนไขว่าคำตอบใหม่ต้องไม่เท่ากับคำตอบเก่า
            max_attempts = 5
            for i in range(max_attempts):
                s_new = Solver()
                s_new.add(z3_eq)
                # เพิ่ม constraint ว่าตัวแปรใดๆ ต้องไม่เท่ากับค่าที่พบไปแล้ว
                exclude_condition = []
                for found_sol in solutions:
                    for var_name, val in found_sol.items():
                        if isinstance(val, (int, float)):
                            exclude_condition.append(z3_vars[var_name] != val)
                
                if exclude_condition:
                    s_new.add(exclude_condition) # ต้องไม่ตรงกับอันเดิม
                    
                    if s_new.check() == sat:
                        m_new = s_new.model()
                        new_sol = {}
                        for var_name, z3_var in z3_vars.items():
                            val = m_new.evaluate(z3_var)
                            try:
                                numeric_val = float(val.as_decimal(10))
                                if abs(numeric_val - round(numeric_val)) < 1e-7:
                                    numeric_val = round(numeric_val)
                                new_sol[var_name] = numeric_val
                            except:
                                new_sol[var_name] = str(val)
                        
                        # เช็คว่าเป็นคำตอบใหม่ที่แตกต่างจริงๆ (ไม่ใช่แค่ความคลาดเคลื่อนทศนิยม)
                        is_new = True
                        for old_sol in solutions:
                            match = True
                            for k, v in new_sol.items():
                                if k in old_sol and abs(float(v) - float(old_sol[k])) > 1e-5:
                                    match = False
                                    break
                            if match:
                                is_new = False
                                break
                        
                        if is_new:
                            solutions.append(new_sol)
                            if verbose:
                                res_str = ", ".join([f"{k}={v}" for k,v in new_sol.items()])
                                result["steps"].append(f"**พบคำตอบชุดที่ {len(solutions)}:** {res_str}")
                    else:
                        if verbose:
                            result["steps"].append(f"**ไม่พบคำตอบเพิ่มเติมหลังจาก {len(solutions)} ชุด**")
                        break
                else:
                    break
        else:
            if verbose:
                result["steps"].append("**Z3 ไม่สามารถหาคำตอบได้ (Unsat หรือ Unknown)**")
            # Fallback ไปใช้ Numerical Method ถ้า Z3 หาไม่ได้
            return solve_equation_numerical(equation_str, verbose)

        result["success"] = True
        result["solutions"] = solutions

    except Exception as e:
        result["success"] = False
        result["error"] = str(e)
        if verbose:
            result["steps"].append(f"**เกิดข้อผิดพลาด:** {str(e)}")
        # Fallback ไปใช้ Numerical Method ถ้าเกิด Error
        return solve_equation_numerical(equation_str, verbose)

    return result

def solve_equation_numerical(equation_str: str, verbose: bool = False) -> Dict[str, Any]:
    """
    Fallback: แก้สมการโดยใช้วิธีเชิงตัวเลข (Numerical Method)
    เมื่อ Z3 ไม่สามารถหาคำตอบได้
    """
    result = {
        "success": False,
        "solutions": [],
        "method": "numerical_fallback",
        "steps": [],
        "error": None
    }
    
    if verbose:
        result["steps"].append("**เปลี่ยนไปใช้วิธีคำนวณเชิงตัวเลข (Numerical Method)**")
        result["steps"].append("เนื่องจากสมการซับซ้อนหรือไม่อยู่ในรูปแบบที่ Z3 แก้ได้โดยตรง")

    try:
        # แปลงสมการเป็นฟังก์ชัน Python f(x) = 0
        # สมมติว่าตัวแปรคือ 'x' สำหรับวิธีนี้ (ง่ายที่สุด)
        clean_eq = equation_str.replace('^', '**').replace('=', '-(') + ')'
        # ตัวอย่าง: 3**x = x**9  ->  3**x - (x**9)
        
        # ฟังก์ชันสำหรับประเมินค่า
        def f(x_val):
            local_scope = {'x': x_val, 'math': math}
            try:
                # ใช้ sympy แทน eval เพื่อความปลอดภัย
                from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application, convert_xor
                transformations = standard_transformations + (implicit_multiplication_application, convert_xor)
                expr = parse_expr(clean_eq, transformations=transformations, local_dict=local_scope)
                return float(expr.evalf())
            except:
                return None

        # กวาดหาช่วงที่เครื่องหมายเปลี่ยน (Sign Change)
        solutions = []
        search_range = [i * 0.5 for i in range(-20, 41)] # สแกนจาก -10 ถึง 20
        
        if verbose:
            result["steps"].append(f"**เริ่มสแกนหาค่าในช่วง:** {search_range[0]} ถึง {search_range[-1]}")

        for i in range(len(search_range) - 1):
            x1, x2 = search_range[i], search_range[i+1]
            y1, y2 = f(x1), f(x2)
            
            if y1 is None or y2 is None:
                continue
            
            # ตรวจหาการเปลี่ยนเครื่องหมาย (Root Bracketing)
            if y1 * y2 < 0:
                # ใช้ Bisection Method หาคำตอบในช่วงนี้
                low, high = x1, x2
                for _ in range(50): # 50 iterations for precision
                    mid = (low + high) / 2
                    y_mid = f(mid)
                    if y_mid == 0 or (high - low) < 1e-7:
                        break
                    if y1 * y_mid < 0:
                        high = mid
                        y2 = y_mid
                    else:
                        low = mid
                        y1 = y_mid
                
                root = (low + high) / 2
                # ตรวจสอบว่าซ้ำกับคำตอบที่มีไหม
                is_duplicate = False
                for existing in solutions:
                    if abs(existing['x'] - root) < 1e-4:
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    solutions.append({'x': round(root, 6)})
                    if verbose:
                        result["steps"].append(f"**พบรากในช่วง ({x1}, {x2}): x ≈ {round(root, 6)}")

        if solutions:
            result["success"] = True
            result["solutions"] = solutions
        else:
            result["error"] = "ไม่พบคำตอบในช่วงที่ค้นหา"
            if verbose:
                result["steps"].append("**ไม่พบการเปลี่ยนเครื่องหมายของฟังก์ชันในช่วงที่ตรวจสอบ**")

    except Exception as e:
        result["error"] = f"Numerical method failed: {str(e)}"
        if verbose:
            result["steps"].append(f"**ข้อผิดพลาดในการคำนวณเชิงตัวเลข:** {str(e)}")

    return result

def solve_system_of_equations_sympy(equation_parts: List[str], verbose: bool = False) -> Dict[str, Any]:
    """
    แก้ระบบสมการหลายตัวแปรโดยใช้ SymPy
    เช่น ["A + B = 15", "A - B = 5"]
    """
    result = {
        "success": False,
        "solutions": [],
        "method": "sympy_system_solver",
        "steps": [],
        "error": None
    }
    
    if verbose:
        result["steps"].append(f"**แก้ระบบสมการด้วย SymPy:** {equation_parts}")
    
    try:
        # รวบรวมตัวแปรทั้งหมดที่ปรากฏในสมการ
        all_vars = set()
        for eq in equation_parts:
            # หาตัวแปรภาษาอังกฤษ (ตัวอักษรเดียวหรือหลายตัว)
            vars_in_eq = re.findall(r'\b([A-Za-z][A-Za-z0-9]*)\b', eq)
            # กรองคำสงวนและค่าคงที่
            reserved = {'sin', 'cos', 'tan', 'exp', 'log', 'sqrt', 'pi', 'e', 'abs'}
            vars_in_eq = [v for v in vars_in_eq if v not in reserved]
            all_vars.update(vars_in_eq)
        
        if not all_vars:
            result["error"] = "ไม่พบตัวแปรในระบบสมการ"
            return result
        
        # สร้าง SymPy symbols สำหรับทุกตัวแปร
        sympy_vars = {var: symbols(var) for var in all_vars}
        
        if verbose:
            result["steps"].append(f"**ตัวแปรที่พบ:** {', '.join(all_vars)}")
        
        # แปลงสมการแต่ละสมการเป็น SymPy Eq
        equations = []
        for eq_str in equation_parts:
            if '=' in eq_str:
                lhs_str, rhs_str = eq_str.split('=', 1)
                lhs = sympy_parse(lhs_str.strip(), local_dict=sympy_vars)
                rhs = sympy_parse(rhs_str.strip(), local_dict=sympy_vars)
                equations.append(Eq(lhs, rhs))
            else:
                # ถ้าไม่มี = ถือว่าเป็นนิพจน์ที่ต้องการให้เป็น 0
                expr = sympy_parse(eq_str.strip(), local_dict=sympy_vars)
                equations.append(Eq(expr, 0))
        
        if verbose:
            result["steps"].append(f"**สร้างสมการ:** {[str(eq) for eq in equations]}")
        
        # แก้ระบบสมการ
        solution = sympy_solve(equations, list(sympy_vars.values()))
        
        if solution:
            # แปลงผลลัพธ์เป็น dictionary ที่อ่านง่าย
            if isinstance(solution, dict):
                sol_dict = {str(k): float(v.evalf()) if hasattr(v, 'evalf') else float(v) 
                           for k, v in solution.items()}
                result["solutions"].append(sol_dict)
            elif isinstance(solution, list) and len(solution) > 0:
                # กรณีได้หลายคำตอบ
                if isinstance(solution[0], tuple):
                    # มีหลายตัวแปร
                    for sol_tuple in solution:
                        sol_dict = {}
                        for i, var in enumerate(sympy_vars.keys()):
                            val = sol_tuple[i]
                            sol_dict[var] = float(val.evalf()) if hasattr(val, 'evalf') else float(val)
                        result["solutions"].append(sol_dict)
                elif isinstance(solution[0], dict):
                    for sol_dict_raw in solution:
                        sol_dict = {str(k): float(v.evalf()) if hasattr(v, 'evalf') else float(v) 
                                   for k, v in sol_dict_raw.items()}
                        result["solutions"].append(sol_dict)
            
            if verbose:
                result["steps"].append(f"**พบคำตอบ:** {result['solutions']}")
            
            result["success"] = True
        else:
            result["error"] = "ไม่พบคำตอบสำหรับระบบสมการนี้"
            if verbose:
                result["steps"].append("**SymPy ไม่พบคำตอบ**")
    
    except Exception as e:
        result["error"] = f"SymPy solver failed: {str(e)}"
        if verbose:
            result["steps"].append(f"**ข้อผิดพลาด:** {str(e)}")
    
    return result

