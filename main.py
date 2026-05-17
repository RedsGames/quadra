import uuid
from src.models import Trip, Expense, Category
from src.repository import TripRepository
from src.manager import TripManager
from src.calculator import BudgetCalculator
from src.exporter import ReportExporter

class CLI:
    def __init__(self):
        self.manager = TripManager(TripRepository())

    def run(self):
        while True:
            print("\n1. Новая поездка\n2. Добавить расход\n3. Показать бюджет\n4. Экспорт отчета\n5. Выход")
            choice = input("> ")
            if choice == "1":
                try:
                    name = input("Название: ")
                    dates = input("Даты: ")
                    people = int(input("Количество человек: "))
                    if people <= 0: raise ValueError
                    self.manager.add_trip(Trip(str(uuid.uuid4()), name, dates, people))
                except ValueError:
                    print("Ошибка: Количество человек должно быть числом > 0.")
            elif choice == "2":
                name = input("Название поездки: ")
                trip = self.manager.get_trip_by_name(name)
                if trip:
                    try:
                        exp_name = input("Название расхода: ")
                        amount = float(input("Сумма: "))
                        while True:
                            print("1. Транспорт, 2. Жильё, 3. Еда, 4. Развлечения, 5. Подушка безопасности, 6. Прочее")
                            cat_choice = input("Выберите номер категории (1-6): ")
                            cat = Category.from_input(cat_choice)
                            
                            if cat:
                                if cat == Category.OTHER:
                                    custom = input("Введите название для категории (или нажмите Enter для 'Прочее'): ")
                                    if custom.strip():
                                        cat = Category.CUSTOM
                                        cat._value_ = custom
                                trip.expenses.append(Expense(exp_name, amount, cat))
                                self.manager.repo.save_all(self.manager.trips)
                                break
                            else:
                                print("Ошибка: Выберите номер от 1 до 6.")
                    except ValueError:
                        print("Ошибка: Сумма должна быть числом.")
            elif choice == "3":
                name = input("Название поездки: ")
                trip = self.manager.get_trip_by_name(name)
                if trip:
                    print(f"Общая сумма: {BudgetCalculator.calculate_total(trip)}")
                    print(f"На человека: {BudgetCalculator.calculate_per_person(trip)}")
            elif choice == "4":
                name = input("Название поездки: ")
                trip = self.manager.get_trip_by_name(name)
                if trip:
                    ReportExporter.export_to_txt(trip, f"report_{trip.name}.txt")
                    print("Отчет сохранен.")
            elif choice == "5":
                break

if __name__ == "__main__":
    CLI().run()