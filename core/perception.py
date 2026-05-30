"""
Sovereign AI - Perception Engine (Production Grade)
---------------------------------------------------
หน้าที่: วิเคราะห์ข้อความนำเข้า (Input) เพื่อระบุเจตนา (Intent) และดึงพารามิเตอร์ที่จำเป็น
หลักการออกแบบ:
  1. SOLID Principles: แยกส่วน Loading, Matching, Parsing ออกจากกัน
  2. Security: ไม่ใช้ eval/exec, ใช้ Regex และ Decimal สำหรับการประมวลผล
  3. Robustness: ตรวจสอบ Input ทุกจุด, Logging ละเอียด, Handle Exception อย่างชัดเจน
  4. Extensibility: เพิ่ม Intent ใหม่ผ่าน JSON เท่านั้น ไม่ต้องแก้ Code
"""

import json
import re
import logging
import math
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from decimal import Decimal, InvalidOperation
from dataclasses import dataclass, field

# ตั้งค่า Logging สำหรับ Production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Sovereign.Perception")

@dataclass
class IntentMatch:
    """Data Class เก็บผลลัพธ์การจับคู่เจตนา"""
    intent_id: str
    category: str
    name: str
    confidence: float
    parameters: Dict[str, Any] = field(default_factory=dict)
    raw_input: str = ""
    error_message: Optional[str] = None

