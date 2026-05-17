import unittest
from src.models import Trip, Expense, Category
from src.calculator import BudgetCalculator

class TestBudget(unittest.TestCase):
    def test_calculation(self):
        t = Trip("1", "Test", "2026-01-01", 2)
        t.expenses.append(Expense("A", 100.0, Category.FOOD))
        t.expenses.append(Expense("B", 50.0, Category.FOOD))
        self.assertEqual(BudgetCalculator.calculate_total(t), 150.0)
        self.assertEqual(BudgetCalculator.calculate_per_person(t), 75.0)

if __name__ == "__main__":
    unittest.main()