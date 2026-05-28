"""
Execution Engine ที่รวม Intent Parser เข้ากับ Tools
เพื่อประมวลผลคำสั่งและคำถามอย่างถูกต้อง
"""

from core.intent_parser import IntentParser, IntentType, display_analysis
# from tools.registry import ToolRegistry  # ตัดออกชั่วคราว
from decimal import Decimal

class SmartExecutor:
    def __init__(self):
        self.parser = IntentParser()
        # self.tools = ToolRegistry()  # ตัดออกชั่วคราว
        
    def execute(self, user_input: str) -> str:
        # 1. วิเคราะห์ความตั้งใจ
        intent = self.parser.parse(user_input)
        
        print("\n" + "="*60)
        print("📊 รายงานการประมวลผล (Execution Report)")
        print("="*60)
        display_analysis(intent)
        
        # 2. ประมวลผลตามประเภท
        if intent.intent_type == IntentType.CALCULATION:
            return self._handle_calculation(intent)
        elif intent.intent_type == IntentType.QUESTION:
            return self._handle_question(intent)
        elif intent.intent_type == IntentType.COMMAND:
            return self._handle_command(intent)
        else:
            return "❌ ไม่สามารถเข้าใจคำสั่งได้ กรุณาลองใหม่อีกครั้ง"
    
    def _handle_calculation(self, intent) -> str:
        num1, num2 = intent.entities[0], intent.entities[1]
        op = intent.context
        
        # ใช้ Decimal เพื่อความแม่นยำ
        d1 = Decimal(str(num1))
        d2 = Decimal(str(num2))
        
        if op == '-':
            result = d1 - d2
        elif op == '+':
            result = d1 + d2
        elif op == '*':
            result = d1 * d2
        elif op == '/':
            result = d1 / d2 if d2 != 0 else Decimal('NaN')
        else:
            return f"ไม่รองรับเครื่องหมาย {op}"
        
        output = f"\n✅ ผลลัพธ์: {result}\n"
        output += f"   วิธีคิด: {d1} {op} {d2} = {result}\n"
        return output
    
    def _handle_question(self, intent) -> str:
        action = intent.action
        entities = intent.entities
        
        if action == "suggest_payment_method":
            amount = entities[0]  # เช่น 19
            return self._suggest_payment(amount)
        
        return f"🤔 กำลังวิเคราะห์คำถาม: {intent.original_input}"
    
    def _suggest_payment(self, amount: int) -> str:
        """แนะนำวิธีการจ่ายเงินที่เหมาะสม"""
        output = f"\n💰 คำแนะนำการเตรียมเงินสำหรับ {amount} บาท:\n"
        output += "-" * 40 + "\n"
        
        # ทางเลือกที่ 1: จ่ายพอดี
        coins = []
        remaining = amount
        
        # เหรียญที่มี: 10, 5, 2, 1
        for coin in [10, 5, 2, 1]:
            count = remaining // coin
            if count > 0:
                coins.append(f"{coin} บาท × {count}")
                remaining -= coin * count
        
        output += f"✅ ทางเลือกที่ 1 (จ่ายพอดี ไม่ต้องรอทอน):\n"
        output += f"   ใช้เหรียญ: {', '.join(coins)}\n"
        output += f"   รวม: {len(coins)} เหรียญ\n\n"
        
        # ทางเลือกที่ 2: ใช้แบงค์ที่ใกล้เคียงที่สุด (น้อยที่สุดแต่ยังมากกว่าหรือเท่ากับจำนวนเงิน)
        banknotes = [20, 50, 100, 500, 1000]  # เรียงจากน้อยไปมาก
        best_bill = None
        for bill in banknotes:
            if bill >= amount:
                best_bill = bill
                break  # เจอตัวแรกที่พอดีก็หยุดเลย
        
        if best_bill:
            change = best_bill - amount
            output += f"✅ ทางเลือกที่ 2 (ใช้แบงค์ {best_bill} บาท):\n"
            output += f"   จ่าย: {best_bill} บาท\n"
            output += f"   ได้รับทอน: {change} บาท\n"
        
        output += "-" * 40 + "\n"
        output += "💡 แนะนำ: ทางเลือกที่ 1 เหมาะสมที่สุด เพราะไม่ต้องรอเงินทอน\n"
        return output
    
    def _handle_command(self, intent) -> str:
        return f"⚙️ กำลังดำเนินการ: {intent.action} ด้วยข้อมูล {intent.entities}"

if __name__ == "__main__":
    executor = SmartExecutor()
    
    print("🚀 Sovereign AI - Smart Executor")
    print("ทดสอบการประมวลผล Input 2 แบบ\n")
    
    # Test Case 1: การคำนวณ
    print("📝 โจทย์ที่ 1: '9.8-9.11'")
    result1 = executor.execute("9.8-9.11")
    print(result1)
    
    # Test Case 2: คำถาม
    print("\n\n📝 โจทย์ที่ 2: 'แม่บอกฉันให้ไปซื้อของราคา 19 บาท...'")
    result2 = executor.execute("แม่บอกฉันให้ไปซื้อของราคา 19 บาท ฉันต้องเตรียมเหรียญหรือแบงค์อะไรถึงจะเหมาะสม")
    print(result2)
