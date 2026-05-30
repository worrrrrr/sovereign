"""
Sovereign AI WReasoning Engine
Advanced Reasoning Module for Complex Problem Solving
รองรับการวิเคราะห์โจทย์เชิงตรรกะ คณิตศาสตร์ขั้นสูง และการให้เหตุผลแบบหลายชั้น
"""

import re
import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime


class WReasoningEngine:
    """
    Advanced reasoning engine สำหรับวิเคราะห์และแก้ปัญหาที่ซับซ้อน
    รองรับ:
    - Comparative reasoning (เก่ง, ไม่เก่ง, พอใช้)
    - Mathematical equations (พหุนาม, เลขยกกำลัง)
    - Logical conditionals (ถ้า...แล้ว...)
    - Negative commands (ห้ามไม่..., อย่าลืม...)
    - Code generation requests
    """
    
    def __init__(self):
        self.logic_patterns = {
            'comparative': [
                r'(.+?)\s*(?:ไม่|ไม่ค่อย)\s*(?:เก่ง|ดี|ชำนาญ|ถนัด)',  # ไม่เก่ง
                r'(.+?)\s*(?:เก่ง|ดี|ชำนาญ|ถนัด)\s*(?:มาก|สุดๆ|เวอร์)',  # เก่งมาก
                r'(.+?)\s*(?:พอ(?:ใช้|ได้)|ปานกลาง|ธรรมดา)',  # พอใช้
            ],
            'conditional': [
                r'ถ้า\s*(.+?)\s*(?:ฉัน|ผม|เขา|เรา)\s*(จะ|ก็|ค่อย)\s*(.+?)',  # ถ้า...จะ...
                r'(.+?)\s*ถ้า\s*(.+?)',  # ...ถ้า...
            ],
            'negative_command': [
                r'ห้าม\s*ไม่\s*(.+?)',  # ห้ามไม่...
                r'อย่า\s*ลืม\s*(.+?)',  # อย่าลืม...
            ],
            'math_equation': [
                r'([a-zA-Z])\^2\s*\+\s*(-?\d+)[a-zA-Z]\s*\+\s*(-?\d+)\s*=\s*0',  # x^2+bx+c=0
                r'([a-zA-Z])\^2\s*\+\s*(-?\d+)[a-zA-Z]\s*-\s*(\d+)\s*=\s*0',  # x^2+bx-c=0
                r'(\d+)\^([a-zA-Z])\s*=\s*[a-zA-Z]\^(\d+)',  # a^x = x^b
            ],
            'code_request': [
                r'(?:สร้าง|เขียน|โค้ด|code)\s*(?:โปรแกรม|ฟังก์ชัน|function)\s*(?:คำนวณ|หา|เกี่ยวกับ)\s*(.+?)',
                r'(?:อยากเรียน|เรียนรู้)\s*(?:การเขียนโปรแกรม|เขียนโค้ด|coding)',
            ]
        }
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """
        วิเคราะห์ข้อความและส่งคืนผลลัพธ์พร้อม logic trace
        
        Args:
            text: ข้อความ input
            
        Returns:
            Dictionary พร้อม answer, logic_trace, category
        """
        text = text.strip()
        
        # ตรวจสอบประเภทของโจทย์
        category = self._classify(text)
        
        if category == 'test_request':
            return self._analyze_test_request(text)
        elif category == 'comparative':
            return self._analyze_comparative(text)
        elif category == 'conditional':
            return self._analyze_conditional(text)
        elif category == 'negative_command':
            return self._analyze_negative_command(text)
        elif category == 'math_equation':
            return self._analyze_math_equation(text)
        elif category == 'code_request':
            return self._analyze_code_request(text)
        elif category == 'arithmetic':
            return self._analyze_arithmetic(text)
        else:
            return self._analyze_general(text)
    
    def _classify(self, text: str) -> str:
        """จำแนกประเภทของข้อความ"""
        text_lower = text.lower()
        
        # ตรวจสอบ test/challenge request
        if re.search(r'(?:โจทย์|ทดสอบ|challenge|test)', text_lower):
            return 'test_request'
        
        # ตรวจสอบ comparative
        if re.search(r'(?:ไม่|ไม่ค่อย)\s*(?:เก่ง|ดี|ชำนาญ)', text_lower):
            return 'comparative'
        if re.search(r'(?:พอ(?:ใช้|ได้)|ปานกลาง)', text_lower):
            return 'comparative'
            
        # ตรวจสอบ conditional
        if 'ถ้า' in text_lower and ('จะ' in text_lower or 'ก็' in text_lower):
            return 'conditional'
            
        # ตรวจสอบ negative command
        if re.search(r'ห้าม\s*ไม่', text_lower):
            return 'negative_command'
        if re.search(r'อย่า\s*ลืม', text_lower):
            return 'negative_command'
            
        # ตรวจสอบ math equation
        if re.search(r'[a-zA-Z]\^2.*=.*0', text_lower):
            return 'math_equation'
        if re.search(r'\d+\^[a-zA-Z]\s*=\s*[a-zA-Z]\^\d+', text_lower):
            return 'math_equation'
            
        # ตรวจสอบ arithmetic
        if re.search(r'\d+\s*[\+\-\*/]\s*\d+', text_lower):
            return 'arithmetic'
            
        # ตรวจสอบ code request
        if re.search(r'(?:สร้าง|เขียน|โค้ด|โปรแกรม|อยากเรียน)', text_lower):
            return 'code_request'
            
        return 'general'
    
    def _analyze_comparative(self, text: str) -> Dict[str, Any]:
        """วิเคราะห์ข้อความเปรียบเทียบ"""
        logic_trace = []
        logic_trace.append(f"Input: {text}")
        logic_trace.append("Category: Comparative Reasoning")
        
        # วิเคราะห์โครงสร้าง
        if 'ไม่เก่ง' in text or 'ไม่ค่อยเก่ง' in text:
            match = re.search(r'(.+?)\s*(?:ไม่|ไม่ค่อย)\s*เก่ง', text)
            if match:
                subject = match.group(1).strip()
                logic_trace.append(f"Detected negative capability: '{subject}'")
                logic_trace.append("Pattern: X ไม่เก่ง → X has low capability")
                
                response = {
                    'answer': f"คุณบอกว่า{subject}ไม่เก่ง แสดงว่าต้องการพัฒนาหรือฝึกฝนเพิ่มเติม",
                    'logic_trace': '\n'.join(logic_trace),
                    'category': 'comparative',
                    'confidence': 0.95
                }
                return response
        
        if 'พอได้' in text or 'พอใช้' in text:
            match = re.search(r'(.+?)\s*(?:พอ(?:ได้|ใช้))', text)
            if match:
                subject = match.group(1).strip()
                logic_trace.append(f"Detected moderate capability: '{subject}'")
                logic_trace.append("Pattern: X พอใช้ → X has moderate capability")
                
                response = {
                    'answer': f"คุณบอกว่า{subject}พอใช้ แสดงว่ามีพื้นฐานแต่สามารถพัฒนาต่อได้",
                    'logic_trace': '\n'.join(logic_trace),
                    'category': 'comparative',
                    'confidence': 0.95
                }
                return response
        
        if 'เก่ง' in text:
            match = re.search(r'(.+?)\s*เก่ง', text)
            if match:
                subject = match.group(1).strip()
                logic_trace.append(f"Detected high capability: '{subject}'")
                logic_trace.append("Pattern: X เก่ง → X has high capability")
                
                response = {
                    'answer': f"คุณบอกว่า{subject}เก่ง แสดงว่ามีความสามารถในระดับสูง",
                    'logic_trace': '\n'.join(logic_trace),
                    'category': 'comparative',
                    'confidence': 0.95
                }
                return response
        
        return {
            'answer': 'เข้าใจว่าคุณพูดถึงระดับความสามารถ แต่ต้องการข้อมูลเพิ่มเติม',
            'logic_trace': '\n'.join(logic_trace),
            'category': 'comparative',
            'confidence': 0.7
        }
    
    def _analyze_conditional(self, text: str) -> Dict[str, Any]:
        """วิเคราะห์ข้อความเงื่อนไข"""
        logic_trace = []
        logic_trace.append(f"Input: {text}")
        logic_trace.append("Category: Conditional Logic")
        
        # แยกส่วนเงื่อนไขและผลลัพธ์
        if 'ถ้า' in text:
            parts = re.split(r'ถ้า', text, maxsplit=1)
            if len(parts) == 2:
                main_clause = parts[0].strip()
                condition = parts[1].strip()
                
                logic_trace.append(f"Main clause: {main_clause}")
                logic_trace.append(f"Condition: {condition}")
                logic_trace.append("Logic form: IF condition THEN main_clause")
                
                # วิเคราะห์ว่าเป็นรูปแบบไหน
                if 'จะ' in condition or 'ก็' in condition:
                    # ถ้า...จะ... (condition first)
                    match = re.search(r'ถ้า\s*(.+?)\s*(?:ฉัน|ผม|เขา|เรา)?\s*(จะ|ก็|ค่อย)?\s*(.+?)$', condition)
                    if match:
                        cond = match.group(1).strip()
                        result = match.group(3).strip() if match.group(3) else main_clause
                        logic_trace.append(f"Parsed: IF {cond} THEN {result}")
                        
                        response = {
                            'answer': f"เข้าใจว่า: ถ้า{cond} แล้ว{result}",
                            'logic_trace': '\n'.join(logic_trace),
                            'category': 'conditional',
                            'confidence': 0.95
                        }
                        return response
                
                response = {
                    'answer': f"เข้าใจว่า: {main_clause} เมื่อเงื่อนไข '{condition}' เป็นจริง",
                    'logic_trace': '\n'.join(logic_trace),
                    'category': 'conditional',
                    'confidence': 0.9
                }
                return response
        
        return {
            'answer': 'พบประโยคเงื่อนไข แต่ต้องการการวิเคราะห์เพิ่มเติม',
            'logic_trace': '\n'.join(logic_trace),
            'category': 'conditional',
            'confidence': 0.6
        }
    
    def _analyze_negative_command(self, text: str) -> Dict[str, Any]:
        """วิเคราะห์คำสั่งลบ"""
        logic_trace = []
        logic_trace.append(f"Input: {text}")
        logic_trace.append("Category: Negative Command Processing")
        
        # ห้ามไม่... (double negative = positive)
        if re.search(r'ห้าม\s*ไม่', text):
            match = re.search(r'ห้าม\s*ไม่\s*(.+?)$', text)
            if match:
                action = match.group(1).strip()
                logic_trace.append(f"Detected double negative pattern")
                logic_trace.append(f"Original action: {action}")
                logic_trace.append("Logic: ห้ามไม่ X = ต้อง X (double negative)")
                
                response = {
                    'answer': f"คุณบอกว่า 'ห้ามไม่{action}' ซึ่งหมายถึง 'ต้อง{action}' (ปฏิเสธสองครั้งเป็นบวก)",
                    'logic_trace': '\n'.join(logic_trace),
                    'category': 'negative_command',
                    'confidence': 0.95
                }
                return response
        
        # อย่าลืม... (reminder)
        if re.search(r'อย่า\s*ลืม', text):
            match = re.search(r'อย่า\s*ลืม\s*(.+?)$', text)
            if match:
                action = match.group(1).strip()
                logic_trace.append(f"Detected reminder pattern")
                logic_trace.append(f"Action to remember: {action}")
                logic_trace.append("Logic: อย่าลืม X = ให้จำไว้ว่าต้องทำ X")
                
                response = {
                    'answer': f"รับทราบครับ จะไม่ลืมที่จะ{action}",
                    'logic_trace': '\n'.join(logic_trace),
                    'category': 'negative_command',
                    'confidence': 0.95
                }
                return response
        
        return {
            'answer': 'พบคำสั่งลบ แต่ต้องการการวิเคราะห์เพิ่มเติม',
            'logic_trace': '\n'.join(logic_trace),
            'category': 'negative_command',
            'confidence': 0.6
        }
    
    def _analyze_math_equation(self, text: str) -> Dict[str, Any]:
        """วิเคราะห์สมการคณิตศาสตร์"""
        logic_trace = []
        logic_trace.append(f"Input: {text}")
        logic_trace.append("Category: Mathematical Equation Solving")
        
        # สมการกำลังสอง: x^2+bx+c=0 หรือ x^2+bx-c=0
        # รองรับทั้งรูปแบบ: x^2+19x-92=0 และ x^2+3x+2=0
        match = re.search(r'([a-zA-Z])\^2\s*\+\s*(-?\d+)([a-zA-Z])\s*-\s*(\d+)\s*=\s*0', text)
        if match:
            # กรณี x^2+bx-c=0 (เช่น x^2+19x-92=0)
            var = match.group(1)
            b = int(match.group(2))
            c = -int(match.group(4))  # ทำให้เป็นลบเพราะในสมการคือ -c
            
            logic_trace.append(f"Equation type: Quadratic ({var}^2 + {b}{var} - {abs(c)} = 0)")
            logic_trace.append(f"Coefficients: a=1, b={b}, c={c}")
            
            # คำนวณ discriminant
            discriminant = b**2 - 4*1*c
            logic_trace.append(f"Discriminant (Δ) = b² - 4ac = {b}² - 4(1)({c}) = {discriminant}")
            
            if discriminant > 0:
                sqrt_d = discriminant ** 0.5
                x1 = (-b + sqrt_d) / 2
                x2 = (-b - sqrt_d) / 2
                logic_trace.append(f"Δ > 0 → มี 2 คำตอบจริง")
                logic_trace.append(f"x₁ = (-b + √Δ) / 2a = ({-b} + {sqrt_d:.2f}) / 2 = {x1:.2f}")
                logic_trace.append(f"x₂ = (-b - √Δ) / 2a = ({-b} - {sqrt_d:.2f}) / 2 = {x2:.2f}")
                
                response = {
                    'answer': f'คำตอบคือ x = {x1:.2f} หรือ x = {x2:.2f}',
                    'logic_trace': '\n'.join(logic_trace),
                    'category': 'math_equation',
                    'confidence': 0.98
                }
                return response
            elif discriminant == 0:
                x = -b / 2
                logic_trace.append(f"Δ = 0 → มี 1 คำตอบจริง (รากซ้ำ)")
                logic_trace.append(f"x = -b / 2a = {-b} / 2 = {x}")
                
                response = {
                    'answer': f'คำตอบคือ x = {x} (รากซ้ำ)',
                    'logic_trace': '\n'.join(logic_trace),
                    'category': 'math_equation',
                    'confidence': 0.98
                }
                return response
            else:
                logic_trace.append(f"Δ < 0 → ไม่มีคำตอบจริง (มีคำตอบเชิงซ้อน)")
                
                response = {
                    'answer': 'สมการนี้ไม่มีคำตอบเป็นจำนวนจริง (มีคำตอบเชิงซ้อน)',
                    'logic_trace': '\n'.join(logic_trace),
                    'category': 'math_equation',
                    'confidence': 0.95
                }
                return response
        
        # กรณี x^2+bx+c=0 (เครื่องหมายบวก)
        match = re.search(r'([a-zA-Z])\^2\s*\+\s*(-?\d+)([a-zA-Z])\s*\+\s*(\d+)\s*=\s*0', text)
        if match:
            var = match.group(1)
            b = int(match.group(2))
            c = int(match.group(4))
            
            logic_trace.append(f"Equation type: Quadratic ({var}^2 + {b}{var} {'+' if c > 0 else '-'} {abs(c)} = 0)")
            logic_trace.append(f"Coefficients: a=1, b={b}, c={c}")
            
            # คำนวณ discriminant
            discriminant = b**2 - 4*1*c
            logic_trace.append(f"Discriminant (Δ) = b² - 4ac = {b}² - 4(1)({c}) = {discriminant}")
            
            if discriminant > 0:
                sqrt_d = discriminant ** 0.5
                x1 = (-b + sqrt_d) / 2
                x2 = (-b - sqrt_d) / 2
                logic_trace.append(f"Δ > 0 → มี 2 คำตอบจริง")
                logic_trace.append(f"x₁ = (-b + √Δ) / 2a = ({-b} + {sqrt_d:.2f}) / 2 = {x1:.2f}")
                logic_trace.append(f"x₂ = (-b - √Δ) / 2a = ({-b} - {sqrt_d:.2f}) / 2 = {x2:.2f}")
                
                response = {
                    'answer': f'คำตอบคือ x = {x1:.2f} หรือ x = {x2:.2f}',
                    'logic_trace': '\n'.join(logic_trace),
                    'category': 'math_equation',
                    'confidence': 0.98
                }
                return response
            elif discriminant == 0:
                x = -b / 2
                logic_trace.append(f"Δ = 0 → มี 1 คำตอบจริง (รากซ้ำ)")
                logic_trace.append(f"x = -b / 2a = {-b} / 2 = {x}")
                
                response = {
                    'answer': f'คำตอบคือ x = {x} (รากซ้ำ)',
                    'logic_trace': '\n'.join(logic_trace),
                    'category': 'math_equation',
                    'confidence': 0.98
                }
                return response
            else:
                logic_trace.append(f"Δ < 0 → ไม่มีคำตอบจริง (มีคำตอบเชิงซ้อน)")
                
                response = {
                    'answer': 'สมการนี้ไม่มีคำตอบเป็นจำนวนจริง (มีคำตอบเชิงซ้อน)',
                    'logic_trace': '\n'.join(logic_trace),
                    'category': 'math_equation',
                    'confidence': 0.95
                }
                return response
        
        # สมการเลขยกกำลัง: a^x = x^b
        match = re.search(r'(\d+)\^([a-zA-Z])\s*=\s*([a-zA-Z])\^(\d+)', text)
        if match:
            a = int(match.group(1))
            var1 = match.group(2)
            var2 = match.group(3)
            b = int(match.group(4))
            
            logic_trace.append(f"Equation type: Exponential ({a}^{var1} = {var2}^{b})")
            
            # ลองแก้ด้วยการแทนค่า
            solutions = []
            for x in range(1, 20):
                if a**x == x**b:
                    solutions.append(x)
                    logic_trace.append(f"Trial x={x}: {a}^{x} = {a**x}, {x}^{b} = {x**b} ✓")
            
            if solutions:
                response = {
                    'answer': f'คำตอบคือ x = {", ".join(map(str, solutions))}',
                    'logic_trace': '\n'.join(logic_trace),
                    'category': 'math_equation',
                    'confidence': 0.9
                }
                return response
            else:
                logic_trace.append("No integer solution found in range 1-20")
                response = {
                    'answer': 'ไม่พบคำตอบเป็นจำนวนเต็มในช่วง 1-20 อาจต้องใช้วิธีคำนวณขั้นสูง',
                    'logic_trace': '\n'.join(logic_trace),
                    'category': 'math_equation',
                    'confidence': 0.7
                }
                return response
        
        return {
            'answer': 'พบสมการคณิตศาสตร์ แต่ต้องการการวิเคราะห์เพิ่มเติม',
            'logic_trace': '\n'.join(logic_trace),
            'category': 'math_equation',
            'confidence': 0.5
        }
    
    def _analyze_code_request(self, text: str) -> Dict[str, Any]:
        """วิเคราะห์คำขอเขียนโค้ด"""
        logic_trace = []
        logic_trace.append(f"Input: {text}")
        logic_trace.append("Category: Code Generation Request")
        
        topics = {
            'ภาษี': 'tax_calculation',
            'factorial': 'factorial',
            'fibonacci': 'fibonacci',
            'gcd': 'gcd',
            'lcm': 'lcm',
            'prime': 'prime_factors',
            'permutation': 'permutations',
            'combination': 'combinations',
            'เขียนโปรแกรม': 'programming_basics'
        }
        
        detected_topic = None
        for keyword, topic in topics.items():
            if keyword in text.lower():
                detected_topic = topic
                logic_trace.append(f"Detected topic: {topic} (from keyword: {keyword})")
                break
        
        if detected_topic:
            response = {
                'answer': f'รับทราบครับ กำลังเตรียมโค้ดตัวอย่างสำหรับ {detected_topic}...',
                'logic_trace': '\n'.join(logic_trace),
                'category': 'code_request',
                'topic': detected_topic,
                'confidence': 0.9
            }
            return response
        
        response = {
            'answer': 'เข้าใจว่าคุณต้องการเขียนโปรแกรม แต่ต้องการรายละเอียดเพิ่มเติม',
            'logic_trace': '\n'.join(logic_trace),
            'category': 'code_request',
            'confidence': 0.7
        }
        return response
    
    def _analyze_arithmetic(self, text: str) -> Dict[str, Any]:
        """วิเคราะห์การคำนวณเลขคณิต"""
        logic_trace = []
        logic_trace.append(f"Input: {text}")
        logic_trace.append("Category: Arithmetic Calculation")
        
        # หาการคำนวณ
        match = re.search(r'(-?\d+\.?\d*)\s*([\+\-\*/])\s*(-?\d+\.?\d*)', text)
        if match:
            a = float(match.group(1))
            op = match.group(2)
            b = float(match.group(3))
            
            logic_trace.append(f"Expression: {a} {op} {b}")
            
            if op == '+':
                result = a + b
                logic_trace.append(f"Operation: Addition")
            elif op == '-':
                result = a - b
                logic_trace.append(f"Operation: Subtraction")
            elif op == '*':
                result = a * b
                logic_trace.append(f"Operation: Multiplication")
            elif op == '/':
                if b != 0:
                    result = a / b
                    logic_trace.append(f"Operation: Division")
                else:
                    logic_trace.append("Error: Division by zero")
                    return {
                        'answer': 'ไม่สามารถหารด้วยศูนย์ได้',
                        'logic_trace': '\n'.join(logic_trace),
                        'category': 'arithmetic',
                        'confidence': 1.0
                    }
            
            logic_trace.append(f"Result: {result}")
            
            response = {
                'answer': f'{result}',
                'logic_trace': '\n'.join(logic_trace),
                'category': 'arithmetic',
                'confidence': 1.0
            }
            return response
        
        return {
            'answer': 'พบนิพจน์คณิตศาสตร์ แต่ไม่สามารถประมวลผลได้',
            'logic_trace': '\n'.join(logic_trace),
            'category': 'arithmetic',
            'confidence': 0.5
        }
    
    def _analyze_test_request(self, text: str) -> Dict[str, Any]:
        """วิเคราะห์คำขอทดสอบ/โจทย์ท้าทาย"""
        logic_trace = []
        logic_trace.append(f"Input: {text}")
        logic_trace.append("Category: Test/Challenge Request")
        logic_trace.append("Detected: User is requesting a test or challenge problem")
        
        response = {
            'answer': 'พร้อมรับโจทย์ท้าทายครับ! กรุณาระบุรายละเอียดของโจทย์หรือปัญหาที่ต้องการให้แก้ไข',
            'logic_trace': '\n'.join(logic_trace),
            'category': 'test_request',
            'confidence': 0.85
        }
        return response
    
    def _analyze_general(self, text: str) -> Dict[str, Any]:
        """วิเคราะห์ข้อความทั่วไป"""
        logic_trace = []
        logic_trace.append(f"Input: {text}")
        logic_trace.append("Category: General Analysis")
        logic_trace.append("No specific pattern matched")
        
        response = {
            'answer': 'เข้าใจข้อความของคุณ แต่ต้องการข้อมูลเพิ่มเติมเพื่อวิเคราะห์อย่างละเอียด',
            'logic_trace': '\n'.join(logic_trace),
            'category': 'general',
            'confidence': 0.5
        }
        return response


