"""
Sanity Checker Module
ทำหน้าที่ตรวจสอบความสมเหตุสมผลของคำตอบทางคณิตศาสตร์ (Safety by Design)
ก่อนส่งคืนผลลัพธ์ให้ผู้ใช้หรือยืนยันการแก้ไขโค้ด
"""

import math
import sympy
from typing import List, Tuple, Union, Optional

class SanityCheckResult:
    def __init__(self, passed: bool, message: str, details: dict = None):
        self.passed = passed
        self.message = message
        self.details = details or {}

    def __bool__(self):
        return self.passed

    def __str__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"[{status}] {self.message}"

def check_substitution(equation_str: str, solution: float, tolerance: float = 1e-6) -> SanityCheckResult:
    """
    ตรวจสอบโดยการแทนค่าคำตอบกลับลงในสมการ (Left Hand Side == Right Hand Side)
    """
    try:
        # แยกสมการด้วยเครื่องหมาย '='
        if '=' not in equation_str:
            return SanityCheckResult(False, "รูปแบบสมการไม่ถูกต้อง (ไม่พบเครื่องหมาย '=')")

        lhs_str, rhs_str = equation_str.split('=')
        
        # สร้าง Symbol สำหรับตัวแปร (สมมติว่าเป็น 'x')
        x = sympy.symbols('x')
        
        # แปลง string เป็น sympy expression
        lhs = sympy.sympify(lhs_str, locals={'x': x})
        rhs = sympy.sympify(rhs_str, locals={'x': x})
        
        # แทนค่าคำตอบ
        val_lhs = float(lhs.subs(x, solution))
        val_rhs = float(rhs.subs(x, solution))
        
        # ตรวจสอบค่า NaN หรือ Infinity
        if math.isnan(val_lhs) or math.isnan(val_rhs):
            return SanityCheckResult(
                False, 
                f"คำตอบทำให้เกิดค่า NaN (LHS={val_lhs}, RHS={val_rhs})",
                {"lhs": val_lhs, "rhs": val_rhs}
            )
        if math.isinf(val_lhs) or math.isinf(val_rhs):
             # กรณีที่ทั้งคู่เป็น infinity เครื่องหมายเดียวกัน อาจถือว่าผ่านได้ในบางบริบท แต่ที่นี่ตีว่าเสี่ยง
            if val_lhs == val_rhs:
                pass # อนุญาตให้ inf == inf ได้ในบางกรณี
            else:
                return SanityCheckResult(
                    False, 
                    f"คำตอบทำให้เกิดค่า Infinity ที่ไม่ตรงกัน (LHS={val_lhs}, RHS={val_rhs})",
                    {"lhs": val_lhs, "rhs": val_rhs}
                )

        # เปรียบเทียบความแตกต่าง
        diff = abs(val_lhs - val_rhs)
        
        # ใช้ Relative Error ถ้าค่ามาก เพื่อความแม่นยำ
        if abs(val_lhs) > 1e-6 or abs(val_rhs) > 1e-6:
            relative_error = diff / max(abs(val_lhs), abs(val_rhs))
            is_valid = relative_error < tolerance
            error_msg = f"Relative Error: {relative_error:.2e}"
        else:
            is_valid = diff < tolerance
            error_msg = f"Absolute Diff: {diff:.2e}"

        if is_valid:
            return SanityCheckResult(
                True, 
                f"การแทนค่าถูกต้อง (ความคลาดเคลื่อนอยู่ในเกณฑ์)",
                {"lhs": val_lhs, "rhs": val_rhs, "diff": diff}
            )
        else:
            return SanityCheckResult(
                False, 
                f"การแทนค่าไม่เท่ากัน ({error_msg})",
                {"lhs": val_lhs, "rhs": val_rhs, "diff": diff}
            )

    except Exception as e:
        return SanityCheckResult(False, f"เกิดข้อผิดพลาดขณะตรวจสอบ: {str(e)}", {"error": str(e)})

