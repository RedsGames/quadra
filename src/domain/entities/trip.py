from datetime import date
from typing import List
from src.domain.entities.expense import Expense
from src.domain.value_objects.expense_category import ExpenseCategory

class Trip:
    def __init__(self, name: str, start_date: date, end_date: date, people_count: int, ticket_price_per_person: float):
        self._validate(name, start_date, end_date, people_count, ticket_price_per_person)
        self._name = name.strip()
        self._start_date = start_date
        self._end_date = end_date
        self._people_count = people_count
        self._ticket_price_per_person = ticket_price_per_person
        self._expenses: List[Expense] = []

    def update_metadata(self, name: str, start_date: date, end_date: date, people_count: int, ticket_price_per_person: float) -> None:
        self._validate(name, start_date, end_date, people_count, ticket_price_per_person)
        self._name = name.strip()
        self._start_date = start_date
        self._end_date = end_date
        self._people_count = people_count
        self._ticket_price_per_person = ticket_price_per_person

    def _validate(self, name: str, start_date: date, end_date: date, people_count: int, ticket_price_per_person: float) -> None:
        if not name.strip():
            raise ValueError("Trip name cannot be empty")
        if people_count <= 0:
            raise ValueError("People count must be greater than zero")
        if end_date < start_date:
            raise ValueError("End date cannot be earlier than start date")
        if ticket_price_per_person < 0:
            raise ValueError("Ticket price cannot be negative")

    @property
    def name(self) -> str:
        return self._name

    @property
    def start_date(self) -> date:
        return self._start_date

    @property
    def end_date(self) -> date:
        return self._end_date

    @property
    def people_count(self) -> int:
        return self._people_count

    @property
    def ticket_price_per_person(self) -> float:
        return self._ticket_price_per_person

    @property
    def expenses(self) -> List[Expense]:
        return self._expenses.copy()

    def add_expense(self, expense: Expense) -> None:
        self._expenses.append(expense)

    def update_expense_amount(self, index: int, amount: float) -> None:
        if index < 0 or index >= len(self._expenses):
            raise ValueError("Invalid expense index")
        exp = self._expenses[index]
        self._expenses[index] = Expense(amount, exp.category, exp._custom_name)

    def update_expense_category(self, index: int, category: ExpenseCategory, custom_name: str | None) -> None:
        if index < 0 or index >= len(self._expenses):
            raise ValueError("Invalid expense index")
        exp = self._expenses[index]
        self._expenses[index] = Expense(exp.amount, category, custom_name)

    def delete_expense(self, index: int) -> None:
        if index < 0 or index >= len(self._expenses):
            raise ValueError("Invalid expense index")
        self._expenses.pop(index)

    def calculate_transport_total(self) -> float:
        return self._ticket_price_per_person * self._people_count

    def calculate_expenses_total(self) -> float:
        return sum(expense.amount for expense in self._expenses)

    def calculate_grand_total(self) -> float:
        return self.calculate_transport_total() + self.calculate_expenses_total()

    def calculate_cost_per_person(self) -> float:
        return self.calculate_grand_total() / self._people_count