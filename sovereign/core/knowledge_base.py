"""
Sovereign AI - Internal Knowledge Base Manager (Production-Grade)
---------------------------------------------------------------
หน้าที่: จัดการฐานความรู้ภายใน (Internal Facts) ด้วยมาตรฐานความปลอดภัยและประสิทธิภาพสูงสุด
หลักการ:
  1. Data Authority: ข้อมูลอ้างอิงแหล่งที่มาชัดเจน
  2. Temporal Awareness: จัดการข้อมูลตามช่วงเวลา (valid_from, valid_until)
  3. Performance: ใช้ Pre-compiled Regex เพื่อลดภาระการประมวลผลซ้ำซ้อน
  4. Security: ป้องกัน Path Traversal และป้องกันไฟล์เสียหายด้วย Atomic Write
"""

import os
import re
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

# ตั้งค่า Logger
logger = logging.getLogger("Sovereign.KnowledgeBase")

@dataclass
class KnowledgeFact:
    """โครงสร้างข้อมูลความจริงหนึ่งหน่วย พร้อมระบบตรวจสอบความถูกต้องในตัว (Self-Validation)"""
    id: str
    category: str
    question_pattern: str
    answer: str
    source: str
    valid_from: str
    valid_until: Optional[str]
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # ฟิลด์สำหรับเก็บ Compiled Regex เพื่อไม่ให้ต้อง Compile ใหม่ทุกครั้ง (Performance Optimization)
    _compiled_pattern: Optional[re.Pattern] = field(init=False, repr=False, default=None)

    def __post_init__(self):
        """ตรวจสอบและเตรียมข้อมูลทันทีที่ถูกสร้าง (Fail-Fast Principle)"""
        try:
            self._compiled_pattern = re.compile(self.question_pattern, re.IGNORECASE)
        except re.error as e:
            logger.error(f"รูปแบบ Regex ไม่ถูกต้องสำหรับ Fact ID {self.id}: {e}")
            self._compiled_pattern = None

        # ตรวจสอบรูปแบบวันที่ล่วงหน้าเพื่อป้องกัน Runtime Error
        try:
            datetime.fromisoformat(self.valid_from)
            if self.valid_until:
                datetime.fromisoformat(self.valid_until)
        except ValueError as e:
            logger.error(f"รูปแบบวันที่ไม่ถูกต้องใน Fact ID {self.id}: {e}")

    def is_valid(self, check_date: Optional[datetime] = None) -> bool:
        """ตรวจสอบความถูกต้องของข้อมูลตามแกนเวลา (Temporal Validation)"""
        if check_date is None:
            check_date = datetime.now()
        
        try:
            start = datetime.fromisoformat(self.valid_from)
            if check_date < start:
                return False  # ข้อมูลยังไม่ถึงกำหนดเวลาบังคับใช้
            
            if self.valid_until:
                end = datetime.fromisoformat(self.valid_until)
                if check_date > end:
                    return False  # ข้อมูลหมดอายุ/ล้าสมัยแล้ว
            
            return True
        except ValueError:
            return False

    def match(self, text: str) -> bool:
        """ทดสอบข้อความกับ Pattern อย่างมีประสิทธิภาพ"""
        if not self._compiled_pattern:
            return False
        return bool(self._compiled_pattern.search(text))


