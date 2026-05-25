from typing import List
from src.application.interfaces.i_search_trips_use_case import ISearchTripsUseCase
from src.application.dto.trip_dto import TripSearchResultItem
from src.domain.repositories.i_trip_repository import ITripRepository

class SearchTripsUseCase(ISearchTripsUseCase):
    def __init__(self, repository: ITripRepository):
        self._repository = repository

    def search(self, query: str) -> List[TripSearchResultItem]:
        trips = self._repository.find_by_name(query)
        return [
            TripSearchResultItem(
                name=t.name,
                start_date=t.start_date.strftime("%d.%m.%Y"),
                end_date=t.end_date.strftime("%d.%m.%Y")
            )
            for t in trips
        ]

    def get_all(self) -> List[TripSearchResultItem]:
        trips = self._repository.get_all()
        return [
            TripSearchResultItem(
                name=t.name,
                start_date=t.start_date.strftime("%d.%m.%Y"),
                end_date=t.end_date.strftime("%d.%m.%Y")
            )
            for t in trips
        ]

    def select_trip(self, index: int, trips_list: List[TripSearchResultItem]) -> None:
        if index < 0 or index >= len(trips_list):
            raise ValueError("Index out of range")
        
        selected_dto = trips_list[index]
        all_trips = self._repository.get_all()
        
        for t in all_trips:
            if (t.name == selected_dto.name and 
                t.start_date.strftime("%d.%m.%Y") == selected_dto.start_date and 
                t.end_date.strftime("%d.%m.%Y") == selected_dto.end_date):
                self._repository.set_active_trip(t)
                return
        
        raise ValueError("Selected trip not found in repository")