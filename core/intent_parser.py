"""
Intent Parser: วิเคราะห์ Input แยกแยะว่าเป็น 'คำสั่ง', 'คำถาม', หรือ 'โจทย์คณิตศาสตร์/ตรรกะ'
และดึงข้อมูลสำคัญ (Entities) ออกมาเพื่อส่งต่อให้ Engine ที่เหมาะสม
"""
import re
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

class IntentType(Enum):
    CALCULATION = "calculation"
    SOLVE_EQUATION = "solve_equation"       # แก้สมการทั่วไป (SymPy)
    SOLVE_CONSTRAINT = "solve_constraint"   # โจทย์จำนวนเต็ม/ตรรกะ (Z3)
    SOLVE_FUNCTIONAL = "solve_functional"   # สมการเชิงฟังก์ชัน
    QUESTION = "question"
    COMMAND = "command"
    SEARCH_WEB = "search_web"
    UNKNOWN = "unknown"

@dataclass
class ParsedIntent:
    intent_type: IntentType
    original_input: str
    action: str
    entities: List[Any]
    params: Dict[str, Any]  # พารามิเตอร์เฉพาะสำหรับแต่ละ Intent (เช่น สมการ, ตัวแปร)
    context: str
    confidence: float
    reasoning: str

class IntentParser:
    def __init__(self):
        # Patterns สำหรับตรวจจับการคำนวณพื้นฐาน
        self.calc_patterns = [
            r"(\d+\.?\d*)\s*[-+*/]\s*(\d+\.?\d*)",
        ]
        
        # Keywords สำหรับประเภทโจทย์
        self.math_keywords = ["แก้สมการ", "หาค่า", "เท่ากับ", "=", "find x", "solve", "calculate"]
        self.constraint_keywords = ["จำนวนเต็ม", "integer", "ตรรกะ", "logic", "เงื่อนไข", "condition", "divisible", "หารลงตัว"]
        self.functional_keywords = ["f(x)", "f(y)", "functional", "ฟังก์ชัน", "สมการเชิงฟังก์ชัน"]
        self.search_keywords = ["ค้นหา", "search", "google", "ข่าว", "อากาศ", "weather", "news"]

    def parse(self, user_input: str) -> ParsedIntent:
        input_lower = user_input.lower().strip()
        reasoning_steps = []
        params = {}

        # 1. ตรวจสอบโจทย์สมการเชิงฟังก์ชัน (Functional Equation)
        if any(kw in input_lower for kw in self.functional_keywords):
            reasoning_steps.append("ตรวจพบคำสำคัญเกี่ยวกับฟังก์ชัน (f(x), functional)")
            params = self._extract_functional_eq(user_input)
            return ParsedIntent(
                intent_type=IntentType.SOLVE_FUNCTIONAL,
                original_input=user_input,
                action="solve_functional_equation",
                entities=[],
                params=params,
                context="functional_math",
                confidence=0.95,
                reasoning="\n".join(reasoning_steps)
            )

        # 2. ตรวจสอบโจทย์ข้อจำกัด/จำนวนเต็ม (Constraint Satisfaction - Z3)
        if any(kw in input_lower for kw in self.constraint_keywords):
            reasoning_steps.append("ตรวจพบคำสำคัญเกี่ยวกับจำนวนเต็มหรือตรรกะ")
            eq_data = self._extract_equation(user_input)
            params = eq_data
            params['domain'] = 'integer' # บังคับใช้ Z3
            return ParsedIntent(
                intent_type=IntentType.SOLVE_CONSTRAINT,
                original_input=user_input,
                action="solve_constraint_problem",
                entities=[],
                params=params,
                context="integer_logic",
                confidence=0.95,
                reasoning="\n".join(reasoning_steps)
            )

        # 3. ตรวจสอบสมการทั่วไป (Equation Solving - SymPy/Z3 fallback)
        if any(kw in input_lower for kw in self.math_keywords) or ("=" in user_input and re.search(r'[a-zA-Z]', user_input)):
            reasoning_steps.append("ตรวจพบรูปแบบสมการหรือคำขอแก้โจทย์คณิตศาสตร์")
            eq_data = self._extract_equation(user_input)
            params = eq_data
            # ถ้ามีตัวแปรหลายตัวหรือกำลังสูง อาจแนะนำ Z3 ได้ แต่เริ่มที่ SymPy ก่อน
            return ParsedIntent(
                intent_type=IntentType.SOLVE_EQUATION,
                original_input=user_input,
                action="solve_algebraic_equation",
                entities=[],
                params=params,
                context="algebra",
                confidence=0.95,
                reasoning="\n".join(reasoning_steps)
            )

        # 4. ตรวจสอบการค้นหาข้อมูล
        if any(kw in input_lower for kw in self.search_keywords):
            reasoning_steps.append("ตรวจพบคำขอค้นหาข้อมูล")
            return ParsedIntent(
                intent_type=IntentType.SEARCH_WEB,
                original_input=user_input,
                action="search_information",
                entities=[],
                params={"query": user_input},
                context="web_search",
                confidence=0.90,
                reasoning="\n".join(reasoning_steps)
            )

        # 5. ตรวจสอบการคำนวณ murni (เช่น "9.8-9.11")
        calc_match = re.search(r"(-?\d+\.?\d*)\s*([-+*/])\s*(-?\d+\.?\d*)", user_input)
        if calc_match and not any(q in input_lower for q in ["?", "อย่างไร", "what", "how", "หา"]):
            num1 = float(calc_match.group(1))
            op = calc_match.group(2)
            num2 = float(calc_match.group(3))
            reasoning_steps.append(f"ตรวจพบนิพจน์คณิตศาสตร์ล้วน: {num1} {op} {num2}")
            return ParsedIntent(
                intent_type=IntentType.CALCULATION,
                original_input=user_input,
                action=f"calculate_{op}",
                entities=[num1, num2],
                params={"expression": user_input},
                context="simple_arithmetic",
                confidence=0.99,
                reasoning="\n".join(reasoning_steps)
            )

        # 6. ตรวจสอบคำถามทั่วไป
        question_patterns = [r"(.*)\?(.*)", r"อย่างไร", r"ยังไง", r"อะไร", r"แบบไหน"]
        is_question = any(re.search(p, input_lower) for p in question_patterns)
        if is_question:
            reasoning_steps.append("ตรวจพบเครื่องหมาย '?' หรือคำถาม")
            return ParsedIntent(
                intent_type=IntentType.QUESTION,
                original_input=user_input,
                action="answer_question",
                entities=self._extract_entities(user_input),
                params={"query": user_input},
                context="general_qa",
                confidence=0.85,
                reasoning="\n".join(reasoning_steps)
            )

        # Default
        return ParsedIntent(
            intent_type=IntentType.UNKNOWN,
            original_input=user_input,
            action="unknown",
            entities=[],
            params={},
            context="",
            confidence=0.5,
            reasoning="ไม่สามารถระบุเจตนาได้ชัดเจน"
        )

    def _extract_equation(self, text: str) -> Dict[str, Any]:
        """แยกส่วนสมการซ้าย-ขวา และตัวแปร"""
        # พยายามหาเครื่องหมาย =
        if "=" in text:
            parts = text.split("=", 1)
            lhs = parts[0].strip()
            rhs = parts[1].strip() if len(parts) > 1 else "0"
            
            # ล้างคำฟุ่มเฟือยบางคำออก (อย่างง่าย)
            # ในอนาคตอาจใช้ NLP ที่ดีกว่านี้
            clean_lhs = re.sub(r'(แก้สมการ|หาค่า|find|solve|for)', '', lhs, flags=re.IGNORECASE).strip()
            clean_rhs = re.sub(r'(เท่ากับ|to)', '', rhs, flags=re.IGNORECASE).strip()
            
            return {
                "lhs": clean_lhs,
                "rhs": clean_rhs,
                "full_expr": f"{clean_lhs} - ({clean_rhs})", # รูปแบบสำหรับแก้: expr = 0
                "variables": self._detect_variables(clean_lhs + clean_rhs)
            }
        return {"raw": text, "variables": self._detect_variables(text)}

    def _extract_functional_eq(self, text: str) -> Dict[str, Any]:
        return {
            "raw": text,
            "target_func": "f"
        }

    def _detect_variables(self, expr: str) -> List[str]:
        """หาตัวแปรภาษาอังกฤษตัวเดียว (x, y, k, n, etc.)"""
        vars_found = set(re.findall(r'\b([a-zA-Z])\b', expr))
        ignore = {'a', 'i', 'e', 'o'} # ตัดคำเชื่อมบางคำ
        return sorted([v for v in vars_found if v not in ignore])

    def _extract_entities(self, text: str) -> List[Any]:
        entities = []
        numbers = re.findall(r"\d+\.?\d*", text)
        for num in numbers:
            try:
                entities.append(float(num) if '.' in num else int(num))
            except ValueError:
                pass
        return entities

