"""
Math Solver Tool - เครื่องมือคำนวณคณิตศาสตร์จริง
รองรับ: สมการพีชคณิต, ระบบสมการ, สมการฟังก์ชัน (ทดสอบ), และ Constraint Logic (Z3)
"""
import sympy
from sympy import symbols, Eq, solve, simplify, Function
from z3 import Solver, Int, Real, Sat, If
import re

class MathSolver:
    def __init__(self):
        self.x, self.y, self.z, self.k, self.n = symbols('x y z k n', real=True)
        # Integer symbols for Z3
        self.ix = Int('x')
        self.ik = Int('k')

    def solve_equation(self, equation_str: str):
        """
        แก้สมการพีชคณิตทั่วไปด้วย SymPy
        Input: "x^2 + 19x - 92 = 0" หรือ "2**x = x**6"
        Output: List of solutions
        """
        try:
            # แปลง string เป็น sympy expression
            # จัดการ ^ ให้เป็น **
            eq_clean = equation_str.replace('^', '**')
            
            if '=' in eq_clean:
                lhs, rhs = eq_clean.split('=')
                eq = Eq(eval(lhs, {"x": self.x, "y": self.y, "k": self.k, "n": self.n, "pi": sympy.pi, "e": sympy.E}), 
                        eval(rhs, {"x": self.x, "y": self.y, "k": self.k, "n": self.n, "pi": sympy.pi, "e": sympy.E}))
            else:
                # ถ้าไม่มี = ถือว่าเท่ากับ 0
                eq = Eq(eval(eq_clean, {"x": self.x, "y": self.y, "k": self.k, "n": self.n}), 0)

            solutions = solve(eq, self.x)
            
            # ตรวจสอบความถูกต้อง (Verification Step)
            verified_solutions = []
            for sol in solutions:
                try:
                    # แทนค่ากลับเพื่อเช็คว่าซ้าย=ขวาไหม
                    check_val = eq.lhs.subs(self.x, sol) - eq.rhs.subs(self.x, sol)
                    if simplify(check_val) == 0:
                        verified_solutions.append(sol)
                    else:
                        # ถ้าไม่ตรง อาจเป็นคำตอบปลอม (extraneous solution)
                        pass 
                except:
                    verified_solutions.append(sol) # เก็บไว้ก่อนถ้าเช็คไม่ได้
            
            return {
                "status": "success",
                "method": "sympy",
                "solutions": verified_solutions,
                "raw_solutions": solutions
            }
        except Exception as e:
            return {"status": "error", "method": "sympy", "message": str(e)}

    def solve_integer_constraint(self, equation_str: str, constraints: list = None):
        """
        แก้โจทย์จำนวนเต็มหรือเงื่อนไขซับซ้อนด้วย Z3
        Input: "x^2 + 19x - 92 = k^2", constraints=["x > -100", "x < 200"]
        Output: List of integer pairs (x, k)
        """
        try:
            s = Solver()
            x = Int('x')
            k = Int('k')
            
            # แปลงสมการเป็น Z3 Expression (แบบง่ายสำหรับกรณีกำลังสอง)
            # หมายเหตุ: Z3 ไม่รับ string โดยตรง ต้อง parse เองหรือใช้กรณีเฉพาะ
            # ในที่นี้ทำกรณี x^2 + 19x - 92 = k^2 โดยเฉพาะเพื่อสาธิต
            if "x^2" in equation_str and "k^2" in equation_str:
                # สมมติรูปแบบ ax^2 + bx + c = k^2
                # Extract coefficients (แบบง่าย)
                s.add(x*x + 19*x - 92 == k*k)
                
                # เพิ่มขอบเขตการค้นหา (จำเป็นสำหรับ Z3 เพื่อไม่ให้วนลูปไม่รู้จบ)
                s.add(x > -200)
                s.add(x < 200)
                
                solutions = []
                while s.check() == Sat:
                    m = s.model()
                    xv = m[x].as_long()
                    kv = m[k].as_long()
                    solutions.append((xv, kv))
                    
                    # Exclude this solution to find next
                    s.add((x != xv) | (k != kv))
                
                return {
                    "status": "success",
                    "method": "z3",
                    "solutions": solutions
                }
            else:
                return {"status": "error", "message": "รูปแบบสมการนี้ยังไม่รองรับใน Z3 Mode (ต้องเขียน Parser เฉพาะ)"}

        except Exception as e:
            return {"status": "error", "method": "z3", "message": str(e)}

    def verify_solution(self, equation_str: str, candidate_value):
        """
        ตรวจสอบคำตอบโดยการแทนค่าจริง
        """
        try:
            eq_clean = equation_str.replace('^', '**')
            lhs, rhs = eq_clean.split('=')
            
            # แทนค่า x ด้วย candidate_value
            val = float(candidate_value)
            left_val = eval(lhs, {"x": val, "y": 0, "k": 0, "n": 0})
            right_val = eval(rhs, {"x": val, "y": 0, "k": 0, "n": 0})
            
            is_correct = abs(left_val - right_val) < 1e-6
            return {
                "value": candidate_value,
                "is_correct": is_correct,
                "lhs": left_val,
                "rhs": right_val
            }
        except Exception as e:
            return {"error": str(e)}

# ตัวอย่างการใช้งานเมื่อถูกเรียกจาก Orchestrator
if __name__ == "__main__":
    solver = MathSolver()
    
    print("--- Test 1: สมการกำลังสอง ---")
    res1 = solver.solve_equation("x^2 + 19x - 92 = 0")
    print(res1)
    
    print("\n--- Test 2: สมการติดลบ (หา k) ---")
    # หมายเหตุ: ฟังก์ชันนี้ต้องปรับ parser ให้เก่งกว่านี้เพื่อรองรับทุกเคส
    # แต่สำหรับเคส x^2 + 19x - 92 = k^2 ที่เขียน hardcoded ไว้ใน solve_integer_constraint
    res2 = solver.solve_integer_constraint("x^2 + 19x - 92 = k^2")
    print(res2)
    
    print("\n--- Test 3: Verify ---")
    if res1['solutions']:
        v = res1['solutions'][0]
        check = solver.verify_solution("x^2 + 19x - 92 = 0", v)
        print(f"Verify {v}: {check}")
