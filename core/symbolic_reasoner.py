import re
import sympy
from sympy.logic.boolalg import Implies, And, Or, Not, to_cnf
from sympy.logic import satisfiable
from typing import List, Dict, Tuple, Any, Optional
from enum import Enum

class LogicResult(Enum):
    TRUE = "TRUE"
    FALSE = "FALSE"
    UNKNOWN = "UNKNOWN"
    CONTRADICTION = "CONTRADICTION"

class SymbolicReasoner:
    """
    ระบบให้เหตุผลเชิงสัญลักษณ์ (Symbolic Reasoning Engine)
    ใช้ SymPy Logic และ Z3 ในการพิสูจน์ข้อความทางตรรกะ
    """
    
    def __init__(self):
        self.symbols: Dict[str, sympy.Symbol] = {}
        self.facts: List[sympy.Basic] = []
        self.rules: List[sympy.Basic] = []
        
    def _get_symbol(self, name: str) -> sympy.Symbol:
        """สร้างหรือดึง Symbol จากชื่อ"""
        name_clean = name.strip().replace(" ", "_").replace(".", "")
        if name_clean not in self.symbols:
            self.symbols[name_clean] = sympy.Symbol(name_clean)
        return self.symbols[name_clean]
    
    def _parse_premises(self, premises: List[str]) -> Tuple[List[sympy.Basic], Dict[str, sympy.Basic]]:
        """แปลงประโยคภาษาไทยเป็นสมการตรรกะ"""
        logic_exprs = []
        var_map = {}
        
        for p in premises:
            p_clean = p.strip().lower()
            
            # 1. ตรวจจับรูปแบบ "ทุกคน/ทั้งหมด" (Universal Quantifier)
            # เช่น "คนใช้เอไอเก่งทุกคน", "ผู้ใช้ AI ทุกคนเป็นคนเก่ง"
            if any(word in p_clean for word in ['ทุกคน', 'ทั้งหมด', 'every', 'all']):
                # ลบคำว่า ทุกคน/ทั้งหมด ออกก่อนเพื่อวิเคราะห์โครงสร้าง
                p_core = re.sub(r'(ทุกคน|ทั้งหมด|every|all)', '', p_clean).strip()
                
                # ลองใช้ heuristic ใหม่: หาคำกริยาหรือคุณสมบัติที่พบบ่อย
                # คำที่คุณสมบัติมักอยู่ท้ายประโยค
                adj_keywords = ['เก่ง', 'ดี', 'ฉลาด', 'รวย', 'สวย', 'สูง', 'ใหญ่', 'เล็ก', 'น้อย', 'มาก']
                
                found_adj = False
                for adj in adj_keywords:
                    if adj in p_core:
                        # แยกที่คำคุณศัพท์
                        idx = p_core.find(adj)
                        condition_part = p_core[:idx].strip()
                        result_part = p_core[idx:].strip() # รวมคำคุณศัพท์และสิ่งที่ตามมา
                        
                        if condition_part and result_part:
                            # สร้าง symbol ธรรมดาแทน predicate logic เพื่อความเข้ากันได้กับ SymPy SAT solver
                            # คนใช้เอไอ -> คนใช้เอไอ
                            # เก่ง -> เก่ง
                            # Implies(คนใช้เอไอ, เก่ง)
                            cond_sym = self._get_symbol(condition_part)
                            res_sym = self._get_symbol(result_part)
                            logic_exprs.append(Implies(cond_sym, res_sym))
                            found_adj = True
                            break
                
                if not found_adj and len(p_core) > 0:
                    sym = self._get_symbol(p_core)
                    logic_exprs.append(sym)
                
                continue

            # 2. ตรวจจับรูปแบบ "ถ้า...แล้ว..." (If...Then...)
            if 'ถ้า' in p_clean and ('แล้ว' in p_clean or 'จึง' in p_clean):
                match = re.search(r'ถ้า(.+?)แล้ว(.+)', p_clean)
                if not match:
                    match = re.search(r'ถ้า(.+?)จึง(.+)', p_clean)
                
                if match:
                    cond_text = match.group(1).strip()
                    res_text = match.group(2).strip()
                    
                    cond_sym = self._get_symbol(cond_text)
                    res_sym = self._get_symbol(res_text)
                    
                    logic_exprs.append(Implies(cond_sym, res_sym))
                    continue
            
            # 3. ตรวจจับการปฏิเสธ (Negation)
            # เช่น "ถนนไม่เปียก", "ฝนไม่ตก"
            if 'ไม่' in p_clean and not any(word in p_clean for word in ['ถ้า', 'แล้ว', 'จึง', 'ทุกคน', 'ทั้งหมด']):
                # แยกส่วนที่ถูกปฏิเสธ
                # ลองหา pattern "X ไม่ Y" หรือ "ไม่ X"
                match_neg = re.search(r'(.+?)ไม่(.+)', p_clean)
                if match_neg:
                    prefix = match_neg.group(1).strip()
                    suffix = match_neg.group(2).strip()
                    if prefix and suffix:
                        # เช่น "ถนน ไม่ เปียก" -> Not(ถนน_เปียก)
                        sym_name = f"{prefix}_{suffix}"
                        sym = self._get_symbol(sym_name)
                        logic_exprs.append(Not(sym))
                        continue
                    elif suffix:
                        # เช่น "ไม่ ตก" -> Not(ตก)
                        sym = self._get_symbol(suffix)
                        logic_exprs.append(Not(sym))
                        continue
            
            # 4. ตรวจจับข้อเท็จจริงธรรมดา (Fact)
            # ทำความสะอาดข้อความก่อนสร้าง symbol
            # ลบคำเชื่อมที่ไม่จำเป็น เช่น "เป็น", "คือ"
            p_fact = re.sub(r'(เป็น|คือ)', '', p_clean).strip()
            
            # ตรวจสอบรูปแบบพิเศษ: "X เป็น Y" หรือ "X คือ Y" 
            # ถ้า X เป็นตัวอักษรเดียว (เช่น A, B) และ Y เป็นคุณสมบัติ
            # ให้สร้าง symbol เป็น "Y" แทน "x_y" เพื่อให้ตรงกับ rule
            # ตัวอย่าง: "A เป็นคนใช้เอไอ" -> สร้าง symbol "คนใช้เอไอ" ไม่ใช่ "a_คนใช้เอไอ"
            fact_parts = p_fact.split('_', 1)
            if len(fact_parts) == 2:
                prefix = fact_parts[0]
                rest = fact_parts[1]
                # ถ้า prefix สั้นมาก (1-2 ตัวอักษร) ถือว่าเป็น subject แยก
                if len(prefix) <= 2 and prefix.isalpha():
                    # ใช้แค่ส่วน rest เป็น symbol
                    sym = self._get_symbol(rest)
                    logic_exprs.append(sym)
                    continue
            
            sym = self._get_symbol(p_fact)
            logic_exprs.append(sym)
            
        return logic_exprs, var_map

    def evaluate(self, query: str, context: List[str] = None) -> Dict[str, Any]:
        """
        ประเมินข้อความว่าเป็น True, False หรือ Unknown
        """
        if context is None:
            context = []
        
        # แยก Premises และ Query
        # ถ้า query มีรูปแบบ " premise1, premise2 => conclusion "
        if "=>" in query or "ดังนั้น" in query:
            parts = re.split(r'=>|ดังนั้น', query)
            if len(parts) == 2:
                context_str = parts[0].strip()
                conclusion_str = parts[1].strip()
                # แยก context ด้วยเครื่องหมายจุลภาคหรือ newline
                premises = [p.strip() for p in re.split(r'[,\n]', context_str) if p.strip()]
                premises.append(conclusion_str) # ใส่ conclusion เป็นข้อสุดท้ายเพื่อตรวจสอบ
            else:
                premises = [query]
        else:
            # แยกด้วยเครื่องหมายจุลภาค (comma) สำหรับรายการข้อความ
            premises = [p.strip() for p in re.split(r',', query) if p.strip()]

        # Reset symbols
        self.symbols = {}
        self.facts = []
        self.rules = []
        
        # Parse Premises
        parsed_exprs, _ = self._parse_premises(premises)
        
        if not parsed_exprs:
            return {
                "result": LogicResult.UNKNOWN.value,
                "reason": "ไม่สามารถแปลงประโยคเป็นตรรกะได้",
                "steps": []
            }
        
        # แยก Facts และ Rules
        for expr in parsed_exprs:
            if isinstance(expr, Implies):
                self.rules.append(expr)
            else:
                self.facts.append(expr)
        
        # ข้อสรุปคือข้อสุดท้ายในรายการ premises (ถ้ามี)
        # แต่ในที่นี้เราจะลองตรวจสอบความสอดคล้องของทุกข้อ
        # หากต้องการตรวจสอบเฉพาะข้อสรุป ต้องระบุให้ชัดเจน
        
        # วิธีทำงาน: 
        # 1. รวม Facts และ Rules ทั้งหมด
        # 2. ตรวจสอบว่าขัดแย้งกันเองหรือไม่ (Contradiction)
        # 3. หากมีข้อสรุป (เช่น ข้อสุดท้ายเป็นคำถาม) ให้ตรวจสอบว่าเป็นจริงหรือไม่
        
        # ในกรณีนี้ เราจะถือว่าข้อสุดท้ายคือสิ่งที่ต้องการพิสูจน์
        # และข้อก่อนหน้าคือ Premises
        
        if len(premises) < 2:
             return {
                "result": LogicResult.UNKNOWN.value,
                "reason": "ข้อมูลไม่เพียงพอสำหรับการสรุป",
                "steps": ["มีเพียงข้อความเดียว ไม่สามารถหาความสัมพันธ์ได้"]
            }
        
        proof_premises = parsed_exprs[:-1] # ข้อความก่อนหน้าเป็นสมมติฐาน
        conclusion_expr = parsed_exprs[-1] # ข้อความสุดท้ายเป็นข้อสรุปที่ต้องการตรวจสอบ
        
        # รวมสมมติฐานทั้งหมด
        knowledge_base = And(*proof_premises)
        
        steps = []
        steps.append(f"สมมติฐาน: {[str(p) for p in proof_premises]}")
        steps.append(f"ข้อสรุปที่ต้องการตรวจสอบ: {str(conclusion_expr)}")
        
        # ตรวจสอบ 1: ข้อสรุปเป็นจริงโดยนัยจากสมมติฐานหรือไม่?
        # ทฤษฎีบท: ถ้า (Premises -> Conclusion) เป็น Tautology (จริงเสมอ) แล้ว Conclusion เป็นจริง
        # วิธีหนึ่งคือตรวจสอบว่า Negation ของ Implication เป็น Unsatisfiable (ไม่มีทางเป็นจริง)
        # Not(A -> B) เทียบเท่ากับ A AND Not(B)
        # ดังนั้นเราตรวจสอบว่า (Knowledge_Base AND Not(Conclusion)) ขัดแย้งกันหรือไม่
        
        neg_conclusion = Not(conclusion_expr)
        test_expr = And(knowledge_base, neg_conclusion)
        
        # แปลงเป็น CNF และตรวจสอบด้วย SAT Solver
        try:
            cnf_expr = to_cnf(test_expr, simplify=True)
            is_satisfiable = satisfiable(cnf_expr)
            
            if is_satisfiable is False:
                # หมายถึง (Premises AND Not(Conclusion)) เป็นไปไม่ได้
                # ดังนั้น Conclusion ต้องเป็นจริง
                steps.append("ตรวจสอบ: การสมมติว่าข้อสรุปเป็นเท็จทำให้เกิดความขัดแย้งกับสมมติฐาน")
                steps.append("สรุป: ข้อสรุปเป็นจริงตามสมมติฐาน (Modus Ponens/Deduction)")
                return {
                    "result": LogicResult.TRUE.value,
                    "reason": "ข้อสรุปเป็นจริงตามตรรกะ",
                    "steps": steps
                }
            elif is_satisfiable is True:
                # มีความเป็นไปได้ที่ Premises จะเป็นจริง แต่ Conclusion เป็นเท็จ
                # แสดงว่า Conclusion ไม่ได้เป็นจริงเสมอไป (อาจจะเป็น False หรือ Unknown)
                
                # **ปรับปรุง**: ตรวจสอบว่าเราสามารถ derive conclusion จาก premises ได้หรือไม่
                # โดยใช้ Modus Ponens โดยตรง
                # ถ้ามี Rule: Implies(A, B) และ Fact: A แล้วสรุป B ได้
                
                derived = False
                for rule in proof_premises:
                    if isinstance(rule, Implies):
                        antecedent = rule.args[0]
                        consequent = rule.args[1]
                        
                        # ตรวจสอบว่า antecedent ตรงกับ fact ใดๆ ใน proof_premises หรือไม่
                        for fact in proof_premises:
                            if not isinstance(fact, Implies) and str(fact) == str(antecedent):
                                # พบ Modus Ponens: A และ A->B ดังนั้น B
                                if str(consequent) == str(conclusion_expr):
                                    steps.append(f"ตรวจสอบ: พบ Modus Ponens - มีกฎ '{rule}' และข้อเท็จจริง '{fact}'")
                                    steps.append(f"สรุป: '{consequent}' เป็นจริง")
                                    derived = True
                                    break
                        
                        if derived:
                            break
                
                if derived:
                    return {
                        "result": LogicResult.TRUE.value,
                        "reason": "ข้อสรุปเป็นจริงตามกฎ Modus Ponens",
                        "steps": steps
                    }
                
                # ตรวจสอบต่อว่า ข้อสรุปเป็นเท็จเสมอหรือไม่ (Contradiction with Premises?)
                # ลองทดสอบว่า (Premises AND Conclusion) ขัดแย้งไหม
                test_contradiction = And(knowledge_base, conclusion_expr)
                cnf_cont = to_cnf(test_contradiction, simplify=True)
                is_sat_cont = satisfiable(cnf_cont)
                
                if is_sat_cont is False:
                     steps.append("ตรวจสอบ: ข้อสรุปขัดแย้งกับสมมติฐานโดยตรง")
                     return {
                        "result": LogicResult.FALSE.value,
                        "reason": "ข้อสรุปเป็นเท็จเพราะขัดแย้งกับสมมติฐาน",
                        "steps": steps
                    }
                else:
                    steps.append("ตรวจสอบ: มีสถานการณ์ที่สมมติฐานเป็นจริง แต่ข้อสรุปอาจเป็นจริงหรือเท็จก็ได้")
                    return {
                        "result": LogicResult.UNKNOWN.value,
                        "reason": "ไม่สามารถสรุปได้แน่นอนจากข้อมูลที่มี (Insufficient Information)",
                        "steps": steps
                    }
            else:
                # SAT Solver ไม่สามารถตัดสินใจได้ (หาได้ยากใน SymPy)
                return {
                    "result": LogicResult.UNKNOWN.value,
                    "reason": "ระบบไม่สามารถตัดสินได้",
                    "steps": steps
                }
                
        except Exception as e:
            return {
                "result": LogicResult.UNKNOWN.value,
                "reason": f"เกิดข้อผิดพลาดในการประมวลผลตรรกะ: {str(e)}",
                "steps": steps
            }

