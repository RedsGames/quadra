from src.models import Trip
from src.calculator import BudgetCalculator

class ReportExporter:
    @staticmethod
    def export_to_txt(trip: Trip, filename: str):
        total = BudgetCalculator.calculate_total(trip)
        per_person = BudgetCalculator.calculate_per_person(trip)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Отчет: {trip.name}\n")
            f.write(f"Даты: {trip.dates}\n")
            f.write(f"Участников: {trip.people_count}\n")
            f.write("-" * 20 + "\n")
            f.write("Расходы:\n")
            for e in trip.expenses:
                f.write(f"- {e.name} ({e.category.value}): {e.amount}\n")
            f.write("-" * 20 + "\n")
            f.write(f"Итого: {total}\n")
            f.write(f"На человека: {per_person}\n")