from enum import Enum

class ExpenseCategory(Enum):
    """
    Standard categories for trip expenses.
    """
    FOOD = 1
    CLOTHING = 2
    ENTERTAINMENT = 3
    HOTEL = 4
    TAXI = 5
    OTHER = 6