import unittest
from datetime import date
from src.domain.entities.trip import Trip
from src.domain.entities.expense import Expense
from src.domain.value_objects.expense_category import ExpenseCategory

class TestTripCalculations(unittest.TestCase):
    def test_domain_validation_invalid_dates(self) -> None:
        with self.assertRaises(ValueError):
            Trip(
                name="Invalid Dates",
                start_date=date(2026, 5, 24),
                end_date=date(2026, 5, 20),
                people_count=2,
                ticket_price_per_person=1000.0
            )

    def test_domain_validation_invalid_people(self) -> None:
        with self.assertRaises(ValueError):
            Trip(
                name="No People",
                start_date=date(2026, 5, 20),
                end_date=date(2026, 5, 24),
                people_count=0,
                ticket_price_per_person=1000.0
            )

    def test_domain_validation_invalid_ticket_price(self) -> None:
        with self.assertRaises(ValueError):
            Trip(
                name="Negative Ticket Price",
                start_date=date(2026, 5, 20),
                end_date=date(2026, 5, 24),
                people_count=2,
                ticket_price_per_person=-5.0
            )

    def test_domain_validation_invalid_expense_amount(self) -> None:
        with self.assertRaises(ValueError):
            Expense(
                amount=0.0,
                category=ExpenseCategory.FOOD
            )

    def test_calculations_without_expenses(self) -> None:
        trip = Trip(
            name="Tickets Only",
            start_date=date(2026, 5, 20),
            end_date=date(2026, 5, 24),
            people_count=3,
            ticket_price_per_person=5000.0
        )
        self.assertEqual(trip.calculate_transport_total(), 15000.0)
        self.assertEqual(trip.calculate_expenses_total(), 0.0)
        self.assertEqual(trip.calculate_grand_total(), 15000.0)
        self.assertEqual(trip.calculate_cost_per_person(), 5000.0)

    def test_calculations_with_multiple_expenses(self) -> None:
        trip = Trip(
            name="Full Budget",
            start_date=date(2026, 5, 20),
            end_date=date(2026, 5, 24),
            people_count=2,
            ticket_price_per_person=3000.0
        )
        expense_food = Expense(amount=1500.0, category=ExpenseCategory.FOOD)
        expense_hotel = Expense(amount=2500.0, category=ExpenseCategory.HOTEL)
        
        trip.add_expense(expense_food)
        trip.add_expense(expense_hotel)
        
        self.assertEqual(trip.calculate_transport_total(), 6000.0)
        self.assertEqual(trip.calculate_expenses_total(), 4000.0)
        self.assertEqual(trip.calculate_grand_total(), 10000.0)
        self.assertEqual(trip.calculate_cost_per_person(), 5000.0)

if __name__ == "__main__":
    unittest.main()