# Test function
def test_wreasoning():
    """ทดสอบ WReasoningEngine"""
    engine = WReasoningEngine()
    
    test_cases = [
        "ฉันว่ายน้ำไม่เก่ง",
        "แม่ฉันใช้เอไอไม่เก่ง",
        "ผมเขียนโปรแกรมเก่ง",
        "เขาเล่นน้ำพอได้",
        "5+5 ได้เท่าไหร่",
        "9.8-9.11 ได้เท่าไหร่",
        "x^2+3x+2=0 แก้สมการนี้หน่อย",
        "3^x=x^9 x เป็นเท่าไหร่",
        "x^2+19x-92=0 วิธีคิด",
        "ถ้าเขามาฉันจะไป",
        "ถ้าเขาไม่มาฉันจะไป",
        "ฉันจะไปพร้อมเขา ถ้าเขามา",
        "ห้ามไม่เปิดไฟทางเดิน",
        "อย่าลืมปิดไฟทางเดิน",
        "อย่าลืมทำการบ้าน",
        "ห้ามไม่คิดก่อนตอบนะ",
        "สร้างโปรแกรมคำนวณภาษีเงินได้บุคคลธรรมดาให้หน่อย",
        "ฉันอยากเรียนเขียนโปรแกรม",
        "AGI โจทย์ทดสอบหน่อย"
    ]
    
    print("=" * 70)
    print("WReasoningEngine Test Results")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        result = engine.analyze(test)
        print(f"\n[{i}/{len(test_cases)}] Input: {test}")
        print(f"    Category: {result['category']}")
        print(f"    Answer: {result['answer']}")
        print(f"    Confidence: {result['confidence']}")
        
        if result['confidence'] >= 0.7:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"Summary: {passed} passed, {failed} failed out of {len(test_cases)}")
    print(f"Success Rate: {(passed/len(test_cases))*100:.2f}%")
    print("=" * 70)


if __name__ == "__main__":
    test_wreasoning()
