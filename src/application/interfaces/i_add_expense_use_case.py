from abc import ABC, abstractmethod
from src.application.dto.expense_dto import ExpenseCreateRequest

class IAddExpenseUseCase(ABC):
    @abstractmethod
    def execute(self, request: ExpenseCreateRequest) -> None:
        """
        Binds a validated expense item to the active trip.
        @param request: DTO containing expense amount, category index and optional name.
        @raises ValueError: If active trip doesn't exist or input data is incorrect.
        """
        pass