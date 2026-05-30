"""
Sovereign AI - Knowledge Lookup Tool (Production-Grade)
-------------------------------------------------------
หน้าที่: เป็นสะพาน (Wrapper) ระหว่าง Execution Engine และ Knowledge Base
รับประกันความเสถียร ไม่ปล่อยให้ Exception หลุดไปถึงระบบหลัก
"""

import logging
from typing import Dict, Any, Optional
from core.knowledge_base import get_knowledge_base

logger = logging.getLogger("Sovereign.KnowledgeTool")

class KnowledgeLookupTool:
    """เครื่องมือค้นหาข้อมูลจากฐานความรู้ที่มีความตระหนักรู้ด้านเวลา"""
    
    name = "knowledge_lookup"
    description = "ค้นหาข้อเท็จจริงจากฐานข้อมูลภายในที่มีความน่าเชื่อถือสูง (การเมือง, วิทยาศาสตร์, ภูมิศาสตร์)"
    
    def execute(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        ดำเนินการค้นหาและคืนค่าผลลัพธ์ในรูปแบบมาตรฐาน (Standardized Output)
        """
        # 1. Input Validation ป้องกันระบบพังจาก Data Type ผิดพลาด
        if not query or not isinstance(query, str):
            logger.warning("ได้รับคำสั่งสืบค้นที่ไม่ถูกต้อง (Empty or Non-string)")
            return self._build_error_response("คำสั่งสืบค้นไม่ถูกต้องหรือไม่ครบถ้วน")

        try:
            # 2. เรียกใช้งาน Knowledge Base (Singleton)
            kb = get_knowledge_base()
            result = kb.query(query, context)
            
            # 3. จัดการผลลัพธ์ (Response Formatting)
            if result:
                response_text = result['answer']
                
                # เพิ่มแหล่งอ้างอิงเพื่อสนับสนุนหลักการตรวจสอบได้ (Te Principle)
                if result.get('source'):
                    response_text += f"\n(แหล่งข้อมูล: {result['source']})"
                
                # แจ้งเตือนผู้ใช้หากเป็นข้อมูลประวัติศาสตร์ (Fe/Ni Principle)
                if result.get('is_historical'):
                    response_text += "\n*หมายเหตุ: นี่คือข้อมูลในอดีต อาจมีการเปลี่ยนแปลงแล้ว*"
                
                return {
                    "success": True,
                    "result": response_text,
                    "confidence": result['confidence'],
                    "source": result['source'],
                    "metadata": result.get('metadata', {})
                }
            else:
                return self._build_error_response(
                    "ไม่พบข้อมูลที่ตรงกับคำถามในฐานความรู้ปัจจุบัน",
                    "ลองตรวจสอบคำถาม หรือติดต่อผู้ดูแลระบบเพื่อเพิ่มข้อมูลชุดนี้"
                )
                
        except Exception as e:
            # ป้องกันข้อผิดพลาดที่ไม่คาดคิด (Unhandled Exceptions) ทำลายระบบการทำงานหลัก
            logger.error(f"เกิดข้อผิดพลาดรุนแรงขณะสืบค้นข้อมูล: {e}", exc_info=True)
            return self._build_error_response("ระบบสืบค้นข้อมูลขัดข้องชั่วคราว")

    def _build_error_response(self, message: str, suggestion: str = "") -> Dict[str, Any]:
        """ฟังก์ชันช่วยเหลือสำหรับสร้างโครงสร้างผลลัพธ์ที่เป็นมาตรฐานกรณีผิดพลาด"""
        return {
            "success": False,
            "result": message,
            "suggestion": suggestion,
            "confidence": 0.0
        }

# สร้าง Instance ของเครื่องมือสำหรับนำไปลงทะเบียนใน Registry
tool_instance = KnowledgeLookupTool()

def query_general(query: str) -> Dict[str, Any]:
    """Wrapper function for general knowledge queries"""
    return tool_instance.execute(query)

# Register the tool
from tools.registry import global_registry

global_registry.register(
    name="knowledge",
    func=query_general,
    description="เครื่องมือตอบคำถามทั่วไปและค้นหาข้อมูล (จำลอง)",
    category="KNOWLEDGE",
    actions={
        "query_general": query_general
    }
)