def main():
    reasoner = SymbolicReasoner()
    
    # ทดสอบโจทย์: "คนใช้เอไอเก่งทุกคน, A ใช้เอไอไม่ค่อยชำนาญ, A เก่งไหม?"
    # โจทย์ที่ถูกต้องควรเป็น:
    # 1. คนใช้เอไอเก่งทุกคน (UserAI -> Smart)
    # 2. A เป็นคนใช้เอไอ (A_is_UserAI) -> แต่โจทย์เดิมบอกว่า "A ใช้เอไอไม่ค่อยชำนาญ" ซึ่งอาจจะหมายถึง "A ใช้เอไอ" แต่ "ไม่ชำนาญ"
    # ต้องตีความโจทย์ให้ชัด:
    # กรณีที่ 1: "A ใช้เอไอ" (A เป็นสมาชิกของกลุ่มคนใช้เอไอ) -> A ต้องเก่ง
    # กรณีที่ 2: "A ใช้เอไอไม่ค่อยชำนาญ" อาจหมายถึง A ไม่ได้อยู่ในกลุ่ม "คนใช้เอไอเก่ง" หรือแค่บอกระดับความชำนาญ
    
    # ลองทดสอบกับประโยคที่ชัดเจนกว่า:
    test_cases = [
        {
            "name": "คนใช้เอไอเก่งทุกคน + A ใช้เอไอ -> A เก่ง",
            "input": "คนใช้เอไอเก่งทุกคน, A เป็นคนใช้เอไอ, A เก่ง",
            "expected": "TRUE"
        },
        {
            "name": "ถ้าฝนตกถนนเปียก + ถนนไม่เปียก -> ฝนไม่ตก",
            "input": "ถ้าฝนตกแล้วถนนเปียก, ถนนไม่เปียก, ฝนไม่ตก",
            "expected": "TRUE"
        },
        {
            "name": "A > B, B > C -> A > C",
            "input": "A มากกว่า B, B มากกว่า C, A มากกว่า C",
            "expected": "TRUE" # Transitive property (ต้องปรับ parser ให้เข้าใจ 'มากกว่า')
        }
    ]
    
    print("="*60)
    print("ทดสอบ Symbolic Reasoning Engine")
    print("="*60)
    
    for case in test_cases:
        print(f"\nโจทย์: {case['name']}")
        print(f"ข้อความ: {case['input']}")
        result = reasoner.evaluate(case['input'])
        print(f"ผลลัพธ์: {result['result']}")
        print(f"เหตุผล: {result['reason']}")
        print("ขั้นตอน:")
        for step in result['steps']:
            print(f"  - {step}")
        print("-" * 40)

