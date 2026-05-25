from src.application.interfaces.i_add_expense_use_case import IAddExpenseUseCase
from src.application.dto.expense_dto import ExpenseCreateRequest
from src.domain.entities.expense import Expense
from src.domain.value_objects.expense_category import ExpenseCategory
from src.domain.repositories.i_trip_repository import ITripRepository

class AddExpenseUseCase(IAddExpenseUseCase):
    def __init__(self, repository: ITripRepository):
        self._repository = repository

    def execute(self, request: ExpenseCreateRequest) -> None:
        trip = self._repository.get_active_trip()
        if not trip:
            raise ValueError("No active trip found")

        try:
            category = ExpenseCategory(request.category_index)
        except ValueError:
            raise ValueError("Invalid category index")

        expense = Expense(
            amount=request.amount,
            category=category,
            custom_name=request.custom_name
        )
        trip.add_expense(expense)
        self._repository.save(trip)