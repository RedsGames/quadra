from abc import ABC, abstractmethod
from src.application.dto.trip_dto import TripSummaryResponse

class IReportExporter(ABC):
    @abstractmethod
    def export(self, summary: TripSummaryResponse) -> str:
        """
        Generates a formatted text file report from the given summary response.
        
        @param summary: Aggregated financial DTO.
        @return: Relative path to the written file.
        @raises IOError: If disk write permission is denied.
        """
        pass