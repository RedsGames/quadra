from abc import ABC, abstractmethod
from src.application.dto.trip_dto import TripUpdateRequest

class IUpdateTripUseCase(ABC):
    @abstractmethod
    def execute(self, request: TripUpdateRequest) -> None:
        """
        Updates metadata fields of the active trip.
        @param request: TripUpdateRequest DTO containing new metadata.
        @raises ValueError: If no active trip is selected or constraints are violated.
        """
        pass