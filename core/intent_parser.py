"""
Intent Parser: วิเคราะห์ Input แยกแยะว่าเป็น 'คำสั่ง', 'คำถาม', หรือ 'โจทย์คณิตศาสตร์/ตรรกะ'
และดึงข้อมูลสำคัญ (Entities) ออกมาเพื่อส่งต่อให้ Engine ที่เหมาะสม

รองรับ Intent 20 ประเภท และ Core Actions 10 แบบ สำหรับภาษาไทย
"""
import re
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum

# ------------------------------------------------------------
# 1. Intent types (20 แบบ) - จากแนวทางที่ผู้ใช้กำหนด
# ------------------------------------------------------------
class IntentType(Enum):
    # Math & Logic (เดิม)
    CALCULATION = "calculation"
    SOLVE_EQUATION = "solve_equation"
    SOLVE_CONSTRAINT = "solve_constraint"
    SOLVE_FUNCTIONAL = "solve_functional"
    
    # General Communication (20 intents + Noise/Testing + Complex Cases)
    GREETING = "greeting"                    # ทักทาย
    ASK_INFO = "ask_info"                    # ถามข้อมูล
    ANSWER = "answer"                        # ตอบข้อมูล
    COMMAND = "command"                      # สั่งทำ
    REQUEST_HELP = "request_help"            # ขอร้อง/ขอความช่วยเหลือ
    REJECT = "reject"                        # ปฏิเสธ
    ACKNOWLEDGE = "acknowledge"              # ยืนยัน/รับทราบ
    THANK = "thank"                          # ขอบคุณ
    APOLOGIZE = "apologize"                  # ขอโทษ
    EXPRESS_FEELING = "express_feeling"      # แสดงความรู้สึก
    LAUGH = "laugh"                          # หัวเราะ/ขำ
    FAREWELL = "farewell"                    # อำลา
    ADVISE = "advise"                        # แนะนำ
    WARN = "warn"                            # เตือน/ห้าม
    INVITE = "invite"                        # ชักชวน
    ASK_OPINION = "ask_opinion"              # ถามความคิดเห็น
    EXPRESS_OPINION = "express_opinion"      # แสดงความคิดเห็น
    PROMISE = "promise"                      # ให้สัญญา
    ASK_PERMISSION = "ask_permission"        # ขออนุญาต/อนุญาต
    EXPLAIN = "explain"                      # อธิบาย/บอกเล่า
    TEST_NOISE = "test_noise"                # Noise / พิมพ์ผิด / ทดสอบระบบ
    
    # --- เพิ่มใหม่สำหรับกรณีซับซ้อน ---
    VENT_COMPLAIN = "vent_complain"          # บ่น/ระบาย
    EXPRESS_CONFUSION = "express_confusion"  # แสดงความสับสน
    HYPOTHETICAL = "hypothetical"            # สมมติฐาน/เงื่อนไข
    ASK_COMPARISON = "ask_comparison"        # ถามการเปรียบเทียบ
    SARCASM_PASSIVE = "sarcasm_passive"      # ประชด/ตัดพ้อ
    
    # Search & Web
    SEARCH_WEB = "search_web"
    
    # Entertainment
    TELL_JOKE = "tell_joke"              # เล่ามุกตลก
    
    UNKNOWN = "unknown"

# ------------------------------------------------------------
# 2. Core Actions (10 แบบ สำหรับ Intent.COMMAND)
# ------------------------------------------------------------
class CoreAction(Enum):
    OPEN = "เปิด"                   # เปิดไฟ, เปิดแอพ, เปิดเพลง
    CLOSE = "ปิด"                  # ปิดประตู, ปิดโปรแกรม
    ADD_CREATE = "เพิ่ม/สร้าง"      # สร้างโฟลเดอร์, เพิ่มรายชื่อ
    DELETE_CANCEL = "ลบ/ยกเลิก"     # ลบไฟล์, ยกเลิกคำสั่ง
    EDIT_CHANGE = "แก้ไข/เปลี่ยนแปลง" # เปลี่ยนชื่อ, ปรับความสว่าง
    SEARCH_CHECK = "ค้นหา/ตรวจสอบ"  # หาไฟล์, ตรวจสอบสถานะ
    SEND_TRANSFER = "ส่ง/ถ่ายโอน"    # ส่งไลน์, อัปโหลดรูป
    SAVE_STORE = "บันทึก/จัดเก็บ"    # บันทึกเอกสาร, ดาวน์โหลด
    START_STOP = "เริ่ม/หยุด"        # เริ่มงาน, หยุดนาฬิกา, เล่นวีดีโอ
    PROCESS_ANALYZE = "ประมวลผล/วิเคราะห์" # คำนวณ, วิเคราะห์ยอดขาย, สรุป

@dataclass
class ParsedIntent:
    intent_type: IntentType
    original_input: str
    action: str
    entities: List[Any]
    params: Dict[str, Any]  # พารามิเตอร์เฉพาะสำหรับแต่ละ Intent (เช่น สมการ, ตัวแปร)
    context: str
    confidence: float
    reasoning: str
    core_action: Optional[CoreAction] = None  # สำหรับ Intent.COMMAND

