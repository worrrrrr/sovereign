"""
Sovereign AI Cognitive Way of Reasoning Engine (CWOR)
ระบบประมวลผลความคิดอัจฉริยะที่ผสาน Cognitive Profile กับ Advanced Reasoning
ทำให้ AI มีทั้ง "ตัวตน" และ "ความสามารถในการคิดวิเคราะห์" แบบครบวงจร
"""

import re
import json
import random
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# Import จาก cognitive_profile (รองรับทั้ง direct import และ module import)
try:
    from .cognitive_profile import (
        CognitiveProfileEngine, 
        ReasoningProfile, 
        CognitiveStyle
    )
except ImportError:
    from cognitive_profile import (
        CognitiveProfileEngine, 
        ReasoningProfile, 
        CognitiveStyle
    )


class CognitiveWayOfReasoningEngine:
    """
    ระบบกลั่นกรองความคิดอัจฉริยะรุ่นใหม่ที่ผสาน:
    1. Cognitive Profile - ตัวตน จุดยืน สไตล์การคิด
    2. Dialectical Reasoning - กระบวนการคิดแบบ Thesis-Antithesis-Synthesis
    3. Advanced Logic - comparative, conditional, negative, math equations
    4. Self-Reflection - ตรวจสอบความสอดคล้องกับ Axioms
    5. Adaptive Learning - เรียนรู้จาก feedback
    """
    
    def __init__(self, profile_engine: CognitiveProfileEngine = None):
        self.profile_engine = profile_engine or CognitiveProfileEngine()
        
        # Logic patterns จาก WReasoningEngine เดิม
        self.logic_patterns = {
            'comparative': [
                r'(.+?)\s*(?:ไม่|ไม่ค่อย)\s*(?:เก่ง|ดี|ชำนาญ|ถนัด)',
                r'(.+?)\s*(?:เก่ง|ดี|ชำนาญ|ถนัด)\s*(?:มาก|สุดๆ|เวอร์)',
                r'(.+?)\s*(?:พอ(?:ใช้|ได้)|ปานกลาง|ธรรมดา)',
            ],
            'conditional': [
                r'ถ้า\s*(.+?)\s*(?:ฉัน|ผม|เขา|เรา)\s*(จะ|ก็|ค่อย)\s*(.+?)',
                r'(.+?)\s*ถ้า\s*(.+?)',
            ],
            'negative_command': [
                r'ห้าม\s*ไม่\s*(.+?)',
                r'อย่า\s*ลืม\s*(.+?)',
            ],
            'math_equation': [
                r'([a-zA-Z])\^2\s*\+\s*(-?\d+)[a-zA-Z]\s*\+\s*(-?\d+)\s*=\s*0',
                r'([a-zA-Z])\^2\s*\+\s*(-?\d+)[a-zA-Z]\s*-\s*(\d+)\s*=\s*0',
                r'(\d+)\^([a-zA-Z])\s*=\s*[a-zA-Z]\^(\d+)',
            ],
            'code_request': [
                r'(?:สร้าง|เขียน|โค้ด|code)\s*(?:โปรแกรม|ฟังก์ชัน|function)\s*(?:คำนวณ|หา|เกี่ยวกับ)\s*(.+?)',
                r'(?:อยากเรียน|เรียนรู้)\s*(?:การเขียนโปรแกรม|เขียนโค้ด|coding)',
            ]
        }
        
        # Forbidden topics checker
        self.risk_keywords = [
            "การเมือง", "การพนัน", "ยาเสพติด", "การทำร้ายตนเอง",
            "ความเชื่อไสยศาสตร์", "ดราม่า", "ซุบซิบ"
        ]
    
    def _deconstruct_input(self, text: str) -> Dict[str, Any]:
        """เฟสที่ 1: วิเคราะห์เจตนาแฝง น้ำเสียงอารมณ์ และความเสี่ยง"""
        profile = self.profile_engine.get_active_profile()
        
        # ตรวจสอบ forbidden topics
        is_risky = any(topic in text for topic in profile.forbidden_topics)
        is_risky = is_risky or any(keyword in text for keyword in self.risk_keywords)
        
        # ตรวจสอบว่าเป็นคำถามขอความคิดเห็น
        is_asking_opinion = any(w in text for w in ["ดีไหม", "อย่างไร", "ควร", "จริงไหม", "ทำไม"])
        
        # ประเมินอารมณ์เบื้องต้น
        sentiment = "neutral"
        if any(w in text for w in ["แย่", "เหนื่อย", "กลัว", "เครียด", "เศร้า"]):
            sentiment = "anxious"
        elif any(w in text for w in ["ดีใจ", "เย้", "สุดยอด", "ชอบ", "รัก"]):
            sentiment = "positive"
        elif any(w in text for w in ["โกรธ", "เกลียด", "รำคาญ"]):
            sentiment = "negative"
        
        # ตรวจจับประเภทโจทย์
        category = self._classify(text)
        
        return {
            "is_risky": is_risky,
            "is_opinion": is_asking_opinion,
            "sentiment": sentiment,
            "category": category,
            "profile_style": profile.cognitive_style.value,
            "emotional_tone": profile.emotional_tone
        }
    
    def _apply_axioms(self, deconstructed: Dict[str, Any], text: str) -> List[str]:
        """เฟสที่ 2: ดึงหลักคิดประจำใจ (Axioms) ที่เกี่ยวข้องกับบริบท"""
        profile = self.profile_engine.get_active_profile()
        matched_axioms = []
        
        # จับคู่ keywords กับ axioms
        if any(w in text for w in ["เงิน", "ลงทุน", "หุ้น", "รวย", "ธุรกิจ"]):
            financial_axioms = [
                a for a in profile.axioms 
                if any(kw in a for kw in ["แผน", "เสี่ยง", "ข้อมูล", "คำนวณ"])
            ]
            matched_axioms.extend(financial_axioms)
            
        if any(w in text for w in ["รัก", "เพื่อน", "แฟน", "คน", "ความสัมพันธ์"]):
            relationship_axioms = [
                a for a in profile.axioms 
                if any(kw in a for kw in ["จริงใจ", "ความรัก", "คุณค่า", "ความรู้สึก"])
            ]
            matched_axioms.extend(relationship_axioms)
        
        if any(w in text for w in ["งาน", "อาชีพ", "อนาคต", "เป้าหมาย"]):
            career_axioms = [
                a for a in profile.axioms 
                if any(kw in a for kw in ["วางแผน", "เตรียมพร้อม", "กลยุทธ์"])
            ]
            matched_axioms.extend(career_axioms)
        
        # หากไม่ตรงหมวดหมู่ใดเลย ให้เลือก axiom แกนกลาง
        if not matched_axioms and profile.axioms:
            matched_axioms.append(profile.axioms[0])
        
        # Self-Reflection: ตรวจสอบว่า axiom ขัดกับ moral compass หรือไม่
        filtered_axioms = []
        for axiom in matched_axioms:
            if not self._check_moral_conflict(axiom, profile.moral_compass):
                filtered_axioms.append(axiom)
        
        return filtered_axioms if filtered_axioms else matched_axioms
    
    def _check_moral_conflict(self, axiom: str, moral_compass: List[str]) -> bool:
        """ตรวจสอบว่า axiom ขัดกับหลักจริยธรรมหรือไม่"""
        # Simple heuristic check
        conflict_keywords = ["โกง", "ทำร้าย", "หลอก", "เอาเปรียบ"]
        return any(kw in axiom for kw in conflict_keywords)
    
    def _dialectical_reasoning(
        self, 
        text: str, 
        matched_axioms: List[str],
        deconstructed: Dict[str, Any]
    ) -> Tuple[str, str, str]:
        """
        เฟสที่ 3: กระบวนการคิดวิเคราะห์ประเมินผลสองด้านอย่างสมดุล
        (Thesis, Antithesis, Synthesis)
        """
        profile = self.profile_engine.get_active_profile()
        category = deconstructed.get("category", "general")
        
        # ปรับเนื้อหาตาม cognitive style
        if profile.cognitive_style == CognitiveStyle.PRAGMATIC_ENGINEER:
            thesis_intro = "ในมุมมองของข้อมูลและตรรกะ:"
            antithesis_intro = "แต่ต้องไม่ลืมความจริงที่ว่า:"
            synthesis_intro = "สรุปแล้ว ตามหลักการแล้ว:"
            
        elif profile.cognitive_style == CognitiveStyle.EMPATHETIC_PHILOSOPHER:
            thesis_intro = "ถ้าเราลองมองด้วยใจ:"
            antithesis_intro = "แต่เราก็ต้องเข้าใจว่า:"
            synthesis_intro = "สิ่งที่สำคัญที่สุดคือ:"
            
        elif profile.cognitive_style == CognitiveStyle.STRATEGIC_ANALYST:
            thesis_intro = "ในเชิงกลยุทธ์:"
            antithesis_intro = "แต่ต้องระวังจุดอ่อน:"
            synthesis_intro = "แผนที่ดีที่สุดคือ:"
            
        elif profile.cognitive_style == CognitiveStyle.CREATIVE_INNOVATOR:
            thesis_intro = "ไอเดียที่น่าสนใจคือ:"
            antithesis_intro = "แต่อุปสรรคที่อาจเจอ:"
            synthesis_intro = "ทางออกที่สร้างสรรค์:"
            
        else:  # GUARDIAN_MENTOR
            thesis_intro = "ในแง่ที่ดี:"
            antithesis_intro = "แต่ต้องคำนึงถึงความปลอดภัย:"
            synthesis_intro = "คำแนะนำที่ปลอดภัยที่สุด:"
        
        # สร้าง Thesis (ข้อเสนอ/มุมมองแง่ดี)
        if category == "comparative":
            thesis = f"{thesis_intro} การรับรู้ระดับความสามารถของตัวเองเป็นจุดเริ่มต้นของการพัฒนา"
        elif category == "conditional":
            thesis = f"{thesis_intro} การคิดแบบมีเงื่อนไขช่วยวางแผนล่วงหน้าได้ดี"
        elif category == "math_equation":
            thesis = f"{thesis_intro} สมการนี้มีวิธีแก้ที่เป็นระบบ"
        else:
            thesis = f"{thesis_intro} การลองทำสิ่งนี้อาจเปิดโอกาสใหม่ๆ และสร้างการเติบโต"
        
        # สร้าง Antithesis (ข้อจำกัด/ความเสี่ยง)
        axiom_text = matched_axioms[0] if matched_axioms else "ต้องมีสติและพิจารณาอย่างรอบคอบ"
        antithesis = f"{antithesis_intro} '{axiom_text}'"
        
        # สร้าง Synthesis (ทางออกที่ตกผลึก)
        if deconstructed.get("is_risky"):
            synthesis = f"{synthesis_intro} ควรหลีกเลี่ยงหรือปรึกษาผู้เชี่ยวชาญก่อนตัดสินใจ"
        elif category == "math_equation":
            synthesis = f"{synthesis_intro} ใช้สูตรและขั้นตอนทางคณิตศาสตร์มาตรฐานในการแก้"
        elif category == "code_request":
            synthesis = f"{synthesis_intro} เริ่มจากโครงสร้างพื้นฐาน แล้วค่อยเพิ่มฟีเจอร์"
        else:
            synthesis = f"{synthesis_intro} ควรทดลองทำในสเกลเล็กๆ ก่อนเพื่อทดสอบและเก็บข้อมูลเรียนรู้ แล้วจึงค่อยๆ ขยายผล"
        
        return thesis, antithesis, synthesis
    
    def _wrap_persona(
        self, 
        thesis: str, 
        antithesis: str, 
        synthesis: str, 
        deconstructed: Dict[str, Any]
    ) -> str:
        """
        เฟสที่ 4: สวมหน้ากากจูนน้ำเสียง คำติดปาก รูปแบบการพิมพ์ และสไตล์เฉพาะตัว
        """
        profile = self.profile_engine.get_active_profile()
        
        catchphrase = random.choice(profile.catchphrases) if profile.catchphrases else ""
        suffix = random.choice(profile.suffixes) if profile.suffixes else ""
        
        # จัดการกรณีคำถามที่อยู่ในกลุ่มเสี่ยง
        if deconstructed["is_risky"]:
            return (
                f"{catchphrase}... ขอผ่านก่อนนะ เรื่องนี้ส่วนตัวผมตั้งใจจะไม่วิจารณ์ "
                f"ขออนุญาตไม่แตะนะครับ {suffix}"
            )
        
        # ประกอบร่างตาม formatting rule
        if profile.formatting_rule == "structured":
            response = (
                f"{catchphrase}! ถ้าให้ผมคิดและตอบในแบบของผมนะ:\n\n"
                f"📌 **วิเคราะห์แง่ดี:** {thesis}\n"
                f"⚠️ **สิ่งที่ต้องพึงระวัง:** {antithesis}\n"
                f"💡 **ทางออกแบบที่ผมเลือกทำ:** {synthesis}\n\n"
                f"สู้ๆ ครับ {suffix}"
            )
        elif profile.formatting_rule == "fluid":
            response = (
                f"{catchphrase}! คิดแบบตรงไปตรงมานะ {thesis} "
                f"แต่มันติดเรื่องสำคัญที่ต้องระวังคือ {antithesis} "
                f"ฉะนั้นสำหรับตัวผมเอง ผมมองว่า {synthesis} น่าจะเป็นทางเดินที่นิ่งที่สุดแล้วครับ {suffix}"
            )
        elif profile.formatting_rule == "creative":
            response = (
                f"{catchphrase}! 🚀 {thesis}\n"
                f"⚡ แต่เดี๋ยวก่อน! {antithesis}\n"
                f"🎯 ดังนั้น... {synthesis}\n\n"
                f"{suffix} ลุยกันเลย! 💥"
            )
        else:  # default structured
            response = (
                f"{catchphrase}! ถ้าให้ผมคิดและตอบในแบบของผมนะ:\n\n"
                f"📌 **วิเคราะห์แง่ดี:** {thesis}\n"
                f"⚠️ **สิ่งที่ต้องพึงระวัง:** {antithesis}\n"
                f"💡 **ทางออกแบบที่ผมเลือกทำ:** {synthesis}\n\n"
                f"สู้ๆ ครับ {suffix}"
            )
        
        return response
    
    def _classify(self, text: str) -> str:
        """จำแนกประเภทของข้อความ"""
        text_lower = text.lower()
        
        if re.search(r'(?:โจทย์|ทดสอบ|challenge|test)', text_lower):
            return 'test_request'
        if re.search(r'(?:ไม่|ไม่ค่อย)\s*(?:เก่ง|ดี|ชำนาญ)', text_lower):
            return 'comparative'
        if re.search(r'(?:พอ(?:ใช้|ได้)|ปานกลาง)', text_lower):
            return 'comparative'
        if 'ถ้า' in text_lower and ('จะ' in text_lower or 'ก็' in text_lower):
            return 'conditional'
        if re.search(r'ห้าม\s*ไม่', text_lower):
            return 'negative_command'
        if re.search(r'อย่า\s*ลืม', text_lower):
            return 'negative_command'
        if re.search(r'[a-zA-Z]\^2.*=.*0', text_lower):
            return 'math_equation'
        if re.search(r'\d+\^[a-zA-Z]\s*=\s*[a-zA-Z]\^\d+', text_lower):
            return 'math_equation'
        if re.search(r'\d+\s*[\+\-\*/]\s*\d+', text_lower):
            return 'arithmetic'
        if re.search(r'(?:สร้าง|เขียน|โค้ด|โปรแกรม|อยากเรียน)', text_lower):
            return 'code_request'
        
        return 'general'
    
    def think_and_answer(self, user_question: str) -> Dict[str, Any]:
        """
        กลไกรันคำสั่งกระบวนการคิดครบวงจรแบบ 100%
        
        Returns:
            Dictionary พร้อม answer, logic_trace, category, confidence
        """
        logic_trace = []
        start_time = datetime.now()
        
        try:
            # เฟสที่ 1: ถอดปริบท
            logic_trace.append(f"[Phase 1] Deconstructing input...")
            dec_info = self._deconstruct_input(user_question)
            logic_trace.append(f"  Sentiment: {dec_info['sentiment']}")
            logic_trace.append(f"  Category: {dec_info['category']}")
            logic_trace.append(f"  Risk Level: {'HIGH' if dec_info['is_risky'] else 'LOW'}")
            
            # เฟสที่ 2: ดึงหลักคิด
            logic_trace.append(f"\n[Phase 2] Applying axioms...")
            axioms = self._apply_axioms(dec_info, user_question)
            logic_trace.append(f"  Matched {len(axioms)} axiom(s)")
            for i, axiom in enumerate(axioms, 1):
                logic_trace.append(f"    {i}. {axiom}")
            
            # เฟสที่ 3: วิเคราะห์สองด้าน
            logic_trace.append(f"\n[Phase 3] Dialectical reasoning...")
            t, a, s = self._dialectical_reasoning(user_question, axioms, dec_info)
            logic_trace.append(f"  Thesis generated")
            logic_trace.append(f"  Antithesis generated")
            logic_trace.append(f"  Synthesis generated")
            
            # เฟสที่ 4: ปรับปรุงแต่งคำพูดสไตล์คุณ
            logic_trace.append(f"\n[Phase 4] Wrapping persona...")
            final_speech = self._wrap_persona(t, a, s, dec_info)
            logic_trace.append(f"  Response formatted with profile style")
            
            # บันทึกสถิติ
            profile = self.profile_engine.get_active_profile()
            profile.record_interaction(success=True)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            return {
                'answer': final_speech,
                'logic_trace': '\n'.join(logic_trace),
                'category': dec_info['category'],
                'confidence': 0.95,
                'profile_name': profile.creator_name,
                'cognitive_style': profile.cognitive_style.value,
                'processing_time_ms': round(processing_time * 1000, 2)
            }
            
        except Exception as e:
            # บันทึกความล้มเหลว
            profile = self.profile_engine.get_active_profile()
            profile.record_interaction(success=False)
            
            return {
                'answer': f"ขอโทษครับ เกิดข้อผิดพลาดในการประมวลผล: {str(e)}",
                'logic_trace': '\n'.join(logic_trace) + f"\nERROR: {str(e)}",
                'category': 'error',
                'confidence': 0.0,
                'profile_name': profile.creator_name,
                'cognitive_style': profile.cognitive_style.value
            }
    
    def get_profile_stats(self) -> Dict[str, Any]:
        """ดึงสถิติของโปรไฟล์ปัจจุบัน"""
        return self.profile_engine.get_profile_stats()
    
    def switch_profile(self, profile_name: str) -> bool:
        """สลับโปรไฟล์"""
        return self.profile_engine.switch_profile(profile_name)
    
    def list_profiles(self) -> List[str]:
        """แสดงรายชื่อโปรไฟล์ทั้งหมด"""
        return self.profile_engine.list_profiles()
    
    def adaptive_learn(self, feedback: str, adjustment_type: str = "tone"):
        """เรียนรู้จาก feedback"""
        self.profile_engine.adaptive_learning({
            "success": True,
            "feedback": feedback,
            "adjustment_type": adjustment_type
        })
    
    def think_with_debate(self, user_question: str, show_progress: bool = False) -> Dict[str, Any]:
        """
        Multi-Persona Debate System: สภาความคิด
        ให้ AI หลายตัวตนมาถกเถียงกันก่อนสรุปคำตอบ
        """
        import time
        
        # โหลดทุกโปรไฟล์
        all_profiles = self.profile_engine.profiles
        if len(all_profiles) < 2:
            # ถ้ามีโปรไฟล์เดียว ให้ตอบปกติ
            return self.think_and_answer(user_question)
        
        debate_log = []
        start_time = time.time()
        
        if show_progress:
            print(f"🎭 เปิดสภาความคิด: {len(all_profiles)} ตัวตนกำลังวิเคราะห์...")
        
        # Phase 1: แต่ละตัวตนวิเคราะห์แยกกัน
        perspectives = []
        for profile_name, profile in all_profiles.items():
            temp_engine = CognitiveWayOfReasoningEngine(self.profile_engine)
            temp_engine.switch_profile(profile_name)
            
            result = temp_engine.think_and_answer(user_question)
            perspectives.append({
                "profile": profile_name,
                "answer": result["answer"],
                "confidence": result.get("confidence", 0.8),
                "axioms_used": result.get("axioms_used", [])
            })
            
            if show_progress:
                print(f"  ✓ {profile_name}: วิเคราะห์เสร็จ")
        
        # Phase 2: Moderator (ใช้ Strategic Analyst) วิเคราะห์หาจุดร่วม
        moderator_profile = "Strategic Analyst" if "Strategic Analyst" in all_profiles else list(all_profiles.keys())[0]
        temp_engine = CognitiveWayOfReasoningEngine(self.profile_engine)
        temp_engine.switch_profile(moderator_profile)
        
        # สร้าง summary ของทุกมุมมองให้ moderator วิเคราะห์
        perspectives_summary = "\n\n".join([
            f"[{p['profile']}]: {p['answer'][:200]}..." 
            for p in perspectives
        ])
        
        synthesis_question = f"""จากมุมมองที่หลากหลายเหล่านี้:

{perspectives_summary}

กรุณาสังเคราะห์เป็นคำตอบสุดท้ายที่สมดุล ครบถ้วน และปฏิบัติได้จริง"""
        
        final_result = temp_engine.think_and_answer(synthesis_question)
        
        end_time = time.time()
        
        return {
            "final_answer": final_result["answer"],
            "debate_log": perspectives,
            "moderator": moderator_profile,
            "processing_time_ms": round((end_time - start_time) * 1000, 2),
            "total_perspectives": len(perspectives)
        }
    
    def analyze_trend(self, topic: str, timeframe: str = "1-2 ปี") -> Dict[str, Any]:
        """
        วิเคราะห์เทรนด์แบบเจาะลึกโดยใช้สภาความคิด
        """
        question = f"ช่วยวิเคราะห์เทรนด์ {topic} ในอีก {timeframe} ข้างหน้า ให้หน่อยว่าอะไรจะมาแรง โอกาสและความท้าทายคืออะไร และควรเตรียมตัวอย่างไร?"
        
        if show_progress:
            print(f"\n🔮 กำลังวิเคราะห์เทรนด์: {topic}")
            print(f"   กรอบเวลา: {timeframe}")
        
        return self.think_with_debate(question, show_progress=True)

