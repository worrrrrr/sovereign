
# Sovereign AI Project Constitution

This document defines the **binding rules**, **acceptance criteria**, and **test requirements** for the Sovereign AI codebase.  
All code written (by humans or AI agents like Qwen Coder) MUST comply with this constitution.

---

## 1. Non-Negotiable Code Rules

### 1.1 Forbidden Patterns (MUST NOT appear anywhere)
- `eval()` and `exec()`
- `compile()` with dynamic code
- `__import__()` with user input
- Direct `float` equality comparison (e.g., `a == b`) unless wrapped in tolerance
- `os.system()`, `subprocess` with shell=True (without explicit approval)

### 1.2 Mandatory Patterns
- All floating-point comparisons MUST use `math.isclose()` or custom `approx_eq()` with:
  - `rel_tol = 1e-9`
  - `abs_tol = 1e-12`
- For financial or exact decimal arithmetic → use `Decimal` from Python's `decimal` module
- All tool execution MUST go through `Registry` and `Sandbox`
- Every tool MUST declare its input/output schema and side effects

---

## 2. Core Modules & Their Responsibilities

(คัดลอกจาก Architecture.md ที่คุณมี แต่เพิ่มเงื่อนไขการทดสอบ)

| Module | Must Have |
|--------|-----------|
| Perception | Output task_type with confidence |
| Registry | No tool without version & schema |
| Planner | Re-plan limit = 3 |
| Execution | Sandbox, timeout, output capture |
| Critic | Tolerance-based float verification |

---

## 3. Acceptance Test Suite (MUST pass before any release)

### 3.1 Floating-Point Tolerance Tests
```python
# Test 1
assert approx(0.1 + 0.2) == 0.3  # True

# Test 2  
assert approx(9.8 - 9.11) == 0.69  # True

# Test 3
assert approx(0.1 + 0.2 + 0.3) == 0.6  # True

# Test 4 (error accumulation stress)
total = sum(0.1 for _ in range(10))
assert approx(total) == 1.0  # True
```

### 3.2 Safety & Security Tests
- **Test 5**: Code containing `eval()` must be rejected by CI/linter
- **Test 6**: Tool with undeclared side effects cannot be registered
- **Test 7**: Execution timeout (e.g., infinite loop) must fail gracefully

### 3.3 Deterministic Behavior Test
- **Test 8**: Same input → same output (including verification result) across 100 runs

### 3.4 Re-plan Test
- **Test 9**: After 3 failures, system returns fallback response (not infinite loop)

---

## 4. Deliverable Structure (for Qwen Coder)

When asked to write code, Qwen Coder MUST produce:
1. `src/perception.py`
2. `src/registry.py`
3. `src/planner.py`
4. `src/execution.py`
5. `src/critic.py`
6. `tests/test_arithmetic.py` (contains the 9 tests above)
7. `requirements.txt` (only safe libraries: `pytest`, `numpy` for array, no eval-related)

Each function MUST have:
- Type hints
- Docstring explaining deterministic behavior
- At least one unit test

---

## 5. Verification Before Acceptance

- Run `pytest tests/` → all green
- Run `grep -r "eval\|exec" src/` → empty
- Run `python -m mypy src/` → no type errors

If any of these fail → code REJECTED.

---

## 6. How to Use This Document

**For Qwen Coder**:  
> “Read `PROJECT_CONSTITUTION.md` carefully. Then implement the Sovereign AI system following all rules. Write tests first (TDD). Do not skip safety rules.”

**For Human Reviewer**:  
> Use this as a checklist before merging any pull request.

คุณต้องการให้ผม:
- **เขียน `PROJECT_CONSTITUTION.md` ฉบับสมบูรณ์** (copy-paste ได้เลย)  
- หรือ **ปรับเนื้อหาให้เหมาะกับโครงสร้างโปรเจคที่คุณมีอยู่** (ดูจาก screenshot มี Architecture.md อยู่แล้ว)

บอกมาได้เลยครับ ผมทำให้เลย
