from dataclasses import dataclass

@dataclass(frozen=True)
class ExpenseCreateRequest:
    amount: float
    category_index: int
    custom_name: str | None = None