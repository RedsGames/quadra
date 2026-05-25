from abc import ABC, abstractmethod

class IManageExpensesUseCase(ABC):
    @abstractmethod
    def update_amount(self, index: int, amount: float) -> None:
        """
        Updates the financial amount of an existing expense by its index.
        @param index: Positional index of the expense in the active trip list.
        @param amount: New positive expense amount.
        @raises ValueError: If no active trip is selected or index is out of bounds.
        """
        pass

    @abstractmethod
    def update_category(self, index: int, category_index: int, custom_name: str | None) -> None:
        """
        Updates the category type of an existing expense by its index.
        @param index: Positional index of the expense.
        @param category_index: New category identifier.
        @param custom_name: Custom name if category is OTHER (6).
        @raises ValueError: If no active trip is found or inputs are invalid.
        """
        pass

    @abstractmethod
    def delete_expense(self, index: int) -> None:
        """
        Deletes an expense item by its index.
        @param index: Positional index of the expense to delete.
        @raises ValueError: If no active trip is found.
        """
        pass