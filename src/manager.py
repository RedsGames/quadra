from typing import List, Optional
from src.models import Trip
from src.repository import TripRepository

class TripManager:
    def __init__(self, repo: TripRepository):
        self.repo = repo
        self.trips: List[Trip] = self.repo.load_all()

    def add_trip(self, trip: Trip):
        self.trips.append(trip)
        self.repo.save_all(self.trips)

    def get_trip_by_name(self, name: str) -> Optional[Trip]:
        return next((t for t in self.trips if t.name == name), None)