def check_domain(equation_str: str, solution: float) -> SanityCheckResult:
    """
    ตรวจสอบว่าคำตอบอยู่ในโดเมนที่กำหนด (เช่น ฐานต้องเป็นบวกในบางกรณี)
    """
    try:
        x = sympy.symbols('x')
        expr = sympy.sympify(equation_str.replace('=', '-(') + ')', locals={'x': x}) # แปลงเป็น expr เดียวเพื่อเช็ค domain
        
        # ตรวจสอบเงื่อนไขพื้นฐาน
        # 1. ห้ามหารด้วยศูนย์ (ถ้ามี)
        # 2. ฐานของ log ต้องเป็นบวก
        # 3. ฐานของเลขชี้กำลังที่เป็นจำนวนจริงทั่วไปควรเป็นบวก (เพื่อหลีกเลี่ยงจำนวนเชิงซ้อนที่ไม่ต้องการ)
        
        # ตรวจสอบอย่างง่าย: ลองคำนวณค่าดูว่าติด complex หรือไม่ (ถ้าคาดหวัง real)
        # ในที่นี้เน้นตรวจเรื่อง Division by Zero หรือ Log of negative
        
        # Sympy มักจะจัดการเรื่อง domain ให้แล้วตอน solve แต่ถ้าเราแทนค่าแล้วได้ complex ล้วนๆ อาจมีปัญหา
        val = complex(expr.subs(x, solution))
        
        if val.imag != 0 and abs(val.imag) > 1e-10:
             return SanityCheckResult(
                False, 
                f"คำตอบทำให้เกิดจำนวนเชิงซ้อน (Imaginary part: {val.imag})",
                {"value": val}
            )
            
        return SanityCheckResult(True, "คำตอบอยู่ในโดเมนที่ถูกต้อง (Real Number)")
        
    except Exception as e:
        return SanityCheckResult(False, f"ตรวจสอบโดเมนไม่ผ่าน: {str(e)}")

def check_magnitude(solution: float, expected_range: Optional[Tuple[float, float]] = None) -> SanityCheckResult:
    """
    ตรวจสอบขนาดของคำตอบว่าสมเหตุสมผลหรือไม่ (ไม่ใหญ่เกินไปจน Overflow หรือเล็กเกินไป)
    """
    if math.isnan(solution):
        return SanityCheckResult(False, "คำตอบเป็น NaN")
    
    if math.isinf(solution):
        return SanityCheckResult(False, "คำตอบเป็น Infinity")

    if abs(solution) > 1e100:
        return SanityCheckResult(False, f"คำตอบมีขนาดใหญ่เกินไป ({solution}) อาจเกิด Overflow")
    
    if expected_range:
        min_val, max_val = expected_range
        if not (min_val <= solution <= max_val):
            return SanityCheckResult(False, f"คำตอบ ({solution}) ไม่อยู่ในช่วงที่คาดหวัง [{min_val}, {max_val}]")

    return SanityCheckResult(True, "ขนาดของคำตอบสมเหตุสมผล")

def run_full_sanity_check(equation: str, solutions: List[float]) -> Tuple[bool, List[str]]:
    """
    รันการตรวจสอบทั้งหมดสำหรับรายการคำตอบ
    Returns: (Passed, List of Error Messages)
    """
    errors = []
    
    if not solutions:
        return False, ["ไม่พบคำตอบ"]

    for i, sol in enumerate(solutions):
        # 1. Check Substitution
        res_sub = check_substitution(equation, sol)
        if not res_sub:
            errors.append(f"คำตอบที่ {i+1} ({sol}): {res_sub.message}")
        
        # 2. Check Domain
        res_dom = check_domain(equation, sol)
        if not res_dom:
            errors.append(f"คำตอบที่ {i+1} ({sol}): {res_dom.message}")
            
        # 3. Check Magnitude
        res_mag = check_magnitude(sol)
        if not res_mag:
            errors.append(f"คำตอบที่ {i+1} ({sol}): {res_mag.message}")

    passed = len(errors) == 0
    return passed, errors

if __name__ == "__main__":
    # ทดสอบการทำงาน
    print("Testing Sanity Checker...")
    
    # Test Case 1: 3^x = x^9, x = 27
    eq1 = "3**x = x**9"
    sol1 = [27.0]
    passed1, errs1 = run_full_sanity_check(eq1, sol1)
    print(f"Test 1 (3^x = x^9, x=27): {'PASS' if passed1 else 'FAIL'}")
    if errs1: print(errs1)
    
    # Test Case 2: 3^x = x^9, x = 1.1508
    sol2 = [1.150825]
    passed2, errs2 = run_full_sanity_check(eq1, sol2)
    print(f"Test 2 (3^x = x^9, x=1.15): {'PASS' if passed2 else 'FAIL'}")
    if errs2: print(errs2)

    # Test Case 3: Wrong answer
    sol3 = [10.0]
    passed3, errs3 = run_full_sanity_check(eq1, sol3)
    print(f"Test 3 (3^x = x^9, x=10 [Wrong]): {'PASS' if passed3 else 'FAIL'}")
    if errs3: print(errs3)
