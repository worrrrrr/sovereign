"""
Advanced Logic & Equation Solver Engine
รองรับ:
- ระบบสมการเชิงเส้นตัวแปรเดียว (เช่น "x + 5 = 10")
- โจทย์ตรรกะคำพูด (เช่น "A มากกว่า B อยู่ 5, A+B=15")
- การอนุมานเหตุผลแบบง่าย
"""
import re
from typing import Optional, Dict, Any

class AdvancedLogicEngine:
    def __init__(self):
        self.name = "AdvancedLogicEngine"
    
    def can_handle(self, text: str) -> bool:
        text_lower = text.lower()
        # ตรวจสอบ pattern สมการ หรือ คำว่า "แก้สมการ", "หาค่า x", "ตรรกะ"
        patterns = [
            r'แก้สมการ', r'หาค่า\s*[x-y]', r'สมการ', 
            r'\d*\s*[x-y]\s*[+\-*/]=\s*\d+', # pattern เช่น x+5=10
            r'มากกว่า', r'น้อยกว่า', r'รวมกัน', r'จงหา'
        ]
        return any(re.search(p, text_lower) for p in patterns)

    def execute(self, text: str) -> Dict[str, Any]:
        result = {
            "status": "success",
            "data": {},
            "message": ""
        }

        # 1. ลองแก้สมการคณิตศาสตร์โดยตรง (เช่น "แก้สมการ x + 5 = 10")
        equation_result = self._solve_equation(text)
        if equation_result:
            result["data"] = equation_result
            result["message"] = f"คำตอบคือ: {equation_result['solution']}"
            return result

        # 2. ลองแก้โจทย์ตรรกะคำพูด (เช่น "A มากกว่า B อยู่ 5, A+B=15")
        logic_result = self._solve_word_logic(text)
        if logic_result:
            result["data"] = logic_result
            result["message"] = self._format_logic_result(logic_result)
            return result

        result["status"] = "failed"
        result["message"] = "ไม่สามารถวิเคราะห์โจทย์ตรรกะหรือสมการนี้ได้"
        return result

    def _solve_equation(self, text: str) -> Optional[Dict]:
        # ค้นหา pattern สมการอย่างง่าย ax + b = c
        # ลบคำรบกวน
        clean_text = re.sub(r'แก้สมการ|จงหาค่า|x\s*=', '', text, flags=re.IGNORECASE)
        
        # พยายามหาสมการในรูปแบบ a*x + b = c หรือ x + b = c
        # รองรับทั้ง x และ y
        match = re.search(r'(-?\d*)\s*([xy])\s*([+\-])\s*(\d+)\s*=\s*(-?\d+)', clean_text)
        
        if match:
            coef_str, var, op, const_str, result_str = match.groups()
            coef = int(coef_str) if coef_str and coef_str not in ['-', ''] else (1 if not coef_str or coef_str == '' else -1)
            if coef_str == '-': coef = -1
            
            const = int(const_str)
            target = int(result_str)
            
            # คำนวณ
            if op == '+':
                # ax + b = c  => ax = c - b => x = (c-b)/a
                numerator = target - const
            else: # '-'
                # ax - b = c => ax = c + b => x = (c+b)/a
                numerator = target + const
            
            if coef != 0:
                solution = numerator / coef
                # ถ้าเป็นจำนวนเต็ม ให้แสดงเป็นจำนวนเต็ม
                if solution.is_integer():
                    solution = int(solution)
                
                return {
                    "type": "equation",
                    "variable": var,
                    "solution": solution,
                    "steps": f"{coef}{var} {op} {const} = {target} -> {coef}{var} = {numerator} -> {var} = {solution}"
                }
        return None

    def _solve_word_logic(self, text: str) -> Optional[Dict]:
        # ตัวอย่าง: "A มากกว่า B อยู่ 5 และ A+B=15 จงหา A"
        # Pattern: A > B + x, A + B = y
        
        numbers = re.findall(r'\d+', text)
        if len(numbers) < 2:
            return None
            
        # สมมติฐานง่ายๆ สำหรับโจทย์ 2 ตัวแปร
        try:
            nums = [int(n) for n in numbers]
            
            # กรณีที่ 1: "มากกว่า ... อยู่ n1" และ "รวมกัน/บวก/เท่ากับ n2"
            if 'มากกว่า' in text and ('รวม' in text or 'บวก' in text or 'เท่ากับ' in text):
                diff = nums[0] # ค่าที่มากกว่า
                total = nums[1] # ผลรวม
                
                # สูตร: (Total + Diff) / 2 = ตัวใหญ่, (Total - Diff) / 2 = ตัวเล็ก
                val_large = (total + diff) / 2
                val_small = (total - diff) / 2
                
                if val_large.is_integer(): val_large = int(val_large)
                if val_small.is_integer(): val_small = int(val_small)
                
                return {
                    "type": "logic_word_problem",
                    "variables": {"large": val_large, "small": val_small},
                    "diff": diff,
                    "total": total
                }
            
            # กรณีที่ 2: "มากกว่า ... อยู่ X" และมี pattern "A+B=Y" หรือ "A-B=Y" ในข้อความ
            # เช่น "A มากกว่า B อยู่ 5 และ A+B=15"
            if 'มากกว่า' in text and 'อยู่' in text:
                # หาตัวเลขหลังจากคำว่า "อยู่"
                diff_match = re.search(r'อยู่\s*(\d+)', text)
                if diff_match:
                    diff = int(diff_match.group(1))
                    
                    # หาสมการในรูปแบบ A+B=Y หรือ A-B=Y
                    eq_match = re.search(r'([A-Za-z])\s*([+\-])\s*([A-Za-z])\s*=\s*(\d+)', text)
                    if eq_match:
                        var1, op, var2, total_str = eq_match.groups()
                        total = int(total_str)
                        
                        # ถ้าเป็น A+B=Y
                        if op == '+':
                            # สูตร: (Total + Diff) / 2 = ตัวใหญ่, (Total - Diff) / 2 = ตัวเล็ก
                            val_large = (total + diff) / 2
                            val_small = (total - diff) / 2
                            
                            if val_large.is_integer(): val_large = int(val_large)
                            if val_small.is_integer(): val_small = int(val_small)
                            
                            # กำหนดว่าตัวไหนคือ A หรือ B
                            # A มากกว่า B ดังนั้น A = val_large, B = val_small
                            variables = {var1.upper(): val_large, var2.upper(): val_small}
                            
                            return {
                                "type": "logic_word_problem",
                                "variables": variables,
                                "diff": diff,
                                "total": total,
                                "equation": f"{var1} {op} {var2} = {total}"
                            }
                            
        except Exception as e:
            pass
        return None

    def _format_logic_result(self, data: Dict) -> str:
        if data.get('type') == 'logic_word_problem':
            variables = data.get('variables', {})
            
            # กรณีที่มี large/small keys
            if 'large' in variables and 'small' in variables:
                return f"จากการคำนวณ: ตัวที่มีค่ามากกว่าคือ {variables['large']} และตัวที่น้อยกว่าคือ {variables['small']}"
            
            # กรณีที่มี variable names (เช่น A, B)
            else:
                result_parts = []
                for var_name, value in variables.items():
                    result_parts.append(f"{var_name} = {value}")
                
                diff = data.get('diff', '')
                total = data.get('total', '')
                equation = data.get('equation', '')
                
                response = f"จากการคำนวณ: {', '.join(result_parts)}"
                if equation:
                    response += f"\nจากสมการ: {equation}"
                if diff and total:
                    response += f"\nโดยที่ {list(variables.keys())[0]} มากกว่า {list(variables.keys())[1]} อยู่ {diff} และรวมกันได้ {total}"
                
                return response
        
        return ""
