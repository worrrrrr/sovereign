"""
Sovereign AI - Tool Registry
----------------------------
หน้าที่: ลงทะเบียนและจัดการเครื่องมือ (Tools) ทั้งหมดในระบบ
หลักการ: Centralized Registry Pattern เพื่อให้ Execution Engine เรียกใช้ได้ง่าย
"""

from typing import Dict, Callable, Any, List
import logging

logger = logging.getLogger("Sovereign.Tools")

class ToolRegistry:
    """
    คลังเก็บเครื่องมือทั้งหมด
    แต่ละ Tool ต้องมี: name, description, function
    """
    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, func: Callable, description: str, category: str):
        """ลงทะเบียนเครื่องมือใหม่"""
        if name in self._tools:
            logger.warning(f"Tool '{name}' is already registered. Overwriting...")
        
        self._tools[name] = {
            "name": name,
            "function": func,
            "description": description,
            "category": category
        }
        logger.debug(f"Registered tool: {name} ({category})")

    def get_tool(self, name: str) -> Callable:
        """ดึงฟังก์ชันของเครื่องมือตามชื่อ"""
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found in registry.")
        return self._tools[name]["function"]

    def get_tool_info(self, name: str) -> Dict[str, Any]:
        """ดึงข้อมูลรายละเอียดของเครื่องมือ"""
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found in registry.")
        return {
            "name": self._tools[name]["name"],
            "description": self._tools[name]["description"],
            "category": self._tools[name]["category"]
        }

    def list_tools(self) -> List[str]:
        """แสดงรายชื่อเครื่องมือทั้งหมด"""
        return list(self._tools.keys())

    def has_tool(self, name: str) -> bool:
        """ตรวจสอบว่ามีเครื่องมือนี้อยู่หรือไม่"""
        return name in self._tools

# สร้าง Instance กลางสำหรับทั้งระบบ
global_registry = ToolRegistry()