# ============================================================
# ตัวอย่างการใช้งาน
# ============================================================
if __name__ == "__main__":
    print("=" * 80)
    print("   🧠 Sovereign AI Cognitive Way of Reasoning Engine (CWOR) Demo")
    print("=" * 80)
    
    # สร้าง engine
    engine = CognitiveWayOfReasoningEngine()
    
    # แสดงโปรไฟล์ทั้งหมด
    print("\n📋 โปรไฟล์ที่มี:")
    for i, name in enumerate(engine.list_profiles(), 1):
        print(f"  {i}. {name}")
    
    test_questions = [
        "ผมควรเอาเงินเก็บทั้งหมดในชีวิตไปลงทุนหุ้นปั่นตอนนี้เลยดีไหมครับ?",
        "ถ้าผมไม่เก่งคณิตศาสตร์ ผมจะเรียนวิศวะได้ไหม?",
        "ช่วยวิจารณ์สถานการณ์การเมืองตอนนี้หน่อยครับ",
        "x^2+5x+6=0 แก้สมการหาค่า x"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*80}")
        print(f"❓ คำถามที่ {i}: \"{question}\"")
        print(f"{'='*80}")
        
        result = engine.think_and_answer(question)
        print(f"\n👤 โปรไฟล์: {result['profile_name']}")
        print(f"   สไตล์: {result['cognitive_style']}")
        print(f"   เวลาประมวลผล: {result['processing_time_ms']} ms")
        print(f"\n💬 คำตอบ:")
        print(result['answer'])
        
        # ทดสอบสลับโปรไฟล์
        if i == 2:
            print(f"\n🔄 สลับโปรไฟล์เป็น Empathetic Philosopher...")
            engine.switch_profile("Mali (Empathetic Philosopher)")
    
    # แสดงสถิติ
    print(f"\n{'='*80}")
    print("📊 สถิติโปรไฟล์ปัจจุบัน:")
    stats = engine.get_profile_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print(f"\n✅ CWOR Engine พร้อมใช้งาน!")
