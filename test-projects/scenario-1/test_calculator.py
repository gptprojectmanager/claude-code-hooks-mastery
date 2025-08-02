"""
Test suite for Calculator class.

This module contains comprehensive tests for the Calculator class,
including parametrized tests and edge case coverage.
"""

import pytest
from calculator import Calculator


class TestCalculator:
    """Test cases for Calculator class."""

    @pytest.fixture
    def calc(self):
        """Create a Calculator instance for testing."""
        return Calculator()

    @pytest.mark.parametrize("a,b,expected", [
        (2, 3, 5),
        (0, 5, 5),
        (-2, 3, 1),
        (-5, -3, -8),
        (10.5, 2.5, 13.0),
        (100, 0, 100)
    ])
    def test_add(self, calc, a, b, expected):
        """Test addition operation with various inputs."""
        assert calc.add(a, b) == expected

    @pytest.mark.parametrize("a,b,expected", [
        (5, 3, 2),
        (0, 5, -5),
        (-2, 3, -5),
        (-5, -3, -2),
        (10.5, 2.5, 8.0),
        (100, 100, 0)
    ])
    def test_subtract(self, calc, a, b, expected):
        """Test subtraction operation with various inputs."""
        assert calc.subtract(a, b) == expected

    @pytest.mark.parametrize("a,b,expected", [
        (2, 3, 6),
        (0, 5, 0),
        (-2, 3, -6),
        (-5, -3, 15),
        (2.5, 4, 10.0),
        (100, 0, 0)
    ])
    def test_multiply(self, calc, a, b, expected):
        """Test multiplication operation with various inputs."""
        assert calc.multiply(a, b) == expected

    @pytest.mark.parametrize("a,b,expected", [
        (6, 3, 2),
        (0, 5, 0),
        (-6, 3, -2),
        (-6, -3, 2),
        (10.0, 2.5, 4.0),
        (100, 4, 25)
    ])
    def test_divide(self, calc, a, b, expected):
        """Test division operation with various inputs."""
        assert calc.divide(a, b) == expected

    def test_divide_by_zero_positive(self, calc):
        """Test division by zero with positive dividend."""
        with pytest.raises(ZeroDivisionError, match="Cannot divide by zero"):
            calc.divide(5, 0)

    def test_divide_by_zero_negative(self, calc):
        """Test division by zero with negative dividend."""
        with pytest.raises(ZeroDivisionError, match="Cannot divide by zero"):
            calc.divide(-5, 0)

    def test_divide_by_zero_zero(self, calc):
        """Test division by zero with zero dividend."""
        with pytest.raises(ZeroDivisionError, match="Cannot divide by zero"):
            calc.divide(0, 0)

    def test_large_numbers(self, calc):
        """Test operations with large numbers."""
        large_num = 1e10
        assert calc.add(large_num, large_num) == 2e10
        assert calc.multiply(large_num, 2) == 2e10

    def test_small_numbers(self, calc):
        """Test operations with very small numbers."""
        small_num = 1e-10
        assert abs(calc.add(small_num, small_num) - 2e-10) < 1e-15
        assert abs(calc.multiply(small_num, 2) - 2e-10) < 1e-15

    def test_float_precision(self, calc):
        """Test floating point precision edge cases."""
        # Test cases that might have precision issues
        result = calc.add(0.1, 0.2)
        assert abs(result - 0.3) < 1e-10

        result = calc.divide(1, 3)
        expected = 1 / 3
        assert abs(result - expected) < 1e-15
