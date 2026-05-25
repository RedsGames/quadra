# ОТЧЁТ ПО УЧЕБНОЙ ПРАКТИКЕ

**ФИО:** Дмитриева Евгения Валерьевна | **Группа:** ИС-31 | **Вариант №:** 19
**Тема:** Личный финансовый трекер
**Сроки:** 21.05.2026 – 25.05.2026
**Руководитель:** Копосов Андрей Сергеевич

---

## 1. Цель и задачи

**Цель:** разработать консольный инструмент на Python для учёта личных финансов с персистентным JSON-хранилищем, фильтрацией транзакций, подсчётом баланса и экспортом отчётов.

**Задачи, которые ставились:**

- Реализовать добавление, просмотр и удаление транзакций (доход / расход)
- Обеспечить персистентное хранение данных в формате JSON
- Реализовать фильтрацию транзакций по дате (год / месяц / полная дата) и категории
- Реализовать подсчёт итогового баланса (доходы − расходы)
- Добавить экспорт сводки в текстовый файл `.txt` с выровненной таблицей
- Разработать альтернативное хранилище на SQLite
- Реализовать визуализацию расходов (круговая диаграмма)
- Покрыть основную логику автоматическими тестами (pytest)

**Требования ТЗ, которые были выполнены:**

| Требование | Статус |
|---|---|
| Добавление транзакций (тип, категория, сумма, дата, описание) | ✅ выполнено |
| Список пресет-категорий | ✅ выполнено |
| Просмотр всех транзакций в виде таблицы | ✅ выполнено |
| Фильтрация по дате и категории | ✅ выполнено |
| Подсчёт баланса | ✅ выполнено |
| Хранение в JSON-файле | ✅ выполнено |
| Удаление транзакции по ID | ✅ выполнено |
| Экспорт отчёта в .txt | ✅ выполнено |
| SQLite-хранилище | ✅ выполнено |
| Визуализация расходов | ✅ выполнено |
| Тесты pytest | ✅ выполнено |

---

## 2. Архитектура и стек

**Язык и версия:** Python 3.8+

**Ключевые библиотеки:**

| Библиотека | Версия | Назначение |
|---|---|---|
| `json` | stdlib | Сериализация / десериализация данных |
| `sqlite3` | stdlib | Альтернативное реляционное хранилище |
| `dataclasses` | stdlib | Описание модели Transaction |
| `typing` | stdlib | Аннотации типов и Protocol |
| `os` | stdlib | Работа с файловой системой |
| `sys` | stdlib | Выход из приложения |
| `matplotlib` | 3.x | Генерация круговых диаграмм |
| `pytest` | 7.x+ | Автоматические тесты |

**Структура модулей:**

```
quadra/
├── src/
│   ├── models.py           # Датакласс Transaction + to_dict()
│   ├── storage.py          # JsonStorage: load() и save()
│   ├── services.py         # FinanceService: вся бизнес-логика
│   ├── database.py         # SQLiteRepository: альтернативный бэкенд
│   ├── cli.py              # ConsoleUI: интерактивное меню
│   ├── visualization.py    # ChartGenerator: круговая диаграмма
│   └── protocols.py        # ITransactionRepository, IVisualizer
├── tests/
│   ├── test_scripts.py     # Тест запуска и load_config
│   └── test_report.py      # Тест баланса, фильтрации, экспорта
├── data/                   # JSON-файлы (создаются автоматически)
├── main.py                 # Точка входа
└── requirements.txt
```

**Схема взаимодействия компонентов:**

