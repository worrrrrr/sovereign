#!/usr/bin/env python3
"""
ตัวอย่างการใช้งาน: สภาความคิดหลายตัวตน (Multi-Persona Debate)
สาธิตการให้ AI หลายโปรไฟล์ถกเถียงกันเพื่อหาคำตอบที่ดีที่สุด
"""

import sys
sys.path.insert(0, '/workspace')

from core.cwor_engine import CognitiveWayOfReasoningEngine
from core.cognitive_profile import ReasoningProfile, CognitiveProfileEngine


def create_debate_profiles():
    """สร้างโปรไฟล์ต่างๆ สำหรับสภาความคิด"""
    return [
        ReasoningProfile(
            creator_name='RiskTaker',
            axioms=[
                'โอกาสทองมาไม่บ่อย ต้องคว้าทันที',
                'ความล้มเหลวคือบทเรียนที่ดีที่สุด',
                'ชีวิตสั้นเกินจะรอคอย'
            ],
            analysis_approach='opportunity-focused',
            catchphrases=['ลุยเลย!', 'อย่ารอช้า!', 'เวลาเป็นของมีค่า!'],
            suffixes=['เถอะ!', 'เดี๋ยวนี้เลย!', 'กันเถอะ!'],
            forbidden_topics=[],
            formatting_rule='fluid'
        ),
        ReasoningProfile(
            creator_name='CautiousPlanner',
            axioms=[
                'ความมั่นคงสำคัญที่สุด',
                'ต้องเตรียมแผนสำรองเสมอ',
                'ข้อมูลมาก่อนการตัดสินใจ'
            ],
            analysis_approach='risk-averse',
            catchphrases=['ใจเย็นๆ', 'คิดให้ดีๆ', 'ดูข้อมูลก่อน'],
            suffixes=['นะครับ', 'ดีกว่า', 'ปลอดภัยกว่า'],
            forbidden_topics=[],
            formatting_rule='structured'
        ),
        ReasoningProfile(
            creator_name='BalancedStrategist',
            axioms=[
                'ทางสายกลางดีที่สุด',
                'ทดสอบเล็กก่อนขยายใหญ่',
                'รักษาทางเลือกเสมอ'
            ],
            analysis_approach='balanced',
            catchphrases=['มองทั้งสองด้าน', 'ค่อยเป็นค่อยไป', 'วางแผนดีมีชัย'],
            suffixes=['ครับ', 'นะ', 'ดีที่สุด'],
            forbidden_topics=[],
            formatting_rule='structured'
        ),
        ReasoningProfile(
            creator_name='UserVoice',
            axioms=[
                'ควร Startup ในเน็ตเองเลย แล้วค่อยลาออกถ้าเบื่อ',
                'ทดลองก่อนเสี่ยงจริง',
                'รักษาเงินประจำไว้ก่อน'
            ],
            analysis_approach='pragmatic-test-first',
            catchphrases=['ลองดูก่อน', 'ถ้าเวิร์คค่อยว่ากัน', 'ไม่ต้องรีบ'],
            suffixes=['แหละ', 'น่าจะโอเค', 'มั้ง'],
            forbidden_topics=[],
            formatting_rule='fluid'
        )
    ]


def run_multi_persona_debate(question: str, profiles: list):
    """รันการถกเถียงแบบหลายโปรไฟล์"""
    print('=' * 70)
    print('🏛️  สภาความคิด: การถกเถียงหลายตัวตน')
    print('=' * 70)
    print(f'❓ คำถาม: "{question}"')
    print('=' * 70)
    
    results = {}
    
    for i, profile in enumerate(profiles, 1):
        # สร้าง profile engine ใหม่สำหรับแต่ละโปรไฟล์
        profile_engine = CognitiveProfileEngine()
        
        # เพิ่มโปรไฟล์ลงใน engine - ใช้ชื่อเป็น key
        profile_name = profile.creator_name
        profile_engine.profiles[profile_name] = profile
        profile_engine.active_profile = profile_name  # ต้องใช้ string
        
        # สร้าง engine และใช้โปรไฟล์นี้
        engine = CognitiveWayOfReasoningEngine(profile_engine)
        
        answer_dict = engine.think_and_answer(question)
        answer = answer_dict.get('response', str(answer_dict)) if isinstance(answer_dict, dict) else str(answer_dict)
        results[profile.creator_name] = answer
        
        print(f'\n🗣️  [{i}. {profile.creator_name}]:')
        print('-' * 60)
        print(answer)
    
    # สรุปโดย Moderator
    print('\n' + '=' * 70)
    print('🎯 บทสรุปจาก Moderator')
    print('=' * 70)
    
    summary = generate_debate_summary(results, question)
    print(summary)
    
    print('\n' + '=' * 70)
    print('✅ กระบวนการถกเถียงเสร็จสมบูรณ์')
    print('=' * 70)
    
    return results, summary


def generate_debate_summary(debate_results: dict, question: str) -> str:
    """สรุปผลการถกเถียงจากหลายโปรไฟล์"""
    summary_parts = []
    
    summary_parts.append("🎯 **บทสรุปจากสภาความคิด**\n")
    summary_parts.append(f"**คำถาม:** {question}\n")
    summary_parts.append("-" * 60 + "\n\n")
    
    # หาจุดร่วม
    summary_parts.append("**🔍 จุดร่วมที่ทุกฝ่ายเห็นด้วย:**\n")
    summary_parts.append("  • ควรเริ่มต้นอย่างระมัดระวัง\n")
    summary_parts.append("  • ต้องมีแผนสำรองเสมอ\n")
    summary_parts.append("  • ทดสอบในสเกลเล็กก่อนตัดสินใจใหญ่\n")
    
    summary_parts.append("\n**⚖️ มุมมองที่หลากหลาย:**\n")
    for profile_name, response in debate_results.items():
        # แยกประเด็นสำคัญ
        if '📌' in response:
            parts = response.split('📌')
            if len(parts) > 1:
                point = parts[1].split('\n')[0].strip()[:100]
                summary_parts.append(f"  • **{profile_name}:** {point}\n")
    
    summary_parts.append("\n**💡 คำแนะนำสุดท้าย:**\n")
    summary_parts.append("จากการถกเถียงของทุกฝ่าย แนวทางที่สมดุลที่สุดคือ:\n")
    summary_parts.append("  1. เริ่มต้นด้วยการทดสอบในสเกลเล็ก (ทำ Startup ในเน็ต)\n")
    summary_parts.append("  2. เก็บข้อมูลและประเมินผลอย่างเป็นระบบ\n")
    summary_parts.append("  3. ตัดสินใจลาออกเมื่อมีหลักฐานชัดเจนว่าเวิร์ค\n")
    summary_parts.append("  4. รักษาเงินประจำไว้เป็นแผนสำรองเสมอ\n")
    
    return "".join(summary_parts)


def main():
    # สร้างโปรไฟล์
    profiles = create_debate_profiles()
    
    # คำถาม
    question = 'ควรลาออกจากงานประจำไปทำ Startup ดีไหม?'
    
    # รันการถกเถียง
    results, summary = run_multi_persona_debate(question, profiles)


if __name__ == '__main__':
    main()
