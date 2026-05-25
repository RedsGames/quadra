from abc import ABC, abstractmethod

class IExportReportUseCase(ABC):
    @abstractmethod
    def execute(self) -> str:
        """
        Orchestrates trip report generation and file persistence.
        
        @return: Saved filename path.
        @raises ValueError: If no active trip is selected.
        @raises IOError: If file writing fails.
        """
        pass