```
 main.py (точка входа)
         │
         ▼
 ConsoleUI (cli.py)
         │
         ├─── [Добавить / Удалить] ──► FinanceService.add_transaction()
         │                                        │
         │                              Transaction(dataclass)
         │                                        │
         │                              JsonStorage.save() ──► data/*.json
         │
         ├─── [Показать / Фильтр]  ──► FinanceService.filter_transactions()
         │                                        │
         │                              JsonStorage.load() ◄── data/*.json
         │                                        │
         │                              вывод таблицы в ConsoleUI
         │
         ├─── [Баланс]             ──► FinanceService.get_balance()
         │                                        │
         │                              sum(income) - sum(expense)
         │
         ├─── [Экспорт .txt]       ──► FinanceService.export_summary()
         │                                        │
         │                              finance_report.txt (utf-8-sig)
         │
         └─── [Диаграмма]          ──► ChartGenerator.generate_expense_pie_chart()
                                                   │
                                         matplotlib → .png
```

---

## 3. Реализация ключевых функций

### 3.1 Модель данных (`models.py`)

Каждая финансовая операция описана датаклассом `Transaction`. Метод `to_dict()` используется при сохранении в JSON.

```python
@dataclass
class Transaction:
    id: int
    type: str        # "income" или "expense"
    category: str
    amount: float
    date: str        # формат YYYY-MM-DD
    description: Optional[str] = ""

    def to_dict(self):
        return asdict(self)
```

### 3.2 Хранилище (`storage.py`)

`JsonStorage` реализует load/save через стандартный модуль `json`. При отсутствии файла возвращает пустой список — это позволяет первому запуску работать без ошибок.

```python
def load(self, filename: str) -> list:
    if not os.path.exists(filename):
        return []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def save(self, filename: str, data: list) -> None:
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
```

### 3.3 Бизнес-логика (`services.py`)

Ключевой момент — генерация нового `id` через `max(..., default=0) + 1`, что корректно работает на пустом списке. Метод `filter_transactions` поддерживает поиск по подстроке даты (год `2026`, месяц `2026-05` или полная дата `2026-05-01`) и по категории без учёта регистра.

```python
def add_transaction(self, t_type, category, amount, date, description):
    new_id = max([t.id for t in self.transactions], default=0) + 1
    new_t = Transaction(new_id, t_type, category, amount, date, description)
    self.transactions.append(new_t)
    self._sync()

def filter_transactions(self, date=None, category=None):
    result = self.transactions
    if date:
        target_date = date.strip()
        result = [t for t in result if target_date in t.date]
    if category:
        target_cat = category.strip().lower()
        result = [t for t in result if t.category.strip().lower() == target_cat]
    return result
```

### 3.4 Альтернативное хранилище (`database.py`)

`SQLiteRepository` реализует тот же интерфейс (`ITransactionRepository`) через встроенный `sqlite3`. Таблица создаётся автоматически при первом подключении. Метод `get_by_period` использует `LIKE`-запрос по маске `YYYY-MM%`.

```python
def get_by_period(self, year: int, month: int) -> List[Transaction]:
    period = f"{year}-{month:02d}%"
    with sqlite3.connect(self.db_path) as conn:
        cursor = conn.execute(
            "SELECT id, type, category, amount, date, description "
            "FROM transactions WHERE date LIKE ?", (period,)
        )
        return [Transaction(*r) for r in cursor.fetchall()]
```

### 3.5 Визуализация (`visualization.py`)

`ChartGenerator` группирует расходы по категориям и строит круговую диаграмму через `matplotlib`. При отсутствии расходов метод завершается без создания файла.

```python
def generate_expense_pie_chart(self, transactions, output_path):
    expenses = [t for t in transactions if t.type == 'expense']
    if not expenses:
        return

    data = {}
    for t in expenses:
        data[t.category] = data.get(t.category, 0) + t.amount

    plt.figure(figsize=(10, 7))
    plt.pie(data.values(), labels=data.keys(), autopct='%1.1f%%')
    plt.title("Expenses by Category")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    plt.close()
```

---

## 4. Тестирование и отладка

### Автоматические тесты

Тесты написаны на `pytest`. Каждый тест использует фикстуру `service_instance`, которая создаёт чистый сервис с временным файлом в `data/test_audit.json` и удаляет его после теста.

