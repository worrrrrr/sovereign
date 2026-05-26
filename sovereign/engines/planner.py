"""
Sovereign AI - Planner Engine (Production Grade)
------------------------------------------------
หน้าที่: แปลง Intent ที่วิเคราะห์ได้ ให้เป็น "แผนการเรียกใช้ Tools" (Execution Plan)
หลักการ: Mapping Logic จาก Intent ID ไปยัง Tool Name ที่เหมาะสม
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger("Sovereign.Planner")

@dataclass
class ExecutionStep:
    """ขั้นตอนการดำเนินการหนึ่งขั้น"""
    tool_name: str
    arguments: Dict[str, Any]
    description: str

@dataclass
class ExecutionPlan:
    """แผนการดำเนินงานทั้งหมด"""
    intent_id: str
    steps: List[ExecutionStep]
    is_valid: bool
    error_message: Optional[str] = None

class PlannerEngine:
    """
    รับผิดชอบในการวางแผน (Planning)
    Input: IntentMatch (จาก Perception)
    Output: ExecutionPlan (สำหรับ Execution Engine)
    """
    
    # Mapping Table: กำหนดว่า Intent ไหน ควรใช้ Tool อะไร
    # สามารถขยายเพิ่มได้ง่ายโดยไม่ต้องแก้ Logic หลัก
    INTENT_TO_TOOL_MAP = {
        "math_arithmetic_basic": "calculate_arithmetic",
        "finance_payment_advice": "suggest_payment",
        "time_query": "get_current_time",
        "date_query": "get_current_time",
        "joke_request": "get_random_joke",
        "translation_request": "translate_simple",
        "system_help": "list_available_tools",
        "general_greeting": None, # ไม่ต้องใช้ Tool, ตอบกลับได้เลย
        "knowledge_factual_query": "knowledge_lookup", # Intent ใหม่สำหรับคำถามข้อเท็จจริง
    }

    def __init__(self):
        logger.info("PlannerEngine initialized.")

    def create_plan(self, intent_match: Any) -> ExecutionPlan:
        """
        สร้างแผนการดำเนินงานจากผลลัพธ์ของ Perception
        """
        intent_id = intent_match.intent_id
        params = intent_match.parameters
        
        # 1. ตรวจสอบว่ามี Tool รองรับ Intent นี้หรือไม่
        tool_name = self.INTENT_TO_TOOL_MAP.get(intent_id)
        
        # กรณีพิเศษ: Greeting หรือ Intent ที่ไม่ต้องใช้ Tool
        if tool_name is None:
            if "GREETING" in intent_id:
                return ExecutionPlan(
                    intent_id=intent_id,
                    steps=[],
                    is_valid=True
                )
            else:
                return ExecutionPlan(
                    intent_id=intent_id,
                    steps=[],
                    is_valid=False,
                    error_message=f"No tool mapping found for intent: {intent_id}"
                )
        
        # 2. จัดเตรียม Arguments ให้ตรงกับที่ Tool ต้องการ
        try:
            step = self._prepare_step(tool_name, params, intent_id)
            
            return ExecutionPlan(
                intent_id=intent_id,
                steps=[step],
                is_valid=True
            )
        except Exception as e:
            logger.error(f"Failed to prepare execution plan: {e}")
            return ExecutionPlan(
                intent_id=intent_id,
                steps=[],
                is_valid=False,
                error_message=str(e)
            )

    def _prepare_step(self, tool_name: str, params: Dict[str, Any], intent_id: str) -> ExecutionStep:
        """แปลง Parameters ให้เป็น Arguments ของ Tool"""
        
        arguments = {}
        
        if tool_name == "calculate_arithmetic":
            arguments = {
                "operand_1": params.get("operand_1"),
                "operator": params.get("operator"),
                "operand_2": params.get("operand_2")
            }
            # Validation
            if not all(k in arguments for k in ["operand_1", "operator", "operand_2"]):
                raise ValueError("Missing required math parameters")
                
        elif tool_name == "suggest_payment":
            arguments = {
                "amount": params.get("amount", 0.0),
                "currency": params.get("currency", "THB")
            }
            
        elif tool_name == "translate_simple":
            arguments = {
                "text": params.get("text", ""),
                "target_lang": params.get("target_lang", "en")
            }
            
        elif tool_name == "knowledge_lookup":
            # Knowledge Lookup ต้องการ query string
            arguments = {
                "query": params.get("query", ""),
                "context": params.get("context", None)
            }
            # Validation
            if not arguments["query"]:
                raise ValueError("Missing required 'query' parameter for knowledge_lookup")
            
        elif tool_name in ["get_current_time", "get_random_joke", "list_available_tools"]:
            arguments = {} # ไม่ต้องการพารามิเตอร์
            
        else:
            # Fallback ส่ง params ทั้งหมดไปเลย (อาจเสี่ยงแต่ยืดหยุ่น)
            arguments = params
            
        return ExecutionStep(
            tool_name=tool_name,
            arguments=arguments,
            description=f"Execute {tool_name} with args: {arguments}"
        )