def display_analysis(intent: ParsedIntent):
    """แสดงผลการวิเคราะห์แบบละเอียด"""
    print("="*60)
    print("🔍 ผลการวิเคราะห์ความตั้งใจ (Intent Analysis)")
    print("="*60)
    print(f"Input เดิม: \"{intent.original_input}\"")
    print("-" * 40)
    print("🧠 กระบวนการคิด (Reasoning):")
    for i, step in enumerate(intent.reasoning.split('\n'), 1):
        print(f"  {i}. {step}")
    print("-" * 40)
    print(f"✅ ประเภท: {intent.intent_type.value.upper()}")
    print(f"🎯 การกระทำที่ต้องการ: {intent.action}")
    if intent.params:
        print(f"📐 พารามิเตอร์: {intent.params}")
    print(f"📦 ข้อมูลที่สกัดได้ (Entities): {intent.entities}")
    print(f"💡 ความมั่นใจ: {intent.confidence * 100:.1f}%")
    print("="*60)

if __name__ == "__main__":
    parser = IntentParser()
    
    test_cases = [
        "จงหาจำนวนเต็มบวก n ทั้งหมดที่ทำให้ n^4 + 4^n เป็นจำนวนเฉพาะ",
        "x^2+19x-92=k^2 หาจำนวนเต็ม x, k",
        "f(x+y)+f(x)f(y)=f(xy)+f(x)+f(y) จงหาฟังก์ชัน f",
        "9.8-9.11",
        "แม่บอกฉันให้ไปซื้อของราคา 19 บาท ฉันต้องเตรียมเหรียญอะไร",
        "อากาศวันนี้เป็นไงบ้าง"
    ]
    
    for case in test_cases:
        result = parser.parse(case)
        display_analysis(result)
        print("\n")
