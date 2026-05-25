from abc import ABC, abstractmethod
from typing import List
from src.domain.entities.trip import Trip

class ITripRepository(ABC):
    @abstractmethod
    def save(self, trip: Trip) -> None:
        """
        Persists or updates the trip state.
        @param trip: Trip entity to persist.
        """
        pass

    @abstractmethod
    def get_active_trip(self) -> Trip | None:
        """
        Retrieves current active trip being edited.
        @return: Active Trip or None if none created or loaded.
        """
        pass

    @abstractmethod
    def set_active_trip(self, trip: Trip | None) -> None:
        """
        Sets the trip as currently active for editing.
        @param trip: Trip entity to activate or None to clear.
        """
        pass

    @abstractmethod
    def get_all(self) -> List[Trip]:
        """
        Retrieves all registered trips.
        @return: List of Trip entities.
        """
        pass

    @abstractmethod
    def find_by_name(self, query: str) -> List[Trip]:
        """
        Searches trips by partial case-insensitive name match.
        @param query: Search keyword.
        @return: List of found Trip entities.
        """
        pass