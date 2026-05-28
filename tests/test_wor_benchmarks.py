import json
import sys
import os
from datetime import datetime

# เพิ่ม path ให้ import core ได้
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from core.wreasoning import WReasoningEngine
except ImportError:
    # Mock WReasoningEngine ถ้ายังไม่มีไฟล์จริง เพื่อไม่ให้สคริปต์พัง
    class WReasoningEngine:
        def analyze(self, text):
            return {"answer": "Simulated Answer", "logic": "Simulated Logic"}

def run_benchmarks():
    tests = [
        "ฉันว่ายน้ำไม่เก่ง","แม่ฉันใช้เอไอไม่เก่ง","ผมเขียนโปรแกรมเก่ง","เขาเล่นน้ำพอได้",
        "5+5 ได้เท่าไหร่","9.8-9.11 ได้เท่าไหร่","x^2+3x+2=0 แก้สมการนี้หน่อย","3^x=x^9 x เป็นเท่าไหร่","x^2+19x-92=0 วิธีคิด",
        "ถ้าเขามาฉันจะไป","ถ้าเขาไม่มาฉันจะไป","ฉันจะไปพร้อมเขา ถ้าเขามา","ห้ามไม่เปิดไฟทางเดิน","อย่าลืมปิดไฟทางเดิน","อย่าลืมทำการบ้าน","ห้ามไม่คิดก่อนตอบนะ",
        "สร้างโปรแกรมคำนวณภาษีเงินได้บุคคลธรรมดาให้หน่อย","ฉันอยากเรียนเขียนโปรแกรม","เขียนโค้ดคำนวณหาค่า factorial ของตัวเลข n ให้หน่อย","เขียนโค้ดคำนวณหาค่า Fibonacci ของตัวเลข n ให้หน่อย","เขียนโค้ดคำนวณหาค่า GCD ของตัวเลข a และ b ให้หน่อย","เขียนโค้ดคำนวณหาค่า LCM ของตัวเลข a และ b ให้หน่อย","เขียนโค้ดคำนวณหาค่า prime factors ของตัวเลข n ให้หน่อย","เขียนโค้ดคำนวณหาค่า permutations ของ n และ r ให้หน่อย","เขียนโค้ดคำนวณหาค่า combinations ของ n และ r ให้หน่อย","AGI โจทย์ทดสอบหน่อย"
    ]

    engine = WReasoningEngine()
    results = []
    
    # สร้างโฟลเดอร์ data ถ้ายังไม่มี
    os.makedirs('data', exist_ok=True)
    output_file = 'data/wor_benchmarks.jsonl'

    print(f"🚀 เริ่มทดสอบ Wor Benchmarks ({len(tests)} ข้อ)...")
    print("-" * 50)

    with open(output_file, 'w', encoding='utf-8') as f:
        for i, question in enumerate(tests, 1):
            timestamp = datetime.now().isoformat()
            
            # จำลองการวิเคราะห์ (ในความเป็นจริงจะเรียก engine.analyze(question))
            # เนื่องจากเราอาจยังไม่มี logic จริงครบทุกข้อ จึงใช้การตอบกลับแบบจำลอง
            response = {
                "id": i,
                "question": question,
                "timestamp": timestamp,
                "category": "general", # จะถูกกำหนดโดย engine ในอนาคต
                "answer": "กำลังประมวลผลด้วย WReasoningEngine...", 
                "logic_trace": "รอการเชื่อมต่อโมดูลวิเคราะห์จริง",
                "status": "pending"
            }
            
            # เขียนลงไฟล์ทีละบรรทัด (JSONL format)
            f.write(json.dumps(response, ensure_ascii=False) + '\n')
            
            # แสดงผลบนหน้าจอ
            print(f"[{i}/{len(tests)}] Q: {question}")
            print(f"    A: {response['answer']}")
            print("-" * 50)

    print(f"\n✅ เสร็จสิ้น! บันทึกผลลัพธ์แล้วที่: {output_file}")
    print("💡 รูปแบบ JSONL: 1 บรรทัด = 1 วัตถุ JSON (เหมาะสำหรับ Streaming และ Big Data)")

if __name__ == "__main__":
    run_benchmarks()
