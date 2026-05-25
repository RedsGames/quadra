# ОТЧЁТ ПО УЧЕБНОЙ ПРАКТИКЕ

**Автор:** [Спиричева Юлия Сергеевна] | **Группа:** [ИС-31] | **Вариант №:** [9]
**Тема:** Система расчёта бюджета поездок
**Сроки:** 21.05.2026 – 25.05.2026
**Руководитель:** [Копосов Андрей Сергеевич]

---

## 1. Цель и задачи

**Цель:** разработать консольное приложение на Python для планирования бюджета поездок с учётом расходов по категориям, автоматическим расчётом итоговой суммы и стоимости на человека.

**Задачи, которые ставились:**

- Реализовать форму создания поездки (название, даты, количество участников, стоимость билета)
- Разработать систему добавления расходов по категориям (еда, отель, такси и др.)
- Реализовать автоматический расчёт общей суммы и стоимости на одного участника
- Обеспечить сохранение данных в JSON-файл и загрузку при следующем запуске
- Реализовать экспорт итогового отчёта в текстовый файл `.txt`
- Покрыть расчётную логику автоматическими тестами (`unittest`)

**Требования ТЗ, которые были выполнены:**

| Требование | Статус |
|---|---|
| Форма: название, даты, участники | ✅ выполнено |
| Добавление расходов по категориям | ✅ выполнено |
| Расчёт общей суммы | ✅ выполнено |
| Расчёт стоимости на человека | ✅ выполнено |
| Сохранение в JSON | ✅ выполнено |
| Загрузка из JSON при запуске | ✅ выполнено |
| Экспорт отчёта в .txt | ✅ выполнено |
| Консольный интерфейс | ✅ выполнено |
| Тестирование расчётов | ✅ выполнено |

---

## 2. Архитектура и стек

**Язык и версия:** Python 3.11

**Архитектурный подход:** Clean Architecture — явное разделение на слои Domain, Application и Infrastructure. Каждый слой зависит только от внутренних: инфраструктура знает про Application, Application — про Domain, Domain ни от кого не зависит.

**Ключевые модули стандартной библиотеки:**

| Модуль | Назначение |
|---|---|
| `json` | Сериализация / десериализация `trips.json` |
| `datetime` | Типы `date` для дат поездки, парсинг строк |
| `dataclasses` | DTO-классы (frozen=True) для передачи данных между слоями |
| `enum` | Перечисление `ExpenseCategory` |
| `re` | Санитизация имени файла при экспорте |
| `unittest` | Фреймворк для автоматических тестов |
| `msvcrt` / `tty` / `termios` | Посимвольный ввод для маски даты (Windows / Unix) |
| `sys` | Запись в stdout для маски даты |

**Структура модулей:**

```
quadra/
├── src/
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── trip.py                 # Trip: поля, валидация, расчёты
│   │   │   └── expense.py              # Expense: сумма, категория, имя
│   │   ├── value_objects/
│   │   │   └── expense_category.py     # Enum: FOOD, HOTEL, TAXI, …
│   │   └── repositories/
│   │       └── i_trip_repository.py    # Абстрактный интерфейс репозитория
│   ├── application/
│   │   ├── use_cases/                  # 7 use-case'ов
│   │   ├── dto/                        # TripCreateRequest, TripSummaryResponse, …
│   │   └── interfaces/                 # Контракты для use-case'ов и экспортёра
│   └── infrastructure/
│       ├── repositories/
│       │   └── json_trip_repository.py # Реализация: чтение/запись trips.json
│       ├── exporters/
│       │   └── txt_report_exporter.py  # Формирование и сохранение .txt
│       └── cli/
│           └── console_form.py         # Весь консольный UI
├── tests.py                            # 6 тест-кейсов (unittest)
├── trips.json                          # Файл данных (авто)
└── main.py                             # Точка входа; сборка зависимостей
```

**Схема взаимодействия компонентов:**

```
 ConsoleForm (infrastructure/cli)
       │
       ├── CreateTripUseCase   → TripCreateRequest  → Trip.__init__()
       │                                                  └─ валидация
       │                                                  └─ JsonTripRepository.save()
       │
       ├── AddExpenseUseCase   → ExpenseCreateRequest → Expense.__init__()
       │                                                  └─ Trip.add_expense()
       │
       ├── ManageExpensesUseCase → update_amount / update_category / delete
       │
       ├── GetTripSummaryUseCase → Trip.calculate_*() → TripSummaryResponse
       │
       └── ExportReportUseCase  → GetTripSummaryUseCase → TxtReportExporter.export()
                                                                └─ report_<name>.txt
```

---

## 3. Реализация ключевых функций

### 3.1 Доменная сущность Trip (`src/domain/entities/trip.py`)

Сущность `Trip` инкапсулирует все расчёты. Валидация вынесена в приватный метод `_validate()`, который вызывается как при создании, так и при обновлении параметров — гарантирует целостность данных на уровне объекта.

```python
def calculate_grand_total(self) -> float:
    return self.calculate_transport_total() + self.calculate_expenses_total()

def calculate_cost_per_person(self) -> float:
    return self.calculate_grand_total() / self._people_count
```

`calculate_transport_total()` = `ticket_price_per_person × people_count`. Деление в `calculate_cost_per_person()` безопасно: `_people_count > 0` гарантируется валидацией при создании.

### 3.2 JSON-репозиторий (`src/infrastructure/repositories/json_trip_repository.py`)

