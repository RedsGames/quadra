from abc import ABC, abstractmethod
from src.application.dto.trip_dto import TripCreateRequest

class ICreateTripUseCase(ABC):
    @abstractmethod
    def execute(self, request: TripCreateRequest) -> None:
        """
        Validates parameters and registers a new active trip.
        @param request: DTO containing core trip parameters.
        @raises ValueError: If business constraints are broken.
        """
        pass