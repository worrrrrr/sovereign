"""
Intent Parser: วิเคราะห์ Input แยกแยะว่าเป็น 'คำสั่ง' หรือ 'คำถาม'
และดึงข้อมูลสำคัญ (Entities) ออกมา
"""
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class IntentType(Enum):
    CALCULATION = "calculation"
    QUESTION = "question"
    COMMAND = "command"
    UNKNOWN = "unknown"

@dataclass
class ParsedIntent:
    intent_type: IntentType
    original_input: str
    action: str  # เช่น "subtract", "prepare_money"
    entities: List[Any]  # ข้อมูลตัวเลขหรือข้อความที่สำคัญ
    context: str  # บริบทเพิ่มเติม
    confidence: float
    reasoning: str  # เหตุผลในการตัดสินใจ (แสดงวิธีคิด)

class IntentParser:
    def __init__(self):
        # Patterns สำหรับตรวจจับการคำนวณ
        self.calc_patterns = [
            r"(\d+\.?\d*)\s*[-+*/]\s*(\d+\.?\d*)",  # 9.8-9.11
            r"calculate\s+(.+)",
            r"find\s+(.+)",
        ]
        
        # Patterns สำหรับตรวจจับคำถาม
        self.question_patterns = [
            r"(.*)\?(.*)",  # มีเครื่องหมาย ?
            r"อย่างไร", r"ยังไง", r"อะไร", r"แบบไหน", r"เตรียม.*เหมาะสม",
            r"how\s+to", r"what\s+", r"which\s+"
        ]
        
        # Keywords สำหรับคำสั่งเฉพาะ
        self.command_keywords = {
            "ซื้อ": "buy",
            "เตรียม": "prepare",
            "ไป": "go",
            "เขียน": "write",
            "สร้าง": "create"
        }

    def parse(self, user_input: str) -> ParsedIntent:
        input_lower = user_input.lower().strip()
        reasoning_steps = []
        
        # 1. ตรวจสอบว่าเป็นการคำนวณ murni หรือไม่ (เช่น "9.8-9.11")
        calc_match = re.search(r"(-?\d+\.?\d*)\s*([-+*/])\s*(-?\d+\.?\d*)", user_input)
        if calc_match and not any(q in input_lower for q in ["?", "อย่างไร", "what", "how"]):
            num1 = float(calc_match.group(1))
            op = calc_match.group(2)
            num2 = float(calc_match.group(3))
            
            reasoning_steps.append(f"ตรวจพบรูปแบบนิพจน์คณิตศาสตร์: {num1} {op} {num2}")
            reasoning_steps.append(f"ไม่พบคำ/question words จึงจัดเป็น 'คำสั่งคำนวณ'")
            
            return ParsedIntent(
                intent_type=IntentType.CALCULATION,
                original_input=user_input,
                action=f"calculate_{op}",
                entities=[num1, num2],
                context=op,
                confidence=0.99,
                reasoning="\n".join(reasoning_steps)
            )

        # 2. ตรวจสอบว่าเป็นคำถามหรือไม่
        is_question = any(re.search(p, input_lower) for p in self.question_patterns)
        
        if is_question:
            reasoning_steps.append("ตรวจพบเครื่องหมาย '?' หรือคำถาม (อย่างไร, อะไร, อะไรเหมาะสม)")
            action = self._extract_action(input_lower)
            entities = self._extract_entities(user_input)
            
            reasoning_steps.append(f"สรุปการกระทำที่ต้องการ: {action}")
            reasoning_steps.append(f"ข้อมูลที่สกัดได้: {entities}")
            
            return ParsedIntent(
                intent_type=IntentType.QUESTION,
                original_input=user_input,
                action=action,
                entities=entities,
                context="user_seeking_advice",
                confidence=0.95,
                reasoning="\n".join(reasoning_steps)
            )

        # 3. ตรวจสอบคำสั่งทั่วไป
        for keyword, action_code in self.command_keywords.items():
            if keyword in input_lower:
                entities = self._extract_entities(user_input)
                reasoning_steps.append(f"ตรวจพบคำกริยา '{keyword}' แปลเป็น action: {action_code}")
                return ParsedIntent(
                    intent_type=IntentType.COMMAND,
                    original_input=user_input,
                    action=action_code,
                    entities=entities,
                    context="direct_command",
                    confidence=0.90,
                    reasoning="\n".join(reasoning_steps)
                )

        # Default
        return ParsedIntent(
            intent_type=IntentType.UNKNOWN,
            original_input=user_input,
            action="unknown",
            entities=[],
            context="",
            confidence=0.5,
            reasoning="ไม่สามารถระบุเจตนาได้ชัดเจน ต้องการข้อมูลเพิ่มเติม"
        )

    def _extract_action(self, text: str) -> str:
        if "เตรียม" in text and ("เหรียญ" in text or "แบงค์" in text or "เงิน" in text):
            return "suggest_payment_method"
        if "ซื้อ" in text:
            return "analyze_purchase"
        return "general_inquiry"

    def _extract_entities(self, text: str) -> List[Any]:
        entities = []
        # หาตัวเลขทั้งหมด (รวมถึงทศนิยม)
        numbers = re.findall(r"\d+\.?\d*", text)
        for num in numbers:
            try:
                if '.' in num:
                    entities.append(float(num))
                else:
                    entities.append(int(num))
            except ValueError:
                pass
        
        # หาหน่วยเงิน
        if "บาท" in text:
            entities.append({"currency": "THB"})
            
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
    print(f"📦 ข้อมูลที่สกัดได้ (Entities): {intent.entities}")
    print(f"💡 ความมั่นใจ: {intent.confidence * 100:.1f}%")
    print("="*60)

if __name__ == "__main__":
    parser = IntentParser()
    
    # ทดสอบโจทย์ทั้ง 2 ข้อ
    test_cases = [
        "9.8-9.11",
        "แม่บอกฉันให้ไปซื้อของราคา 19 บาท ฉันต้องเตรียมเหรียญหรือแบงค์อะไรถึงจะเหมาะสม"
    ]
    
    for case in test_cases:
        result = parser.parse(case)
        display_analysis(result)
        print("\n")