class IntentParser:
    def __init__(self):
        # Patterns สำหรับตรวจจับการคำนวณพื้นฐาน
        self.calc_patterns = [
            r"(\d+\.?\d*)\s*[-+*/]\s*(\d+\.?\d*)",
        ]
        
        # Keywords สำหรับประเภทโจทย์
        self.math_keywords = ["แก้สมการ", "หาค่า", "find x", "solve", "calculate"]
        self.constraint_keywords = ["จำนวนเต็ม", "integer", "ตรรกะ", "logic", "เงื่อนไข", "condition", "divisible", "หารลงตัว"]
        self.functional_keywords = ["f(x)", "f(y)", "functional", "ฟังก์ชัน", "สมการเชิงฟังก์ชัน"]
        self.search_keywords = ["ค้นหา", "search", "google", "ข่าว", "อากาศ", "weather", "news"]
        
        # Thai math operation keywords (สำหรับตรวจจับการคำนวณภาษาไทย)
        self.thai_math_ops = {
            "ผลบวก": "+",
            "บวก": "+",
            "ผลลบ": "-",
            "ลบ": "-",
            "ผลต่าง": "-",
            "ต่าง": "-",  # เพิ่ม "ต่าง" เฉยๆ ด้วย (สำหรับ "หาผลต่าง")
            "ผลคูณ": "*",
            "คูณ": "*",
            "ผลหาร": "/",
            "หาร": "/",
        }
        
        # ----------------------------------------------------
        # Helper: Mapping คำกริยาไทย -> CoreAction
        # ----------------------------------------------------
        self.core_action_mapping = {
            "เปิด": CoreAction.OPEN,
            "ปิด": CoreAction.CLOSE,
            "เพิ่ม": CoreAction.ADD_CREATE,
            "สร้าง": CoreAction.ADD_CREATE,
            "ลบ": CoreAction.DELETE_CANCEL,
            "ยกเลิก": CoreAction.DELETE_CANCEL,
            "แก้ไข": CoreAction.EDIT_CHANGE,
            "เปลี่ยน": CoreAction.EDIT_CHANGE,
            "ปรับ": CoreAction.EDIT_CHANGE,
            "ค้นหา": CoreAction.SEARCH_CHECK,
            # หมายเหตุ: "หา" ในบริบทคณิตศาสตร์จะจัดการแยกต่างหาก (ไม่ใช้ SEARCH_CHECK)
            "ตรวจสอบ": CoreAction.SEARCH_CHECK,
            "ส่ง": CoreAction.SEND_TRANSFER,
            "โอน": CoreAction.SEND_TRANSFER,
            "อัปโหลด": CoreAction.SEND_TRANSFER,
            "บันทึก": CoreAction.SAVE_STORE,
            "เซฟ": CoreAction.SAVE_STORE,
            "ดาวน์โหลด": CoreAction.SAVE_STORE,
            "เริ่ม": CoreAction.START_STOP,
            "หยุด": CoreAction.START_STOP,
            "เล่น": CoreAction.START_STOP,    # เล่น = เริ่มเล่น
            "คำนวณ": CoreAction.PROCESS_ANALYZE,
            "วิเคราะห์": CoreAction.PROCESS_ANALYZE,
            "สรุป": CoreAction.PROCESS_ANALYZE,
            "เปรียบเทียบ": CoreAction.PROCESS_ANALYZE,
            "เรียง": CoreAction.PROCESS_ANALYZE,
            "กรอง": CoreAction.PROCESS_ANALYZE,
            "แปลง": CoreAction.PROCESS_ANALYZE,
        }
        
        # ----------------------------------------------------
        # Patterns สำหรับ Intent ทั้ง 20 ประเภท (ภาษาไทย)
        # ----------------------------------------------------
        self.intent_patterns = {
            IntentType.GREETING: [r'^(สวัสดี|หวัดดี|hello|hi|สวัสดีครับ|สวัสดีคะ|เฮโล)$'],
            IntentType.FAREWELL: [r'(บาย|ลาก่อน|ไปละ|เจอกัน|goodbye|bye|have a nice day|bon voyage|แล้วเจอกัน)'],
            IntentType.THANK: [r'(ขอบคุณ|ขอบใจ|thanks|thank you|ซึ้งใจ|พระคุณ)'],
            IntentType.APOLOGIZE: [r'(ขอโทษ|sorry|โทษที|ผิดไปแล้ว|อภัย)'],
            IntentType.LAUGH: [r'(55+|ฮ่า+|ขำ|haha|lol|อิอิ|555+)'],
            IntentType.ACKNOWLEDGE: [r'^(อือ|อืม|ครับ|ค่ะ|ได้|ok|yes|ใช่|เข้าใจ|รับทราบ)$'],
            IntentType.REJECT: [r'^(ไม่|ไม่ได้|ไม่เอา|ไม่ครับ|ไม่ค่ะ|ไม่อยาก|ปฏิเสธ)$'],
        }
        
        # Keywords สำหรับ Intent ประเภทอื่น ๆ
        self.intent_keywords = {
            IntentType.REQUEST_HELP: ['ช่วย', 'ขอร้อง', 'กรุณา', 'ให้หน่อย', 'โปรด'],
            IntentType.WARN: ['ห้าม', 'อย่า', 'เตือน', 'ระวัง', 'อันตราย'],
            IntentType.ADVISE: ['แนะนำ', 'น่าจะ', 'ควร', ' ought to', 'should'],
            IntentType.INVITE: ['ชวน', 'ไปกัน', 'มา', 'ร่วม', 'ด้วยกัน'],
            IntentType.PROMISE: ['สัญญา', 'จะทำ', 'รับรอง', 'ให้คำมั่น'],
            IntentType.ASK_PERMISSION: ['ขออนุญาต', 'ขอ', 'ได้ไหม', '可否'],
            IntentType.EXPLAIN: ['อธิบาย', 'บอกเล่า', 'เล่าให้ฟัง', 'เรื่อง', 'ที่มาที่ไป'],
            IntentType.EXPRESS_FEELING: ['ดีใจ', 'เสียใจ', 'โกรธ', 'เหงา', 'มีความสุข', 'เศร้า', 'ตื่นเต้น'],
            IntentType.EXPRESS_OPINION: ['คิดว่า', 'เห็นว่า', 'ความเห็น', 'ว่าแต่', 'ชอบ', 'ไม่ชอบ', 'รู้สึก'],
            IntentType.ASK_OPINION: ['คิดเห็นยังไง', 'ว่ายังไง', 'คิดว่าไง', 'เห็นด้วยไหม', 'อย่างไร'],
            # --- เพิ่มใหม่สำหรับกรณีซับซ้อน ---
            IntentType.VENT_COMPLAIN: ['เบื่อ', 'รำคาญ', 'เหนื่อย', 'เซ็ง', 'หงุดหงิด', 'น่าเบื่อ', 'ทำไมต้อง', 'อีกแล้ว', 'บ่น', 'ระบาย', 'ปวดหัว', 'วุ่นวาย', 'ยุ่งยาก'],
            IntentType.EXPRESS_CONFUSION: ['งง', 'สับสน', 'ไม่เข้าใจ', 'หมายความว่าไง', 'ยังไงนะ', 'อะไรนะ', 'เหรอ', 'จริงเหรอ', 'แน่ใจเหรอ', 'แปลก', 'พิลึก'],
            IntentType.HYPOTHETICAL: ['ถ้าเกิด', 'สมมติ', 'ถ้าหาก', 'ในกรณีที่', 'ลองคิดดูว่า', 'จะเกิดอะไรขึ้นถ้า', 'what if', 'suppose'],
            IntentType.ASK_COMPARISON: ['ต่างกันยังไง', 'ต่างกับ', 'เทียบกับ', 'เปรียบเทียบกับ', 'อันไหนดีกว่า', 'เลือกอันไหน', 'ต่างกันไหม', 'เหมือนหรือต่าง'],
            IntentType.SARCASM_PASSIVE: ['ก็เก่งนี่นา', 'ดีมากเลยนะ', 'ฉลาดจัง', 'ทำได้ดีมาก', 'เยี่ยมไปเลย', 'สุดยอด', 'เก่งมาก', 'น่ารักจัง'],
            # Entertainment
            IntentType.TELL_JOKE: ['เล่ามุก', 'เรื่องตลก', ' joke', 'ตลก', 'ฮา', 'ขำขัน', 'เล่าเรื่องตลก', 'เล่าเรื่องฮา', 'ทำให้ขำ', 'make me laugh', 'tell me a joke'],
        }
        
        # คำถาม patterns
        self.question_keywords = ['อะไร', 'อย่างไร', 'ไหม', 'หรือ', 'เท่าไหร่', 'ไหน', 'ใคร', 'เมื่อไหร่', 'ทำไม', 'ยังไง']

    def extract_core_action(self, text: str) -> Optional[CoreAction]:
        """คืน CoreAction อันแรกที่พบในข้อความ"""
        text_lower = text.lower()
        for word, action in self.core_action_mapping.items():
            if word in text_lower:
                return action
        return None

    def classify_general_intent(self, text: str) -> Optional[IntentType]:
        """จำแนก Intent ทั่วไป 20 ประเภท + Noise/Testing"""
        text_lower = text.lower().strip()
        
        # ----------------------------------------------------
        # 0. ตรวจสอบ Noise / พิมพ์ผิด / ทดสอบระบบ (ก่อนเป็นลำดับแรก)
        # ----------------------------------------------------
        
        # 0.1 ข้อความสั้นเกินไปหรือซ้ำๆ (เช่น "...", "55555", "aaaa")
        if len(text_lower) < 2:
            return IntentType.TEST_NOISE
        
        # เช็คการซ้ำกันของตัวอักษร (เช่น "....", "..", "55555", "aaaa") - ซ้ำเกิน 1 ตัว (รวม 2+ ตัว)
        if re.match(r'^(.)\1{1,}$', text_lower):
            # ยกเว้น "555" ที่หมายถึงขำ (ต้องยาวอย่างน้อย 2 ตัวถึงจะเข้า pattern นี้)
            if not re.match(r'^5+$', text_lower):
                return IntentType.TEST_NOISE
            else:
                return IntentType.LAUGH  # 55, 555, 5555, 55555 = ขำ
        
        # 0.2 คำว่า "ทดสอบ", "test", "เช็คระบบ" โดยตรง (ตรวจสอบก่อน patterns อื่นๆ)
        test_keywords = ['ทดสอบ', 'test', 'เช็ค', 'ลองของ', 'test_ready', 'เช็คว่า', 
                         'มีใครอยู่ไหม', 'ได้ยินไหม', 'พร้อมไหม', 'ready', 'check']
        if any(word in text_lower for word in test_keywords):
            return IntentType.TEST_NOISE
        
        # 0.3 ตัวอักษรภาษาอังกฤษมั่วๆ (Keyboard smash) เช่น "asdfg", "zxcv"
        # เฉพาะข้อความที่ยาว 3 ตัวขึ้นไป และไม่ใช่คำที่รู้จัก
        if re.match(r'^[a-z]{3,}$', text_lower):
            # ยกเว้นคำที่รู้จัก (ต้อง check ก่อนเพราะเป็น valid words)
            known_words = ['hi', 'ok', 'yes', 'no', 'lol', 'haha', 'hey', 'bye', 'wow', 'oh', 'ah', 'the', 'and', 'for', 'you', 'are', 'was', 'but', 'not', 'all', 'any', 'can', 'had', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use', 'dad', 'mom', 'cat', 'dog', 'red', 'big', 'small',
                          'thanks', 'thank', 'sorry', 'please', 'help', 'good', 'bad', 'nice', 'cool', 'sure', 'why', 'what', 'when', 'where', 'which', 'whom', 'whose']
            if text_lower not in known_words:
                # เช็คว่าเป็นรูปแบบพิมพ์มั่วหรือไม่
                # วิธี 1: ถ้าไม่มีสระเลย (ยกเว้น 'a' ที่อาจเป็นปุ่มค้าง)
                vowels = set('aeiou')
                vowel_count = sum(1 for c in text_lower if c in vowels)
                
                # วิธี 2: เช็คความหลากหลายของตัวอักษร (ถ้าซ้ำ ๆ กันมากเกินไป)
                unique_ratio = len(set(text_lower)) / len(text_lower)
                
                # วิธี 3: เช็ค consecutive consonants (พยัญชนะติดกันเกิน 2 ตัว)
                consonants = set('bcdfghjklmnpqrstvwxyz')
                consec_consonants = 0
                max_consec = 0
                for c in text_lower:
                    if c in consonants:
                        consec_consonants += 1
                        max_consec = max(max_consec, consec_consonants)
                    else:
                        consec_consonants = 0
                
                # วิธี 4: เช็ค keyboard patterns ที่พบบ่อย (qwer, asdf, zxcv, etc.)
                keyboard_patterns = ['qwer', 'asdf', 'zxcv', 'qazw', 'wsxe', 'edcr', 'rfvt', 'tgby', 'yhnu', 'ujmi', 'ik,.', 'ol;p', 
                                     'qwerty', 'asdfgh', 'zxcvbn', 'poiuy', 'lkjhg', 'mnbvc']
                is_keyboard_pattern = any(pattern in text_lower for pattern in keyboard_patterns)
                
                # ถ้ามีลักษณะอย่างน้อย 1 ใน 4 อย่าง ถือว่าเป็น noise
                # ปรับเกณฑ์: vowel_count==0 หรือ unique_ratio ต่ำ หรือ พยัญชนะติดกัน >= 3 หรือ เป็น keyboard pattern
                if vowel_count == 0 or unique_ratio < 0.5 or max_consec >= 3 or is_keyboard_pattern:
                    return IntentType.TEST_NOISE
        
        # 0.4 Keyboard smash ภาษาไทย (แถวคีย์บอร์ดติดกัน)
        # ต้องเช็คเฉพาะข้อความที่ไม่มีสระหรือคำที่มีความหมายชัดเจน
        thai_keyboard_rows = [
            'ฟหกดเา้ั่ป',  # แถวบน
            'ฤฆฏฎชซญ๋ตทธนบ',  # แถวกลาง
            'ผฝพถุึคตจขช',  # แถวล่าง (ปรับให้ถูกต้อง)
        ]
        for row in thai_keyboard_rows:
            # เช็คว่ามีตัวอักษรจากแถวเดียวกันติดกัน 6 ตัวขึ้นไป (เพิ่มจาก 4 เป็น 6 เพื่อลด false positive)
            pattern = f'[{row}]{{6,}}'
            if re.search(pattern, text_lower):
                return IntentType.TEST_NOISE
        
        # 0.5 ข้อความที่มีแต่ตัวเลขซ้ำๆ (เช่น "1111", "99999") แต่ไม่ใช่ "555" ที่หมายถึงขำ
        if re.match(r'^(\d)\1{3,}$', text_lower) and not re.match(r'^5+$', text_lower):
            return IntentType.TEST_NOISE
        
        # ----------------------------------------------------
        # 1. ตรวจสอบ Patterns ก่อน (สำหรับคำสั้น ๆ ที่ชัดเจน)
        # ใช้ search แทน match เพื่อให้พบคำในทุกตำแหน่ง
        # ----------------------------------------------------
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return intent_type
        
        # ----------------------------------------------------
        # 2. ตรวจสอบคำสั่ง (COMMAND) ที่มี CoreAction ชัดเจน
        # ต้องตรวจสอบก่อน REQUEST_HELP เพื่อความแม่นยำ
        # แต่ต้องตรวจหลังจาก HYPOTHETICAL และ ASK_COMPARISON แล้ว
        # ----------------------------------------------------
        
        # ----------------------------------------------------
        # 3. ตรวจสอบ Keywords สำหรับ Intent ประเภทอื่น ๆ
        # ตามลำดับความสำคัญ
        # ----------------------------------------------------
        
        # การถามความคิดเห็น (ตรวจสอบก่อน เพราะมีความเฉพาะสูง)
        if any(kw in text_lower for kw in ['คิดเห็นยังไง', 'ว่ายังไง', 'คิดว่าไง', 'เห็นด้วยไหม', 'คิดยังไง']):
            return IntentType.ASK_OPINION
        
        # การแสดงความคิดเห็น (ต้องมีคำว่า คิดว่า, เห็นว่า, ชอบ, ไม่ชอบ แต่ไม่ใช่คำถาม)
        if any(kw in text_lower for kw in ['คิดว่า', 'เห็นว่า', 'ความเห็น', 'ว่าแต่']):
            return IntentType.EXPRESS_OPINION
        if 'ชอบ' in text_lower and '?' not in text_lower and 'ไหม' not in text_lower:
            return IntentType.EXPRESS_OPINION
        if 'ไม่ชอบ' in text_lower:
            return IntentType.EXPRESS_OPINION
        
        # การขอความช่วยเหลือ (REQUEST_HELP) - ต้องมีคำขอร้อง
        if any(kw in text_lower for kw in ['ช่วย', 'ขอร้อง', 'กรุณา', 'ให้หน่อย', 'โปรด']):
            return IntentType.REQUEST_HELP
        
        # การเตือน/ห้าม (WARN) - ต้องขึ้นต้นหรือมีคำห้ามชัดเจน
        if any(text_lower.startswith(kw) for kw in ['ห้าม', 'อย่า', 'ระวัง']):
            return IntentType.WARN
        if any(kw in text_lower for kw in ['เตือน', 'อันตราย']) and 'ทำ' not in text_lower:
            return IntentType.WARN
        
        # การแนะนำ (ADVISE)
        if any(kw in text_lower for kw in ['แนะนำ', 'น่าจะ', 'ควร', ' ought to', 'should']):
            return IntentType.ADVISE
        
        # การชักชวน (INVITE) - ต้องมีคำชวนชัดเจน
        if any(kw in text_lower for kw in ['ชวน', 'ไปกัน', 'ร่วม', 'ด้วยกัน']):
            return IntentType.INVITE
        # แยก "มา" ที่เป็นคำชวน กับ "มาก" ที่เป็นคำวิเศษณ์
        if re.search(r'\bมา\b', text_lower) and 'มาก' not in text_lower and 'ถ้า' not in text_lower:
            return IntentType.INVITE
        
        # การให้สัญญา - ต้องระวังไม่ overlap กับ HYPOTHETICAL
        if any(kw in text_lower for kw in ['สัญญา', 'รับรอง', 'ให้คำมั่น']):
            return IntentType.PROMISE
        # "จะทำ" เฉย ๆ อาจเป็นได้ทั้ง PROMISE และ HYPOTHETICAL
        # ถ้ามี "ถ้า", "สมมติ" นำหน้า ให้เป็น HYPOTHETICAL แทน
        if 'จะทำ' in text_lower and not any(kw in text_lower for kw in ['ถ้า', 'สมมติ', 'ถ้าเกิด', 'ถ้าหาก']):
            return IntentType.PROMISE
        
        # การขออนุญาต
        if any(kw in text_lower for kw in ['ขออนุญาต', 'ขอ...หน่อย', '可否']):
            return IntentType.ASK_PERMISSION
        # "ขอ" เฉย ๆ อาจสับสนกับ REQUEST_HELP
        if 'ขอ' in text_lower and 'ช่วย' not in text_lower and 'หน่อย' not in text_lower:
            # ตรวจสอบว่าเป็นคำถามหรือไม่
            if any(q in text_lower for q in ['ไหม', 'ได้ไหม', 'หรือไม่']):
                return IntentType.ASK_PERMISSION
        
        # การอธิบาย/บอกเล่า
        if any(kw in text_lower for kw in ['อธิบาย', 'บอกเล่า', 'เล่าให้ฟัง']):
            return IntentType.EXPLAIN
        if 'เรื่อง' in text_lower and 'อะไร' not in text_lower and 'ไหน' not in text_lower:
            return IntentType.EXPLAIN
        
        # --- เพิ่มใหม่: ตรวจสอบกรณีซับซ้อนตามลำดับความสำคัญ (ย้ายขึ้นมาตรวจก่อน COMMAND) ---
        
        # การประชด/ตัดพ้อ (SARCASM_PASSIVE) - ตรวจสอบก่อนเพราะมักมีคำบวกแต่ความหมายลบ
        if any(kw in text_lower for kw in ['ก็เก่งนี่นา', 'ดีมากเลยนะ', 'ฉลาดจัง', 'ทำได้ดีมาก', 'เยี่ยมไปเลย', 'สุดยอด', 'เก่งมาก', 'น่ารักจัง']):
            return IntentType.SARCASM_PASSIVE
        
        # การบ่น/ระบาย (VENT_COMPLAIN) - ตรวจสอบก่อน ASK_INFO เพราะมีคำถามเชิงบ่น
        if any(kw in text_lower for kw in ['เบื่อ', 'รำคาญ', 'เหนื่อย', 'เซ็ง', 'หงุดหงิด', 'น่าเบื่อ', 'อีกแล้ว', 'บ่น', 'ระบาย', 'ปวดหัว', 'วุ่นวาย', 'ยุ่งยาก']):
            return IntentType.VENT_COMPLAIN
        # เช็คว่าเป็นคำถามเชิงบ่น เช่น "ทำไมต้อง..." 
        if text_lower.startswith('ทำไมต้อง') or text_lower.startswith('ทำไมเราต้อง'):
            return IntentType.VENT_COMPLAIN
        
        # ความสับสน (EXPRESS_CONFUSION) - ตรวจสอบก่อน ASK_INFO
        if any(kw in text_lower for kw in ['งง', 'สับสน', 'ไม่เข้าใจ', 'หมายความว่าไง', 'ยังไงนะ', 'อะไรนะ', 'เหรอ', 'จริงเหรอ', 'แน่ใจเหรอ', 'แปลก', 'พิลึก']):
            return IntentType.EXPRESS_CONFUSION
        
        # สมมติฐาน (HYPOTHETICAL) - ตรวจสอบก่อน COMMAND และ ASK_INFO
        if any(kw in text_lower for kw in ['ถ้าเกิด', 'สมมติ', 'ถ้าหาก', 'ในกรณีที่', 'ลองคิดดูว่า', 'จะเกิดอะไรขึ้นถ้า', 'what if', 'suppose']):
            return IntentType.HYPOTHETICAL
        
        # การเปรียบเทียบ (ASK_COMPARISON) - ตรวจสอบก่อน COMMAND และ ASK_INFO
        if any(kw in text_lower for kw in ['ต่างกันยังไง', 'ต่างกับ', 'เทียบกับ', 'เปรียบเทียบกับ', 'อันไหนดีกว่า', 'เลือกอันไหน', 'เหมือนหรือต่าง']):
            return IntentType.ASK_COMPARISON
        
        # มุกตลก/เรื่องฮา (TELL_JOKE) - ตรวจสอบก่อน ASK_INFO
        if any(kw in text_lower for kw in ['เล่ามุก', 'เรื่องตลก', 'ตลก', 'ฮา', 'ขำขัน', 'เล่าเรื่องตลก', 'เล่าเรื่องฮา', 'ทำให้ขำ', 'make me laugh', 'tell me a joke']):
            return IntentType.TELL_JOKE
        
        # คำถามทั่วไป (ASK_INFO) - ตรวจสอบสุดท้ายเพื่อไม่ให้ overlap
        question_indicators = ['?', 'อะไร', 'อย่างไร', 'ยังไง', 'ไหม', 'หรือ', 'เท่าไหร่', 'ไหน', 'ใคร', 'เมื่อไหร่', 'ทำไม']
        if any(ind in text_lower for ind in question_indicators):
            return IntentType.ASK_INFO
        
        # การตอบข้อมูล (ถ้ามีบริบทการตอบ)
        if re.search(r'(ตอบ|คำตอบคือ|ได้ผลว่า)', text_lower):
            return IntentType.ANSWER
        
        # ----------------------------------------------------
        # ตรวจสอบคำสั่ง (COMMAND) ที่มี CoreAction ชัดเจน (ย้ายมาตรวจสุดท้าย)
        # หลังจากตรวจสอบ Intent อื่น ๆ ทั้งหมดแล้ว
        # ----------------------------------------------------
        core_act = self.extract_core_action(text_lower)
        if core_act:
            # ยกเว้นบางกรณีที่ไม่ใช่คำสั่งจริง ๆ
            non_command_keywords = ['อยาก', 'จะ', 'เคย', 'ชอบ', 'รู้สึก']
            if not any(kw in text_lower for kw in non_command_keywords):
                return IntentType.COMMAND
        
        return None

    def parse(self, user_input: str) -> ParsedIntent:
        input_lower = user_input.lower().strip()
        reasoning_steps = []
        params = {}

        # =====================================================
        # ขั้นตอนที่ 1: ตรวจสอบโจทย์คณิตศาสตร์/ตรรกะก่อน (มีความเฉพาะสูง)
        # ต้องตรวจสอบก่อน Intent ทั่วไป เพราะมี keywords เฉพาะ
        # =====================================================
        
        # 1.1 ตรวจสอบโจทย์สมการเชิงฟังก์ชัน (Functional Equation)
        if any(kw in input_lower for kw in self.functional_keywords):
            reasoning_steps.append("ตรวจพบคำสำคัญเกี่ยวกับฟังก์ชัน (f(x), functional)")
            params = self._extract_functional_eq(user_input)
            return ParsedIntent(
                intent_type=IntentType.SOLVE_FUNCTIONAL,
                original_input=user_input,
                action="solve_functional_equation",
                entities=[],
                params=params,
                context="functional_math",
                confidence=0.95,
                reasoning="\n".join(reasoning_steps)
            )

        # 1.2 ตรวจสอบโจทย์ข้อจำกัด/จำนวนเต็ม (Constraint Satisfaction - Z3)
        if any(kw in input_lower for kw in self.constraint_keywords):
            reasoning_steps.append("ตรวจพบคำสำคัญเกี่ยวกับจำนวนเต็มหรือตรรกะ")
            eq_data = self._extract_equation(user_input)
            params = eq_data
            params['domain'] = 'integer' # บังคับใช้ Z3
            return ParsedIntent(
                intent_type=IntentType.SOLVE_CONSTRAINT,
                original_input=user_input,
                action="solve_constraint_problem",
                entities=[],
                params=params,
                context="integer_logic",
                confidence=0.95,
                reasoning="\n".join(reasoning_steps)
            )

        # 1.3 ตรวจสอบสมการ/ตรรกะภาษาไทย (เช่น "แก้สมการ x + 5 = 10", "A มากกว่า B อยู่ 5, A+B=15")
        # ต้องตรวจสอบก่อนสมการทั่วไป เพราะอาจมี pattern ซ้อนกัน
        logic_check = self._check_logic_equation(user_input)
        if logic_check:
            reasoning_steps.append("ตรวจพบโจทย์สมการหรือตรรกะภาษาไทย")
            return ParsedIntent(
                intent_type=IntentType.SOLVE_EQUATION,
                original_input=user_input,
                action="solve_logic_equation",
                entities=[],
                params={
                    "equation": user_input,
                    "requires_logic_solver": True,
                    "intent_type": "logic_equation"
                },
                context="logic_equation",
                confidence=0.95,
                reasoning="\n".join(reasoning_steps)
            )

        # 1.4 ตรวจสอบสมการทั่วไป (Equation Solving - SymPy/Z3 fallback)
        # ต้องมีตัวแปรจริงๆ (เช่น x, y) ไม่ใช่แค่คำลงท้าย "เท่ากับเท่าไหร่"
        has_real_variable = bool(re.search(r'[a-zA-Z]', user_input)) and not re.search(r'เท่ากับเท่าไหร่|ได้เท่าไร|เท่ากับ', user_input)
        
        if any(kw in input_lower for kw in self.math_keywords) or ("=" in user_input and has_real_variable):
            reasoning_steps.append("ตรวจพบรูปแบบสมการหรือคำขอแก้โจทย์คณิตศาสตร์")
            eq_data = self._extract_equation(user_input)
            params = eq_data
            return ParsedIntent(
                intent_type=IntentType.SOLVE_EQUATION,
                original_input=user_input,
                action="solve_algebraic_equation",
                entities=[],
                params=params,
                context="algebra",
                confidence=0.95,
                reasoning="\n".join(reasoning_steps)
            )

        # 1.5 ตรวจสอบการคำนวณภาษาไทย (เช่น "หาผลบวกของ 123 และ 456", "หาผลคูณของ 5 และ 3")
        # ต้องตรวจสอบก่อนการคำนวณรูปแบบตัวเลขล้วน
        thai_calc_match = self._extract_thai_calculation(user_input)
        if thai_calc_match:
            num1, op, num2 = thai_calc_match
            reasoning_steps.append(f"ตรวจพบการคำนวณภาษาไทย: {num1} {op} {num2}")
            return ParsedIntent(
                intent_type=IntentType.CALCULATION,
                original_input=user_input,
                action=f"calculate_{op}",
                entities=[num1, num2],
                params={"expression": user_input, "num1": num1, "num2": num2, "operator": op},
                context="simple_arithmetic",
                confidence=0.98,
                reasoning="\n".join(reasoning_steps)
            )

        # 1.5 ตรวจสอบการคำนวณ murni (เช่น "9.8-9.11", "คำนวณ 9.8-9.11", "9.8-9.11 ได้เท่าไร")
        # รองรับทั้งรูปแบบไทยและอังกฤษ มีหรือไม่มีคำลงท้ายก็ได้
        calc_patterns = [
            r"(-?\d+\.?\d*)\s*([-+*/])\s*(-?\d+\.?\d*)",  # พื้นฐาน: 9.8-9.11
            r"(-?\d+\.?\d*)\s*([-+*/])\s*(-?\d+\.?\d*)\s*(?:ได้เท่าไร|เท่ากับ|เท่าไหร่|ค่า)?",  # ไทย: มีคำลงท้าย
        ]
        
        calc_match = None
        for pattern in calc_patterns:
            calc_match = re.search(pattern, user_input)
            if calc_match:
                break
        
        if calc_match and not any(q in input_lower for q in ["?", "อย่างไร", "what", "how"]):
            num1 = float(calc_match.group(1))
            op = calc_match.group(2)
            num2 = float(calc_match.group(3))
            reasoning_steps.append(f"ตรวจพบนิพจน์คณิตศาสตร์ล้วน: {num1} {op} {num2}")
            return ParsedIntent(
                intent_type=IntentType.CALCULATION,
                original_input=user_input,
                action=f"calculate_{op}",
                entities=[num1, num2],
                params={"expression": user_input, "num1": num1, "num2": num2, "operator": op},
                context="simple_arithmetic",
                confidence=0.99,
                reasoning="\n".join(reasoning_steps)
            )

        # =====================================================
        # ขั้นตอนที่ 2: ตรวจสอบ Intent ทั่วไป 20 ประเภท
        # =====================================================
        general_intent = self.classify_general_intent(user_input)
        
        if general_intent:
            reasoning_steps.append(f"จำแนก Intent ทั่วไป: {general_intent.value}")
            
            # กรณี COMMAND: ดึง CoreAction ด้วย
            core_action = None
            if general_intent == IntentType.COMMAND:
                core_action = self.extract_core_action(user_input)
                if core_action:
                    reasoning_steps.append(f"ตรวจพบ CoreAction: {core_action.value}")
            
            return ParsedIntent(
                intent_type=general_intent,
                original_input=user_input,
                action=general_intent.value,
                entities=[],
                params={"message": user_input},
                context="general_communication",
                confidence=0.90,
                reasoning="\n".join(reasoning_steps),
                core_action=core_action
            )

        # =====================================================
        # ขั้นตอนที่ 3: ตรวจสอบการค้นหาข้อมูล
        # =====================================================
        if any(kw in input_lower for kw in self.search_keywords):
            reasoning_steps.append("ตรวจพบคำขอค้นหาข้อมูล")
            return ParsedIntent(
                intent_type=IntentType.SEARCH_WEB,
                original_input=user_input,
                action="search_information",
                entities=[],
                params={"query": user_input},
                context="web_search",
                confidence=0.90,
                reasoning="\n".join(reasoning_steps)
            )

        # =====================================================
        # Default: UNKNOWN
        # =====================================================
        return ParsedIntent(
            intent_type=IntentType.UNKNOWN,
            original_input=user_input,
            action="unknown",
            entities=[],
            params={},
            context="",
            confidence=0.5,
            reasoning="ไม่สามารถระบุเจตนาได้ชัดเจน"
        )

    def _extract_equation(self, text: str) -> Dict[str, Any]:
        """แยกส่วนสมการซ้าย-ขวา และตัวแปร"""
        # พยายามหาเครื่องหมาย =
        if "=" in text:
            parts = text.split("=", 1)
            lhs = parts[0].strip()
            rhs = parts[1].strip() if len(parts) > 1 else "0"
            
            # ล้างคำฟุ่มเฟือยบางคำออก (อย่างง่าย)
            # ในอนาคตอาจใช้ NLP ที่ดีกว่านี้
            clean_lhs = re.sub(r'(แก้สมการ|หาค่า|find|solve|for)', '', lhs, flags=re.IGNORECASE).strip()
            clean_rhs = re.sub(r'(เท่ากับ|to)', '', rhs, flags=re.IGNORECASE).strip()
            
            return {
                "lhs": clean_lhs,
                "rhs": clean_rhs,
                "full_expr": f"{clean_lhs} - ({clean_rhs})", # รูปแบบสำหรับแก้: expr = 0
                "variables": self._detect_variables(clean_lhs + clean_rhs)
            }
        return {"raw": text, "variables": self._detect_variables(text)}

    def _extract_functional_eq(self, text: str) -> Dict[str, Any]:
        return {
            "raw": text,
            "target_func": "f"
        }

    def _detect_variables(self, expr: str) -> List[str]:
        """หาตัวแปรภาษาอังกฤษตัวเดียว (x, y, k, n, etc.)"""
        vars_found = set(re.findall(r'\b([a-zA-Z])\b', expr))
        ignore = {'a', 'i', 'e', 'o'} # ตัดคำเชื่อมบางคำ
        return sorted([v for v in vars_found if v not in ignore])

    def _extract_entities(self, text: str) -> List[Any]:
        entities = []
        numbers = re.findall(r"\d+\.?\d*", text)
        for num in numbers:
            try:
                entities.append(float(num) if '.' in num else int(num))
            except ValueError:
                pass
        return entities

    def _extract_thai_calculation(self, text: str) -> Optional[Tuple[float, str, float]]:
        """
        แยกการคำนวณภาษาไทย เช่น "หาผลบวกของ 123 และ 456"
        คืนค่า (num1, operator, num2) หรือ None ถ้าไม่พบ
        """
        text_lower = text.lower()
        
        # Pattern: หาผล[บวก/ลบ/คูณ/หาร] ของ <number1> และ <number2>
        # หรือ: ผล[บวก/ลบ/คูณ/หาร] ของ <number1> กับ <number2>
        thai_calc_patterns = [
            # รูปแบบ: หาผลXXX ของ N1 และ N2 (รวม "ผลต่าง" ด้วย)
            r"(?:หา)?ผล(บวก|ลบ|ต่าง|คูณ|หาร)\s*ของ\s*(\d+\.?\d*)\s*(?:และ|กับ|,)\s*(\d+\.?\d*)",
            # รูปแบบ: XXX N1 ด้วย N2
            r"(?:หา)?(บวก|ลบ|คูณ|หาร)\s*(\d+\.?\d*)\s*(?:ด้วย|และ|กับ|,)\s*(\d+\.?\d*)",
            # รูปแบบ: N1 XXX N2 (เช่น "123 บวก 456")
            r"(\d+\.?\d*)\s*(?:หา)?(บวก|ลบ|คูณ|หาร)\s*(\d+\.?\d*)",
        ]
        
        for pattern in thai_calc_patterns:
            match = re.search(pattern, text_lower)
            if match:
                groups = match.groups()
                
                # กรณี pattern 1: (operation, num1, num2) - operation เป็น "บวก", "ลบ", "ต่าง", "คูณ", "หาร"
                if len(groups) == 3 and groups[0] in self.thai_math_ops:
                    op = self.thai_math_ops[groups[0]]
                    num1 = float(groups[1])
                    num2 = float(groups[2])
                    return (num1, op, num2)
                
                # กรณี pattern 2: (operation, num1, num2) - operation เป็นคำกริยา
                elif len(groups) == 3 and groups[0] in self.thai_math_ops:
                    op = self.thai_math_ops[groups[0]]
                    num1 = float(groups[1])
                    num2 = float(groups[2])
                    return (num1, op, num2)
                
                # กรณี pattern 3: (num1, operation, num2)
                elif len(groups) == 3 and groups[1] in self.thai_math_ops:
                    num1 = float(groups[0])
                    op = self.thai_math_ops[groups[1]]
                    num2 = float(groups[2])
                    return (num1, op, num2)
        
        return None

    def _check_logic_equation(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นสมการหรือโจทย์ตรรกะที่ควรใช้ AdvancedLogicEngine หรือไม่
        Pattern: "แก้สมการ...", "หาค่า x", "...มากกว่า...อยู่...", "A+B=..., A มากกว่า B"
        """
        text_lower = text.lower()
        
        # Pattern ที่บ่งชี้ว่าเป็นสมการ/ตรรกะ
        logic_patterns = [
            r'แก้สมการ',                    # แก้สมการ x + 5 = 10
            r'หาค่า\s*[x-y]',              # หาค่า x, หาค่า y
            r'\d*\s*[x-y]\s*[+\-*/]=\s*\d+', # x+5=10, 2x-3=7
            r'มากกว่า.*อยู่',               # A มากกว่า B อยู่ 5
            r'น้อยกว่า.*อยู่',               # A น้อยกว่า B อยู่ 3
            r'.*มากกว่า.*และ.*รวม.*',       # A มากกว่า B และ A รวม B เท่ากับ...
            r'.*มากกว่า.*และ.*บวก.*',       # โจทย์ตรรกะที่มีทั้ง "มากกว่า" และ "บวก"
        ]
        
        return any(re.search(p, text_lower) for p in logic_patterns)

def display_analysis(intent: ParsedIntent):
    """แสดงผลการวิเคราะห์แบบละเอียด"""
    print("="*60)
    print("🔍 ผลการวิเคราะห์ความตั้งใจ (Intent Analysis)")
    print("="*60)
    print(f"Input เดิม: \"{intent.original_input}\"")
    print("-" * 40)
    print("🧠 กระบวนการคิด (Reasoning):")
    for i, step in enumerate(intent.reasoning.split('\n'), 1):
        print(f"  {i}. {step}")
    print("-" * 40)
    print(f"✅ ประเภท: {intent.intent_type.value.upper()}")
    print(f"🎯 การกระทำที่ต้องการ: {intent.action}")
    if intent.params:
        print(f"📐 พารามิเตอร์: {intent.params}")
    print(f"📦 ข้อมูลที่สกัดได้ (Entities): {intent.entities}")
    print(f"💡 ความมั่นใจ: {intent.confidence * 100:.1f}%")
    print("="*60)

if __name__ == "__main__":
    parser = IntentParser()
    
    # ทดสอบ Intent ทั่วไป 20 ประเภท + Core Actions
    test_cases = [
        # Greeting & Farewell
        "สวัสดีครับ",
        "หวัดดี",
        "ลาก่อน",
        "บายจ้า",
        
        # Thank & Apologize
        "ขอบคุณมากครับ",
        "ขอโทษที",
        
        # Laugh & Acknowledge & Reject
        "555 ขำมาก",
        "ฮ่าๆๆ",
        "ครับ ยินดี",
        "ไม่เอาหรอก",
        
        # Commands with Core Actions
        "เปิดไฟหน่อย",
        "ปิดประตูด้วย",
        "สร้างโฟลเดอร์ใหม่",
        "ลบไฟล์นี้",
        "แก้ไขชื่อเอกสาร",
        "ค้นหาไฟล์งานเก่า",
        "ส่งข้อความไปหาแม่",
        "บันทึกเอกสาร",
        "เริ่มทำงาน",
        "หยุดพัก",
        "คำนวณ 5+5",
        "วิเคราะห์ข้อมูลยอดขาย",
        
        # Request Help
        "ช่วยเปิดแอร์ให้หน่อย",
        "กรุณาส่งไฟล์ให้ด้วย",
        
        # Questions (ASK_INFO)
        "อากาศวันนี้เป็นไงบ้าง",
        "นี่คืออะไร",
        "ทำอย่างไร",
        
        # Opinions
        "คิดว่าไงกับหนังเรื่องนี้",
        "ฉันชอบเพลงนี้มาก",
        
        # Feelings
        "ฉันดีใจมาก",
        "รู้สึกเหงาจัง",
        
        # Advise & Warn
        "คุณควรออกกำลังกาย",
        "ห้ามสูบบุหรี่ที่นี่",
        
        # Math & Logic (เดิม)
        "จงหาจำนวนเต็มบวก n ทั้งหมดที่ทำให้ n^4 + 4^n เป็นจำนวนเฉพาะ",
        "x^2+19x-92=k^2 หาจำนวนเต็ม x, k",
        "f(x+y)+f(x)f(y)=f(xy)+f(x)+f(y) จงหาฟังก์ชัน f",
        "9.8-9.11",
        "แม่บอกฉันให้ไปซื้อของราคา 19 บาท ฉันต้องเตรียมเหรียญอะไร",
    ]
    
    print("="*100)
    print(f"{'ข้อความ':45} | {'Intent':25} | {'Core Action':20}")
    print("="*100)
    
    for t in test_cases:
        result = parser.parse(t)
        core_action_str = result.core_action.value if result.core_action else "-"
        print(f"{t:45} | {result.intent_type.value:25} | {core_action_str:20}")
    
    print("\n\n")
    
    # แสดงผลแบบละเอียดสำหรับบางเคส
    detail_cases = [
        "เปิดไฟหน่อย",
        "ช่วยคำนวณ 5+5 ให้หน่อย",
        "คิดว่าไงกับหนังเรื่องนี้",
        "x^2+19x-92=k^2 หาจำนวนเต็ม x, k",
    ]
    
    for case in detail_cases:
        result = parser.parse(case)
        display_analysis(result)
        print("\n")
