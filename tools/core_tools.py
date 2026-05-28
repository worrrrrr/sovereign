"""
Sovereign AI - Core Tools Implementation
----------------------------------------
หน้าที่: จัดเตรียมเครื่องมือพื้นฐานสำหรับระบบ (Math, Finance, General)
ความปลอดภัย: ห้ามใช้ eval/exec, ใช้ Decimal สำหรับคณิตศาสตร์
"""

import math
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, List
from datetime import datetime
import random

from tools.registry import global_registry

# ==============================================================================
# 1. MATHEMATICAL TOOLS (เครื่องมือคำนวณ)
# ==============================================================================

def calculate_arithmetic(operand_1: float, operator: str, operand_2: float) -> Dict[str, Any]:
    """
    คำนวณทางคณิตศาสตร์พื้นฐาน (+, -, *, /)
    ใช้ Decimal เพื่อความแม่นยำสูงสุด
    """
    try:
        # แปลงเป็น Decimal เพื่อหลีกเลี่ยง Floating Point Error
        op1 = Decimal(str(operand_1))
        op2 = Decimal(str(operand_2))
        
        if operator == '+':
            result = op1 + op2
        elif operator == '-':
            result = op1 - op2
        elif operator in ['*', 'x']:
            result = op1 * op2
        elif operator in ['/', '÷']:
            if op2 == 0:
                return {"success": False, "error": "Division by zero is not allowed."}
            result = op1 / op2
        else:
            return {"success": False, "error": f"Unsupported operator: {operator}"}
        
        # ปัดเศษทศนิยมให้สวยงาม (สูงสุด 6 ตำแหน่ง)
        final_result = float(result.quantize(Decimal('0.000001')))
        
        return {
            "success": True,
            "result": final_result,
            "expression": f"{operand_1} {operator} {operand_2}",
            "precision_used": "Decimal"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# ลงทะเบียน Tool
global_registry.register(
    name="calculate_arithmetic",
    func=calculate_arithmetic,
    description="คำนวณบวก ลบ คูณ หาร ด้วยความแม่นยำสูง",
    category="MATHEMATICS"
)

# ==============================================================================
# 2. FINANCE TOOLS (เครื่องมือทางการเงิน)
# ==============================================================================

def suggest_payment(amount: float, currency: str = "THB") -> Dict[str, Any]:
    """
    แนะนำวิธีการชำระเงินที่เหมาะสมที่สุด (จำนวนเหรียญ/แบงค์น้อยที่สุด)
    """
    if amount <= 0:
        return {"success": False, "error": "Amount must be positive."}
    
    # สกุลเงินบาทไทย (THB)
    denominations = [1000, 500, 100, 50, 20, 10, 5, 2, 1]
    if currency != "THB":
        denominations = [100, 50, 20, 10, 5, 1] # USD/EUR fallback
    
    remaining = int(amount * 100) / 100  # Normalize float
    suggestion = []
    
    for denom in denominations:
        count = int(remaining // denom)
        if count > 0:
            suggestion.append({"denomination": denom, "count": count, "type": "bill" if denom >= 20 else "coin"})
            remaining -= count * denom
            remaining = round(remaining, 2)
    
    # กรณีมีเศษสตางค์ (ถ้ามี)
    if remaining > 0.001:
        suggestion.append({"denomination": remaining, "count": 1, "type": "change"})

    return {
        "success": True,
        "amount": amount,
        "currency": currency,
        "suggestion": suggestion,
        "total_items": sum(item['count'] for item in suggestion)
    }

global_registry.register(
    name="suggest_payment",
    func=suggest_payment,
    description="แนะนำวิธีเตรียมเงินหรือเหรียญให้เหมาะสมกับยอดเงิน",
    category="FINANCE"
)

# ==============================================================================
# 3. GENERAL KNOWLEDGE TOOLS (เครื่องมือความรู้ทั่วไป)
# ==============================================================================

def get_current_time() -> Dict[str, Any]:
    """ดึงเวลาปัจจุบัน"""
    now = datetime.now()
    return {
        "success": True,
        "time": now.strftime("%H:%M:%S"),
        "date": now.strftime("%Y-%m-%d"),
        "timezone": "Local"
    }

global_registry.register(
    name="get_current_time",
    func=get_current_time,
    description="บอกเวลาและวันที่ปัจจุบัน",
    category="GENERAL"
)

def get_random_joke() -> Dict[str, Any]:
    """สุ่มมุกตลก"""
    jokes = [
        "ทำไมนกกระจอกเทศถึงไม่บิน? ... เพราะมันขี้เกียจออกแรง!",
        "เลข 0 พูดกับเลข 8 ว่า... เธอคาดเข็มขัดสวยจัง!",
        "อะไรเอ่ย? อยู่ที่ไหนก็หนาว... คำตอบ: ขั้วโลกเหนือ (เพราะอยู่ขั้ว)",
        "ครู: หนูช่วยแต่งประโยคที่มีคำว่า 'น้ำตาล' ให้หน่อย... นักเรียน: กาแฟช้อนนี้หวานจัง!",
    ]
    return {
        "success": True,
        "joke": random.choice(jokes),
        "category": "thai_humor"
    }

global_registry.register(
    name="get_random_joke",
    func=get_random_joke,
    description="เล่าเรื่องตลกสุ่ม",
    category="ENTERTAINMENT"
)

def translate_simple(text: str, target_lang: str = "en") -> Dict[str, Any]:
    """
    จำลองการแปลภาษาแบบง่าย (Hardcoded dictionary สำหรับคำศัพท์พื้นฐาน)
    ใน Production จริงควรเชื่อมต่อกับ API เช่น Google Translate
    """
    dictionary = {
        "สวัสดี": {"en": "Hello", "jp": "Konnichiwa"},
        "ขอบคุณ": {"en": "Thank you", "jp": "Arigato"},
        "ใช่": {"en": "Yes", "jp": "Hai"},
        "ไม่ใช่": {"en": "No", "jp": "Iie"},
        "น้ำ": {"en": "Water", "jp": "Mizu"},
        "อาหาร": {"en": "Food", "jp": "Tabemono"},
    }
    
    clean_text = text.strip()
    if clean_text in dictionary:
        translation = dictionary[clean_text].get(target_lang, "Translation not found")
        return {
            "success": True,
            "original": clean_text,
            "translation": translation,
            "target_language": target_lang
        }
    
    return {
        "success": False,
        "error": f"Word '{clean_text}' not found in basic dictionary.",
        "note": "This is a demo translator. Please connect to a real API for full support."
    }

global_registry.register(
    name="translate_simple",
    func=translate_simple,
    description="แปลคำศัพท์พื้นฐาน (Demo)",
    category="LANGUAGE"
)

# ==============================================================================
# 4. SYSTEM TOOLS (เครื่องมือระบบ)
# ==============================================================================

def list_available_tools() -> Dict[str, Any]:
    """แสดงรายชื่อเครื่องมือทั้งหมดที่มีในระบบ"""
    tools = global_registry.list_tools()
    details = []
    for tool_name in tools:
        info = global_registry.get_tool_info(tool_name)
        details.append(info)
    
    return {
        "success": True,
        "count": len(tools),
        "tools": details
    }

global_registry.register(
    name="list_available_tools",
    func=list_available_tools,
    description="แสดงรายชื่อเครื่องมือทั้งหมดที่ใช้งานได้",
    category="SYSTEM"
)

# ==============================================================================
# 5. KNOWLEDGE BASE TOOLS (เครื่องมือฐานความรู้ภายใน)
# ==============================================================================

def knowledge_lookup_wrapper(query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Wrapper สำหรับเรียกใช้ KnowledgeLookupTool จาก core_tools
    เพื่อให้สอดคล้องกับรูปแบบการลงทะเบียน Tool อื่นๆ
    """
    from tools.knowledge_tool import tool_instance
    
    # เรียก execute โดยตรงจาก instance
    result = tool_instance.execute(query, context)
    
    # แปลงผลลัพธ์ให้ตรงกับรูปแบบมาตรฐานของ core_tools
    if result.get("success"):
        return {
            "success": True,
            "result": result.get("result"),
            "confidence": result.get("confidence", 0.0),
            "source": result.get("source", "Internal KB"),
            "metadata": result.get("metadata", {})
        }
    else:
        return {
            "success": False,
            "error": result.get("result"),
            "suggestion": result.get("suggestion", "")
        }

global_registry.register(
    name="knowledge_lookup",
    func=knowledge_lookup_wrapper,
    description="ค้นหาข้อเท็จจริงจากฐานข้อมูลภายในที่มีความน่าเชื่อถือสูง (การเมือง, วิทยาศาสตร์, ภูมิศาสตร์)",
    category="KNOWLEDGE"
)
