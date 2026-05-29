"""
Router Module - ศูนย์กลางการตัดสินใจและกระจายงาน
เชื่อมระหว่าง Intent Parser -> Knowledge Base / Tools / Response Generator
"""

from typing import Dict, Any, Optional, Tuple
from enum import Enum

# Import modules ที่สร้างไว้
import sys
sys.path.insert(0, '/workspace')

from core.intent_parser import IntentParser, IntentType, ParsedIntent
from knowledge.base import KnowledgeBase
from tools.registry import global_registry as tool_registry
from core.reasoning_engine import get_reasoning_engine

class RouteDecision(Enum):
    USE_KNOWLEDGE = "knowledge"      # ใช้ฐานความรู้
    USE_TOOL = "tool"                # ใช้เครื่องมือ
    USE_RESPONSE = "response"        # ใช้คำตอบสำเร็จรูป (Greeting, Emotion)
    UNCLEAR = "unclear"              # ไม่ชัดเจน ต้องถามกลับ

class Router:
    """ตัวกำหนดเส้นทางและตัดสินใจ"""
    
    def __init__(self, verbose: bool = False):
        self.kb = KnowledgeBase()
        self.intent_parser = IntentParser()
        self.confidence_threshold = 0.7
        self.verbose = verbose
        self.reasoning_engine = get_reasoning_engine()
    
    def route(self, text: str) -> Dict[str, Any]:
        """
        วิเคราะห์ข้อความและตัดสินใจว่าจะใช้โมดูลไหน
        Returns: {
            "decision": RouteDecision,
            "intent": IntentType,
            "parsed_intent": ParsedIntent,
            "target": str,  # KB key, Tool name, หรือ Response type
            "confidence": float,
            "payload": any  # ข้อมูลเพิ่มเติมสำหรับโมดูลปลายทาง
        }
        """
        
        # ขั้นตอนที่ 1: แยก Intent
        parsed = self.intent_parser.parse(text)
        intent = parsed.intent_type
        
        # ขั้นตอนที่ 2: ตัดสินใจตาม Intent
        decision, target, confidence, payload = self._decide_route(text, intent, parsed)
        
        return {
            "decision": decision,
            "intent": intent,
            "parsed_intent": parsed,
            "target": target,
            "confidence": confidence,
            "payload": payload
        }
    
    def _decide_route(self, text: str, intent: IntentType, parsed: ParsedIntent) -> Tuple[RouteDecision, str, float, Any]:
        """ตรรกะการตัดสินใจ"""
        
        # กลุ่มที่ 1: ตอบสนองทางอารมณ์/สังคม (ไม่ต้องใช้ KB หรือ Tool)
        social_intents = [IntentType.GREETING, IntentType.THANK, IntentType.APOLOGIZE, 
                      IntentType.FAREWELL, IntentType.LAUGH, IntentType.ACKNOWLEDGE, 
                      IntentType.REJECT, IntentType.EXPRESS_FEELING]
        
        if intent in social_intents:
            return RouteDecision.USE_RESPONSE, f"response:{intent.value}", 1.0, {"text": text, "parsed": parsed}
        
        # กลุ่มที่ 2: คำสั่ง (COMMAND) -> ใช้ Tools
        if intent == IntentType.COMMAND:
            core_action = parsed.core_action
            if core_action:
                # เลือก Tool ตาม Action
                tool_name = self._map_action_to_tool(core_action.name if hasattr(core_action, 'name') else str(core_action))
                if tool_name:
                    return RouteDecision.USE_TOOL, tool_name, 0.9, {
                        "action": core_action,
                        "text": text,
                        "parsed": parsed
                    }
            
            # ถ้าไม่พบ Tool ที่ตรง ให้ลองหาใน KB
            return RouteDecision.USE_KNOWLEDGE, "command_fallback", 0.5, {"text": text}
        
        # กลุ่มใหม่: การคำนวณ (CALCULATION) -> ใช้ Math Tool โดยตรง
        if intent == IntentType.CALCULATION:
            return RouteDecision.USE_TOOL, "math", 0.95, {
                "text": text,
                "parsed": parsed,
                "entities": parsed.entities
            }
        
        # กลุ่มที่ 3: ถามข้อมูล (ASK_INFO, EXPLAIN, ASK_OPINION) -> ใช้ KB
        question_intents = [IntentType.ASK_INFO, IntentType.EXPLAIN, IntentType.ASK_OPINION, 
                      IntentType.ASK_COMPARISON, IntentType.HYPOTHETICAL]
        
        if intent in question_intents:
            # ค้นหาใน Knowledge Base
            result, confidence, source = self.kb.query(text)
            
            if confidence >= self.confidence_threshold:
                return RouteDecision.USE_KNOWLEDGE, source, confidence, {
                    "query": text,
                    "kb_result": result
                }
            
            # ถ้า KB ไม่มี อาจต้องใช้ Tool ในการคำนวณหรือวิเคราะห์
            tool_suggestion = self._suggest_tool_for_question(text)
            if tool_suggestion:
                return RouteDecision.USE_TOOL, tool_suggestion, 0.6, {
                    "question": text,
                    "intent": intent.value
                }
            
            return RouteDecision.UNCLEAR, "no_knowledge", confidence, {"text": text}
        
        # กลุ่มที่ 4: ขอความช่วยเหลือ (REQUEST_HELP) -> พิจารณาตามบริบท
        if intent == IntentType.REQUEST_HELP:
            # ลองตรวจสอบว่ามีคำกริยาที่ตรงกับ Tool หรือไม่
            tool_suggestion = self._suggest_tool_for_question(text)
            if tool_suggestion:
                return RouteDecision.USE_TOOL, tool_suggestion, 0.7, {
                    "help_request": text
                }
            
            return RouteDecision.USE_KNOWLEDGE, "help_fallback", 0.5, {"text": text}
        
        # กลุ่มที่ 5: อื่นๆ -> UNCLEAR
        return RouteDecision.UNCLEAR, "unknown_intent", 0.3, {"text": text, "intent": intent.value}
    
    def _map_action_to_tool(self, action: str) -> Optional[str]:
        """แปลง Core Action เป็นชื่อ Tool"""
        
        action_to_tool = {
            "คำนวณ": "calculator",
            "ประมวลผล": "calculator",
            "วิเคราะห์": "text_analyzer",
            "สรุป": "text_analyzer",
            "ค้นหา": "pattern_finder",
            "ตรวจสอบ": "pattern_finder",
            "เพิ่ม": "list_processor",
            "สร้าง": "list_processor",
            "ลบ": "list_processor",
            "เรียง": "list_processor",
            "กรอง": "list_processor",
            "แปลง": "calculator",
            "เปรียบเทียบ": "calculator",
        }
        
        return action_to_tool.get(action)
    
    def _suggest_tool_for_question(self, text: str) -> Optional[str]:
        """แนะนำ Tool สำหรับคำถาม"""
        
        text_lower = text.lower()
        
        # คำถามคณิตศาสตร์
        if any(word in text_lower for word in ["บวก", "ลบ", "คูณ", "หาร", "คำนวณ", "เลข", "เท่าไร"]):
            return "calculator"
        
        # คำถามเกี่ยวกับข้อความ
        if any(word in text_lower for word in ["นับ", "วิเคราะห์", "คำ", "ตัวอักษร"]):
            return "text_analyzer"
        
        # คำถามเกี่ยวกับการค้นหา
        if any(word in text_lower for word in ["หา", "ค้นหา", "ค้น"]):
            return "pattern_finder"
        
        return None
    
    def execute_decision(self, route_result: Dict[str, Any]) -> Any:
        """ดำเนินการตามผลการตัดสินใจ"""
        
        decision = route_result["decision"]
        target = route_result["target"]
        payload = route_result["payload"]
        
        if decision == RouteDecision.USE_RESPONSE:
            return self._handle_response(route_result)
        
        elif decision == RouteDecision.USE_KNOWLEDGE:
            return self._handle_knowledge(route_result)
        
        elif decision == RouteDecision.USE_TOOL:
            return self._handle_tool(route_result)
        
        elif decision == RouteDecision.UNCLEAR:
            return self._handle_unclear(route_result)
        
        return None
    
    def _handle_response(self, route_result: Dict) -> str:
        """จัดการการตอบสนองแบบสำเร็จรูป"""
        intent = route_result["intent"]
        text = route_result["payload"].get("text", "")
        
        # Template คำตอบง่ายๆ (ในอนาคตสามารถขยายเป็น Response Engine เต็มรูปแบบ)
        responses = {
            "ทักทาย": ["สวัสดีครับ", "ยินดีต้อนรับครับ", "มีอะไรให้ช่วยบอกได้เลยนะครับ"],
            "ขอบคุณ": ["ยินดีครับ", "ไม่เป็นไรครับ", "พร้อมช่วยเหลือเสมอครับ"],
            "ขอโทษ": ["ไม่เป็นไรครับ", "ไม่มีปัญหาครับ"],
            "อำลา": ["ลาก่อนครับ", "แล้วพบกันใหม่ครับ", "โชคดีครับ"],
            "หัวเราะ/ขำ": ["😄", "ขำดีนะครับ", "มีความสุขจังเลยครับ"],
            "ยืนยัน/รับทราบ": ["ครับ", "เข้าใจแล้วครับ"],
            "ปฏิเสธ": ["ได้ครับ ไม่ต้องกังวลครับ"],
            "แสดงความรู้สึก": ["เข้าใจเลยครับ", "เป็นกำลังใจให้นะครับ"],
        }
        
        intent_key = intent.value
        if intent_key in responses:
            import random
            return random.choice(responses[intent_key])
        
        return "..."
    
    def _handle_knowledge(self, route_result: Dict) -> Any:
        """จัดการการค้นหาจาก Knowledge Base"""
        payload = route_result["payload"]
        
        if "kb_result" in payload and payload["kb_result"]:
            return payload["kb_result"]
        
        # Fallback ถ้า KB ไม่มีข้อมูล
        return "ขออภัย ฉันยังไม่มีข้อมูลนี้ในระบบความรู้ปัจจุบัน"
    
    def _handle_tool(self, route_result: Dict) -> Any:
        """จัดการการเรียกใช้เครื่องมือ"""
        target = route_result["target"]
        payload = route_result["payload"]
        text = payload.get("text") or payload.get("question") or payload.get("help_request", "")
        
        try:
            # Import tools ที่มีอยู่จริงในระบบ
            from tools.registry import global_registry
            from tools import core_tools, math  # โหลด tools ทั้งหมด
            import re
            
            if target == "calculator" or target == "math":
                # แยกสมการคณิตศาสตร์จากข้อความภาษาไทย
                equation_str = text
                
                # พยายาม extract สมการจากข้อความ
                pattern = r'(-?\d+\.?\d*)\s*([+\-\*/])\s*(-?\d+\.?\d*)'
                match = re.search(pattern, text)
                
                if match and '=' not in text:
                    # เป็นนิพจน์คณิตศาสตร์ธรรมดา (เช่น 9.8-9.11)
                    num1 = match.group(1)
                    op = match.group(2)
                    num2 = match.group(3)
                    equation_str = f'{num1}{op}{num2}'
                
                # ใช้ math tool ที่มีอยู่แล้ว
                result_dict = global_registry.get_tool("math")(equation_str=equation_str)
                
                if result_dict.get("success"):
                    solutions = result_dict.get("solutions", [])
                    
                    # ใช้ Reasoning Engine สร้างคำอธิบาย
                    if self.verbose:
                        explained = self.reasoning_engine.process_tool_result(
                            tool_name="math",
                            tool_result=result_dict,
                            verbose=True
                        )
                        return explained.get('explanation', str(solutions[0]) if solutions else "คำนวณได้แต่ไม่มีคำตอบ")
                    else:
                        if solutions:
                            return f"ผลลัพธ์คือ {solutions[0]}"
                        return "คำนวณได้แต่ไม่มีคำตอบ"
                else:
                    return f"เกิดข้อผิดพลาด: {result_dict.get('error', 'ไม่ทราบสาเหตุ')}" 
            
            elif target == "text_analyzer":
                # วิเคราะห์ข้อความแบบง่าย
                return {
                    "char_count": len(text),
                    "word_count": len(text.split()),
                    "thai_chars": len([c for c in text if '\u0E00' <= c <= '\u0E7F'])
                }
            
            elif target == "pattern_finder":
                # ค้นหารูปแบบตัวเลข
                import re
                numbers = re.findall(r"\d+", text)
                return f"พบตัวเลข: {numbers}"
            
            elif target == "list_processor":
                return "เครื่องมือประมวลผลรายการพร้อมใช้งาน"
            
            else:
                # ลองเรียก tool ตามชื่อตรงๆ
                try:
                    func = global_registry.get_tool(target)
                    # พยายามเรียกด้วย parameter ที่เหมาะสม
                    result = func(equation_str=text) if target == "math" else func(text=text)
                    return str(result)
                except KeyError:
                    return f"เครื่องมือ '{target}' ไม่พบในระบบ"
                except Exception as e:
                    return f"เครื่องมือ '{target}' ทำงานแต่เกิดข้อผิดพลาด: {str(e)}"
        
        except Exception as e:
            return f"เกิดข้อผิดพลาดในการประมวลผล: {str(e)}"
    
    def _handle_unclear(self, route_result: Dict) -> str:
        """จัดการกรณีที่ไม่ชัดเจน"""
        return "ขออภัย ฉันยังไม่เข้าใจคำถามของคุณ ช่วยอธิบายเพิ่มเติมได้ไหมครับ?"

