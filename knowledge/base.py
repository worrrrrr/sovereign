"""
Knowledge Base Module
จัดการฐานความรู้แบบ Deterministic (Rule-based & Pattern-based)
"""

from typing import Dict, List, Optional, Any, Tuple
import re

class KnowledgeEntry:
    """โครงสร้างข้อมูลความรู้หนึ่งชิ้น"""
    def __init__(self, 
                 key: str, 
                 value: Any, 
                 patterns: List[str] = None,
                 category: str = "general",
                 confidence_threshold: float = 0.8):
        self.key = key
        self.value = value
        self.patterns = patterns or [key]
        self.category = category
        self.confidence_threshold = confidence_threshold

class KnowledgeBase:
    """ฐานความรู้แบบ Rule-based"""
    
    def __init__(self):
        # เก็บความรู้ในรูปแบบ Dictionary
        self.entries: Dict[str, KnowledgeEntry] = {}
        self.category_index: Dict[str, List[str]] = {}
        
        # โหลดความรู้เริ่มต้น
        self._load_default_knowledge()
    
    def _load_default_knowledge(self):
        """โหลดความรู้พื้นฐานของระบบ"""
        
        # 1. ความรู้ทั่วไป (General Info)
        self.add_entry(KnowledgeEntry(
            key="system_name",
            value="Sovereign AI",
            patterns=["ชื่ออะไร", "คือใคร", "ชื่อระบบ", "คุณชื่ออะไร"],
            category="general"
        ))
        
        self.add_entry(KnowledgeEntry(
            key="system_capability",
            value="ฉันเป็นระบบ AI แบบ Deterministic ที่ทำงานด้วยกฎและเครื่องมือ ไม่ใช้ LLM",
            patterns=["ทำอะไรได้บ้าง", "ความสามารถ", "ช่วยอะไรได้", "เก่งอะไร"],
            category="general"
        ))
        
        # 2. ความรู้ด้านคณิตศาสตร์ (Math Rules)
        self.add_entry(KnowledgeEntry(
            key="math_addition_rule",
            value="rule:addition",
            patterns=["บวก", "ผลบวก", "รวมกัน"],
            category="math"
        ))
        
        self.add_entry(KnowledgeEntry(
            key="math_subtraction_rule",
            value="rule:subtraction",
            patterns=["ลบ", "ผลต่าง", "น้อยกว่า"],
            category="math"
        ))
        
        # 3. ความรู้เฉพาะโดเมน (Domain Specific)
        self.add_entry(KnowledgeEntry(
            key="thai_currency_units",
            value={"บาท": 1, "สตางค์": 0.01, "พัน": 1000, "หมื่น": 10000},
            patterns=["หน่วยเงิน", "เงินไทย", "สกุลเงิน"],
            category="finance"
        ))
        
        # 4. คำตอบสำหรับคำถามที่พบบ่อย (FAQ)
        self.add_entry(KnowledgeEntry(
            key="faq_how_to_use",
            value="พิมพ์คำสั่งหรือคำถามลงมา ระบบจะวิเคราะห์และดำเนินการให้โดยอัตโนมัติ",
            patterns=["ใช้อย่างไร", "วิธีใช้", "เริ่มต้นยังไง"],
            category="faq"
        ))
        
        self.add_entry(KnowledgeEntry(
            key="faq_accuracy",
            value="ระบบทำงานด้วยกฎที่กำหนดไว้ จึงให้ผลลัพธ์ที่แน่นอนและไม่มั่วข้อมูล",
            patterns=["แม่นยำไหม", "เชื่อถือได้ไหม", "ผิดหรือเปล่า"],
            category="faq"
        ))

    def add_entry(self, entry: KnowledgeEntry):
        """เพิ่มความรู้ใหม่"""
        self.entries[entry.key] = entry
        
        # สร้าง Index ตาม Category
        if entry.category not in self.category_index:
            self.category_index[entry.category] = []
        self.category_index[entry.category].append(entry.key)
    
    def query(self, text: str, intent: str = None) -> Tuple[Optional[Any], float, str]:
        """
        ค้นหาความรู้จากข้อความ
        Returns: (result, confidence_score, source_key)
        """
        text_lower = text.lower().strip()
        best_match = None
        best_score = 0.0
        best_key = None
        
        # 1. Exact Match (จับคู่คำตรงๆ)
        for key, entry in self.entries.items():
            if key.lower() in text_lower or text_lower in key.lower():
                score = 1.0
                if score > best_score:
                    best_score = score
                    best_match = entry.value
                    best_key = key
        
        # 2. Pattern Match (จับคู่ด้วย Pattern)
        if best_score < 0.9:  # ถ้ายังไม่เจอคำตอบที่ดีพอ
            for key, entry in self.entries.items():
                for pattern in entry.patterns:
                    # ตรวจสอบว่า pattern อยู่ในข้อความหรือไม่
                    if pattern.lower() in text_lower:
                        # คำนวณคะแนนจากความยาวของ pattern ที่ตรง
                        score = len(pattern) / max(len(text_lower), len(pattern))
                        score = min(score * 1.2, 0.95)  # Boost แต่ไม่เกิน 0.95
                        
                        if score > best_score:
                            best_score = score
                            best_match = entry.value
                            best_key = key
        
        # 3. Regex Pattern สำหรับคำถามเฉพาะ
        if best_score < 0.8:
            best_match, best_score, best_key = self._regex_query(text_lower)
        
        # ตรวจสอบ Threshold
        if best_match is not None and best_score >= 0.5:
            return best_match, best_score, best_key or "unknown"
        
        return None, 0.0, "not_found"
    
    def _regex_query(self, text: str) -> Tuple[Optional[Any], float, str]:
        """ค้นหาด้วย Regex Patterns เฉพาะ"""
        
        # Pattern: ถามชื่อ
        if re.search(r'(ชื่อ|นาม).*(อะไร|ใด|ไหน)', text):
            return self.entries.get("system_name").value, 0.95, "system_name"
        
        # Pattern: ถามความสามารถ
        if re.search(r'(ทำ|ช่วย|สามารถ).*(ได้|ไหม|ยังไง|อย่างไร)', text):
            return self.entries.get("system_capability").value, 0.9, "system_capability"
        
        # Pattern: วิธีใช้
        if re.search(r'(ใช้|เริ่ม|วิธี).*(ไง|อย่างไร|แบบไหน)', text):
            return self.entries.get("faq_how_to_use").value, 0.85, "faq_how_to_use"
        
        return None, 0.0, "not_found"
    
    def get_category(self, category: str) -> List[KnowledgeEntry]:
        """ดึงความรู้ทั้งหมดในหมวดหมู่"""
        keys = self.category_index.get(category, [])
        return [self.entries[key] for key in keys if key in self.entries]
    
    def list_categories(self) -> List[str]:
        """แสดงหมวดหมู่ทั้งหมด"""
        return list(self.category_index.keys())

# ทดสอบ
if __name__ == "__main__":
    kb = KnowledgeBase()
    
    test_queries = [
        "คุณชื่ออะไร",
        "ทำอะไรได้บ้าง",
        "ใช้อย่างไร",
        "ระบบแม่นยำไหม",
        "อยากรู้เรื่องเงินไทย",
        "บวกลบเลขทำยังไง",
        "สวัสดีครับ",  # ไม่ควรมีคำตอบจาก KB
    ]
    
    print("="*70)
    print(f"{'คำถาม':30} | {'คำตอบ':25} | {'Confidence':10}")
    print("="*70)
    
    for q in test_queries:
        result, confidence, source = kb.query(q)
        result_str = str(result)[:25] + "..." if result and len(str(result)) > 25 else str(result)
        print(f"{q:30} | {result_str:25} | {confidence:.2f}")
