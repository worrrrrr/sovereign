"""
Test Suite for Mathematical Equation Solving

Tests for solving exponential equations like 3^x = x^9 and 4^x = x^8
using Lambert W function and numerical methods.
"""
import pytest
import sympy
from sympy import LambertW as lambertw


class TestExponentialEquations:
    """Test suite for solving exponential equations."""
    
    def test_01_solve_3_pow_x_equals_x_pow_9(self):
        """Test solving 3^x = x^9 using Lambert W function."""
        # Equation: 3^x = x^9
        # Transform: x * ln(3) = 9 * ln(x)
        # Solution using Lambert W: x = -9 * W(-ln(3)/9) / ln(3)
        
        val = -sympy.log(3) / 9
        
        # Branch k=0 (default) gives the smaller solution
        solution_k0 = -9 * lambertw(val) / sympy.log(3)
        sol_k0_numeric = float(solution_k0.evalf())
        
        # Branch k=-1 gives the larger solution (x=27)
        solution_k_minus1 = -9 * lambertw(val, -1) / sympy.log(3)
        sol_k_minus1_numeric = float(solution_k_minus1.evalf())
        
        # Verify the solutions
        # For k=0: approximately 1.15-1.37
        assert 1.0 < sol_k0_numeric < 2.0, f"Solution k=0 should be between 1 and 2, got {sol_k0_numeric}"
        
        # For k=-1: exactly 27
        assert abs(sol_k_minus1_numeric - 27.0) < 0.001, f"Solution k=-1 should be 27, got {sol_k_minus1_numeric}"
        
        # Verify by substitution
        x1 = sol_k0_numeric
        lhs1 = 3 ** x1
        rhs1 = x1 ** 9
        assert abs(lhs1 - rhs1) / max(lhs1, rhs1) < 1e-6, f"3^{x1} != {x1}^9"
        
        x2 = 27.0
        lhs2 = 3 ** x2
        rhs2 = x2 ** 9
        assert abs(lhs2 - rhs2) / max(lhs2, rhs2) < 1e-10, f"3^{x2} != {x2}^9"
    
    def test_02_count_real_solutions_3_pow_x_equals_x_pow_9(self):
        """Test that 3^x = x^9 has exactly 2 real solutions."""
        val = -sympy.log(3) / 9
        
        # Get both branches
        solutions = []
        for k in [None, -1]:  # None means default branch (k=0)
            try:
                if k is None:
                    sol = -9 * lambertw(val) / sympy.log(3)
                else:
                    sol = -9 * lambertw(val, k) / sympy.log(3)
                sol_numeric = sol.evalf()
                if sol_numeric.is_real:
                    solutions.append(float(sol_numeric))
            except:
                pass
        
        # Should have exactly 2 real solutions
        assert len(solutions) == 2, f"Expected 2 real solutions, got {len(solutions)}: {solutions}"
        
        # One should be ~1.15-1.37, one should be 27
        solutions.sort()
        assert 1.0 < solutions[0] < 2.0, f"First solution should be between 1 and 2, got {solutions[0]}"
        assert abs(solutions[1] - 27.0) < 0.001, f"Second solution should be 27, got {solutions[1]}"
    
    def test_03_solve_4_pow_x_equals_x_pow_8(self):
        """Test solving 4^x = x^8 using Lambert W function."""
        # Equation: 4^x = x^8
        # Transform: x * ln(4) = 8 * ln(x)
        # Solution: x = -8 * W(-ln(4)/8) / ln(4)
        
        val = -sympy.log(4) / 8
        
        solutions = []
        for k in [None, -1]:  # None means default branch (k=0)
            try:
                if k is None:
                    sol = -8 * lambertw(val) / sympy.log(4)
                else:
                    sol = -8 * lambertw(val, k) / sympy.log(4)
                sol_numeric = sol.evalf()
                if sol_numeric.is_real:
                    solutions.append(float(sol_numeric))
            except:
                pass
        
        # Should have at least 2 positive real solutions
        assert len(solutions) >= 2, f"Expected at least 2 real solutions, got {len(solutions)}"
        
        # One should be exactly 16
        solutions_sorted = sorted(solutions)
        # Check if any solution is close to 16
        found_16 = any(abs(s - 16.0) < 0.001 for s in solutions_sorted)
        assert found_16, f"One solution should be 16, got {solutions_sorted}"
        
        # Verify x=16
        x = 16.0
        lhs = 4 ** x
        rhs = x ** 8
        assert abs(lhs - rhs) / max(lhs, rhs) < 1e-10, f"4^{x} != {x}^8"
    
    def test_04_verify_solution_substitution(self):
        """Test that solutions satisfy the original equation by direct substitution."""
        # Test case 1: 3^27 = 27^9
        x = 27
        lhs = 3 ** x
        rhs = x ** 9
        assert lhs == rhs, f"3^{x} should equal {x}^9"
        
        # Test case 2: 4^16 = 16^8
        x = 16
        lhs = 4 ** x
        rhs = x ** 8
        assert lhs == rhs, f"4^{x} should equal {x}^8"
    
    def test_05_lambert_w_branches(self):
        """Test understanding of Lambert W function branches."""
        # For equation a^x = x^b where a, b > 0
        # The argument to Lambert W is: -ln(a)/b
        # Real solutions exist when argument >= -1/e
        
        # Test with 3^x = x^9
        arg = -sympy.log(3) / 9
        threshold = -1 / sympy.E
        
        # Argument should be greater than -1/e for real solutions
        assert arg > threshold, f"Argument {arg} should be > {threshold} for real solutions"
        
        # Both branches k=0 (default) and k=-1 should give real solutions
        sol_k0 = lambertw(arg)
        sol_k_minus1 = lambertw(arg, -1)
        
        assert sol_k0.is_real, "Branch k=0 should give real solution"
        assert sol_k_minus1.is_real, "Branch k=-1 should give real solution"
    
    def test_06_edge_case_equal_bases(self):
        """Test edge case where base equals exponent base."""
        # Equation: 2^x = x^2
        # Known solutions: x = 2, x = 4
        
        val = -sympy.log(2) / 2
        
        solutions = []
        for k in [None, -1]:  # None means default branch (k=0)
            try:
                if k is None:
                    sol = -2 * lambertw(val) / sympy.log(2)
                else:
                    sol = -2 * lambertw(val, k) / sympy.log(2)
                sol_numeric = sol.evalf()
                if sol_numeric.is_real:
                    solutions.append(float(sol_numeric))
            except:
                pass
        
        # Should find solutions close to 2 and 4
        solutions_sorted = sorted(solutions)
        assert len(solutions_sorted) >= 2, f"Expected at least 2 solutions for 2^x = x^2"
        
        # Check for solutions near 2 and 4
        found_2 = any(abs(s - 2.0) < 0.1 for s in solutions_sorted)
        found_4 = any(abs(s - 4.0) < 0.1 for s in solutions_sorted)
        
        assert found_2, "Should find solution near 2"
        assert found_4, "Should find solution near 4"


class TestNumericalVerification:
    """Test suite for numerical verification of solutions."""
    
    def test_07_numerical_tolerance(self):
        """Test that solutions are within acceptable numerical tolerance."""
        from core.utils import approx_eq
        
        # Test 3^27 = 27^9
        x = 27
        lhs = 3 ** x
        rhs = x ** 9
        assert approx_eq(float(lhs), float(rhs), rel_tol=1e-10)
        
        # Test 4^16 = 16^8
        x = 16
        lhs = 4 ** x
        rhs = x ** 8
        assert approx_eq(float(lhs), float(rhs), rel_tol=1e-10)
    
    def test_08_approximate_solution_accuracy(self):
        """Test accuracy of approximate solutions."""
        # For 3^x = x^9, the smaller solution is approximately 1.15-1.37
        # Let's verify it numerically
        
        # Binary search or Newton's method could be used
        # Here we just verify a known approximate value
        x_approx = 1.150825  # From earlier calculation
        
        lhs = 3 ** x_approx
        rhs = x_approx ** 9
        
        # Relative error should be small
        rel_error = abs(lhs - rhs) / max(lhs, rhs)
        assert rel_error < 0.01, f"Relative error {rel_error} too large for approximate solution"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
