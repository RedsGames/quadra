from src.domain.value_objects.expense_category import ExpenseCategory

class Expense:
    def __init__(self, amount: float, category: ExpenseCategory, custom_name: str | None = None):
        if amount <= 0:
            raise ValueError("Expense amount must be greater than zero")
        self._amount = amount
        self._category = category
        self._custom_name = custom_name.strip() if custom_name else None

    @property
    def amount(self) -> float:
        return self._amount

    @property
    def category(self) -> ExpenseCategory:
        return self._category

    @property
    def name(self) -> str:
        if self._category == ExpenseCategory.OTHER and self._custom_name:
            return self._custom_name
        
        names = {
            ExpenseCategory.FOOD: "Еда",
            ExpenseCategory.CLOTHING: "Одежда",
            ExpenseCategory.ENTERTAINMENT: "Развлечения",
            ExpenseCategory.HOTEL: "Отель",
            ExpenseCategory.TAXI: "Такси",
            ExpenseCategory.OTHER: "Прочее"
        }
        return names[self._category]