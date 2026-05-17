from dataclasses import dataclass, field
from typing import List
from enum import Enum

class Category(Enum):
    TRANSPORT = "Транспорт"
    ACCOMMODATION = "Жильё"
    FOOD = "Еда"
    ENTERTAINMENT = "Развлечения"
    SAFETY_NET = "Подушка безопасности"
    OTHER = "Прочее"
    CUSTOM = "Пользовательская"

    @classmethod
    def from_input(cls, choice: str):
        mapping = {
            "1": cls.TRANSPORT,
            "2": cls.ACCOMMODATION,
            "3": cls.FOOD,
            "4": cls.ENTERTAINMENT,
            "5": cls.SAFETY_NET,
            "6": cls.OTHER
        }
        return mapping.get(choice)

    @classmethod
    def from_str(cls, value: str):
        for member in cls:
            if member.value == value:
                return member
        # Если не нашли, создаем "кастомную" категорию
        obj = cls.CUSTOM
        obj._value_ = value
        return obj

@dataclass
class Expense:
    name: str
    amount: float
    category: Category

@dataclass
class Trip:
    id: str
    name: str
    dates: str
    people_count: int
    expenses: List[Expense] = field(default_factory=list)