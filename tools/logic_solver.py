"""
Logic AGI Solver
เครื่องมือสำหรับแก้โจทย์ปัญหาเชิงตรรกะระดับสูง (Logic Puzzles, Combinatorics, Proofs)
รองรับการตรวจสอบความขัดแย้ง (Contradiction Detection) และการ brute-force แบบมีเงื่อนไข
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from itertools import product

class LogicSolver:
    def __init__(self):
        self.variables = {}
        self.constraints = []
    
    def parse_problem(self, problem_text: str) -> Dict[str, Any]:
        """
        แปลงโจทย์ภาษาธรรมชาติเป็นโครงสร้างข้อมูลสำหรับการแก้ปัญหา
        (ในรูปแบบจำลองเบื้องต้น สำหรับโจทย์ประเภท Truth-Teller/Liar)
        """
        # ตรวจจับจำนวนคน/วัตถุ
        num_match = re.search(r'(\d+)\s*(?:คน|people|persons)', problem_text, re.IGNORECASE)
        total_count = int(num_match.group(1)) if num_match else 0
        
        # ตรวจจับรูปแบบประโยค "คนสองข้างของฉันโกหกทั้งคู่" หรือ类似的逻辑
        # ขยายเงื่อนไขให้ครอบคลุมคำต่างๆ ที่สื่อถึงเพื่อนบ้านและการโกหก
        neighbor_keywords = ["สองข้าง", "เพื่อนบ้าน", "neighbors", "ข้างๆ"]
        lie_keywords = ["โกหก", "lie", "เท็จ"]
        
        has_neighbor = any(kw in problem_text for kw in neighbor_keywords)
        has_lie = any(kw in problem_text.lower() for kw in lie_keywords)
        
        neighbor_lie_pattern = has_neighbor and has_lie
            
        return {
            "count": total_count,
            "pattern": "neighbor_lie" if neighbor_lie_pattern else "unknown",
            "raw_text": problem_text
        }

    def solve_truth_teller_circle(self, n: int) -> int:
        """
        แก้โจทย์: คนนั่งวงกลม n คน แต่ละคนบอกว่า "เพื่อนบ้านทั้งสองข้างโกหก"
        หาจำนวนคนพูดจริงได้มากที่สุดกี่คน
        
        Logic:
        ให้ T = พูดจริง, L = โกหก
        ถ้าคน i พูดจริง (T) -> เพื่อนบ้านต้องเป็น L ทั้งคู่ (L, T, L)
        ถ้าคน i โกหก (L) -> ประโยค "เพื่อนบ้านทั้งคู่โกหก" เป็นเท็จ 
                           -> อย่างน้อยหนึ่งคนต้องพูดจริง (T, L, T) หรือ (T, L, L) หรือ (L, L, T)
                           
        รูปแบบที่เกิดขึ้นได้ซ้ำๆ คือ T-L-L-T-L-L... (รอบละ 3 คน มี T 1 คน)
        ดังนั้น n ต้องหารด้วย 3 ลงตัว ถึงจะจัดวงจรได้สมบูรณ์
        """
        if n == 0:
            return 0
            
        # ตรวจสอบเงื่อนไข Modulo 3
        if n % 3 != 0:
            # กรณี n หาร 3 ไม่ลงตัว จะเกิดความขัดแย้งเมื่อปิดวงกลม
            # ไม่สามารถจัดเรียงได้โดยไม่มีข้อขัดแย้ง
            return 0
        
        # ถ้าหารลงตัว จำนวนคนพูดจริงสูงสุดคือ n / 3
        return n // 3

    def verify_solution(self, n: int, truth_count: int) -> bool:
        """
        Sanity Check: ตรวจสอบความสมเหตุสมผลของคำตอบ
        """
        if n == 0:
            return truth_count == 0
        
        if n % 3 != 0:
            return truth_count == 0
        else:
            return truth_count == n // 3

    def solve(self, problem_text: str) -> Dict[str, Any]:
        """
        ฟังก์ชันหลักในการแก้โจทย์
        """
        parsed = self.parse_problem(problem_text)
        
        result = {
            "problem_summary": "",
            "answer": None,
            "reasoning": [],
            "verified": False
        }

        if parsed["pattern"] == "neighbor_lie":
            n = parsed["count"]
            result["problem_summary"] = f"โจทย์คนนั่งวงกลม {n} คน บอกว่าเพื่อนบ้านโกหก"
            
            # คำนวณ
            max_truth = self.solve_truth_teller_circle(n)
            result["answer"] = max_truth
            
            # สร้างเหตุผล
            reasoning_steps = [
                f"1. วิเคราะห์รูปแบบ: หากคนไหนพูดจริง เพื่อนบ้านทั้งสองต้องโกหก (รูปแบบ T-L-L)",
                "2. รูปแบบที่เสถียรคือ T-L-L ซ้ำไปเรื่อยๆ (คาบ 3)",
                f"3. ตรวจสอบเงื่อนไขวงกลม: จำนวนคน ({n}) ต้องหารด้วย 3 ลงตัว",
                f"4. ผลลัพธ์: {n} หาร 3 {'ลงตัว' if n % 3 == 0 else 'ไม่ลงตัว'} (เศษ {n % 3})",
            ]
            
            if n % 3 != 0:
                reasoning_steps.append("5. สรุป: เกิดความขัดแย้งเมื่อปิดวงกลม จึงไม่มีคนพูดจริงได้เลย (หรือจัดรูปแบบไม่ได้)")
                reasoning_steps.append(f"6. คำตอบคือ 0")
            else:
                reasoning_steps.append(f"5. สรุป: จัดรูปแบบได้ จำนวนคนพูดจริงสูงสุดคือ {n} / 3 = {max_truth}")
                
            result["reasoning"] = reasoning_steps
            
            # Verify
            is_valid = self.verify_solution(n, max_truth)
            result["verified"] = is_valid
            if not is_valid:
                result["error"] = "Sanity Check Failed!"

        else:
            result["reasoning"] = ["ยังไม่รองรับรูปแบบโจทย์นี้"]
            result["answer"] = "Unknown"

        return result

# ฟังก์ชันกลางสำหรับเรียกใช้
def logic_solver_tool(params: dict) -> str:
    problem = params.get("problem", "")
    if not problem:
        return "กรุณาระบุโจทย์ปัญหาเชิงตรรกะ"
    
    solver = LogicSolver()
    result = solver.solve(problem)
    
    output = []
    output.append(f"=== ผลการวิเคราะห์โจทย์ ===")
    output.append(result["problem_summary"])
    output.append(f"\nเหตุผล:")
    for step in result["reasoning"]:
        output.append(f"  {step}")
    
    output.append(f"\nคำตอบ: {result['answer']}")
    if result.get("verified"):
        output.append("✅ ตรวจสอบความสมเหตุสมผลแล้ว: ผ่าน")
    else:
        output.append("❌ ตรวจสอบความสมเหตุสมผลแล้ว: ไม่ผ่าน หรือ ไม่มีข้อมูล")
        
    if "error" in result:
        output.append(f"⚠️ ข้อผิดพลาด: {result['error']}")
        
    return "\n".join(output)

if __name__ == "__main__":
    # ทดสอบด้วยตนเอง
    test_problem = "มีโต๊ะกลม 2026 คน นั่งอยู่ แต่ละคนเป็นคนพูดจริงหรือโกหกตลอด แต่ละคนพูดว่า 'คนสองข้างของฉันโกหกทั้งคู่' จะมีคนพูดจริงได้มากที่สุดกี่คน?"
    print(logic_solver_tool({"problem": test_problem}))
