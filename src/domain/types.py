from dataclasses import dataclass
from enum import Enum
from datetime import date
from typing import Optional, List, Dict

class TransactionType(Enum):
    INCOME = "Доход"
    EXPENSE = "Расход"

@dataclass
class Transaction:
    id: Optional[int]
    amount: float
    category: str
    date_added: date
    type: TransactionType
    description: str = ""

@dataclass
class TransactionFilter:
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    category: Optional[str] = None
    type: Optional[TransactionType] = None

@dataclass
class DashboardSummary:
    total_income: float
    total_expense: float
    balance: float
    expense_by_category: Dict[str, float] 
    balance_history: Dict[str, float]