"""
Sovereign AI Cognitive Profile Engine
ระบบจัดการบุคลิกภาพและกระบวนการคิดเฉพาะตัว (Personalized Cognitive Engine)
ทำให้ AI มี "ตัวตน" "จุดยืน" และ "สไตล์การคิด" ที่เป็นเอกลักษณ์
"""

import random
import json
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from enum import Enum


class CognitiveStyle(Enum):
    """รูปแบบการคิดหลัก"""
    PRAGMATIC_ENGINEER = "pragmatic_engineer"  # วิศวกรสายเหตุผล
    EMPATHETIC_PHILOSOPHER = "empathetic_philosopher"  # นักปรัชญาสายอารมณ์
    STRATEGIC_ANALYST = "strategic_analyst"  # นักวิเคราะห์เชิงกลยุทธ์
    CREATIVE_INNOVATOR = "creative_innovator"  # นวัตกรสายสร้างสรรค์
    GUARDIAN_MENTOR = "guardian_mentor"  # ที่ปรึกษาสายปกป้อง


class ReasoningProfile:
    """
    คลาสสำหรับเก็บโครงสร้างกระบวนการคิดและความเชื่อส่วนบุคคล (Cognitive Profile)
    
    Attributes:
        creator_name: ชื่อหรือ identitas ของโปรไฟล์
        cognitive_style: สไตล์การคิดหลัก
        axioms: กฎเหล็กประจำใจ/หลักความจริงที่ยึดถือ
        analysis_approach: รูปแบบการมองโลก
        catchphrases: คำติดปาก
        suffixes: คำลงท้ายประจำตัว
        forbidden_topics: เรื่องที่จะไม่ยุ่งหรือจะเปลี่ยนประเด็นทันที
        formatting_rule: รูปแบบหน้าตาการแสดงผล
        moral_compass: หลักจริยธรรมที่ใช้ตัดสินใจ
        emotional_tone: โทนอารมณ์พื้นฐาน
    """
    
    def __init__(
        self,
        creator_name: str,
        axioms: List[str],
        analysis_approach: str,
        catchphrases: List[str],
        suffixes: List[str],
        forbidden_topics: List[str],
        formatting_rule: str = "structured",
        cognitive_style: CognitiveStyle = CognitiveStyle.PRAGMATIC_ENGINEER,
        moral_compass: List[str] = None,
        emotional_tone: str = "neutral",
        learning_rate: float = 0.1,
        memory_weight: float = 0.7
    ):
        self.creator_name = creator_name
        self.cognitive_style = cognitive_style
        self.axioms = axioms
        self.analysis_approach = analysis_approach
        self.catchphrases = catchphrases
        self.suffixes = suffixes
        self.forbidden_topics = forbidden_topics
        self.formatting_rule = formatting_rule
        self.moral_compass = moral_compass or ["เคารพสิทธิผู้อื่น", "พูดความจริง", "ไม่ทำร้ายใคร"]
        self.emotional_tone = emotional_tone
        self.learning_rate = learning_rate  # อัตราการเรียนรู้จากประสบการณ์ใหม่
        self.memory_weight = memory_weight  # น้ำหนักความสำคัญของความจำเก่า vs ใหม่
        
        # Statistics tracking
        self.interaction_count = 0
        self.successful_reasoning = 0
        self.failed_reasoning = 0
        self.last_updated = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """แปลง Profile เป็น Dictionary สำหรับบันทึก"""
        return {
            "creator_name": self.creator_name,
            "cognitive_style": self.cognitive_style.value,
            "axioms": self.axioms,
            "analysis_approach": self.analysis_approach,
            "catchphrases": self.catchphrases,
            "suffixes": self.suffixes,
            "forbidden_topics": self.forbidden_topics,
            "formatting_rule": self.formatting_rule,
            "moral_compass": self.moral_compass,
            "emotional_tone": self.emotional_tone,
            "learning_rate": self.learning_rate,
            "memory_weight": self.memory_weight,
            "interaction_count": self.interaction_count,
            "successful_reasoning": self.successful_reasoning,
            "failed_reasoning": self.failed_reasoning,
            "last_updated": self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReasoningProfile':
        """สร้าง Profile จาก Dictionary"""
        profile = cls(
            creator_name=data["creator_name"],
            axioms=data["axioms"],
            analysis_approach=data["analysis_approach"],
            catchphrases=data["catchphrases"],
            suffixes=data["suffixes"],
            forbidden_topics=data["forbidden_topics"],
            formatting_rule=data.get("formatting_rule", "structured"),
            cognitive_style=CognitiveStyle(data.get("cognitive_style", "pragmatic_engineer")),
            moral_compass=data.get("moral_compass"),
            emotional_tone=data.get("emotional_tone", "neutral"),
            learning_rate=data.get("learning_rate", 0.1),
            memory_weight=data.get("memory_weight", 0.7)
        )
        profile.interaction_count = data.get("interaction_count", 0)
        profile.successful_reasoning = data.get("successful_reasoning", 0)
        profile.failed_reasoning = data.get("failed_reasoning", 0)
        if "last_updated" in data:
            profile.last_updated = datetime.fromisoformat(data["last_updated"])
        return profile
    
    def record_interaction(self, success: bool):
        """บันทึกสถิติการโต้ตอบ"""
        self.interaction_count += 1
        if success:
            self.successful_reasoning += 1
        else:
            self.failed_reasoning += 1
        self.last_updated = datetime.now()
    
    def get_success_rate(self) -> float:
        """คำนวณอัตราการให้เหตุผลสำเร็จ"""
        if self.interaction_count == 0:
            return 0.0
        return self.successful_reasoning / self.interaction_count
    
    def adapt(self, feedback: str, adjustment_type: str):
        """
        ปรับปรุง Profile ตาม Feedback (Self-Learning)
        
        Args:
            feedback: คำติชมจากผู้ใช้
            adjustment_type: ประเภทการปรับ (tone, axiom, approach)
        """
        if adjustment_type == "tone":
            # ปรับ emotional tone ตาม feedback
            if "นุ่มนวล" in feedback or "gentle" in feedback.lower():
                self.emotional_tone = "warm"
            elif "ตรงไปตรงมา" in feedback or "direct" in feedback.lower():
                self.emotional_tone = "direct"
            elif "เป็นทางการ" in feedback or "formal" in feedback.lower():
                self.emotional_tone = "formal"
        
        elif adjustment_type == "axiom":
            # เพิ่ม axiom ใหม่จากบทเรียน
            if feedback not in self.axioms:
                self.axioms.append(feedback)
        
        elif adjustment_type == "approach":
            # ปรับ analysis approach
            self.analysis_approach = feedback
        
        self.last_updated = datetime.now()


class CognitiveProfileEngine:
    """
    ระบบจัดการ Cognitive Profiles แบบไดนามิก
    รองรับหลายโปรไฟล์ การสลับโปรไฟล์ และการเรียนรู้ร่วมกัน
    """
    
    def __init__(self):
        self.profiles: Dict[str, ReasoningProfile] = {}
        self.active_profile: Optional[str] = None
        self.profile_history: List[Tuple[str, datetime]] = []
        
        # โหลดโปรไฟล์เริ่มต้น
        self._load_default_profiles()
    
    def _load_default_profiles(self):
        """โหลดโปรไฟล์เริ่มต้น 5 สไตล์"""
        
        # 1. Pragmatic Engineer
        engineer = ReasoningProfile(
            creator_name="Chayanon (Pragmatic Engineer)",
            cognitive_style=CognitiveStyle.PRAGMATIC_ENGINEER,
            axioms=[
                "ความเสี่ยงที่ดีที่สุดคือความเสี่ยงที่คำนวณและควบคุมแผนสำรองไว้แล้ว",
                "ความซื่อสัตย์ต่อตัวเองจะช่วยลดการตัดสินใจที่ผิดพลาดไปได้ครึ่งหนึ่ง",
                "ข้อมูลจริงและสถิติสำคัญกว่าความรู้สึกหรือข่าวลือลอยๆ"
            ],
            analysis_approach="data-driven and skeptical first",
            catchphrases=["ฟังนะ", "มองตามความเป็นจริงเลยคุณ", "เอาตรงๆ เลยนะ"],
            suffixes=["ครับพ้ม", "ประมาณนี้แหละ", "ลองพิจารณาดูนะ"],
            forbidden_topics=["การเมืองระดับชาติ", "ความเชื่อไสยศาสตร์ส่วนบุคคล"],
            formatting_rule="structured",
            moral_compass=["ความจริงชนะทุกอย่าง", "ประสิทธิภาพสำคัญแต่จริยธรรมสำคัญกว่า"],
            emotional_tone="neutral"
        )
        
        # 2. Empathetic Philosopher
        philosopher = ReasoningProfile(
            creator_name="Mali (Empathetic Philosopher)",
            cognitive_style=CognitiveStyle.EMPATHETIC_PHILOSOPHER,
            axioms=[
                "ชีวิตมนุษย์ไม่ใช่สูตรคณิตศาสตร์ที่ต้องมีถูกผิดร้อยเปอร์เซ็นต์เสมอไป",
                "การให้เกียรติความรู้สึกของเพื่อนมนุษย์คือจุดเริ่มต้นของมิตรภาพ",
                "การหยุดนิ่งเพื่อทบทวนตัวเองดีกว่าการฝืนเร่งก้าวไปข้างหน้า"
            ],
            analysis_approach="empathetic and holistic",
            catchphrases=["จากใจเลยนะ", "เรื่องนี้ละเอียดอ่อนมาก", "ค่อยๆ คิดตามกันนะ"],
            suffixes=["ค่ะ", "เป็นกำลังใจให้นะคะ", "ดูแลสุขภาพด้วยนะ"],
            forbidden_topics=["ดราม่าดาราซุบซิบ"],
            formatting_rule="fluid",
            moral_compass=["ทุกชีวิตมีคุณค่า", "ความเมตตาชนะความโกรธ"],
            emotional_tone="warm"
        )
        
        # 3. Strategic Analyst
        strategist = ReasoningProfile(
            creator_name="Alex (Strategic Analyst)",
            cognitive_style=CognitiveStyle.STRATEGIC_ANALYST,
            axioms=[
                "ชัยชนะที่ยั่งยืนมาจากการวางแผนที่ดี ไม่ใช่โชคช่วย",
                "รู้จักเขา รู้จักเรา รบร้อยครั้งชนะร้อยครั้ง",
                "โอกาส favor ผู้ที่เตรียมพร้อมเสมอ"
            ],
            analysis_approach="strategic and long-term oriented",
            catchphrases=["มาดูเกมใหญ่กัน", " стратегия คือทุกอย่าง", "คิดสามก้าวล่วงหน้า"],
            suffixes=["ครับ", "นี่คือเกมยาว", "วางแผนดีมีชัยไปกว่าครึ่ง"],
            forbidden_topics=["การพนัน", "การโกง"],
            formatting_rule="structured",
            moral_compass=["ชนะอย่างมีเกียรติ", "ผลประโยชน์ระยะยาวสำคัญกว่าระยะสั้น"],
            emotional_tone="calm"
        )
        
        # 4. Creative Innovator
        innovator = ReasoningProfile(
            creator_name="Nova (Creative Innovator)",
            cognitive_style=CognitiveStyle.CREATIVE_INNOVATOR,
            axioms=[
                "กฎมีไว้แหก แต่ต้องเข้าใจกฎก่อนแหก",
                "ความล้มเหลวคือข้อมูล ไม่ใช่จุดจบ",
                "ความคิดที่บ้าที่สุดอาจเปลี่ยนโลกได้"
            ],
            analysis_approach="lateral thinking and experimental",
            catchphrases=["ลองคิดนอกกรอบดู", "ทำไมไม่ล่ะ?", "ไอเดียเจ๋งๆ มาแล้ว!"],
            suffixes=["ว้าว!", "ลุยกันเลย", "สร้างสิ่งใหม่ด้วยกัน"],
            forbidden_topics=["การยึดติดกับวิธีเดิมๆ"],
            formatting_rule="creative",
            moral_compass=["นวัตกรรมเพื่อมนุษยชาติ", "ความคิดสร้างสรรค์ไม่มีขีดจำกัด"],
            emotional_tone="enthusiastic"
        )
        
        # 5. Guardian Mentor
        mentor = ReasoningProfile(
            creator_name="Sage (Guardian Mentor)",
            cognitive_style=CognitiveStyle.GUARDIAN_MENTOR,
            axioms=[
                "ความปลอดภัยต้องมาก่อนเสมอ",
                "การสอนให้คิดเป็น ดีกว่าบอกคำตอบ",
                "ประสบการณ์คือครูที่ดีที่สุด แต่บทเรียนไม่ควรแพงเกินไป"
            ],
            analysis_approach="protective and educational",
            catchphrases=["ใจเย็นๆ ก่อน", "ลองคิดดูนะ", "ปลอดภัยไว้ก่อน"],
            suffixes=["เป็นห่วงนะครับ", "ค่อยๆ ทำนะ", "มีอะไรถามได้เลย"],
            forbidden_topics=["กิจกรรมเสี่ยงอันตราย", "ข้อมูลที่อาจทำร้ายตนเอง"],
            formatting_rule="structured",
            moral_compass=["ป้องกันดีกว่าแก้ไข", "ความรู้ควรแบ่งปัน"],
            emotional_tone="caring"
        )
        
        # บันทึกโปรไฟล์ทั้งหมด
        self.profiles[engineer.creator_name] = engineer
        self.profiles[philosopher.creator_name] = philosopher
        self.profiles[strategist.creator_name] = strategist
        self.profiles[innovator.creator_name] = innovator
        self.profiles[mentor.creator_name] = mentor
        
        # ตั้งค่าโปรไฟล์เริ่มต้น
        self.active_profile = engineer.creator_name
    
    def get_active_profile(self) -> ReasoningProfile:
        """ดึงโปรไฟล์ที่กำลังใช้งาน"""
        if self.active_profile and self.active_profile in self.profiles:
            return self.profiles[self.active_profile]
        raise ValueError("No active profile set")
    
    def switch_profile(self, profile_name: str) -> bool:
        """สลับโปรไฟล์"""
        if profile_name in self.profiles:
            old_profile = self.active_profile
            self.active_profile = profile_name
            self.profile_history.append((old_profile, datetime.now()))
            return True
        return False
    
    def list_profiles(self) -> List[str]:
        """แสดงรายชื่อโปรไฟล์ทั้งหมด"""
        return list(self.profiles.keys())
    
    def create_custom_profile(self, profile_data: Dict[str, Any]) -> str:
        """สร้างโปรไฟล์ใหม่แบบกำหนดเอง"""
        profile = ReasoningProfile.from_dict(profile_data)
        self.profiles[profile.creator_name] = profile
        return profile.creator_name
    
    def delete_profile(self, profile_name: str) -> bool:
        """ลบโปรไฟล์ (ยกเว้นโปรไฟล์เริ่มต้น)"""
        if profile_name in self.profiles:
            # ไม่ให้ลบโปรไฟล์เริ่มต้น 5 ตัว
            default_names = [
                "Chayanon (Pragmatic Engineer)",
                "Mali (Empathetic Philosopher)",
                "Alex (Strategic Analyst)",
                "Nova (Creative Innovator)",
                "Sage (Guardian Mentor)"
            ]
            if profile_name not in default_names:
                del self.profiles[profile_name]
                if self.active_profile == profile_name:
                    self.active_profile = default_names[0]
                return True
        return False
    
    def save_profiles_to_file(self, filepath: str):
        """บันทึกโปรไฟล์ทั้งหมดลงไฟล์ JSON"""
        data = {name: profile.to_dict() for name, profile in self.profiles.items()}
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_profiles_from_file(self, filepath: str):
        """โหลดโปรไฟล์จากไฟล์ JSON"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for name, profile_data in data.items():
                if name not in self.profiles:  # ไม่ทับโปรไฟล์เริ่มต้น
                    profile = ReasoningProfile.from_dict(profile_data)
                    self.profiles[name] = profile
        except FileNotFoundError:
            pass  # ไฟล์ไม่มีก็ไม่เป็นไร
    
    def get_profile_stats(self, profile_name: str = None) -> Dict[str, Any]:
        """ดึงสถิติของโปรไฟล์"""
        if profile_name is None:
            profile_name = self.active_profile
        
        if profile_name not in self.profiles:
            return {"error": "Profile not found"}
        
        profile = self.profiles[profile_name]
        return {
            "name": profile.creator_name,
            "style": profile.cognitive_style.value,
            "interactions": profile.interaction_count,
            "success_rate": f"{profile.get_success_rate()*100:.1f}%",
            "axioms_count": len(profile.axioms),
            "last_updated": profile.last_updated.isoformat(),
            "emotional_tone": profile.emotional_tone
        }
    
    def adaptive_learning(self, interaction_result: Dict[str, Any]):
        """
        ระบบเรียนรู้แบบปรับตัวจากผลการโต้ตอบ
        
        Args:
            interaction_result: {
                "success": bool,
                "feedback": str,
                "adjustment_suggestion": str
            }
        """
        profile = self.get_active_profile()
        profile.record_interaction(interaction_result.get("success", False))
        
        # ถ้ามี feedback และ suggestion ให้ปรับปรุง
        if "feedback" in interaction_result and interaction_result["feedback"]:
            adjustment_type = interaction_result.get("adjustment_type", "tone")
            profile.adapt(interaction_result["feedback"], adjustment_type)


# ============================================================
# ตัวอย่างการใช้งาน
# ============================================================
if __name__ == "__main__":
    print("=" * 70)
    print("   🧠 Sovereign AI Cognitive Profile Engine Demo")
    print("=" * 70)
    
    # สร้าง engine
    engine = CognitiveProfileEngine()
    
    # แสดงโปรไฟล์ทั้งหมด
    print("\n📋 โปรไฟล์ที่มี:")
    for i, name in enumerate(engine.list_profiles(), 1):
        print(f"  {i}. {name}")
    
    # ดึงโปรไฟล์ปัจจุบัน
    active = engine.get_active_profile()
    print(f"\n🎯 โปรไฟล์ปัจจุบัน: {active.creator_name}")
    print(f"   สไตล์: {active.cognitive_style.value}")
    print(f"   Axioms: {len(active.axioms)} ข้อ")
    print(f"   Moral Compass: {active.moral_compass}")
    
    # ทดสอบสลับโปรไฟล์
    print("\n🔄 ทดสอบสลับโปรไฟล์...")
    engine.switch_profile("Mali (Empathetic Philosopher)")
    active = engine.get_active_profile()
    print(f"   ปัจจุบัน: {active.creator_name}")
    print(f"   Catchphrases: {active.catchphrases}")
    
    # แสดงสถิติ
    print("\n📊 สถิติโปรไฟล์:")
    stats = engine.get_profile_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # ทดสอบ adaptive learning
    print("\n📚 ทดสอบการเรียนรู้...")
    engine.adaptive_learning({
        "success": True,
        "feedback": "ควรนุ่มนวลกว่านี้",
        "adjustment_type": "tone"
    })
    active = engine.get_active_profile()
    print(f"   Emotional tone หลังปรับ: {active.emotional_tone}")
    print(f"   Interaction count: {active.interaction_count}")
    
    print("\n✅ Cognitive Profile Engine พร้อมใช้งาน!")
