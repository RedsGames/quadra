from abc import ABC, abstractmethod
from typing import List
from src.application.dto.trip_dto import TripSearchResultItem

class ISearchTripsUseCase(ABC):
    @abstractmethod
    def search(self, query: str) -> List[TripSearchResultItem]:
        """
        Searches all trips by query string and returns simple response list.
        @param query: Keyword for lookup.
        @return: List of TripSearchResultItem DTOs.
        """
        pass

    @abstractmethod
    def get_all(self) -> List[TripSearchResultItem]:
        """
        Lists all available trips.
        @return: List of TripSearchResultItem DTOs.
        """
        pass

    @abstractmethod
    def select_trip(self, index: int, trips_list: List[TripSearchResultItem]) -> None:
        """
        Marks chosen trip as currently active for other use cases.
        @param index: Selected index from the list.
        @param trips_list: List of previously searched results.
        @raises ValueError: If index is invalid or trip cannot be found.
        """
        pass