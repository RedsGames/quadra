from src.application.interfaces.i_create_trip_use_case import ICreateTripUseCase
from src.application.dto.trip_dto import TripCreateRequest
from src.domain.entities.trip import Trip
from src.domain.repositories.i_trip_repository import ITripRepository

class CreateTripUseCase(ICreateTripUseCase):
    def __init__(self, repository: ITripRepository):
        self._repository = repository

    def execute(self, request: TripCreateRequest) -> None:
        trip = Trip(
            name=request.name,
            start_date=request.start_date,
            end_date=request.end_date,
            people_count=request.people_count,
            ticket_price_per_person=request.ticket_price_per_person
        )
        self._repository.save(trip)