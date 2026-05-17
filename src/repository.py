import json
from typing import List
from src.models import Trip, Expense, Category

class TripRepository:
    def __init__(self, filename: str = "trips.json"):
        self.filename = filename

    def save_all(self, trips: List[Trip]):
        data =[]
        for trip in trips:
            data.append({
                "id": trip.id,
                "name": trip.name,
                "dates": trip.dates,
                "people_count": trip.people_count,
                "expenses":[
                    {"name": e.name, "amount": e.amount, "category": e.category.value}
                    for e in trip.expenses
                ]
            })
        with open(self.filename, 'w') as f:
            json.dump(data, f, indent=4)

    def load_all(self) -> List[Trip]:
        try:
            with open(self.filename, 'r') as f:
                data = json.load(f)
                trips =[]
                for item in data:
                    trip = Trip(item['id'], item['name'], item['dates'], item['people_count'])
                    for exp in item['expenses']:
                        trip.expenses.append(Expense(exp['name'], exp['amount'], Category.from_str(exp['category'])))
                    trips.append(trip)
                return trips
        except (FileNotFoundError, json.JSONDecodeError):
            return[]