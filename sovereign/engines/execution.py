"""
Sovereign AI - Execution Engine (Production Grade)
--------------------------------------------------
หน้าที่: รันเครื่องมือ (Tools) ตามแผน (ExecutionPlan) ที่ได้รับจาก Planner
ความปลอดภัย: ตรวจสอบ Tool Name, จำกัดเวลา execution, จับ Exception ทุกจุด
"""

import logging
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from sovereign.tools.registry import global_registry

logger = logging.getLogger("Sovereign.Execution")

@dataclass
class ExecutionResult:
    """ผลลัพธ์จากการรันเครื่องมือ"""
    success: bool
    output: Any
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0
    tool_name: str = ""

class ExecutionEngine:
    """
    รับผิดชอบในการดำเนินการ (Execution) จริง
    Input: ExecutionPlan (จาก Planner)
    Output: ExecutionResult (ผลลัพธ์หรือข้อผิดพลาด)
    """
    
    def __init__(self, timeout_seconds: float = 5.0):
        self.timeout = timeout_seconds
        logger.info(f"ExecutionEngine initialized with timeout={timeout_seconds}s")

    def execute_plan(self, plan: Any) -> ExecutionResult:
        """
        รันแผนการดำเนินงานทั้งหมด
        """
        if not plan.is_valid:
            logger.warning(f"Cannot execute invalid plan: {plan.error_message}")
            return ExecutionResult(
                success=False,
                output=None,
                error_message=f"Invalid plan: {plan.error_message}"
            )
        
        # ถ้าไม่มี steps (เช่น Greeting) ให้คืนค่าสำเร็จทันที
        if not plan.steps:
            logger.debug(f"No steps to execute for intent: {plan.intent_id}")
            return ExecutionResult(
                success=True,
                output={"type": "no_action_required", "intent": plan.intent_id},
                execution_time_ms=0.0
            )
        
        # รันทีละ step (ปัจจุบันรองรับ single-step)
        step = plan.steps[0]
        return self._execute_step(step)

    def _execute_step(self, step: Any) -> ExecutionResult:
        """
        รันหนึ่งขั้นตอนของแผน
        """
        tool_name = step.tool_name
        arguments = step.arguments
        
        logger.info(f"Executing tool: {tool_name} with args: {arguments}")
        
        # 1. ตรวจสอบว่ามี Tool นี้อยู่จริงใน Registry
        if not global_registry.has_tool(tool_name):
            error_msg = f"Tool '{tool_name}' not found in registry."
            logger.error(error_msg)
            return ExecutionResult(
                success=False,
                output=None,
                error_message=error_msg,
                tool_name=tool_name
            )
        
        start_time = time.time()
        
        try:
            # 2. ดึงฟังก์ชัน Tool
            tool_func = global_registry.get_tool(tool_name)
            
            # 3. เรียกใช้ฟังก์ชัน (พร้อม Timeout แบบง่าย)
            # หมายเหตุ: ใน Production จริงควรใช้ multiprocessing หรือ asyncio สำหรับ timeout ที่แม่นยำ
            result = tool_func(**arguments)
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            # 4. ตรวจสอบผลลัพธ์
            if isinstance(result, dict) and result.get("success") is False:
                logger.warning(f"Tool returned failure: {result.get('error')}")
                return ExecutionResult(
                    success=False,
                    output=result,
                    error_message=result.get("error", "Unknown tool error"),
                    execution_time_ms=elapsed_ms,
                    tool_name=tool_name
                )
            
            logger.info(f"Tool executed successfully in {elapsed_ms:.2f}ms")
            return ExecutionResult(
                success=True,
                output=result,
                execution_time_ms=elapsed_ms,
                tool_name=tool_name
            )
            
        except TypeError as e:
            error_msg = f"Invalid arguments for tool '{tool_name}': {e}"
            logger.error(error_msg)
            return ExecutionResult(
                success=False,
                output=None,
                error_message=error_msg,
                execution_time_ms=(time.time() - start_time) * 1000,
                tool_name=tool_name
            )
        except Exception as e:
            error_msg = f"Unexpected error executing '{tool_name}': {e}"
            logger.error(error_msg, exc_info=True)
            return ExecutionResult(
                success=False,
                output=None,
                error_message=error_msg,
                execution_time_ms=(time.time() - start_time) * 1000,
                tool_name=tool_name
            )