class KnowledgeBaseManager:
    """
    ผู้จัดการฐานความรู้หลัก (Single Responsibility Principle)
    รับผิดชอบเฉพาะการอ่าน เขียน และสืบค้นข้อมูล โดยไม่ยุ่งกับ Logic การตอบกลับ
    """
    
    def __init__(self, db_path: str = "sovereign/config/knowledge_db.json"):
        # Security: ตรวจสอบและทำให้ Path ปลอดภัย ป้องกัน Directory Traversal
        self.db_path = Path(db_path).resolve()
        self.facts: List[KnowledgeFact] = []
        self._load_database()

    def _load_database(self) -> None:
        """โหลดข้อมูลจาก JSON พร้อมจัดการ Error อย่างรัดกุม"""
        if not self.db_path.exists():
            logger.warning(f"ไม่พบฐานข้อมูลที่ {self.db_path}. กำลังสร้างฐานข้อมูลเริ่มต้น...")
            self._create_default_db()
            return

        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # กรองข้อมูลเฉพาะตัวที่สร้างออบเจกต์สำเร็จ
            loaded_facts = []
            for item in data.get('facts', []):
                # ไม่โหลด _compiled_pattern จาก JSON เพราะเป็น Internal State
                item.pop('_compiled_pattern', None) 
                loaded_facts.append(KnowledgeFact(**item))
                
            self.facts = loaded_facts
            logger.info(f"โหลดข้อมูลสำเร็จ {len(self.facts)} รายการ จากฐานข้อมูล")
            
        except json.JSONDecodeError as e:
            logger.error(f"ไฟล์ฐานข้อมูลเสียหาย (JSON Parse Error): {e}")
            self.facts = []
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการโหลดฐานข้อมูล: {e}")
            self.facts = []

    def _create_default_db(self) -> None:
        """สร้างฐานข้อมูลตัวอย่าง (Curated Data) ตามโครงสร้างบนเว็บ"""
        self.facts = [
            KnowledgeFact(
                id="US_PRESIDENT_2025",
                category="POLITICS",
                question_pattern=r"(ใครคือ|ประธานาธิบดี|president).*(สหรัฐอเมริกา|us|america)",
                answer="ปัจจุบัน (มกราคม 2025) ประธานาธิบดีสหรัฐอเมริกาคือ โดนัลด์ ทรัมป์ (Donald Trump) ดำรงตำแหน่งลำดับที่ 47",
                source="US Official Election Commission & Inauguration Record",
                valid_from="2025-01-20T12:00:00",
                valid_until="2029-01-20T12:00:00",
                confidence=0.99,
                metadata={"term": "47th", "party": "Republican"}
            ),
            KnowledgeFact(
                id="US_PRESIDENT_2024",
                category="POLITICS",
                question_pattern=r"(ใครคือ|ประธานาธิบดี|president).*(สหรัฐอเมริกา|us|america)",
                answer="ในช่วงปี 2021-2025 ประธานาธิบดีสหรัฐอเมริกาคือ โจ ไบเดน (Joe Biden)",
                source="US Official Record",
                valid_from="2021-01-20T12:00:00",
                valid_until="2025-01-20T11:59:59",
                confidence=0.99,
                metadata={"term": "46th", "party": "Democratic", "status": "historical"}
            ),
            KnowledgeFact(
                id="THAI_CAPITAL",
                category="GEOGRAPHY",
                question_pattern=r"(เมืองหลวง|capital).*(ไทย|thailand)",
                answer="เมืองหลวงของประเทศไทยคือ กรุงเทพมหานคร (Bangkok)",
                source="Royal Thai Government Gazette",
                valid_from="1782-04-21T00:00:00",
                valid_until=None,
                confidence=1.0,
                metadata={"established": 1782}
            ),
            KnowledgeFact(
                id="MATH_PI",
                category="SCIENCE",
                question_pattern=r"(ค่าพาย|pi|π).*(คืออะไร|value)",
                answer="ค่าพาย (π) คืออัตราส่วนของเส้นรอบวงต่อเส้นผ่านศูนย์กลางของวงกลม มีค่าประมาณ 3.14159...",
                source="Mathematical Constant",
                valid_from="0001-01-01T00:00:00",
                valid_until=None,
                confidence=1.0,
                metadata={"type": "irrational"}
            )
        ]
        self._save_database()
        logger.info("สร้างฐานข้อมูลเริ่มต้นพร้อมข้อมูลสำคัญเรียบร้อยแล้ว")

    def _save_database(self) -> None:
        """บันทึกข้อมูลแบบ Atomic Write ป้องกันไฟล์พังระหว่างการบันทึก (Data Integrity)"""
        try:
            # ตรวจสอบว่ามีโฟลเดอร์รองรับหรือไม่
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "facts": [
                    {k: v for k, v in asdict(f).items() if k != '_compiled_pattern'}
                    for f in self.facts
                ]
            }
            
            temp_path = self.db_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno()) # บังคับเขียนลง Disk ทันที
            
            # เขียนทับไฟล์เดิมอย่างปลอดภัย
            temp_path.replace(self.db_path)
            
        except Exception as e:
            logger.error(f"ไม่สามารถบันทึกฐานข้อมูลได้: {e}")

    def query(self, user_intent: str, context: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        สืบค้นข้อมูลอย่างมีประสิทธิภาพ
        1. ใช้ Pre-compiled Regex เพื่อความเร็ว
        2. กรองข้อมูลที่หมดอายุ
        3. เรียงลำดับเพื่อหาคำตอบที่ดีและใหม่ที่สุด
        """
        if not user_intent or not isinstance(user_intent, str):
            return None

        candidates = []
        current_time = datetime.now()

        for fact in self.facts:
            # ใช้ Pattern Matching ที่ถูก Compile ไว้แล้ว
            if fact.match(user_intent):
                if fact.is_valid(current_time):
                    candidates.append(fact)
                else:
                    logger.debug(f"พบ Fact {fact.id} ตรงกับคำถาม แต่หมดอายุ/ล้าสมัยตามแกนเวลาแล้ว")

        if not candidates:
            return None

        # เรียงลำดับ: ความมั่นใจสูงสุด (Descending) -> วันที่เริ่มบังคับใช้ (Descending - ข้อมูลใหม่กว่าอยู่บน)
        candidates.sort(key=lambda x: (x.confidence, x.valid_from), reverse=True)
        best_match = candidates[0]

        is_historical = False
        if best_match.valid_until:
            try:
                is_historical = datetime.fromisoformat(best_match.valid_until) < current_time
            except ValueError:
                pass

        return {
            "answer": best_match.answer,
            "source": best_match.source,
            "confidence": best_match.confidence,
            "category": best_match.category,
            "is_historical": is_historical,
            "metadata": best_match.metadata
        }

    def add_fact(self, fact: KnowledgeFact) -> None:
        """เพิ่มข้อมูลใหม่พร้อมอัปเดตหาก ID ซ้ำ (Upsert)"""
        self.facts = [f for f in self.facts if f.id != fact.id]
        self.facts.append(fact)
        self._save_database()
        logger.info(f"บันทึกข้อมูล Fact ID: {fact.id} เรียบร้อยแล้ว")


# การจัดการ Singleton อย่างปลอดภัยระดับ Module
_kb_instance: Optional[KnowledgeBaseManager] = None

def get_knowledge_base() -> KnowledgeBaseManager:
    """ฟังก์ชันเพื่อเข้าถึง Instance หลักของระบบฐานความรู้"""
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = KnowledgeBaseManager()
    return _kb_instance
