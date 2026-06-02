"""
Sovereign AI - Dynamic Prompt Generator
----------------------------------------
หน้าที่: สร้าง prompt แบบไดนามิกเพื่อเพิ่มความสามารถในการจับ intent
โดยเฉพาะคำสั่งที่ซับซ้อนและหลายรูปแบบ
"""

import re
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass


@dataclass
class PatternTemplate:
    """Template สำหรับสร้าง pattern แบบไดนามิก"""
    name: str
    templates: List[str]
    variables: Dict[str, List[str]]
    intent_type: str
    confidence_base: float = 0.85


class DynamicPromptGenerator:
    """
    สร้าง patterns แบบไดนามิกสำหรับ intent detection
    รองรับหลายรูปแบบและหลายภาษา
    """
    
    def __init__(self):
        self.pattern_templates = self._build_payment_templates()
        self.generated_patterns = []
        self._generate_all_patterns()
    
    def _build_payment_templates(self) -> List[PatternTemplate]:
        """สร้าง templates สำหรับคำสั่งเกี่ยวกับการชำระเงิน"""
        
        templates = [
            # Template 1: ถามเกี่ยวกับเงินทอน
            PatternTemplate(
                name="change_query",
                templates=[
                    r"ทอน{amount}บาท",
                    r"เงินทอน{question}",
                    r"ทอนเงิน{question}",
                    r"จะได้ทอน{question}",
                    r"ต้องทอน{question}",
                    r"รับทอน{question}",
                    r"ขอทอน{question}",
                    r"ทอนอีก{question}",
                    r"ทอนให้{question}",
                    r"เงินทอนจาก{amount}บาท",
                    r"ทอน.*?{amount}.*?บาท",
                ],
                variables={
                    'amount': [r'\d+', r'\d+\.\d+'],
                    'question': [r'.*?เท่าไหร่', r'.*?กี่บาท', r'.*?เท่าไร', r'.*?多少', r'.*?how much']
                },
                intent_type="PAYMENT_QUERY",
                confidence_base=0.90
            ),
            
            # Template 2: จ่ายเงิน/ชำระบิล
            PatternTemplate(
                name="payment_action",
                templates=[
                    r"{action}.*?{amount}.*?บาท",
                    r"{action}เงิน.*?{amount}.*?บาท",
                    r"{action}เป็นเงิน.*?{amount}.*?บาท",
                    r"{action}ยอด.*?{amount}.*?บาท",
                    r"{action}ทั้งหมด.*?{amount}.*?บาท",
                    r"{action}จำนวน.*?{amount}.*?บาท",
                ],
                variables={
                    'action': [r'จ่าย', r'ชำระ', r'โอนเงิน', r'โอนเงินให้', r'ส่งเงิน'],
                    'amount': [r'\d+', r'\d+\.\d+']
                },
                intent_type="PAYMENT_QUERY",
                confidence_base=0.88
            ),
            
            # Template 3: คำนวณเงิน/ยอดรวม
            PatternTemplate(
                name="money_calculation",
                templates=[
                    "{calc_word}{question_word}",
                    "{calc_word}เป็น{question_word}",
                    "{calc_word}ได้{question_word}",
                    "{calc_word}ให้หน่อย",
                    "{calc_word}หน่อย",
                    "รวม{question_word}",
                    "ยอดรวม{question_word}",
                ],
                variables={
                    'calc_word': ['คิดเงิน', 'คำนวณเงิน', 'รวมเงิน', 'เช็คยอด', 'ดูยอด', 'หายอด'],
                    'question_word': ['เท่าไหร่', 'กี่บาท', 'เท่าไร', '多少']
                },
                intent_type="MONEY_CALCULATION",
                confidence_base=0.87
            ),
            
            # Template 4: ถามราคา/มูลค่า
            PatternTemplate(
                name="price_inquiry",
                templates=[
                    "{item}ราคา{question_word}",
                    "{item}กี่บาท",
                    "{item}เท่าไหร่",
                    "ราคา{item}{question_word}",
                    "มูลค่า{item}{question_word}",
                    "{item}คิดเป็นเงิน{question_word}",
                ],
                variables={
                    'item': ['สินค้า', 'ของ', 'อันนี้', 'สิ่งนี้', 'บริการ', 'เมนูนี้'],
                    'question_word': ['เท่าไหร่', 'กี่บาท', 'เท่าไร', '多少', 'how much']
                },
                intent_type="PAYMENT_QUERY",
                confidence_base=0.82
            ),
            
            # Template 5: เตรียมเงิน/แนะนำการชำระเงิน
            PatternTemplate(
                name="payment_preparation",
                templates=[
                    r"เตรียมเงิน.*?{amount}.*?บาท.*{prep}",
                    r"ต้องมีเงิน.*?{amount}.*?บาท.*{prep}",
                    r"ใช้เงิน.*?{amount}.*?บาท.*{prep}",
                    r"ต้องการเงิน.*?{amount}.*?บาท.*{prep}",
                    r"แนะนำวิธีชำระ.*?{amount}.*?บาท",
                    r"แนะนำวิธีจ่ายเงิน.*?{amount}.*?บาท",
                    r"วิธีเตรียมเงิน.*?{amount}.*?บาท",
                    r"ควรเตรียมเงิน.*?{amount}.*?บาท.*{prep}",
                ],
                variables={
                    'amount': [r'\d+', r'\d+\.\d+'],
                    'prep': [r'.*?ยังไง', r'.*?อย่างไร', r'.*?ดี', r'.*?แบบไหน', r'.*?ดีครับ', r'.*?ดีค่ะ', r'']
                },
                intent_type="PAYMENT_ADVICE",
                confidence_base=0.89
            ),
            
            # Template 6: ทอนเงินแบบระบุจำนวน
            PatternTemplate(
                name="specific_change",
                templates=[
                    r"ทอน.*?{amount1}.*?จาก.*?{amount2}",
                    r"ทอนเงิน.*?{amount1}.*?จาก.*?{amount2}",
                    r"ให้ทอน.*?{amount1}.*?จาก.*?{amount2}",
                    r"จ่าย.*?{amount2}.*?ทอน.*?{amount1}",
                    r"ให้.*?{amount2}.*?ทอน.*?{amount1}",
                    r"สลึง.*?{amount2}.*?ทอน.*?{amount1}",
                ],
                variables={
                    'amount1': [r'\d+', r'\d+\.\d+'],
                    'amount2': [r'\d+', r'\d+\.\d+']
                },
                intent_type="PAYMENT_QUERY",
                confidence_base=0.91
            ),
        ]
        
        return templates
    
    def _generate_all_patterns(self):
        """Generate all patterns from templates"""
        for template in self.pattern_templates:
            patterns = self._expand_template(template)
            self.generated_patterns.extend(patterns)
    
    def _expand_template(self, template: PatternTemplate) -> List[Tuple[str, str, float]]:
        """
        ขยาย template เป็น patterns จริงๆ
        Returns: List of (pattern_regex, intent_type, confidence)
        """
        patterns = []
        
        for tmpl in template.templates:
            # Replace variables with their possible values
            expanded = [tmpl]
            
            for var_name, var_values in template.variables.items():
                new_expanded = []
                pattern_placeholder = '{' + var_name + '}'
                
                for current_pattern in expanded:
                    if pattern_placeholder in current_pattern:
                        for value in var_values:
                            new_pattern = current_pattern.replace(pattern_placeholder, value)
                            new_expanded.append(new_pattern)
                    else:
                        new_expanded.append(current_pattern)
                
                expanded = new_expanded
            
            # Convert to regex patterns
            for pattern_text in expanded:
                regex = self._text_to_regex(pattern_text)
                patterns.append((regex, template.intent_type, template.confidence_base))
        
        return patterns
    
    def _text_to_regex(self, text: str) -> str:
        """แปลงข้อความเป็น regex pattern"""
        # Escape special characters except our placeholders
        result = text
        
        # Handle number placeholders - convert \d+ to capture group
        result = result.replace('\\d+', r'(\d+(?:\.\d+)?)')
        
        # Add flexible spacing between Thai characters
        result = result.replace(" ", r"\\s*")
        
        # Make it case-insensitive friendly (but don't add word boundaries for Thai)
        # Thai language doesn't use word boundaries like English
        if re.search(r'[\u0E00-\u0E7F]', result):
            # Thai text - don't add \b
            result = r'(?i)' + result
        else:
            # English text - add word boundaries
            result = r'(?i)\b' + result + r'\b'
        
        return result
    
    def get_patterns_for_intent(self, intent_type: str) -> List[Tuple[str, float]]:
        """ดึง patterns ทั้งหมดสำหรับ intent ที่กำหนด"""
        return [(p, c) for p, t, c in self.generated_patterns if t == intent_type]
    
    def match_input(self, user_input: str) -> List[Dict[str, Any]]:
        """
        ตรวจสอบ input กับ generated patterns ทั้งหมด
        Returns: List of matches with intent type and confidence
        """
        matches = []
        
        for pattern, intent_type, confidence in self.generated_patterns:
            try:
                match = re.search(pattern, user_input, re.IGNORECASE)
                if match:
                    # Extract amounts if present
                    amounts = []
                    groups = match.groups()
                    for g in groups:
                        if g and re.match(r'\d+(?:\.\d+)?', g):
                            amounts.append(float(g))
                    
                    matches.append({
                        'intent_type': intent_type,
                        'confidence': confidence,
                        'matched_pattern': pattern,
                        'matched_text': match.group(0),
                        'amounts': amounts,
                        'groups': groups
                    })
            except re.error:
                # Skip invalid patterns
                continue
        
        # Sort by confidence (highest first)
        matches.sort(key=lambda x: x['confidence'], reverse=True)
        
        return matches
    
    def add_custom_template(self, template: PatternTemplate):
        """เพิ่ม template ใหม่แบบไดนามิก"""
        self.pattern_templates.append(template)
        new_patterns = self._expand_template(template)
        self.generated_patterns.extend(new_patterns)
    
    def get_statistics(self) -> Dict[str, Any]:
        """แสดงสถิติของ generated patterns"""
        stats = {
            'total_templates': len(self.pattern_templates),
            'total_patterns': len(self.generated_patterns),
            'patterns_by_intent': {}
        }
        
        for _, intent_type, _ in self.generated_patterns:
            if intent_type not in stats['patterns_by_intent']:
                stats['patterns_by_intent'][intent_type] = 0
            stats['patterns_by_intent'][intent_type] += 1
        
        return stats


