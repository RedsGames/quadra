import sys

class ConsoleUI:
    def __init__(self, service):
        self.service = service
        self.categories = ["зарплата", "продукты", "транспорт", "развлечения"]

    def run(self):
        while True:
            balance = self.service.get_balance()
            print(f"\n{'='*40}")
            print(f" ТЕКУЩИЙ БАЛАНС: {balance}")
            print(f"{'='*40}")
            print("1. Добавить транзакцию")
            print("2. Показать все транзакции")
            print("3. Фильтрация (дата/категория)")
            print("4. Удалить транзакцию по ID")
            print("5. Экспорт отчета в .txt")
            print("6. Выход")
            
            choice = input("\nВыберите действие: ").strip()
            
            if choice == "1": self._add()
            elif choice == "2": self._show(self.service.transactions)
            elif choice == "3": self._filter()
            elif choice == "4": self._delete()
            elif choice == "5": self._export()
            elif choice == "6": sys.exit()

    def _add(self):
        print(f"\nДоступные пресеты: {', '.join(self.categories)}")
        print("Тип операции: 1. Доход (+) | 2. Расход (-)")
        
        type_input = input(">> ").strip()
        t_type = "income" if type_input == "1" else "expense"
        
        category = input("Категория: ").strip()
        try:
            amount = float(input("Сумма: "))
            date = input("Дата (YYYY-MM-DD): ").strip()
            description = input("Описание: ").strip()
            
            self.service.add_transaction(t_type, category, amount, date, description)
            print("\n[OK] Запись успешно добавлена.")
        except ValueError:
            print("\n[ERROR] Ошибка: Некорректный ввод суммы.")
        
        self._pause()

    def _show(self, items):
        if not items:
            print("\n--- Список транзакций пуст ---")
        else:
            header = f"\n{'ID':<4} | {'Дата':<12} | {'Тип':<8} | {'Категория':<15} | {'Сумма':<10} | {'Описание'}"
            print(header)
            print("-" * len(header) * 2)
            for t in items:
                t_type_display = "+" if t.type == "income" else "-"
                print(f"{t.id:<4} | {t.date:<12} | {t_type_display:<8} | {t.category:<15} | {t.amount:<10} | {t.description}")
        
        self._pause()

    def _filter(self):
        print("\n--- Фильтрация ---")
        print("Подсказка: можно ввести только год (2024) или месяц (2024-05)")
        d = input("Введите год/месяц/дату или [Enter] для пропуска: ").strip()
        c = input("Введите категорию или [Enter] для пропуска: ").strip()
        
        results = self.service.filter_transactions(d or None, c or None)
        self._show(results)

    def _delete(self):
        try:
            t_id = int(input("\nВведите ID для удаления: "))
            if self.service.delete_transaction(t_id):
                print(f"[OK] Транзакция #{t_id} удалена.")
            else:
                print(f"[NOT FOUND] Транзакция с ID {t_id} не найдена.")
        except ValueError:
            print("[ERROR] Ошибка: ID должен быть числом.")
        
        self._pause()

    def _export(self):
        filename = "finance_report.txt"
        self.service.export_summary(filename)
        print(f"\n[OK] Отчет автоматически сохранен в: {filename}")
        print("[INFO] Файл оптимизирован для открытия в Блокноте (Кириллица исправлена)")
        self._pause()

    def _pause(self):
        input("\nНажмите [Enter], чтобы вернуться в меню...")