import json
import os
from datetime import datetime
from typing import List
from src.domain.repositories.i_trip_repository import ITripRepository
from src.domain.entities.trip import Trip
from src.domain.entities.expense import Expense
from src.domain.value_objects.expense_category import ExpenseCategory

class JsonTripRepository(ITripRepository):
    def __init__(self, filepath: str = "trips.json"):
        self._filepath = filepath
        self._trips: List[Trip] = []
        self._active_trip: Trip | None = None
        self._load_from_file()

    def save(self, trip: Trip) -> None:
        if trip not in self._trips:
            self._trips.append(trip)
        self._active_trip = trip
        self._save_to_file()

    def get_active_trip(self) -> Trip | None:
        return self._active_trip

    def set_active_trip(self, trip: Trip | None) -> None:
        self._active_trip = trip

    def get_all(self) -> List[Trip]:
        return self._trips.copy()

    def find_by_name(self, query: str) -> List[Trip]:
        normalized_query = query.strip().lower()
        return [
            t for t in self._trips
            if normalized_query in t.name.lower()
        ]

    def _load_from_file(self) -> None:
        if not os.path.exists(self._filepath):
            return
        
        try:
            with open(self._filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            self._trips = []
            for trip_data in data:
                start_date = datetime.strptime(trip_data["start_date"], "%Y-%m-%d").date()
                end_date = datetime.strptime(trip_data["end_date"], "%Y-%m-%d").date()
                trip = Trip(
                    name=trip_data["name"],
                    start_date=start_date,
                    end_date=end_date,
                    people_count=trip_data["people_count"],
                    ticket_price_per_person=trip_data["ticket_price_per_person"]
                )
                for exp_data in trip_data.get("expenses", []):
                    expense = Expense(
                        amount=exp_data["amount"],
                        category=ExpenseCategory(exp_data["category"]),
                        custom_name=exp_data.get("custom_name")
                    )
                    trip.add_expense(expense)
                self._trips.append(trip)
        except (json.JSONDecodeError, KeyError, ValueError):
            pass

    def _save_to_file(self) -> None:
        data = []
        for t in self._trips:
            expenses_data = [
                {
                    "amount": e.amount,
                    "category": e.category.value,
                    "custom_name": e._custom_name
                }
                for e in t.expenses
            ]
            trip_dict = {
                "name": t.name,
                "start_date": t.start_date.strftime("%Y-%m-%d"),
                "end_date": t.end_date.strftime("%Y-%m-%d"),
                "people_count": t.people_count,
                "ticket_price_per_person": t.ticket_price_per_person,
                "expenses": expenses_data
            }
            data.append(trip_dict)
            
        with open(self._filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)