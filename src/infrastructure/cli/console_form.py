import sys
from datetime import datetime, date
from src.application.interfaces.i_create_trip_use_case import ICreateTripUseCase
from src.application.interfaces.i_update_trip_use_case import IUpdateTripUseCase
from src.application.interfaces.i_search_trips_use_case import ISearchTripsUseCase
from src.application.interfaces.i_add_expense_use_case import IAddExpenseUseCase
from src.application.interfaces.i_get_trip_summary_use_case import IGetTripSummaryUseCase
from src.application.interfaces.i_export_report_use_case import IExportReportUseCase
from src.application.interfaces.i_manage_expenses_use_case import IManageExpensesUseCase
from src.application.dto.trip_dto import TripCreateRequest, TripUpdateRequest
from src.application.dto.expense_dto import ExpenseCreateRequest

_has_raw_terminal = True
try:
    import msvcrt
    def get_char() -> str:
        ch = msvcrt.getch()
        if ch == b'\x08':
            return '\x08'
        if ch in (b'\r', b'\n'):
            return '\r'
        return ch.decode('utf-8', errors='ignore')
except ImportError:
    try:
        import tty
        import termios
        def get_char() -> str:
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            if ch in ('\r', '\n'):
                return '\r'
            if ch == '\x7f':
                return '\x08'
            return ch
    except ImportError:
        _has_raw_terminal = False
        def get_char() -> str:
            return ""

class ExitSignal(Exception):
    pass