# ทดสอบ
if __name__ == "__main__":
    router = Router()
    
    test_cases = [
        "สวัสดีครับ",
        "เปิดไฟหน่อย",
        "ช่วยคำนวณ 5 + 3 ให้หน่อย",
        "คุณชื่ออะไร",
        "ทำอะไรได้บ้าง",
        "ฉันดีใจมาก",
        "ขอบคุณครับ",
        "分析一下这个文本",  # ไม่ชัดเจน
        "ซื้อของ 19 บาท ต้องเตรียมเงินยังไง",
    ]
    
    print("="*80)
    print(f"{'ข้อความ':35} | {'Decision':15} | {'Target':20} | {'Confidence':10}")
    print("="*80)
    
    for text in test_cases:
        result = router.route(text)
        decision_str = result["decision"].value[:15]
        target_str = result["target"][:20] if result["target"] else "-"
        print(f"{text:35} | {decision_str:15} | {target_str:20} | {result['confidence']:.2f}")
    
    print("\n" + "="*80)
    print("ทดสอบการ Execute:")
    print("="*80)
    
    execution_tests = [
        "สวัสดีครับ",
        "ช่วยคำนวณ 10 + 5 ให้หน่อย",
        "คุณชื่ออะไร",
        "นับคำในประโยคนี้ให้หน่อย",
    ]
    
    for text in execution_tests:
        route_result = router.route(text)
        response = router.execute_decision(route_result)
        print(f"\nQ: {text}")
        print(f"A: {response}")
