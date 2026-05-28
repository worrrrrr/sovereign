#!/usr/bin/env python3
"""
Sovereign AI - Main CLI Entry Point
-----------------------------------
ใช้งาน: python main.py "ข้อความของคุณ"
"""

import sys
import logging
from core.orchestrator import get_orchestrator

# ตั้งค่า Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

def main():
    if len(sys.argv) < 2:
        print("🤖 Sovereign AI - ระบบประมวลผลอัจฉริยะ")
        print("=" * 50)
        print("วิธีใช้: python main.py \"ข้อความของคุณ\"")
        print("\nตัวอย่าง:")
        print('  python main.py "9.8-9.11 ได้เท่าไร"')
        print('  python main.py "ซื้อของ 19 บาท ต้องเตรียมเงินยังไง"')
        print('  python main.py "สวัสดี"')
        print('  python main.py "เล่ามุกตลกให้ฟังหน่อย"')
        sys.exit(0)
    
    # รวมข้อความทั้งหมดจาก arguments (รองรับช่องว่าง)
    user_input = " ".join(sys.argv[1:])
    
    try:
        # ดึง Orchestrator instance
        orchestrator = get_orchestrator()
        
        # ประมวลผล
        response = orchestrator.process(user_input)
        
        # แสดงผลลัพธ์
        print("\n" + "=" * 50)
        if response.success:
            print(f"🎯 เจตนา: {response.intent_id}")
            print("-" * 50)
            print(response.response_text)
        else:
            print(f"❌ เกิดข้อผิดพลาด: {response.error_message}")
            print(response.response_text)
        print("=" * 50)
        
    except Exception as e:
        print(f"💥 ระบบเกิดข้อผิดพลาดร้ายแรง: {e}")
        logging.exception(e)
        sys.exit(1)

if __name__ == "__main__":
    main()
