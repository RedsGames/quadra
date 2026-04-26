from abc import ABC, abstractmethod
from typing import List
from src.domain.types import Transaction, TransactionFilter, TransactionType

class ITransactionRepository(ABC):
    @abstractmethod
    def add(self, transaction: Transaction) -> None:
        pass

    @abstractmethod
    def update(self, transaction: Transaction) -> None:
        pass

    @abstractmethod
    def delete(self, transaction_id: int) -> None:
        pass

    @abstractmethod
    def get_filtered(self, filters: TransactionFilter) -> List[Transaction]:
        pass

    @abstractmethod
    def get_categories(self) -> List[str]:
        pass

    @abstractmethod
    def get_categories_by_type(self, tx_type: TransactionType) -> List[str]:
        pass

    @abstractmethod
    def add_category(self, name: str) -> None:
        pass