# Singleton instance
_global_generator = None

def get_prompt_generator() -> DynamicPromptGenerator:
    """ดึง instance ของ DynamicPromptGenerator (Singleton)"""
    global _global_generator
    if _global_generator is None:
        _global_generator = DynamicPromptGenerator()
    return _global_generator


# Test function
if __name__ == "__main__":
    generator = get_prompt_generator()
    
    test_inputs = [
        "ทอนอีก 2 บาท",
        "เงินทอนเท่าไหร่",
        "จ่าย 500 บาท",
        "โอนเงิน 1000 บาท",
        "คิดเงินให้หน่อย",
        "รวมเงินเท่าไหร่",
        "เตรียมเงิน 500 บาทยังไง",
        "ทอน 20 จาก 100",
        "สินค้าราคาเท่าไหร่",
    ]
    
    print("=" * 60)
    print("Dynamic Prompt Generator - Test Results")
    print("=" * 60)
    print(f"\nTotal patterns generated: {len(generator.generated_patterns)}")
    print(f"\nStatistics: {generator.get_statistics()}")
    print("\n" + "=" * 60)
    
    for test_input in test_inputs:
        matches = generator.match_input(test_input)
        print(f"\nInput: '{test_input}'")
        if matches:
            best_match = matches[0]
            print(f"  ✓ Matched: {best_match['intent_type']}")
            print(f"    Confidence: {best_match['confidence']}")
            print(f"    Amounts: {best_match['amounts']}")
        else:
            print("  ✗ No match found")
    
    print("\n" + "=" * 60)