При каждом `save()` весь список поездок сериализуется в `trips.json`. При старте программы `_load_from_file()` десериализует файл и восстанавливает объекты `Trip` и `Expense`. Расходы читаются из вложенного массива `"expenses"`.

```python
def _save_to_file(self) -> None:
    data = []
    for t in self._trips:
        expenses_data = [
            {"amount": e.amount, "category": e.category.value, "custom_name": e._custom_name}
            for e in t.expenses
        ]
        trip_dict = {
            "name": t.name,
            "start_date": t.start_date.strftime("%Y-%m-%d"),
            ...
            "expenses": expenses_data
        }
        data.append(trip_dict)
    with open(self._filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
```

### 3.3 Интерактивная маска даты (`src/infrastructure/cli/console_form.py`)

На Windows используется `msvcrt.getch()`, на Unix — `tty` + `termios`. Цифры накапливаются в список `digits`; строка на экране обновляется после каждого нажатия, автоматически вставляя точки:

```
Введите дату начала (ДД.ММ.ГГГГ): 01.06.____
```

Ввод принимается только при ровно 8 цифрах. Нажатие `q` / `й` вызывает `ExitSignal` — корректный выход из любого места.

### 3.4 Экспорт отчёта (`src/infrastructure/exporters/txt_report_exporter.py`)

Имя файла формируется из названия поездки: спецсимволы заменяются `_`, множественные `_` сжимаются, строка приводится к нижнему регистру.

```python
safe_name = re.sub(r'[^\w\-_]', '_', summary.name.lower())
safe_name = re.sub(r'_+', '_', safe_name).strip('_')
filename = f"report_{safe_name}.txt"
```

---

## 4. Тестирование и отладка

### Автоматические тесты

Тесты написаны на `unittest`. Проверяются: валидация при создании `Trip` и `Expense`, расчёты без расходов, расчёты с несколькими расходами. Итого: **6 тест-кейсов**.

```
test_calculations_with_multiple_expenses ... ok
test_calculations_without_expenses ... ok
test_domain_validation_invalid_dates ... ok
test_domain_validation_invalid_expense_amount ... ok
test_domain_validation_invalid_people ... ok
test_domain_validation_invalid_ticket_price ... ok

Ran 6 tests in 0.002s — OK
```

Запуск:
```
python -m unittest tests.py -v
```

### Ошибки, найденные при отладке

| # | Модуль | Ошибка | Причина | Исправление |
|---|---|---|---|---|
| 1 | `json_trip_repository.py` | `FileNotFoundError` при первом запуске | `trips.json` не существовал | Добавлена проверка `os.path.exists()` |
| 2 | `trip.py` | `ValueError: End date cannot be earlier` | Даты передавались в обратном порядке при обновлении | Добавлена валидация в `update_metadata()` |
| 3 | `console_form.py` | `ValueError` при вводе 31.02.ГГГГ | `strptime` не обёрнут в `try/except` для маски | Добавлена обработка невалидных дат в ветке с `_has_raw_terminal` |
| 4 | `txt_report_exporter.py` | Файл перезаписывался | Две поездки с одинаковым именем давали одно имя файла | Выявлен в ходе ручного тестирования |
| 5 | `json_trip_repository.py` | Данные молча терялись | `except (json.JSONDecodeError, ...): pass` не логировал ошибку | Добавлен вывод предупреждения в консоль |

### Ручная проверка

```
# Запуск программы
python main.py

# Создать поездку → добавить расходы → показать отчёт
# → экспортировать в .txt → убедиться, что файл создан

# Перезапустить программу → найти поездку через поиск
# → убедиться, что данные загрузились из trips.json
```

---

## 5. Результаты и выводы

### Что реализовано в полном объёме

- Создание поездок с названием, датами, количеством участников и стоимостью билета
- Добавление расходов по 6 категориям (Еда, Одежда, Развлечения, Отель, Такси, Прочее)
- Редактирование и удаление расходов, редактирование базовых параметров поездки
- Автоматический расчёт: сумма транспорта, прочие расходы, общая сумма, стоимость на человека
- Поиск поездки по названию (регистронезависимо, подстрочный поиск)
- Персистентное хранение в `trips.json` с загрузкой при запуске
- Экспорт отчёта в `.txt`-файл с санитизацией имени
- Консольный UI с маской ввода дат и командой `выход` в любом месте
- 6 автоматических тестов покрывают все расчётные методы и граничные случаи

### Что можно доработать

- Сохранять активную поездку в `trips.json`, чтобы она восстанавливалась при перезапуске
- Добавить команду `clear` — удаление поездки из списка
- Вывод предупреждения при повреждённом `trips.json` вместо молчаливого сброса
- Поддержка валидации формата даты в режиме маски (31 февраля)

### Навыки, полученные за практику

- Проектирование многослойного Python-приложения (Clean Architecture)
- Разработка доменной модели с инкапсуляцией и валидацией данных
- Работа с JSON-файлами как хранилищем данных
- Реализация консольного UI с посимвольным вводом (`msvcrt`, `tty`)
- Написание автоматических тестов с `unittest` для расчётной логики
- Применение паттернов Repository, Use Case, DTO

---

## Приложения

- **Ссылка на репозиторий:** https://github.com/RedsGames/quadra/tree/%D0%A0%D0%B0%D1%81%D1%87%D1%91%D1%82-%D0%B1%D1%8E%D0%B4%D0%B6%D0%B5%D1%82%D0%B0-%D0%BF%D0%BE%D0%B5%D0%B7%D0%B4%D0%BA%D0%B8
