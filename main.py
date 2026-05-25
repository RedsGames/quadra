import sys
from src.infrastructure.repositories.json_trip_repository import JsonTripRepository
from src.infrastructure.exporters.txt_report_exporter import TxtReportExporter
from src.application.use_cases.create_trip import CreateTripUseCase
from src.application.use_cases.update_trip import UpdateTripUseCase
from src.application.use_cases.search_trips import SearchTripsUseCase
from src.application.use_cases.add_expense import AddExpenseUseCase
from src.application.use_cases.get_trip_summary import GetTripSummaryUseCase
from src.application.use_cases.export_report import ExportReportUseCase
from src.application.use_cases.manage_expenses import ManageExpensesUseCase
from src.infrastructure.cli.console_form import ConsoleForm, ExitSignal

def main() -> None:
    repository = JsonTripRepository()
    exporter = TxtReportExporter()
    
    create_use_case = CreateTripUseCase(repository)
    update_use_case = UpdateTripUseCase(repository)
    search_use_case = SearchTripsUseCase(repository)
    add_expense_use_case = AddExpenseUseCase(repository)
    summary_use_case = GetTripSummaryUseCase(repository)
    export_use_case = ExportReportUseCase(summary_use_case, exporter)
    manage_expenses_use_case = ManageExpensesUseCase(repository)
    
    form = ConsoleForm(
        create_use_case,
        update_use_case,
        search_use_case,
        add_expense_use_case,
        summary_use_case,
        export_use_case,
        manage_expenses_use_case
    )
    
    try:
        form.run()
    except ExitSignal:
        print("\nЗавершение работы по требованию пользователя. До встречи!")

if __name__ == "__main__":
    main()