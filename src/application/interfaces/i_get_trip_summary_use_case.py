from abc import ABC, abstractmethod
from src.application.dto.trip_dto import TripSummaryResponse

class IGetTripSummaryUseCase(ABC):
    @abstractmethod
    def execute(self) -> TripSummaryResponse:
        """
        Processes complex calculation logic for totals and returns compiled financial summary.
        @return: Aggregated DTO containing totals and averages.
        @raises ValueError: If active trip doesn't exist.
        """
        pass