"""Сервис калькулятора бюджета поездки."""
import json
import os
import uuid
from dataclasses import dataclass, asdict, field
from typing import Optional


@dataclass
class TripProfile:
    id: str
    name: str
    destination: str
    currency: str
    budget_items: list[dict]
    total_base: float = 0.0
    total_converted: float = 0.0
    target_currency: str = "RUB"
    notes: str = ""

    def to_dict(self):
        return asdict(self)


class BudgetService:
    def __init__(self, filepath: str = "data/budgets.json"):
        self.filepath = filepath
        self._profiles: dict[str, TripProfile] = {}
        self._load()

    def _load(self):
        if not os.path.exists(self.filepath):
            return
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                p = TripProfile(**item)
                self._profiles[p.id] = p
        except (json.JSONDecodeError, IOError, TypeError):
            pass

    def _save(self):
        os.makedirs(os.path.dirname(self.filepath) or ".", exist_ok=True)
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump([p.to_dict() for p in self._profiles.values()], f, ensure_ascii=False, indent=4)

    def create_profile(
        self,
        name: str,
        destination: str,
        currency: str,
        budget_items: list[dict],
        target_currency: str = "RUB",
        notes: str = "",
    ) -> TripProfile:
        trip_id = str(uuid.uuid4())[:8]
        total_base = sum(item.get("amount", 0) for item in budget_items)
        profile = TripProfile(
            id=trip_id,
            name=name,
            destination=destination,
            currency=currency,
            budget_items=budget_items,
            total_base=total_base,
            total_converted=0.0,
            target_currency=target_currency,
            notes=notes,
        )
        self._profiles[trip_id] = profile
        self._save()
        return profile

    def get_profile(self, trip_id: str) -> Optional[TripProfile]:
        return self._profiles.get(trip_id)

    def list_profiles(self) -> list[TripProfile]:
        return list(self._profiles.values())

    def update_converted(self, trip_id: str, rate: float):
        """Сохраняет итог после конвертации валют."""
        profile = self._profiles.get(trip_id)
        if profile:
            profile.total_converted = round(profile.total_base * rate, 2)
            self._save()

    def delete_profile(self, trip_id: str) -> bool:
        if trip_id in self._profiles:
            del self._profiles[trip_id]
            self._save()
            return True
        return False
