"""
Calculator module providing basic mathematical operations.

This module contains the Calculator class which implements
basic arithmetic operations with proper error handling.
"""


class Calculator:
    """A simple calculator class for basic mathematical operations.

    This class provides methods for addition, subtraction,
    multiplication, and division with proper error handling.
    """

    def add(self, a: float, b: float) -> float:
        """Add two numbers together.

        Args:
            a: The first number
            b: The second number

        Returns:
            The sum of a and b
        """
        return a + b

    def subtract(self, a: float, b: float) -> float:
        """Subtract the second number from the first.

        Args:
            a: The number to subtract from
            b: The number to subtract

        Returns:
            The difference of a and b
        """
        return a - b

    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers together.

        Args:
            a: The first number
            b: The second number

        Returns:
            The product of a and b
        """
        return a * b

    def divide(self, a: float, b: float) -> float:
        """Divide the first number by the second.

        Args:
            a: The dividend
            b: The divisor

        Returns:
            The quotient of a and b

        Raises:
            ZeroDivisionError: If b is zero
        """
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return a / b
