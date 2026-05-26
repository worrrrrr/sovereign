"""
Sovereign AI Perception Engine

Analyzes input to identify intents, extract entities, and classify tasks.
Uses intent taxonomy matching with pattern recognition (no ML).
Supports both English and Thai languages.
"""
import re
import json
import os
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field


@dataclass
class Task:
    """
    Represents a classified task from perception analysis.
    
    Attributes:
        task_type: Category of the task (e.g., 'arithmetic', 'file_operation')
        intent_id: Specific intent identifier from taxonomy
        confidence: Confidence score 0.0-1.0
        parameters: Extracted parameters for execution
        constraints: Any constraints or requirements
        language: Detected language ('en', 'th', or 'mixed')
    """
    task_type: str
    intent_id: str = 'unknown'
    confidence: float = 0.0
    parameters: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    language: str = 'en'


class PerceptionEngine:
    """
    Intent-based perception engine for task classification.
    
    Uses intent taxonomy to match user inputs to specific intents,
    then extracts parameters for execution.
    Deterministic behavior: Same input always produces same Task object.
    """
    
    def __init__(self, taxonomy_path: Optional[str] = None):
        # Load intent taxonomy
        if taxonomy_path is None:
            taxonomy_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'config',
                'intent_taxonomy.json'
            )
        
        self.taxonomy = self._load_taxonomy(taxonomy_path)
        self.patterns = self._build_intent_patterns()
        
        # Legacy patterns for backward compatibility
        self.legacy_patterns = {
            'arithmetic': [
                (r'(\d+\.?\d*)\s*([\+\-\*\/])\s*(\d+\.?\d*)', self._parse_arithmetic),
                (r'(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\s*ได้เท่าไหร่', self._parse_thai_arithmetic),
            ],
            'file_operation': [
                (r'(อ่าน|เขียน|ลบ|เปิด)\s*(ไฟล์|file)\s*[\'"]?([^\'"]+)[\'"]?', self._parse_file_op),
            ],
            'count_rows': [
                (r'count.*rows.*where\s+(\w+)\s*=\s*[\'"]?(\w+)[\'"]?', self._parse_count_filter),
                (r'นับ.*แถว.*ที่\s+(\w+)\s*=\s*[\'"]?(\w+)[\'"]?', self._parse_count_filter_thai),
            ]
        }
    
    def _load_taxonomy(self, path: str) -> Dict[str, Any]:
        """Load intent taxonomy from JSON file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Return minimal taxonomy if file not found
            return {
                'version': '1.0.0',
                'intents': [],
                'categories': [],
                'confidence_thresholds': {'high': 0.85, 'medium': 0.65, 'low': 0.45}
            }
    
    def _build_intent_patterns(self) -> Dict[str, List[Tuple[str, str, callable]]]:
        """Build pattern matchers from intent taxonomy."""
        patterns = {}
        
        for intent in self.taxonomy.get('intents', []):
            intent_id = intent['id']
            category = intent['category']
            patterns_list = intent.get('patterns', [])
            
            if category not in patterns:
                patterns[category] = []
            
            # Create regex patterns for each keyword/pattern
            for pattern_text in patterns_list:
                # Escape special regex characters except spaces
                escaped = re.escape(pattern_text)
                # Allow flexible spacing
                regex_pattern = r'\b' + escaped.replace(r'\ ', r'\s*') + r'\b'
                
                patterns[category].append((
                    regex_pattern,
                    intent_id,
                    lambda m, pid=intent_id, cat=category, pt=pattern_text: 
                        self._parse_intent_match(m, pid, cat, pt)
                ))
        
        return patterns
    
    def _parse_intent_match(self, match: re.Match, intent_id: str, 
                           category: str, pattern_text: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Generic parser for intent matches."""
        return (
            {'matched_pattern': pattern_text, 'original_text': match.group(0)},
            {'intent_category': category}
        )
    
    # Legacy pattern parsers (for backward compatibility)
    def _parse_arithmetic(self, match: re.Match) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Parse arithmetic expression from regex match."""
        num1 = float(match.group(1))
        operator = match.group(2)
        num2 = float(match.group(3))
        
        params = {
            'num1': num1,
            'num2': num2,
            'operator': operator,
            'expression': f"{num1} {operator} {num2}"
        }
        constraints = {'requires_float_tolerance': True}
        return params, constraints
    
    def _parse_thai_arithmetic(self, match: re.Match) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Parse Thai arithmetic expression."""
        num1 = float(match.group(1))
        num2 = float(match.group(2))
        
        params = {
            'num1': num1,
            'num2': num2,
            'operator': '-',
            'expression': f"{num1} - {num2}",
            'language': 'th'
        }
        constraints = {'requires_float_tolerance': True}
        return params, constraints
    
    def _parse_file_op(self, match: re.Match) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Parse file operation command."""
        action_map = {'อ่าน': 'read', 'เขียน': 'write', 'ลบ': 'delete', 'เปิด': 'open'}
        action_th = match.group(1)
        filename = match.group(3)
        
        params = {
            'action': action_map.get(action_th, action_th),
            'filename': filename,
            'original_action': action_th
        }
        constraints = {'requires_file_access': True}
        return params, constraints
    
    def _parse_count_filter(self, match: re.Match) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Parse count rows with filter (English)."""
        column = match.group(1)
        value = match.group(2)
        
        params = {
            'operation': 'count',
            'column': column,
            'filter_value': value
        }
        constraints = {'requires_data_access': True}
        return params, constraints
    
    def _parse_count_filter_thai(self, match: re.Match) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Parse count rows with filter (Thai)."""
        column = match.group(1)
        value = match.group(2)
        
        params = {
            'operation': 'count',
            'column': column,
            'filter_value': value,
            'language': 'th'
        }
        constraints = {'requires_data_access': True}
        return params, constraints
    
    def analyze(self, input_text: str) -> Task:
        """
        Analyze input text and classify into a Task using intent detection.
        
        Args:
            input_text: Raw user input
        
        Returns:
            Task object with classification, intent, and parameters
        
        Deterministic: Same input_text always returns same Task.
        """
        # Step 1: Detect language
        language = self._detect_language(input_text)
        
        # Step 2: Try intent-based matching first
        best_match = self._match_intents(input_text)
        
        if best_match and best_match['confidence'] >= 0.45:  # Low threshold
            intent_id = best_match['intent_id']
            category = best_match['category']
            
            # Map intent category to task type
            task_type = self._map_category_to_task_type(category, input_text)
            
            # Extract additional parameters based on intent
            params, constraints = self._extract_parameters_by_intent(
                intent_id, input_text, best_match.get('matched_pattern', '')
            )
            
            return Task(
                task_type=task_type,
                intent_id=intent_id,
                confidence=best_match['confidence'],
                parameters=params,
                constraints=constraints,
                language=language
            )
        
        # Step 3: Fallback to legacy pattern matching
        for task_type, pattern_list in self.legacy_patterns.items():
            for pattern, parser in pattern_list:
                match = re.search(pattern, input_text, re.IGNORECASE)
                if match:
                    params, constraints = parser(match)
                    return Task(
                        task_type=task_type,
                        intent_id=f'{task_type}_legacy',
                        confidence=0.85,
                        parameters=params,
                        constraints=constraints,
                        language=language
                    )
        
        # Step 4: Default fallback - classify by content analysis
        return self._fallback_classification(input_text, language)
    
    def _detect_language(self, text: str) -> str:
        """Detect language of input text."""
        thai_chars = re.findall(r'[\u0E00-\u0E7F]', text)
        english_chars = re.findall(r'[a-zA-Z]', text)
        
        if len(thai_chars) > 0 and len(english_chars) == 0:
            return 'th'
        elif len(english_chars) > 0 and len(thai_chars) == 0:
            return 'en'
        elif len(thai_chars) > 0 and len(english_chars) > 0:
            return 'mixed'
        else:
            return 'en'  # Default
    
    def _match_intents(self, text: str) -> Optional[Dict[str, Any]]:
        """Match text against all intent patterns, return best match."""
        best_match = None
        best_score = 0.0
        
        text_lower = text.lower()
        
        for category, patterns in self.patterns.items():
            for pattern, intent_id, parser in patterns:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    # Calculate confidence based on pattern specificity
                    matched_text = match.group(0)
                    pattern_length = len(pattern.replace('\\b', ''))
                    match_ratio = len(matched_text) / max(len(text), 1)
                    
                    # Boost confidence for exact matches
                    if matched_text.strip() == text.strip():
                        confidence = 0.95
                    else:
                        # Base confidence on match quality
                        confidence = min(0.7 + (match_ratio * 0.3), 0.95)
                    
                    if confidence > best_score:
                        best_score = confidence
                        best_match = {
                            'intent_id': intent_id,
                            'category': category,
                            'confidence': confidence,
                            'matched_pattern': matched_text,
                            'match_object': match
                        }
        
        return best_match
    
    def _map_category_to_task_type(self, category: str, input_text: str) -> str:
        """Map intent category to task type for execution."""
        category_mapping = {
            'calculation': 'arithmetic',
            'finance': 'financial_advice',
            'inquiry': 'question',
            'command': 'command',
            'social': 'greeting',
            'response': 'response',
            'utility': 'utility',
            'language': 'language_task',
            'programming': 'code_task',
            'file_operation': 'file_operation',
            'system': 'system_task',
            'analytics': 'analysis',
            'productivity': 'productivity_task',
            'communication': 'communication_task',
            'entertainment': 'entertainment',
            'health': 'health_query',
            'emergency': 'emergency',
            'education': 'learning',
            'shopping': 'shopping',
            'travel': 'travel',
            'cooking': 'cooking',
            'social_advice': 'advice',
            'legal': 'legal_query',
            'news': 'news_query',
            'sports': 'sports_query',
            'lifestyle': 'lifestyle',
            'technology': 'tech_support',
            'meta': 'meta_query',
            'fallback': 'unknown'
        }
        
        return category_mapping.get(category, 'unknown')
    
    def _extract_parameters_by_intent(self, intent_id: str, input_text: str, 
                                     matched_pattern: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Extract parameters based on specific intent."""
        params = {'original_input': input_text, 'matched_intent': intent_id}
        constraints = {'intent_based': True}
        
        # Extract numbers for calculation intents
        if 'math' in intent_id or 'arithmetic' in intent_id:
            numbers = re.findall(r'\d+\.?\d*', input_text)
            if len(numbers) >= 2:
                params['numbers'] = [float(n) for n in numbers]
            
            # Detect operator
            if '+' in input_text or 'plus' in input_text.lower() or 'บวก' in input_text:
                params['operator'] = '+'
            elif '-' in input_text or 'minus' in input_text.lower() or 'ลบ' in input_text:
                params['operator'] = '-'
            elif '*' in input_text or 'times' in input_text.lower() or 'คูณ' in input_text:
                params['operator'] = '*'
            elif '/' in input_text or 'divide' in input_text.lower() or 'หาร' in input_text:
                params['operator'] = '/'
            
            constraints['requires_float_tolerance'] = True
        
        # Extract amount for payment/finance intents
        if 'payment' in intent_id or 'money' in intent_id:
            amounts = re.findall(r'(\d+)\s*(?:บาท|baht|THB)?', input_text, re.IGNORECASE)
            if amounts:
                params['amount'] = int(amounts[0])
                params['currency'] = 'THB' if 'บาท' in input_text else 'USD'
        
        # Extract question words for inquiry intents
        if 'question' in intent_id:
            question_words = ['what', 'who', 'when', 'where', 'why', 'how', 'อะไร', 'ใคร', 'เมื่อไหร่', 'ที่ไหน', 'ทำไม', 'อย่างไร']
            for qword in question_words:
                if qword in input_text.lower():
                    params['question_type'] = qword
                    break
        
        return params, constraints
    
    def _fallback_classification(self, input_text: str, language: str) -> Task:
        """Fallback classification when no intent matches."""
        text_lower = input_text.lower()
        
        # Simple heuristic classification
        if re.search(r'\d+.*[\+\-\*\/].*\d+', text_lower):
            return Task(
                task_type='arithmetic',
                intent_id='math_arithmetic_basic',
                confidence=0.75,
                parameters={'raw_input': input_text},
                constraints={'requires_float_tolerance': True},
                language=language
            )
        elif any(word in text_lower for word in ['hello', 'hi', 'สวัสดี', 'hey']):
            return Task(
                task_type='greeting',
                intent_id='greeting_hello',
                confidence=0.80,
                parameters={'raw_input': input_text},
                constraints={},
                language=language
            )
        elif any(word in text_lower for word in ['thank', 'thanks', 'ขอบคุณ']):
            return Task(
                task_type='response',
                intent_id='greeting_thanks',
                confidence=0.85,
                parameters={'raw_input': input_text},
                constraints={},
                language=language
            )
        else:
            return Task(
                task_type='unknown',
                intent_id='unclear_ambiguous',
                confidence=0.30,
                parameters={'raw_input': input_text},
                constraints={},
                language=language
            )
    
    def get_intent_info(self, intent_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific intent."""
        for intent in self.taxonomy.get('intents', []):
            if intent['id'] == intent_id:
                return intent
        return None
    
    def list_intents_by_category(self, category: str) -> List[str]:
        """List all intent IDs in a given category."""
        return [
            intent['id'] 
            for intent in self.taxonomy.get('intents', [])
            if intent.get('category') == category
        ]