```
tests/test_report.py::test_balance_calculation  PASSED
tests/test_report.py::test_filter_functionality PASSED
tests/test_report.py::test_export_existence     PASSED
tests/test_scripts.py::test_load_config_returns_dict PASSED
```

### Ошибки, найденные при отладке

| # | Модуль | Ошибка | Причина | Исправление |
|---|---|---|---|---|
| 1 | `services.py` | `ValueError: max() arg is an empty sequence` | `max()` без `default` на пустом списке | Добавлен `default=0` |
| 2 | `cli.py` | Фильтрация не находила записи | Лишние пробелы во вводе пользователя | Добавлены `.strip()` и `.lower()` |
| 3 | `cli.py` | Поле `type` принимало произвольный текст | Нет проверки ввода кроме `if == "1"` | Введён строгий выбор через `1` / `2` |
| 4 | `cli.py` | Разделитель таблицы вдвое длиннее заголовка | `"-" * len(header) * 2` | Убран лишний `* 2` |
| 5 | `services.py` | Экспорт не содержал колонки ID и описание | Метод не включал эти поля | Обновлена структура таблицы в `export_summary` |
| 6 | `visualization.py` | `FileNotFoundError: makedirs("")` | `os.path.dirname("chart.png")` → `""` | Добавлена проверка: если `dirname` пустой, `makedirs` не вызывается |

### Ручная проверка

```bash
# Запустить программу
python main.py

# Добавить доход: зарплата, 50000, 2026-05-01
# Добавить расход: продукты, 3200, 2026-05-15
# Проверить баланс в заголовке меню: 46800.0
# Фильтрация по месяцу 2026-05: 2 записи
# Фильтрация по категории "зарплата": 1 запись
# Экспорт: файл finance_report.txt создан

# Запустить тесты
pytest -v
```

---

## 5. Результаты и выводы

### Что реализовано в полном объёме

- Полный CRUD для транзакций: добавление, просмотр, удаление по ID
- Персистентное JSON-хранилище с автоматическим созданием папки `data/`
- Фильтрация по подстроке даты (год / месяц / полная дата) и по категории
- Автоматический подсчёт баланса в реальном времени
- Экспорт финансового отчёта в `.txt` с выровненными столбцами (кодировка UTF-8-SIG)
- Альтернативное SQLite-хранилище (`database.py`) с тем же интерфейсом
- Круговая диаграмма расходов по категориям через `matplotlib`
- Протоколы (`protocols.py`) для слабой связанности хранилища и визуализатора
- Автоматические тесты pytest с изолированной фикстурой

### Что можно доработать

- Валидация формата даты YYYY-MM-DD при вводе (сейчас принимается любая строка)
- Явная обработка некорректного ввода типа операции (сейчас всё, кроме "1", становится расходом)
- Логирование ошибок при повреждённом JSON-файле
- Защита от обхода директории при вводе имени файла БД
- Команда для очистки всех транзакций или сброса базы
- Округление баланса до 2 знаков при выводе (проблема float IEEE 754)

### Навыки, полученные за практику

- Проектирование многомодульного Python-приложения с чёткими зонами ответственности
- Работа с JSON как форматом персистентного хранения данных
- Использование `dataclasses` для описания моделей данных
- Реализация протокольных интерфейсов через `typing.Protocol`
- Работа с реляционной БД через встроенный `sqlite3`
- Написание автоматических тестов с pytest и фикстурами
- Генерация диаграмм через `matplotlib`
- Настройка кодировки файлов для корректного отображения кириллицы на Windows

---

## Приложения

- **Ссылка на репозиторий:** https://github.com/RedsGames/quadra/tree/%D0%A2%D1%80%D0%B5%D0%BA%D0%B5%D1%80-%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BE%D0%B2/%D0%B4%D0%BE%D1%85%D0%BE%D0%B4%D0%BE%D0%B2
