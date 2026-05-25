from src.application.interfaces.i_update_trip_use_case import IUpdateTripUseCase
from src.application.dto.trip_dto import TripUpdateRequest
from src.domain.repositories.i_trip_repository import ITripRepository

class UpdateTripUseCase(IUpdateTripUseCase):
    def __init__(self, repository: ITripRepository):
        self._repository = repository

    def execute(self, request: TripUpdateRequest) -> None:
        trip = self._repository.get_active_trip()
        if not trip:
            raise ValueError("No active trip found")
        
        trip.update_metadata(
            name=request.name,
            start_date=request.start_date,
            end_date=request.end_date,
            people_count=request.people_count,
            ticket_price_per_person=request.ticket_price_per_person
        )
        self._repository.save(trip)