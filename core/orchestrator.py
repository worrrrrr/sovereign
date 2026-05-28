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
        
        # กรณี Greeting (ไม่มี output จาก tool)
        if task.intent_id == "greeting_hello":
            return "สวัสดีครับ! มีอะไรให้ผมช่วยวันนี้บอกได้เลยนะครับ 😊"
        
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

# Singleton instance สำหรับใช้งานทั่วระบบ
_global_orchestrator: Optional[Orchestrator] = None

def get_orchestrator() -> Orchestrator:
    """ดึง instance ของ Orchestrator (Singleton Pattern)"""
    global _global_orchestrator
    if _global_orchestrator is None:
        _global_orchestrator = Orchestrator()
    return _global_orchestrator
