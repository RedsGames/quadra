from src.application.interfaces.i_get_trip_summary_use_case import IGetTripSummaryUseCase
from src.application.dto.trip_dto import TripSummaryResponse, ExpenseItemResponse
from src.domain.repositories.i_trip_repository import ITripRepository

class GetTripSummaryUseCase(IGetTripSummaryUseCase):
    def __init__(self, repository: ITripRepository):
        self._repository = repository

    def execute(self) -> TripSummaryResponse:
        trip = self._repository.get_active_trip()
        if not trip:
            raise ValueError("No active trip found")

        expenses_list = [
            ExpenseItemResponse(
                category_name=exp.name,
                amount=exp.amount
            )
            for exp in trip.expenses
        ]

        return TripSummaryResponse(
            name=trip.name,
            start_date=trip.start_date.strftime("%d.%m.%Y"),
            end_date=trip.end_date.strftime("%d.%m.%Y"),
            people_count=trip.people_count,
            ticket_price_per_person=trip.ticket_price_per_person,
            transport_total=trip.calculate_transport_total(),
            expenses_total=trip.calculate_expenses_total(),
            grand_total=trip.calculate_grand_total(),
            cost_per_person=trip.calculate_cost_per_person(),
            expenses=expenses_list
        )