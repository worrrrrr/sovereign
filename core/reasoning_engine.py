"""
Sovereign AI Reasoning Engine

Engine สำหรับสร้างคำอธิบายและแสดงวิธีคิดแบบละเอียด
รองรับโหมด verbose สำหรับแสดงขั้นตอนการแก้ปัญหา
"""
from typing import Dict, Any, Optional, List


class ReasoningEngine:
    """
    กลไกการสร้างเหตุผลและคำอธิบาย
    ทำหน้าที่แปลงผลลัพธ์จาก Tools ให้เป็นคำอธิบายที่มนุษย์เข้าใจได้
    """
    
    def __init__(self):
        pass
    
    def explain_arithmetic(self, operation: str, a: float, b: float, 
                          result: float, verbose: bool = False) -> Dict[str, Any]:
        """
        สร้างคำอธิบายสำหรับการคำนวณเลขคณิตพื้นฐาน
        
        Args:
            operation: การดำเนินการ ('add', 'subtract', 'multiply', 'divide')
            a: ตัวเลขตัวแรก
            b: ตัวเลขตัวที่สอง
            result: ผลลัพธ์
            verbose: ถ้า True จะแสดงวิธีทำแบบละเอียด
            
        Returns:
            Dictionary พร้อมคำอธิบายและขั้นตอน
        """
        response = {
            'operation': operation,
            'input_a': a,
            'input_b': b,
            'result': result,
            'explanation': '',
            'steps': []
        }
        
        if operation == 'subtract':
            # จัดการการลบ
            response['explanation'] = f"การลบ {a} - {b}"
            
            if verbose:
                steps = []
                steps.append(f"**โจทย์:** {a} - {b}")
                steps.append("")
                
                # แปลงเป็น Decimal เพื่อความแม่นยำในการแสดงผล
                from decimal import Decimal
                a_dec = Decimal(str(a))
                b_dec = Decimal(str(b))
                
                # หาจำนวนตำแหน่งทศนิยม
                a_places = max(0, -a_dec.as_tuple().exponent)
                b_places = max(0, -b_dec.as_tuple().exponent)
                max_places = max(a_places, b_places)
                
                steps.append("**วิธีคิดแบบตั้งลบ:**")
                steps.append("")
                steps.append("1. **จัดหลักทศนิยมให้ตรงกัน**")
                
                if a_places != b_places or max_places > 0:
                    a_formatted = f"{a:.{max_places}f}"
                    b_formatted = f"{b:.{max_places}f}"
                    steps.append(f"   เติม 0 ต่อท้ายให้จำนวนหลักทศนิยมเท่ากัน:")
                    steps.append(f"   {a} → {a_formatted}")
                    steps.append(f"   {b} → {b_formatted}")
                else:
                    a_formatted = str(a)
                    b_formatted = str(b)
                
                steps.append("")
                steps.append("2. **ทำการลบจากขวาไปซ้าย**")
                
                # แสดงการยืมถ้าจำเป็น
                if a_dec < b_dec:
                    steps.append(f"   เนื่องจาก {a} < {b} ผลลัพธ์จะเป็นลบ")
                    steps.append(f"   คำนวณ {b} - {a} ก่อน แล้วเติมเครื่องหมายลบ")
                    diff = b_dec - a_dec
                else:
                    diff = a_dec - b_dec
                
                steps.append("")
                steps.append("3. **ผลลัพธ์:**")
                steps.append(f"   {a_formatted} - {b_formatted} = {float(diff)}")
                steps.append("")
                steps.append(f"**คำตอบ:** {float(diff)}")
                
                response['steps'] = steps
                response['explanation'] = '\n'.join(steps)
            else:
                response['explanation'] = f"{a} - {b} = {result}"
                
        elif operation == 'add':
            response['explanation'] = f"การบวก {a} + {b}"
            if verbose:
                steps = [
                    f"**โจทย์:** {a} + {b}",
                    "",
                    "**วิธีคิด:**",
                    f"นำ {a} และ {b} มาบวกกัน",
                    f"{a} + {b} = {result}",
                    "",
                    f"**คำตอบ:** {result}"
                ]
                response['steps'] = steps
                response['explanation'] = '\n'.join(steps)
            else:
                response['explanation'] = f"{a} + {b} = {result}"
                
        elif operation == 'multiply':
            response['explanation'] = f"การคูณ {a} × {b}"
            if verbose:
                steps = [
                    f"**โจทย์:** {a} × {b}",
                    "",
                    "**วิธีคิด:**",
                    f"นำ {a} คูณกับ {b}",
                    f"{a} × {b} = {result}",
                    "",
                    f"**คำตอบ:** {result}"
                ]
                response['steps'] = steps
                response['explanation'] = '\n'.join(steps)
            else:
                response['explanation'] = f"{a} × {b} = {result}"
                
        elif operation == 'divide':
            response['explanation'] = f"การหาร {a} ÷ {b}"
            if verbose:
                if b == 0:
                    steps = [
                        f"**โจทย์:** {a} ÷ {b}",
                        "",
                        "**ข้อผิดพลาด:** ไม่สามารถหารด้วยศูนย์ได้",
                        "",
                        "**คำตอบ:** Undefined (หาค่าไม่ได้)"
                    ]
                else:
                    steps = [
                        f"**โจทย์:** {a} ÷ {b}",
                        "",
                        "**วิธีคิด:**",
                        f"นำ {a} หารด้วย {b}",
                        f"{a} ÷ {b} = {result}",
                        "",
                        f"**คำตอบ:** {result}"
                    ]
                response['steps'] = steps
                response['explanation'] = '\n'.join(steps)
            else:
                if b == 0:
                    response['explanation'] = "ข้อผิดพลาด: ไม่สามารถหารด้วยศูนย์ได้"
                else:
                    response['explanation'] = f"{a} ÷ {b} = {result}"
        
        return response
    
    def explain_equation_solution(self, equation: str, solution_result: Dict[str, Any], 
                                 verbose: bool = False) -> Dict[str, Any]:
        """
        สร้างคำอธิบายสำหรับการแก้สมการ
        
        Args:
            equation: สมการต้นฉบับ
            solution_result: ผลลัพธ์จาก solve_equation tool
            verbose: ถ้า True จะแสดงวิธีทำแบบละเอียด
            
        Returns:
            Dictionary พร้อมคำอธิบายและขั้นตอน
        """
        response = {
            'equation': equation,
            'solutions': solution_result.get('solutions', []),
            'method': solution_result.get('method', 'unknown'),
            'explanation': '',
            'steps': []
        }
        
        if not solution_result.get('success', False):
            response['explanation'] = f"ไม่สามารถแก้สมการได้: {solution_result.get('error', 'Unknown error')}"
            return response
        
        if verbose:
            steps = []
            steps.append(f"**สมการ:** {equation}")
            steps.append("")
            steps.append("**วิธีแก้:**")
            
            method = solution_result.get('method', '')
            if method == 'sympy_solve':
                steps.append("ใช้ SymPy Solver ในการแก้สมการเชิงพีชคณิต")
            elif method == 'z3_diophantine':
                steps.append("ใช้ Z3 SMT Solver หาคำตอบจำนวนเต็ม")
            elif method == 'evaluation':
                steps.append("ประเมินค่าโดยตรง")
            
            steps.append("")
            
            # เพิ่มขั้นตอนจาก solution_result ถ้ามี
            if 'steps' in solution_result:
                existing_steps = solution_result['steps']
                if isinstance(existing_steps, str):
                    # แยกบรรทัด
                    for line in existing_steps.split('\n'):
                        if line.strip():
                            steps.append(line)
                elif isinstance(existing_steps, list):
                    steps.extend(existing_steps)
            
            steps.append("")
            steps.append("**คำตอบ:**")
            solutions = solution_result.get('solutions', [])
            for i, sol in enumerate(solutions):
                steps.append(f"  {i+1}. {sol}")
            
            response['steps'] = steps
            response['explanation'] = '\n'.join(steps)
        else:
            # โหมดสั้น
            solutions = solution_result.get('solutions', [])
            if solutions:
                sol_str = ', '.join([str(s) for s in solutions])
                response['explanation'] = f"คำตอบของสมการ {equation} คือ: {sol_str}"
            else:
                response['explanation'] = f"แก้สมการ {equation} ได้สำเร็จ"
        
        return response
    
    def process_tool_result(self, tool_name: str, tool_result: Dict[str, Any], 
                           verbose: bool = False) -> Dict[str, Any]:
        """
        ประมวลผลผลลัพธ์จาก Tool และสร้างคำอธิบาย
        
        Args:
            tool_name: ชื่อ tool ที่เรียก
            tool_result: ผลลัพธ์จาก tool
            verbose: โหมดแสดงวิธีทำละเอียด
            
        Returns:
            Dictionary พร้อมคำอธิบาย
        """
        if tool_name == 'math':
            # ตรวจสอบว่าเป็นการคำนวณพื้นฐานหรือแก้สมการ
            if 'operation' in tool_result and tool_result['operation'] in ['add', 'subtract', 'multiply', 'divide']:
                return self.explain_arithmetic(
                    operation=tool_result['operation'],
                    a=tool_result.get('input_a', 0),
                    b=tool_result.get('input_b', 0),
                    result=tool_result.get('result', 0),
                    verbose=verbose
                )
            elif 'equation' in tool_result or 'solutions' in tool_result:
                return self.explain_equation_solution(
                    equation=tool_result.get('raw_input', ''),
                    solution_result=tool_result,
                    verbose=verbose
                )
        
        # Default case สำหรับ tools อื่นๆ
        return {
            'tool': tool_name,
            'result': tool_result,
            'explanation': str(tool_result),
            'verbose': verbose
        }


# Singleton instance
reasoning_engine = ReasoningEngine()


def get_reasoning_engine() -> ReasoningEngine:
    """Return the singleton reasoning engine instance"""
    return reasoning_engine
