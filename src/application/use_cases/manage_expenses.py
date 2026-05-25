from src.application.interfaces.i_manage_expenses_use_case import IManageExpensesUseCase
from src.domain.value_objects.expense_category import ExpenseCategory
from src.domain.repositories.i_trip_repository import ITripRepository

class ManageExpensesUseCase(IManageExpensesUseCase):
    def __init__(self, repository: ITripRepository):
        self._repository = repository

    def update_amount(self, index: int, amount: float) -> None:
        trip = self._repository.get_active_trip()
        if not trip:
            raise ValueError("No active trip found")
        trip.update_expense_amount(index, amount)
        self._repository.save(trip)

    def update_category(self, index: int, category_index: int, custom_name: str | None) -> None:
        trip = self._repository.get_active_trip()
        if not trip:
            raise ValueError("No active trip found")
        try:
            category = ExpenseCategory(category_index)
        except ValueError:
            raise ValueError("Invalid category index")
        trip.update_expense_category(index, category, custom_name)
        self._repository.save(trip)

    def delete_expense(self, index: int) -> None:
        trip = self._repository.get_active_trip()
        if not trip:
            raise ValueError("No active trip found")
        trip.delete_expense(index)
        self._repository.save(trip)