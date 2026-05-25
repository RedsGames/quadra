from src.application.interfaces.i_export_report_use_case import IExportReportUseCase
from src.application.interfaces.i_get_trip_summary_use_case import IGetTripSummaryUseCase
from src.application.interfaces.i_report_exporter import IReportExporter

class ExportReportUseCase(IExportReportUseCase):
    def __init__(self, summary_use_case: IGetTripSummaryUseCase, exporter: IReportExporter):
        self._summary_use_case = summary_use_case
        self._exporter = exporter

    def execute(self) -> str:
        summary = self._summary_use_case.execute()
        return self._exporter.export(summary)