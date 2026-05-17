from src.models import Trip

class BudgetCalculator:
    @staticmethod
    def calculate_total(trip: Trip) -> float:
        """@returns Sum of all expenses"""
        return sum(e.amount for e in trip.expenses)

    @staticmethod
    def calculate_per_person(trip: Trip) -> float:
        """@returns Cost per person rounded to 2 decimal places"""
        if trip.people_count <= 0:
            return 0.0
        total = BudgetCalculator.calculate_total(trip)
        return round(total / trip.people_count, 2)