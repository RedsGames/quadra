from dataclasses import dataclass
from datetime import date
from typing import List

@dataclass(frozen=True)
class TripCreateRequest:
    name: str
    start_date: date
    end_date: date
    people_count: int
    ticket_price_per_person: float

@dataclass(frozen=True)
class TripUpdateRequest:
    name: str
    start_date: date
    end_date: date
    people_count: int
    ticket_price_per_person: float

@dataclass(frozen=True)
class TripSearchResultItem:
    name: str
    start_date: str
    end_date: str

@dataclass(frozen=True)
class ExpenseItemResponse:
    category_name: str
    amount: float

@dataclass(frozen=True)
class TripSummaryResponse:
    name: str
    start_date: str
    end_date: str
    people_count: int
    ticket_price_per_person: float
    transport_total: float
    expenses_total: float
    grand_total: float
    cost_per_person: float
    expenses: List[ExpenseItemResponse]