class ConsoleForm:
    def __init__(
        self, 
        create_use_case: ICreateTripUseCase,
        update_use_case: IUpdateTripUseCase,
        search_use_case: ISearchTripsUseCase,
        add_expense_use_case: IAddExpenseUseCase,
        summary_use_case: IGetTripSummaryUseCase,
        export_use_case: IExportReportUseCase,
        manage_expenses_use_case: IManageExpensesUseCase
    ):
        self._create_use_case = create_use_case
        self._update_use_case = update_use_case
        self._search_use_case = search_use_case
        self._add_expense_use_case = add_expense_use_case
        self._summary_use_case = summary_use_case
        self._export_use_case = export_use_case
        self._manage_expenses_use_case = manage_expenses_use_case

    def run(self) -> None:
        while True:
            print("=== Система расчета бюджета поездок ===")
            print("(Для выхода на любом этапе введите 'выход')\n")
            print("1. Создать новую поездку")
            print("2. Найти и редактировать существующую поездку")
            print("3. Выйти")
            choice = self._get_input("Выберите действие (1-3): ")

            if choice == "1":
                self._create_trip_flow()
            elif choice == "2":
                self._search_and_select_trip_flow()
            elif choice == "3":
                raise ExitSignal()
            else:
                print("Ошибка: выберите пункт 1, 2 или 3.\n")

    def _create_trip_flow(self) -> None:
        print("\n=== Создание новой поездки ===")
        name, start_date, end_date, people_count, ticket_price = self._read_trip_inputs()

        try:
            request = TripCreateRequest(
                name=name,
                start_date=start_date,
                end_date=end_date,
                people_count=people_count,
                ticket_price_per_person=ticket_price
            )
            self._create_use_case.execute(request)
            print("\nПоездка успешно создана!\n")
            self._trip_manager_menu()
        except ValueError as error:
            print(f"\nОшибка при создании поездки: {error}\n")

    def _search_and_select_trip_flow(self) -> None:
        print("\n=== Поиск существующей поездки ===")
        query = self._get_input("Введите название для поиска (или Enter для показа всех): ").strip()

        if query:
            results = self._search_use_case.search(query)
        else:
            results = self._search_use_case.get_all()

        if not results:
            print("Поездок не найдено.\n")
            return

        print("\nПохожие поездки в системе:")
        for idx, item in enumerate(results, 1):
            print(f"  {idx}. {item.name} ({item.start_date} - {item.end_date})")

        choice = self._read_range_int("\nВыберите поездку по номеру: ", 1, len(results))
        
        try:
            self._search_use_case.select_trip(choice - 1, results)
            print("Поездка выбрана и загружена.\n")
            self._trip_manager_menu()
        except ValueError as error:
            print(f"Ошибка выбора: {error}\n")

    def _trip_manager_menu(self) -> None:
        while True:
            summary = self._summary_use_case.execute()
            print(f"--- Управление поездкой: {summary.name} ---")
            print("1. Добавить новый расход")
            print("2. Редактировать существующие расходы")
            print("3. Показать итоговый отчет")
            print("4. Экспортировать итоговый отчет в .txt")
            print("5. Редактировать базовые параметры поездки")
            print("6. Назад в главное меню")
            choice = self._get_input("Выберите действие (1-6): ")

            if choice == "1":
                self._add_expense_flow()
            elif choice == "2":
                self._edit_expenses_flow()
            elif choice == "3":
                self._show_summary_flow()
            elif choice == "4":
                self._export_report_flow()
            elif choice == "5":
                self._edit_trip_metadata_flow()
            elif choice == "6":
                print()
                break
            else:
                print("Ошибка: выберите пункт от 1 до 6.\n")

    def _edit_trip_metadata_flow(self) -> None:
        summary = self._summary_use_case.execute()
        print("\n=== Редактирование параметров поездки ===")
        print(f"1. Редактировать текущую поездку ({summary.name})")
        print("2. Найти и переключиться на другую поездку")
        print("3. Назад")
        nav_choice = self._get_input("Выберите действие (1-3): ")

        if nav_choice == "3":
            print()
            return
        elif nav_choice == "2":
            query = self._get_input("Введите название для поиска (или Enter для показа всех): ").strip()
            if query:
                results = self._search_use_case.search(query)
            else:
                results = self._search_use_case.get_all()

            if not results:
                print("Поездок не найдено.\n")
                return

            print("\nДоступные поездки:")
            for idx, item in enumerate(results, 1):
                print(f"  {idx}. {item.name} ({item.start_date} - {item.end_date})")

            choice = self._read_range_int("\nВыберите поездку по номеру: ", 1, len(results))
            try:
                self._search_use_case.select_trip(choice - 1, results)
                print("Поездка успешно изменена.\n")
            except ValueError as error:
                print(f"Ошибка выбора: {error}\n")
                return
        elif nav_choice != "1":
            print("Ошибка: выберите пункт 1, 2 или 3.\n")
            return

        while True:
            summary = self._summary_use_case.execute()
            current_name = summary.name
            current_start_date = datetime.strptime(summary.start_date, "%d.%m.%Y").date()
            current_end_date = datetime.strptime(summary.end_date, "%d.%m.%Y").date()
            current_people_count = summary.people_count
            current_ticket_price = summary.ticket_price_per_person

            print("\n=== Изменение параметров ===")
            print(f"1. Название поездки: {current_name}")
            print(f"2. Дата начала: {summary.start_date}")
            print(f"3. Дата окончания: {summary.end_date}")
            print(f"4. Количество человек: {current_people_count}")
            print(f"5. Стоимость билета на одного: {current_ticket_price:.2f} руб.")
            print("6. Назад в меню управления")
            
            choice = self._get_input("Выберите параметр для изменения (1-6): ")

            if choice == "6":
                print()
                break

            new_name = current_name
            new_start_date = current_start_date
            new_end_date = current_end_date
            new_people_count = current_people_count
            new_ticket_price = current_ticket_price

            if choice == "1":
                new_name = self._read_non_empty_string("Введите новое название: ")
            elif choice == "2":
                new_start_date = self._read_date("Введите новую дату начала (ДД.ММ.ГГГГ): ")
            elif choice == "3":
                new_end_date = self._read_date_after("Введите новую дату окончания (ДД.ММ.ГГГГ): ", current_start_date)
            elif choice == "4":
                new_people_count = self._read_positive_int("Введите новое количество человек: ")
            elif choice == "5":
                new_ticket_price = self._read_positive_float("Введите новую стоимость билета: ")
            else:
                print("Ошибка: выберите пункт от 1 до 6.\n")
                continue

            try:
                request = TripUpdateRequest(
                    name=new_name,
                    start_date=new_start_date,
                    end_date=new_end_date,
                    people_count=new_people_count,
                    ticket_price_per_person=new_ticket_price
                )
                self._update_use_case.execute(request)
                print("Параметр успешно обновлен!\n")
            except ValueError as error:
                print(f"\nОшибка изменения параметра: {error}\n")

    def _edit_expenses_flow(self) -> None:
        while True:
            summary = self._summary_use_case.execute()
            if not summary.expenses:
                print("\nРасходов пока нет.\n")
                break

            print("\n=== Редактирование расходов ===")
            for idx, exp in enumerate(summary.expenses, 1):
                print(f"  {idx}. {exp.category_name}: {exp.amount:.2f} руб.")
            print(f"  {len(summary.expenses) + 1}. Назад")

            choice_idx = self._read_range_int("\nВыберите расход для изменения/удаления: ", 1, len(summary.expenses) + 1)
            if choice_idx == len(summary.expenses) + 1:
                break

            target_idx = choice_idx - 1
            selected_exp = summary.expenses[target_idx]

            print(f"\nВыбран расход: {selected_exp.category_name} ({selected_exp.amount:.2f} руб.)")
            print("1. Изменить сумму")
            print("2. Изменить категорию")
            print("3. Удалить расход")
            print("4. Отмена")
            action = self._get_input("Выберите действие (1-4): ")

            if action == "4":
                continue

            try:
                if action == "1":
                    new_amount = self._read_positive_float("Введите новую сумму: ")
                    self._manage_expenses_use_case.update_amount(target_idx, new_amount)
                    print("Сумма успешно обновлена!\n")
                elif action == "2":
                    print("\nВыберите новую категорию:")
                    print("1. Еда")
                    print("2. Одежда")
                    print("3. Развлечения")
                    print("4. Отель")
                    print("5. Такси")
                    print("6. Прочее")
                    category_idx = self._read_range_int("Номер категории (1-6): ", 1, 6)
                    custom_name = None
                    if category_idx == 6:
                        custom_choice = self._get_input("Задать кастомное имя вместо 'Прочее'? (да/нет): ").strip().lower()
                        if custom_choice in ("да", "д", "yes", "y"):
                            custom_name = self._read_non_empty_string("Введите название расхода: ")
                    self._manage_expenses_use_case.update_category(target_idx, category_idx, custom_name)
                    print("Категория успешно обновлена!\n")
                elif action == "3":
                    confirm = self._get_input("Вы уверены, что хотите удалить этот расход? (да/нет): ").strip().lower()
                    if confirm in ("да", "д", "yes", "y"):
                        self._manage_expenses_use_case.delete_expense(target_idx)
                        print("Расход успешно удален!\n")
                else:
                    print("Ошибка: выберите пункт от 1 до 4.\n")
            except ValueError as error:
                print(f"\nОшибка изменения расхода: {error}\n")

    def _export_report_flow(self) -> None:
        try:
            filename = self._export_use_case.execute()
            print(f"\nОтчет успешно экспортирован в файл: {filename}\n")
        except (ValueError, IOError) as error:
            print(f"\nОшибка при экспорте отчета: {error}\n")

    def _read_trip_inputs(self) -> tuple[str, date, date, int, float]:
        name = self._read_non_empty_string("Введите название поездки: ")
        start_date = self._read_date("Введите дату начала (ДД.ММ.ГГГГ): ")
        end_date = self._read_date_after("Введите дату окончания (ДД.ММ.ГГГГ): ", start_date)
        people_count = self._read_positive_int("Введите количество человек: ")
        ticket_price = self._read_positive_float("Введите стоимость билета туда-обратно на 1 человека: ")
        return name, start_date, end_date, people_count, ticket_price

    def _add_expense_flow(self) -> None:
        print("\n--- Добавление нового расхода ---")
        amount = self._read_positive_float("Введите сумму расхода: ")
        
        print("\nВыберите категорию расхода:")
        print("1. Еда")
        print("2. Одежда")
        print("3. Развлечения")
        print("4. Отель")
        print("5. Такси")
        print("6. Прочее")
        category_idx = self._read_range_int("Номер категории (1-6): ", 1, 6)

        custom_name = None
        if category_idx == 6:
            custom_choice = self._get_input("Задать кастомное имя вместо 'Прочее'? (да/нет): ").strip().lower()
            if custom_choice in ("да", "д", "yes", "y"):
                custom_name = self._read_non_empty_string("Введите название расхода: ")

        try:
            request = ExpenseCreateRequest(
                amount=amount,
                category_index=category_idx,
                custom_name=custom_name
            )
            self._add_expense_use_case.execute(request)
            print("Расход успешно добавлен.\n")
        except ValueError as error:
            print(f"Ошибка сохранения расхода: {error}\n")

    def _show_summary_flow(self) -> None:
        summary = self._summary_use_case.execute()
        print("\n==========================================")
        print("           ИТОГОВЫЙ ОТЧЕТ ПОЕЗДКИ          ")
        print("==========================================")
        print(f"Поездка: {summary.name}")
        print(f"Даты: {summary.start_date} - {summary.end_date}")
        print(f"Количество участников: {summary.people_count}")
        print(f"Стоимость билета (на одного): {summary.ticket_price_per_person:.2f} руб.")
        print(f"Всего за билеты (на всех): {summary.transport_total:.2f} руб.")
        print("------------------------------------------")
        
        if summary.expenses:
            print("Прочие расходы по категориям:")
            for idx, exp in enumerate(summary.expenses, 1):
                print(f"  {idx}. {exp.category_name}: {exp.amount:.2f} руб.")
            print(f"Всего прочих расходов: {summary.expenses_total:.2f} руб.")
        else:
            print("Прочих расходов не добавлено.")
        
        print("------------------------------------------")
        print(f"ОБЩИЕ ЗАТРАТЫ НА ПОЕЗДКУ: {summary.grand_total:.2f} руб.")
        print(f"СРЕДНИЙ РАСХОД НА ЧЕЛОВЕКА: {summary.cost_per_person:.2f} руб.")
        print("==========================================\n")

    def _get_input(self, prompt: str) -> str:
        value = input(prompt).strip()
        if value.lower() in ("выход", "exit"):
            raise ExitSignal()
        return value

    def _read_non_empty_string(self, prompt: str) -> str:
        while True:
            value = self._get_input(prompt)
            if value:
                return value
            print("Ошибка: значение не может быть пустым.")

    def _read_date(self, prompt: str) -> date:
        return self._read_masked_date(prompt)

    def _read_date_after(self, prompt: str, start_date: date) -> date:
        while True:
            end_date = self._read_masked_date(prompt)
            if end_date < start_date:
                print(f"Ошибка: дата окончания не может быть раньше даты начала ({start_date.strftime('%d.%m.%Y')}).")
                continue
            return end_date

    def _read_masked_date(self, prompt: str) -> date:
        if not _has_raw_terminal:
            while True:
                value = self._get_input(prompt)
                try:
                    return datetime.strptime(value, "%d.%m.%Y").date()
                except ValueError:
                    print("Ошибка: неверный формат даты. Используйте ДД.ММ.ГГГГ.")

        sys.stdout.write(prompt)
        sys.stdout.flush()
        digits = []

        while True:
            ch = get_char()
            if ch in ('\x08', '\x7f'):
                if digits:
                    digits.pop()
            elif ch in ('\r', '\n'):
                if len(digits) == 8:
                    break
            elif ch.isdigit():
                if len(digits) < 8:
                    digits.append(ch)
            elif ch.lower() in ('q', 'й'):
                raise ExitSignal()

            display = self._format_digits_as_date(digits)
            sys.stdout.write('\r' + prompt + display + ' ' * (10 - len(display)) + '\r' + prompt + display)
            sys.stdout.flush()

        print()
        date_str = self._format_digits_as_date(digits)
        return datetime.strptime(date_str, "%d.%m.%Y").date()

    def _format_digits_as_date(self, digits: list[str]) -> str:
        res = []
        for i, d in enumerate(digits):
            if i in (2, 4):
                res.append('.')
            res.append(d)
        return "".join(res)

    def _read_positive_int(self, prompt: str) -> int:
        while True:
            value = self._get_input(prompt)
            try:
                number = int(value)
                if number > 0:
                    return number
                print("Ошибка: число должно быть больше 0.")
            except ValueError:
                print("Ошибка: введите целое число.")

    def _read_range_int(self, prompt: str, min_val: int, max_val: int) -> int:
        while True:
            value = self._get_input(prompt)
            try:
                number = int(value)
                if min_val <= number <= max_val:
                    return number
                print(f"Ошибка: число должно быть в диапазоне от {min_val} до {max_val}.")
            except ValueError:
                print("Ошибка: введите целое число.")

    def _read_positive_float(self, prompt: str) -> float:
        while True:
            value = self._get_input(prompt)
            try:
                number = float(value)
                if number > 0:
                    return number
                print("Ошибка: сумма должна быть больше 0.")
            except ValueError:
                print("Ошибка: введите корректное число.")