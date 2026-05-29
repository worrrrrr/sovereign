"""
Sovereign AI - Orchestrator (Production Grade)
----------------------------------------------
หน้าที่: ประสานงานระหว่าง Perception, Planner, และ Execution Engines
เป็นจุดเข้าใช้งานหลัก (Main Entry Point) สำหรับระบบ
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Import Engines - ใช้จาก engines module ทั้งหมด
from engines.perception import PerceptionEngine, Task
from engines.planner import PlannerEngine, ExecutionPlan
from engines.execution import ExecutionEngine, ExecutionResult

logger = logging.getLogger("Sovereign.Orchestrator")

@dataclass
class OrchestratorResponse:
    """โครงสร้างคำตอบมาตรฐานของระบบ"""
    success: bool
    intent_id: str
    response_text: str
    raw_output: Any = None
    error_message: Optional[str] = None

class Orchestrator:
    """
    ตัวประสานงานหลัก (Central Coordinator)
    ควบคุม Flow: Input -> Perception -> Planner -> Execution -> Response
    """
    
    def __init__(self):
        logger.info("Initializing Sovereign AI Orchestrator...")
        
        try:
            # 1. Initialize Perception Engine
            self.perception = PerceptionEngine(
                taxonomy_path="config/intent_taxonomy.json"
            )
            
            # 2. Initialize Planner Engine
            self.planner = PlannerEngine()
            
            # 3. Initialize Execution Engine
            self.execution = ExecutionEngine(timeout_seconds=5.0)
            
            # Import tools เพื่อลงทะเบียน (ต้อง import math ก่อน core_tools เพราะ core_tools ใช้ registry)
            from tools import math  # noqa: F401
            from tools import core_tools  # noqa: F401
            
            logger.info("Sovereign AI Orchestrator initialized successfully.")
            
        except Exception as e:
            logger.critical(f"Failed to initialize Orchestrator: {e}")
            raise

    def process(self, user_input: str) -> OrchestratorResponse:
        """
        กระบวนการประมวลผลหลัก
        Input: ข้อความจากผู้ใช้
        Output: คำตอบที่พร้อมแสดงผล
        """
        logger.info(f"Processing input: '{user_input}'")
        
        try:
            # Step 1: Perception (วิเคราะห์เจตนา)
            task = self.perception.analyze(user_input)
            logger.debug(f"Task detected: {task.intent_id} (confidence: {task.confidence:.2f})")
            
            # ถ้าไม่รู้จัก Intent เลย
            if task.intent_id == "unknown":
                return OrchestratorResponse(
                    success=False,
                    intent_id="UNKNOWN",
                    response_text="ขอโทษครับ ผมยังไม่เข้าใจคำถามนี้ คุณช่วยลองถามในรูปแบบอื่นได้ไหมครับ?",
                    error_message="Unrecognized intent"
                )
            
            # Step 2: Planning (สร้างแผน)
            plan = self.planner.create_plan(task)
            
            if not plan.is_valid:
                logger.warning(f"Planning failed: {plan.error_message}")
                return OrchestratorResponse(
                    success=False,
                    intent_id=task.intent_id,
                    response_text=f"ขอโทษครับ เกิดข้อผิดพลาดในการวางแผน: {plan.error_message}",
                    error_message=plan.error_message
                )
            
            # Step 3: Execution (รันแผน)
            result = self.execution.execute_plan(plan)
            
            if not result.success:
                logger.error(f"Execution failed: {result.error_message}")
                return OrchestratorResponse(
                    success=False,
                    intent_id=task.intent_id,
                    response_text=f"ขอโทษครับ เกิดข้อผิดพลาดขณะดำเนินการ: {result.error_message}",
                    error_message=result.error_message,
                    raw_output=result.output
                )
            
            # Step 4: Format Response (จัดรูปแบบคำตอบ)
            response_text = self._format_response(task, result)
            
            return OrchestratorResponse(
                success=True,
                intent_id=task.intent_id,
                response_text=response_text,
                raw_output=result.output
            )
            
        except Exception as e:
            logger.error(f"Critical error in orchestrator: {e}", exc_info=True)
            return OrchestratorResponse(
                success=False,
                intent_id="ERROR",
                response_text=f"เกิดข้อผิดพลาดในระบบ: {str(e)}",
                error_message=str(e)
            )

    def _format_response(self, task: Task, result: ExecutionResult) -> str:
        """
        จัดรูปแบบผลลัพธ์ให้เป็นข้อความที่อ่านง่าย
        """
        output = result.output
        
        # ดึง metadata จาก plan (ถ้ามี)
        intent_type = task.parameters.get('intent_type', '') if task.parameters else ''
        
        # กรณี Greeting (ไม่มี output จาก tool)
        if task.intent_id == "greeting_hello":
            return "สวัสดีครับ! มีอะไรให้ผมช่วยวันนี้บอกได้เลยนะครับ 😊"
        
        # กรณี Social/Emotional responses (แสดงความรู้สึก, บ่น, สับสน, ประชด)
        if task.intent_id.startswith('emotion_') or intent_type in ['express_feeling', 'vent_complain', 'express_confusion', 'sarcasm_passive']:
            return self._generate_empathy_response(intent_type, task.parameters.get('original_input', ''))
        
        # กรณี System test/noise
        if task.intent_id == 'system_test_noise' or intent_type == 'test_noise':
            return "✅ ระบบพร้อมใช้งานครับ มีอะไรให้ช่วยบอกได้เลยนะครับ"
        
        # กรณี Social responses (ขอบคุณ, อำลา, ขอโทษ, หัวเราะ, ยืนยัน, ปฏิเสธ)
        if task.intent_id in ['social_thank_you', 'farewell_goodbye', 'social_apologize', 'social_laugh', 'response_acknowledge', 'response_reject']:
            return self._generate_social_response(task.intent_id)
        
        # กรณีคำนวณเลข
        if task.intent_id == "math_arithmetic_basic":
            if isinstance(output, dict):
                expr = output.get('expression', '')
                res = output.get('result')
                return f"ผลลัพธ์ของ {expr} = **{res}**"
        
        # กรณีแนะนำการชำระเงิน
        if task.intent_id == "money_payment_advice":
            if isinstance(output, dict):
                amount = output.get('amount', 0)
                suggestion = output.get('suggestion', [])
                total_items = output.get('total_items', 0)
                
                lines = [f"สำหรับยอดเงิน {amount} บาท แนะนำให้เตรียมดังนี้:"]
                for item in suggestion:
                    denom = item['denomination']
                    count = item['count']
                    item_type = "แบงค์" if item['type'] == 'bill' else "เหรียญ"
                    lines.append(f"  - {item_type} {denomination} บาท จำนวน {count} อัน")
                
                lines.append(f"รวมทั้งหมด {total_items} ชิ้น (ทอนน้อยที่สุด)")
                return "\n".join(lines)
        
        # กรณีถามเวลา
        if task.intent_id in ["time_current", "date_current"]:
            if isinstance(output, dict):
                time_str = output.get('time', '')
                date_str = output.get('date', '')
                return f"ปัจจุบันเวลา {time_str} น. วันที่ {date_str}"
        
        # กรณีมุกตลก
        if task.intent_id == "entertainment_joke":
            if isinstance(output, dict):
                joke = output.get('joke', '')
                return f"😄 {joke}"
        
        # กรณีแปลภาษา
        if task.intent_id == "translation_request":
            if isinstance(output, dict):
                if output.get('success'):
                    original = output.get('original', '')
                    translation = output.get('translation', '')
                    target = output.get('target_language', 'en')
                    return f"'{original}' แปลเป็น {target} คือ '{translation}'"
                else:
                    return output.get('error', 'แปลไม่ได้')
        
        # กรณีแสดงรายชื่อ tools
        if task.intent_id == "system_help":
            if isinstance(output, dict):
                count = output.get('count', 0)
                tools = output.get('tools', [])
                lines = [f"ระบบมีเครื่องมือพร้อมใช้งาน {count} รายการ:"]
                for tool in tools:
                    lines.append(f"  - {tool['name']}: {tool['description']}")
                return "\n".join(lines)
        
        # Fallback: แสดงผลลัพธ์ดิบ
        return f"ผลลัพธ์: {output}"
    
    def _generate_empathy_response(self, intent_type: str, original_input: str) -> str:
        """
        สร้างคำตอบแสดงความเห็นอกเห็นใจตามประเภทอารมณ์
        """
        empathy_responses = {
            'express_feeling': [
                "เข้าใจเลยครับ that's completely normal to feel that way.",
                "ขอบคุณที่แบ่งปันความรู้สึกนะครับ ผมรับฟังเสมอครับ",
                "ความรู้สึกของคุณสำคัญนะครับ มีอะไรให้ช่วยบอกได้เลยครับ"
            ],
            'vent_complain': [
                "เข้าใจเลยครับว่าทำไมถึงรู้สึกแบบนั้น บางทีชีวิตก็มีเรื่องเหนื่อยจริงๆ",
                "ฟังดูว่าคุณผ่านเรื่องหนักมาเยอะเลยนะครับ อยากเล่าเพิ่มไหมครับ?",
                "ผมเข้าใจเลยครับ บางครั้งการได้ระบายออกมาก็ช่วยให้สบายขึ้นนะครับ"
            ],
            'express_confusion': [
                "ไม่ต้องกังวลครับ ถ้าไม่เข้าใจตรงไหนถามผมได้เลยนะครับ",
                "เรื่องนี้มันซับซ้อนจริงๆ ครับ ลองอธิบายให้ฟังอีกทีไหมครับ?",
                "ไม่เป็นไรครับ เราค่อยๆ มาทำความเข้าใจไปด้วยกันนะครับ"
            ],
            'sarcasm_passive': [
                "ผมเข้าใจนะครับว่าอาจมีอะไรที่ไม่เป็นอย่างหวัง 😊",
                "บางครั้งสิ่งที่ดีที่สุดคือการหัวเราะให้กับสถานการณ์นะครับ",
                "ผมอยู่ข้างๆ คุณนะครับ มีอะไรให้ช่วยบอกได้เลยครับ"
            ]
        }
        
        import random
        responses = empathy_responses.get(intent_type, ["ผมเข้าใจครับ มีอะไรให้ช่วยบอกได้เลยนะครับ"])
        return random.choice(responses)
    
    def _generate_social_response(self, intent_id: str) -> str:
        """
        สร้างคำตอบตอบสนองทางสังคม (ขอบคุณ, อำลา, ขอโทษ, ฯลฯ)
        """
        social_responses = {
            'social_thank_you': [
                "ยินดีมากครับ! 😊",
                "ไม่เป็นไรครับ ยินดีที่ได้ช่วยเสมอครับ",
                "ขอบคุณครับที่ไว้ใจให้ผมช่วยนะครับ"
            ],
            'farewell_goodbye': [
                "ลาก่อนครับ! ไว้เจอกันใหม่นะครับ 👋",
                "โชคดีนะครับ แล้วเจอกันใหม่ครับ!",
                "บ๊ายบายครับ ดูแลตัวเองด้วยนะครับ"
            ],
            'social_apologize': [
                "ไม่เป็นไรครับ ไม่ต้องกังวลนะครับ 😊",
                "ไม่มีปัญหาครับ ทุกคนทำผิดพลาดได้ครับ",
                "โอเคครับ ไม่ถือสาหรอกนะครับ"
            ],
            'social_laugh': [
                "555 ขำด้วยคนครับ! 😄",
                "ตลกจังครับ ฮ่าๆๆ",
                "มีความสุขจังเลยครับ ที่เห็นคุณขำก็ทำให้ผม vui ล่ะครับ"
            ],
            'response_acknowledge': [
                "เยี่ยมเลยครับ! 👍",
                "เข้าใจตรงกันแล้วนะครับ",
                "โอเคครับ พร้อมดำเนินการต่อเลยครับ"
            ],
            'response_reject': [
                "โอเคครับ ไม่เป็นไรนะครับ",
                "เข้าใจครับ ถ้าเปลี่ยนใจเมื่อไหร่บอกได้เลยนะครับ",
                "ได้ครับ ไม่มีปัญหาครับ"
            ]
        }
        
        import random
        responses = social_responses.get(intent_id, ["ขอบคุณครับที่พูดคุยกับผมครับ"])
        return random.choice(responses)

# Singleton instance สำหรับใช้งานทั่วระบบ
_global_orchestrator: Optional[Orchestrator] = None

def get_orchestrator() -> Orchestrator:
    """ดึง instance ของ Orchestrator (Singleton Pattern)"""
    global _global_orchestrator
    if _global_orchestrator is None:
        _global_orchestrator = Orchestrator()
    return _global_orchestrator