if __name__ == "__main__":
    main()

# เพิ่มฟังก์ชัน evaluate_syllogism ที่ท้ายไฟล์ (ก่อน main)
def evaluate_syllogism_standalone(reasoner, premises: List[str], conclusion: str = "") -> Dict[str, Any]:
    """
    ประเมินตรรกะแบบ Syllogism (เช่น "ทุกคนใช้ AI เก่ง, A ใช้ AI, A เก่งไหม?")
    
    Args:
        reasoner: SymbolicReasoner instance
        premises: รายการข้อเท็จจริงหรือกฎ เช่น ["คนใช้เอไอเก่งทุกคน", "A ใช้เอไอ"]
        conclusion: ข้อสรุปที่ต้องการพิสูจน์ เช่น "A เก่ง"
    
    Returns:
        Dictionary พร้อมผลลัพธ์ TRUE/FALSE/UNKNOWN และเหตุผล
    """
    # Reset symbols
    reasoner.symbols = {}
    reasoner.facts = []
    reasoner.rules = []
    
    # Parse Premises
    parsed_exprs, var_map = reasoner._parse_premises(premises)
    
    if not parsed_exprs:
        return {
            "result": LogicResult.UNKNOWN.value,
            "reason": "ไม่สามารถแปลงประโยคเป็นตรรกะได้",
            "steps": [],
            "success": False
        }
    
    # แยก Facts และ Rules
    for expr in parsed_exprs:
        if isinstance(expr, Implies):
            reasoner.rules.append(expr)
        else:
            reasoner.facts.append(expr)
    
    steps = []
    steps.append(f"Premises: {premises}")
    steps.append(f"Parsed expressions: {[str(e) for e in parsed_exprs]}")
    steps.append(f"Facts: {[str(f) for f in reasoner.facts]}")
    steps.append(f"Rules: {[str(r) for r in reasoner.rules]}")
    
    # ถ้ามี conclusion ให้ตรวจสอบ
    if conclusion:
        steps.append(f"Conclusion to prove: {conclusion}")
        
        # Parse conclusion
        conclusion_exprs, _ = reasoner._parse_premises([conclusion])
        if not conclusion_exprs:
            return {
                "result": LogicResult.UNKNOWN.value,
                "reason": "ไม่สามารถแปลงข้อสรุปเป็นตรรกะได้",
                "steps": steps,
                "success": False
            }
        
        conclusion_expr = conclusion_exprs[0]
        steps.append(f"Parsed conclusion: {conclusion_expr}")
        
        # ตรวจสอบว่า conclusion เป็นจริงหรือไม่ ภายใต้ premises ที่มี
        negated_conclusion = Not(conclusion_expr)
        all_assertions = And(*reasoner.facts, *reasoner.rules, negated_conclusion)
        
        try:
            is_satisfiable = satisfiable(all_assertions)
            steps.append(f"Checking satisfiability of: Facts + Rules + NOT(Conclusion)")
            steps.append(f"Satisfiable result: {is_satisfiable}")
            
            if is_satisfiable is False:
                return {
                    "result": LogicResult.TRUE.value,
                    "reason": "ข้อสรุปเป็นจริงตามตรรกะ (Proof by Contradiction)",
                    "steps": steps,
                    "success": True
                }
            else:
                all_assertions_with_conclusion = And(*reasoner.facts, *reasoner.rules, conclusion_expr)
                is_conclusion_satisfiable = satisfiable(all_assertions_with_conclusion)
                
                if is_conclusion_satisfiable is False:
                    return {
                        "result": LogicResult.FALSE.value,
                        "reason": "ข้อสรุปขัดแย้งกับข้อมูลที่มี",
                        "steps": steps,
                        "success": True
                    }
                else:
                    return {
                        "result": LogicResult.UNKNOWN.value,
                        "reason": "ไม่สามารถสรุปได้จากข้อมูลที่มี (ข้อมูลไม่เพียงพอ)",
                        "steps": steps,
                        "success": True
                    }
        except Exception as e:
            return {
                "result": LogicResult.UNKNOWN.value,
                "reason": f"เกิดข้อผิดพลาดในการประเมิน: {str(e)}",
                "steps": steps,
                "success": False
            }
    else:
        if reasoner.facts or reasoner.rules:
            all_assertions = And(*reasoner.facts, *reasoner.rules)
            try:
                is_satisfiable = satisfiable(all_assertions)
                if is_satisfiable is False:
                    return {
                        "result": LogicResult.CONTRADICTION.value,
                        "reason": "Premises ขัดแย้งกันเอง",
                        "steps": steps,
                        "success": True
                    }
                else:
                    return {
                        "result": LogicResult.TRUE.value,
                        "reason": "Premises สอดคล้องกัน",
                        "steps": steps,
                        "success": True
                    }
            except Exception as e:
                return {
                    "result": LogicResult.UNKNOWN.value,
                    "reason": f"เกิดข้อผิดพลาด: {str(e)}",
                    "steps": steps,
                    "success": False
                }
        
        return {
            "result": LogicResult.UNKNOWN.value,
            "reason": "ไม่มีข้อมูลเพียงพอ",
            "steps": steps,
            "success": False
        }