class IntentConfigLoader:
    """
    หน้าที่: โหลดและตรวจสอบความถูกต้องของไฟล์ Configuration (JSON)
    หลักการ: Single Responsibility Principle
    """
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        if not self.config_path.exists():
            logger.error(f"Configuration file not found: {self.config_path}")
            raise FileNotFoundError(f"Intent taxonomy file missing: {self.config_path}")

    def load_taxonomy(self) -> List[Dict[str, Any]]:
        """โหลดรายการ Intent จาก JSON พร้อมตรวจสอบโครงสร้าง"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            intents = data.get('intents', [])
            if not isinstance(intents, list):
                raise ValueError("Invalid structure: 'intents' must be a list")
            
            logger.info(f"Successfully loaded {len(intents)} intents from {self.config_path}")
            return intents
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in {self.config_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading config: {e}")
            raise

class ParameterParser:
    """
    หน้าที่: ดึงค่าพารามิเตอร์จากข้อความโดยใช้ Regex และ Logic ทางคณิตศาสตร์
    หลักการ: แยก Logic การ Parse ออกจาก Logic การ Match
    """
    
    @staticmethod
    def extract_math_operands(text: str) -> Optional[Dict[str, Any]]:
        """
        ดึงตัวเลขและเครื่องหมายทางคณิตศาสตร์จากข้อความ
        รองรับทั้งไทยและอังกฤษ และทศนิยม รวมถึงจำนวนลบ
        """
        # Pattern: เลข (อาจมีทศนิยม, อาจเป็นลบ) + ช่องว่าง(หรือไม่) + เครื่องหมาย + ช่องว่าง(หรือไม่) + เลข
        pattern = r"(-?\d+\.?\d*)\s*([\+\-\*\/x÷])\s*(-?\d+\.?\d*)"
        match = re.search(pattern, text)
        
        if match:
            try:
                op1_str, operator, op2_str = match.groups()
                
                # แปลงเป็น Decimal เพื่อความแม่นยำสูงสุด (ป้องกัน Floating Point Error)
                op1 = Decimal(op1_str)
                op2 = Decimal(op2_str)
                
                # ปรับปรุงเครื่องหมายให้เป็นมาตรฐาน
                op_map = {'x': '*', '÷': '/'}
                safe_operator = op_map.get(operator, operator)
                
                return {
                    "operand_1": float(op1),
                    "operand_2": float(op2),
                    "operator": safe_operator,
                    "raw_operand_1": str(op1),
                    "raw_operand_2": str(op2)
                }
            except (InvalidOperation, ValueError) as e:
                logger.warning(f"Failed to parse math operands: {e}")
                return None
        
        # Fallback: ลองหาเฉพาะตัวเลขเดี่ยวๆ ในกรณีที่มีรูปแบบพิเศษ
        # เช่น "999999999.99 + 0.01" ที่อาจมีปัญหาเรื่อง spacing
        fallback_pattern = r"(-?\d+\.?\d*)\s*([\+\-\*\/])\s*(-?\d+\.?\d*)"
        match_fb = re.search(fallback_pattern, text.replace(' ', ''))
        if match_fb:
            try:
                op1_str, operator, op2_str = match_fb.groups()
                op1 = Decimal(op1_str)
                op2 = Decimal(op2_str)
                op_map = {'x': '*', '÷': '/'}
                safe_operator = op_map.get(operator, operator)
                return {
                    "operand_1": float(op1),
                    "operand_2": float(op2),
                    "operator": safe_operator,
                    "raw_operand_1": str(op1),
                    "raw_operand_2": str(op2)
                }
            except (InvalidOperation, ValueError):
                pass
                
        return None

    @staticmethod
    def extract_amount(text: str) -> Optional[Dict[str, Any]]:
        """ดึงจำนวนเงินจากข้อความ"""
        pattern = r"(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:บาท|baht|฿)"
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                amount = float(amount_str)
                return {"amount": amount, "currency": "THB"}
            except ValueError:
                return None
        
        # กรณีไม่มีคำว่าบาท แต่เป็นบริบทเรื่องเงิน (Fallback แบบง่าย)
        pattern_fallback = r"ราคา\s*(\d+)"
        match_fb = re.search(pattern_fallback, text)
        if match_fb:
            return {"amount": float(match_fb.group(1)), "currency": "THB"}
            
        return None

    def parse_parameters(self, intent_id: str, text: str) -> Dict[str, Any]:
        """Router เลือกฟังก์ชัน Parser ตามประเภทของ Intent"""
        params = {}
        
        if "MATH" in intent_id:
            math_params = self.extract_math_operands(text)
            if math_params:
                params.update(math_params)
            else:
                logger.warning(f"Math intent detected but no operands found in: {text}")
                
        elif "PAYMENT" in intent_id or "FINANCE" in intent_id:
            money_params = self.extract_amount(text)
            if money_params:
                params.update(money_params)
        
        elif "KNOWLEDGE" in intent_id or "FACTUAL" in intent_id:
            # สำหรับคำถามความรู้ทั่วไป ให้ส่งข้อความเดิมเป็น query
            params["query"] = text
            
        return params

class PerceptionEngine:
    """
    Facade หลักสำหรับระบบรับรู้ (Perception)
    รับผิดชอบประสานงานระหว่าง Loader, Matcher และ Parser
    """
    
    def __init__(self, config_path: str = "sovereign/config/intent_taxonomy.json"):
        try:
            self.loader = IntentConfigLoader(config_path)
            self.intents = self.loader.load_taxonomy()
            self.parser = ParameterParser()
            logger.info("PerceptionEngine initialized successfully.")
        except Exception as e:
            logger.critical(f"Failed to initialize PerceptionEngine: {e}")
            raise

    def _calculate_confidence(self, text: str, patterns: List[str]) -> Tuple[float, Optional[str]]:
        """
        คำนวณความมั่นใจ (Confidence Score) จากการจับคู่ Pattern
        Returns: (score, matched_pattern)
        """
        # Pre-process: ลบ noise characters (!, ?, @, #, $, etc.) จากข้อความก่อนวิเคราะห์
        # แต่ต้องเก็บเครื่องหมายทางคณิตศาสตร์ไว้: + - * / . และตัวเลข
        clean_text = re.sub(r'[^0-9\w\s\u0E00-\u0E7F\+\-\*\/\.]', '', text).lower()
        
        best_score = 0.0
        best_pattern = None
        
        for pattern in patterns:
            try:
                # เช็คว่าเป็น Regex จริงๆ หรือเป็นแค่คำที่มี character พิเศษ
                # Regex ต้องมีโครงสร้างที่ชัดเจน เช่น มี [.]*+?[]() ในบริบทที่เหมาะสม
                is_regex = self._is_valid_regex_pattern(pattern)
                
                if is_regex:
                    # เป็น Regex
                    if re.search(pattern, clean_text):
                        score = 0.95
                        if score > best_score:
                            best_score = score
                            best_pattern = pattern
                else:
                    # เป็นคำค้นหาธรรมดา (Keyword Matching)
                    if pattern in clean_text:
                        # ปรับปรุงการคำนวณ score: ให้คะแนนสูงสำหรับสัญลักษณ์ทางคณิตศาสตร์
                        # แต่ต้องตรวจสอบบริบทด้วยว่าเป็น mathematical expression จริงๆ
                        if pattern in ['+', '-', '*', '/', '=']:
                            # ตรวจสอบว่ามีตัวเลขอยู่รอบๆ เครื่องหมายหรือไม่
                            # Pattern: เลข + เครื่องหมาย + เลข
                            math_pattern = r'\d\s*[' + re.escape(pattern) + r']\s*\d'
                            if re.search(math_pattern, clean_text):
                                score = 0.75  # คะแนนสูงสำหรับ math operators ที่มีตัวเลขประกอบ
                            else:
                                score = 0.2  # คะแนนต่ำถ้าไม่มีตัวเลขประกอบ (อาจเป็น security threat)
                        else:
                            score = len(pattern) / len(clean_text) if len(clean_text) > 0 else 0
                            score = min(score, 0.85)
                        
                        if score > best_score:
                            best_score = score
                            best_pattern = pattern
            except re.error as e:
                logger.error(f"Invalid regex pattern '{pattern}': {e}")
                continue
                
        return best_score, best_pattern
    
    def _is_valid_regex_pattern(self, pattern: str) -> bool:
        """
        ตรวจสอบว่า pattern เป็น regex ที่ถูกต้องหรือไม่
        โดยตรวจสอบว่ามีโครงสร้าง regex ที่ชัดเจน (เช่น [...], (...), {n}, ^, $)
        ไม่ใช่แค่มี character เดียวเช่น + หรือ *
        """
        # ถ้า pattern สั้นมาก (1-3 ตัวอักษร) ให้ถือว่าเป็น keyword
        if len(pattern) <= 3:
            return False
        
        # Regex ที่มีโครงสร้างชัดเจน
        has_brackets = '[' in pattern or ']' in pattern
        has_parens = '(' in pattern or ')' in pattern
        has_quantifier_braces = '{' in pattern or '}' in pattern
        has_anchors = pattern.startswith('^') or pattern.endswith('$')
        has_dot_star = '.*' in pattern or '.+' in pattern
        
        return has_brackets or has_parens or has_quantifier_braces or has_anchors or has_dot_star

    def analyze(self, user_input: str) -> IntentMatch:
        """
        ฟังก์ชันหลักในการวิเคราะห์ข้อความ
        Input Validation & Error Handling แบบเข้มงวด
        """
        if not user_input or not isinstance(user_input, str):
            logger.warning("Received invalid input (empty or non-string).")
            return IntentMatch(
                intent_id="UNKNOWN",
                category="SYSTEM",
                name="Invalid Input",
                confidence=0.0,
                error_message="Input must be a non-empty string.",
                raw_input=str(user_input)
            )
        
        clean_input = user_input.strip()
        if len(clean_input) == 0:
            return IntentMatch(
                intent_id="UNKNOWN",
                category="SYSTEM",
                name="Empty Input",
                confidence=0.0,
                error_message="Input string is empty after trimming.",
                raw_input=user_input
            )

        logger.debug(f"Analyzing input: '{clean_input}'")

        best_match: Optional[IntentMatch] = None
        highest_confidence = 0.0

        try:
            for intent_def in self.intents:
                patterns = intent_def.get("patterns", [])
                score, matched_pat = self._calculate_confidence(clean_input, patterns)
                
                if score > highest_confidence and score > 0.3:
                    highest_confidence = score
                    params = self.parser.parse_parameters(intent_def['id'], clean_input)
                    
                    best_match = IntentMatch(
                        intent_id=intent_def['id'],
                        category=intent_def['category'],
                        name=intent_def['name'],
                        confidence=score,
                        parameters=params,
                        raw_input=clean_input
                    )
            
            if best_match is None:
                logger.info(f"No confident intent found for: '{clean_input}'. Defaulting to UNKNOWN.")
                return IntentMatch(
                    intent_id="UNKNOWN",
                    category="GENERAL",
                    name="Unrecognized Intent",
                    confidence=0.0,
                    parameters={"original_text": clean_input},
                    raw_input=clean_input
                )
                
            return best_match

        except Exception as e:
            logger.error(f"Critical error during analysis: {e}", exc_info=True)
            return IntentMatch(
                intent_id="ERROR",
                category="SYSTEM",
                name="Analysis Failure",
                confidence=0.0,
                error_message=str(e),
                raw_input=clean_input
            )

if __name__ == "__main__":
    import sys
    import os
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(base_dir, "..", "config", "intent_taxonomy.json")
    
    if not os.path.exists(config_file):
        config_file = "sovereign/config/intent_taxonomy.json"

    try:
        engine = PerceptionEngine(config_path=config_file)
        
        test_cases = [
            "9.8-9.11 ได้เท่าไรหรอ",
            "แม่บอกฉันให้ไปซื้อของราคา 19 บาท ฉันต้องเตรียมเหรียญหรือแบงค์อะไร",
            "สวัสดีครับ",
            "ช่วยหน่อยทำไงดี",
            "คำนวณ 100 * 5"
        ]
        
        print(f"{'Input':<40} | {'Intent':<25} | {'Conf':<5} | {'Params'}")
        print("-" * 90)
        
        for text in test_cases:
            result = engine.analyze(text)
            params_str = json.dumps(result.parameters, ensure_ascii=False)
            print(f"{text:<40} | {result.intent_id:<25} | {result.confidence:.2f} | {params_str}")
            
    except Exception as e:
        print(f"System Startup Failed: {e}")
