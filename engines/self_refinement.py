"""
Self-Refinement Engine for Sovereign AI

This module implements an automatic self-improvement mechanism that:
1. Runs tests automatically
2. Analyzes failures and identifies root causes
3. Modifies the code to fix issues
4. Re-runs tests until they pass or max iterations reached
"""
import subprocess
import re
import os
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path


class SelfRefinementEngine:
    """
    Engine for automatic code self-improvement based on test results.
    """
    
    def __init__(self, target_file: str = "tools/math.py", test_file: str = "tests/test_equation_solver.py"):
        self.target_file = Path(target_file)
        self.test_file = Path(test_file)
        self.max_iterations = 5
        self.tolerance = 1e-6
        
    def run_tests(self) -> Tuple[bool, str]:
        """
        Run the test suite and return (passed, output).
        """
        print(f"\n{'='*60}")
        print(f"🧪 Running tests: {self.test_file}")
        print(f"{'='*60}")
        
        result = subprocess.run(
            ["python", "-m", "pytest", str(self.test_file), "-v", "--tb=short"],
            capture_output=True,
            text=True,
            cwd="/workspace"
        )
        
        passed = result.returncode == 0
        output = result.stdout + "\n" + result.stderr
        
        if passed:
            print("✅ All tests PASSED!")
        else:
            print("❌ Some tests FAILED!")
            print("\n--- Test Output ---")
            print(output[-2000:])  # Show last 2000 chars
            
        return passed, output
    
    def analyze_failures(self, test_output: str) -> List[Dict[str, Any]]:
        """
        Analyze test failures and identify what needs to be fixed.
        Returns a list of issues found.
        """
        issues = []
        
        # Pattern 1: Assertion errors with specific values
        assertion_pattern = r'AssertionError:\s*(.*?)\n'
        for match in re.finditer(assertion_pattern, test_output, re.DOTALL):
            error_msg = match.group(1).strip()
            issues.append({
                'type': 'assertion_error',
                'message': error_msg,
                'severity': 'high'
            })
        
        # Pattern 2: Missing solutions
        if 'Expected' in test_output and 'got' in test_output:
            expected_pattern = r'Expected\s+([^,]+),\s*got\s+([^\n]+)'
            for match in re.finditer(expected_pattern, test_output):
                expected = match.group(1).strip()
                got = match.group(2).strip()
                issues.append({
                    'type': 'missing_solutions',
                    'expected': expected,
                    'got': got,
                    'severity': 'high'
                })
        
        # Pattern 3: Lambert W branch issues
        if 'lambertw' in test_output.lower() or 'branch' in test_output.lower():
            issues.append({
                'type': 'lambert_w_branch',
                'message': 'Lambert W function branches may not be fully explored',
                'severity': 'medium'
            })
        
        # Pattern 4: Tolerance issues
        tolerance_pattern = r'tol|tolerance|1e-\d+|relative.*error'
        if re.search(tolerance_pattern, test_output, re.IGNORECASE):
            issues.append({
                'type': 'tolerance_issue',
                'message': 'Numerical tolerance exceeded',
                'severity': 'medium'
            })
        
        return issues
    
    def read_current_code(self) -> str:
        """Read the current content of the target file."""
        with open(self.target_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    def write_fixed_code(self, new_code: str) -> None:
        """Write the fixed code to the target file."""
        with open(self.target_file, 'w', encoding='utf-8') as f:
            f.write(new_code)
        print(f"💾 Code updated: {self.target_file}")
    
    def generate_fix(self, code: str, issues: List[Dict[str, Any]]) -> str:
        """
        Generate a fix for the identified issues.
        This is a rule-based approach for common mathematical equation solving issues.
        """
        print(f"\n🔍 Analyzing issues and generating fixes...")
        
        fixed_code = code
        
        # Fix 1: Ensure Lambert W branches are checked
        has_lambert_check = 'lambertw' in code and ('k=-1' in code or 'k, -1' in code or 'branch' in code.lower())
        
        if any(issue['type'] in ['lambert_w_branch', 'missing_solutions'] for issue in issues):
            if not has_lambert_check:
                print("  → Adding Lambert W branch checking logic")
                
                # Find the solve_equation function and enhance it
                # Look for where sympy.solve is used
                if 'solve(equation, variable)' in fixed_code:
                    # Add special handling for exponential equations
                    enhancement = '''
        # Special handling for exponential equations of form a^x = x^b
        # These often require Lambert W function with multiple branches
        eq_str = str(equation)
        if '**' in eq_str and '=' in eq_str:
            try:
                from sympy import exp, log, LambertW as lambertw
                
                # Try to detect form: a^x = x^b
                # Transform to: x*ln(a) = b*ln(x) => x = -b*W(-ln(a)/b)/ln(a)
                left, right = (equation.lhs, equation.rhs) if hasattr(equation, 'lhs') else (sympify(cleaned_eq.split('=')[0]), sympify(cleaned_eq.split('=')[1]))
                
                # Check if it's exponential form
                left_funcs = left.atoms() if hasattr(left, 'atoms') else set()
                right_funcs = right.atoms() if hasattr(right, 'atoms') else set()
                
                # Try Lambert W approach for a^x = x^b
                # Pattern matching for base^x = x^power
                import re as regex_module
                eq_text = str(left) + '=' + str(right)
                match_exp = regex_module.search(r'(\\d+)\\s*\\*\\*\\s*x\\s*=\\s*x\\s*\\*\\*\\s*(\\d+)', eq_text.replace(' ', ''))
                if match_exp:
                    base = int(match_exp.group(1))
                    power = int(match_exp.group(2))
                    
                    # Calculate using Lambert W
                    arg_val = -sympy.log(base) / power
                    
                    # Check both real branches
                    lambert_solutions = []
                    for k_branch in [None, -1]:
                        try:
                            if k_branch is None:
                                w_val = lambertw(arg_val)
                            else:
                                w_val = lambertw(arg_val, k_branch)
                            
                            x_sol = -power * w_val / sympy.log(base)
                            x_numeric = x_sol.evalf()
                            
                            if x_numeric.is_real:
                                lambert_solutions.append(float(x_numeric))
                        except:
                            pass
                    
                    if len(lambert_solutions) > 0:
                        # Replace or augment solutions
                        processed_solutions = lambert_solutions
                        steps.append(f"ใช้ Lambert W function (branches k=0 และ k=-1)")
                        for i, sol in enumerate(lambert_solutions):
                            steps.append(f"คำตอบที่ {i+1}: x ≈ {sol:.6f}")
                        
                        return {
                            'success': True,
                            'solutions': processed_solutions,
                            'method': 'lambert_w_multi_branch',
                            'steps': '\\n'.join(steps),
                            'variable': 'x',
                            'raw_input': equation_str
                        }
                except Exception as e:
                    # Fall back to standard solve
                    pass
'''
                    # Insert the enhancement before the return statement in solve_equation
                    # Find the line with "return {" after the solutions processing
                    lines = fixed_code.split('\n')
                    insert_idx = None
                    for i, line in enumerate(lines):
                        if "'method': 'sympy_solve'" in line:
                            # Find the return statement block
                            for j in range(i, min(i+10, len(lines))):
                                if 'return {' in lines[j]:
                                    insert_idx = j
                                    break
                            break
                    
                    if insert_idx:
                        # Insert before the return
                        indent = '        '
                        enhanced_lines = [indent + l if l.strip() else l for l in enhancement.strip().split('\n')]
                        lines = lines[:insert_idx] + enhanced_lines + lines[insert_idx:]
                        fixed_code = '\n'.join(lines)
        
        # Fix 2: Improve numerical precision
        if any(issue['type'] == 'tolerance_issue' for issue in issues):
            if 'evalf()' in fixed_code:
                print("  → Improving numerical precision settings")
                # Already using evalf(), but ensure high precision
                fixed_code = fixed_code.replace('.evalf()', '.evalf(15)')  # Higher precision
        
        # Fix 3: Ensure all real solutions are captured
        if any(issue['type'] == 'missing_solutions' for issue in issues):
            print("  → Enhancing solution filtering to capture all real solutions")
            
            # Improve the solution filtering logic
            old_filter = '''if sol.is_real:
                    num_val = complex(sol.evalf())'''
            
            new_filter = '''# Check if solution is real or can be evaluated to real
                try:
                    num_val = sol.evalf()
                    if num_val.is_real or (hasattr(num_val, 'as_real_imag') and num_val.as_real_imag()[1].evalf() == 0):
                        num_val = complex(num_val)'''
            
            if old_filter in fixed_code:
                fixed_code = fixed_code.replace(old_filter, new_filter)
        
        return fixed_code
    
    def refine(self) -> Dict[str, Any]:
        """
        Main refinement loop: run tests, analyze failures, fix code, repeat.
        """
        print(f"\n{'🚀'*30}")
        print(f"🚀 Starting Self-Refinement Process")
        print(f"🎯 Target: {self.target_file}")
        print(f"📋 Tests: {self.test_file}")
        print(f"🔄 Max iterations: {self.max_iterations}")
        print(f"{'🚀'*30}\n")
        
        iteration = 0
        history = []
        
        while iteration < self.max_iterations:
            iteration += 1
            print(f"\n{'='*60}")
            print(f"📊 Iteration {iteration}/{self.max_iterations}")
            print(f"{'='*60}")
            
            # Step 1: Run tests
            passed, output = self.run_tests()
            
            history.append({
                'iteration': iteration,
                'passed': passed,
                'output_snippet': output[-500:] if len(output) > 500 else output
            })
            
            if passed:
                print(f"\n✅ SUCCESS! Tests passed after {iteration} iteration(s).")
                return {
                    'success': True,
                    'iterations': iteration,
                    'history': history
                }
            
            # Step 2: Analyze failures
            issues = self.analyze_failures(output)
            
            if not issues:
                print("⚠️  No specific issues identified, but tests failed.")
                issues = [{'type': 'unknown', 'message': 'Tests failed for unknown reason'}]
            
            print(f"\n📋 Identified {len(issues)} issue(s):")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. [{issue['type']}] {issue.get('message', issue.get('expected', ''))}")
            
            # Step 3: Generate and apply fix
            current_code = self.read_current_code()
            fixed_code = self.generate_fix(current_code, issues)
            
            # Only write if changes were made
            if fixed_code != current_code:
                self.write_fixed_code(fixed_code)
            else:
                print("⚠️  No automatic fix could be generated.")
                # Try a more aggressive fix
                print("  → Attempting alternative fix strategy...")
                fixed_code = self.aggressive_fix(current_code, issues)
                if fixed_code != current_code:
                    self.write_fixed_code(fixed_code)
                else:
                    print("❌ Unable to generate a fix. Manual intervention required.")
                    break
            
            # Small delay to ensure file system sync
            import time
            time.sleep(0.5)
        
        # Max iterations reached
        print(f"\n❌ Self-refinement did not converge after {self.max_iterations} iterations.")
        print("   Manual code review and fixing is recommended.")
        
        return {
            'success': False,
            'iterations': iteration,
            'history': history,
            'final_status': 'max_iterations_reached'
        }
    
    def aggressive_fix(self, code: str, issues: List[Dict[str, Any]]) -> str:
        """
        Apply more aggressive fixes when standard fixes don't work.
        """
        fixed_code = code
        
        # Completely rewrite the solve_equation function to handle exponential equations better
        if any(issue['type'] in ['lambert_w_branch', 'missing_solutions'] for issue in issues):
            print("  → Applying comprehensive Lambert W implementation")
            
            # Find and replace the entire solve_equation function's core logic
            new_implementation = '''
    try:
        from sympy import symbols, Eq, solve, sympify, S, exp, log, LambertW as lambertw, I
        from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application, convert_xor
        
        # Define transformations to handle ^ as power and implicit multiplication (e.g., 5x -> 5*x)
        transformations = standard_transformations + (implicit_multiplication_application, convert_xor)
        
        # Parse the equation string (using cleaned version)
        if '=' in cleaned_eq:
            left, right = cleaned_eq.split('=', 1)
            left_expr = parse_expr(left.strip(), transformations=transformations)
            right_expr = parse_expr(right.strip(), transformations=transformations)
            equation = Eq(left_expr, right_expr)
        else:
            # Assume it's an expression = 0
            equation = parse_expr(cleaned_eq, transformations=transformations)
        
        # Special handling for exponential equations: a^x = x^b
        eq_text = str(equation)
        import re as regex_module
        
        # Pattern: number^x = x^number
        match_exp = regex_module.search(r'(\\d+)\\s*\\*\\*\\s*x\\s*=\\s*x\\s*\\*\\*\\s*(\\d+)', eq_text.replace(' ', ''))
        
        if match_exp:
            base = int(match_exp.group(1))
            power = int(match_exp.group(2))
            
            steps.append(f"ตรวจพบสมการเอกซ์โพเนนเชียล: {base}^x = x^{power}")
            steps.append(f"ใช้สูตร Lambert W: x = -{power} × W(-ln({base})/{power}) / ln({base})")
            
            # Calculate argument for Lambert W
            arg_val = -sympy.log(base) / power
            steps.append(f"ค่าอาร์กิวเมนต์สำหรับ Lambert W: {arg_val.evalf()}")
            
            # Check threshold for real solutions
            threshold = -1 / sympy.E
            steps.append(f"เกณฑ์สำหรับคำตอบจริง: {threshold.evalf()}")
            
            if arg_val >= threshold:
                steps.append("อาร์กิวเมนต์อยู่ในช่วงที่มีคำตอบจริง")
                
                # Try both real branches: k=0 and k=-1
                lambert_solutions = []
                for k_branch in [0, -1]:
                    try:
                        w_val = lambertw(arg_val, k_branch)
                        x_sol = -power * w_val / sympy.log(base)
                        x_numeric = x_sol.evalf(15)  # High precision
                        
                        if x_numeric.is_real:
                            float_val = float(x_numeric)
                            # Avoid duplicates
                            if not any(abs(float_val - s) < 1e-9 for s in lambert_solutions):
                                lambert_solutions.append(float_val)
                                steps.append(f"Branch k={k_branch}: x ≈ {float_val:.10f}")
                                
                                # Verify by substitution
                                lhs_verify = base ** float_val
                                rhs_verify = float_val ** power
                                rel_err = abs(lhs_verify - rhs_verify) / max(abs(lhs_verify), abs(rhs_verify), 1e-10)
                                steps.append(f"  ตรวจสอบ: {base}^{float_val:.4f} ≈ {lhs_verify:.6f}, {float_val:.4f}^{power} ≈ {rhs_verify:.6f}, ความคลาดเคลื่อน: {rel_err:.2e}")
                    except Exception as e:
                        steps.append(f"Branch k={k_branch}: ไม่สามารถคำนวณได้ ({str(e)})")
                
                if lambert_solutions:
                    return {
                        'success': True,
                        'solutions': sorted(lambert_solutions),
                        'method': 'lambert_w_multi_branch',
                        'steps': '\\n'.join(steps),
                        'variable': 'x',
                        'raw_input': equation_str
                    }
            else:
                steps.append("อาร์กิวเมนต์ต่ำกว่าเกณฑ์ อาจไม่มีคำตอบจริง")
        
        # Fall back to standard SymPy solve for other equation types
        # Find all symbols in the equation
        symbols_in_eq = equation.free_symbols
        if not symbols_in_eq:
            # No variables, just evaluate
            result_val = float(equation.lhs.evalf(15) if hasattr(equation, 'lhs') else equation.evalf(15))
            return {
                'success': True,
                'solutions': [result_val],
                'method': 'evaluation',
                'steps': f"ประเมินค่าโดยตรง: {cleaned_eq} = {result_val}",
                'raw_input': equation_str
            }
        
        # Use the first symbol as the variable to solve for
        variable = list(symbols_in_eq)[0]
        
        # Solve the equation
        solutions = solve(equation, variable)
        
        # Process solutions
        processed_solutions = []
        steps.append(f"วิธีแก้มาตรฐานด้วย SymPy:")
        
        for i, sol in enumerate(solutions):
            try:
                # Try to get numerical value with high precision
                num_val = sol.evalf(15)
                
                # Check if it's real
                if hasattr(num_val, 'is_real') and num_val.is_real:
                    float_val = float(num_val)
                    if not any(abs(float_val - s) < 1e-9 for s in processed_solutions):
                        processed_solutions.append(float_val)
                        steps.append(f"คำตอบที่ {i+1}: {variable} ≈ {float_val:.10f}")
                elif hasattr(num_val, 'as_real_imag'):
                    real_part, imag_part = num_val.as_real_imag()
                    if abs(imag_part.evalf()) < 1e-10:  # Essentially real
                        float_val = float(real_part)
                        if not any(abs(float_val - s) < 1e-9 for s in processed_solutions):
                            processed_solutions.append(float_val)
                            steps.append(f"คำตอบที่ {i+1}: {variable} ≈ {float_val:.10f} (จำนวนจริง)")
                    else:
                        steps.append(f"คำตอบที่ {i+1}: {variable} = {sol} (จำนวนเชิงซ้อน)")
                else:
                    steps.append(f"คำตอบที่ {i+1}: {variable} = {sol}")
            except Exception as e:
                steps.append(f"คำตอบที่ {i+1}: {variable} = {sol} (ไม่สามารถประเมินเป็นตัวเลขได้: {str(e)})")
        
        return {
            'success': True,
            'solutions': processed_solutions,
            'method': 'sympy_solve',
            'steps': '\\n'.join(steps),
            'variable': str(variable),
            'raw_input': equation_str
        }
'''
            
            # Find the start and end of the try block in solve_equation
            lines = fixed_code.split('\n')
            in_try_block = False
            try_start = -1
            try_end = -1
            
            for i, line in enumerate(lines):
                if 'def solve_equation(' in line:
                    # Find the try: statement after this
                    for j in range(i, min(i+50, len(lines))):
                        if lines[j].strip() == 'try:':
                            try_start = j
                            # Find the matching except
                            indent_level = len(lines[j]) - len(lines[j].lstrip())
                            for k in range(j+1, len(lines)):
                                curr_indent = len(lines[k]) - len(lines[k].lstrip()) if lines[k].strip() else indent_level + 4
                                if lines[k].strip().startswith('except') and curr_indent == indent_level:
                                    try_end = k
                                    break
                            break
                    break
            
            if try_start != -1 and try_end != -1:
                # Replace the try block content
                new_lines = lines[:try_start+1] + [new_implementation] + lines[try_end:]
                fixed_code = '\n'.join(new_lines)
        
        return fixed_code


def main():
    """Run the self-refinement process."""
    engine = SelfRefinementEngine(
        target_file="/workspace/tools/math.py",
        test_file="/workspace/tests/test_equation_solver.py"
    )
    
    result = engine.refine()
    
    print("\n" + "="*60)
    print("📊 SELF-REFINEMENT SUMMARY")
    print("="*60)
    print(f"Success: {result['success']}")
    print(f"Iterations: {result['iterations']}")
    
    if result['history']:
        print("\nIteration History:")
        for h in result['history']:
            status = "✅ PASS" if h['passed'] else "❌ FAIL"
            print(f"  Iteration {h['iteration']}: {status}")
    
    return result


if __name__ == "__main__":
    main()
