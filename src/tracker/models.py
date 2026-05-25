from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Transaction:
    id: int
    type: str
    category: str
    amount: float
    date: str
    description: Optional[str] = ""

    def to_dict(self):
        return asdict(self)
