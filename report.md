# ОТЧЁТ ПО УЧЕБНОЙ ПРАКТИКЕ

**ФИО:** Анисько Павел Владимирович, Спиричева Юлия Сергеевна, Спиричева Анастасия Сергеевна, Дмитриева Евгения Валерьевна | **Группа:** [ИС-31] |
**Тема:** Quadra — единый веб-сервис из четырёх Python-модулей
**Сроки:** 20.05.2026 – 25.05.2026
**Руководитель:** [Копосов Андрей Сергеевич]

---

## 1. Цель и задачи

**Цель:** разработать единый веб-сайт на Python, объединяющий четыре учебных модуля (трекер доходов/расходов, QR-генератор, калькулятор бюджета поездки, email-отправщик), задеплоить его на сервер и продемонстрировать работу в браузере.

**Задачи, которые ставились:**

- Перенести готовые CLI-модули (трекер, QR) в веб-архитектуру без потери логики
- Разработать модуль бюджета поездки с нуля (ТЗ было, кода не было)
- Создать единый FastAPI-бэкенд с отдельными роутерами для каждого модуля
- Подключить HTML-шаблоны (Jinja2) с адаптивной вёрсткой (Tailwind CSS)
- Настроить конвертацию валют через внешний API без ключей
- Реализовать отправку email через SMTP с поддержкой планировщика задач
- Покрыть бизнес-логику всех модулей автоматическими тестами (pytest)
- Задеплоить приложение на сервер redsgames.ru (Nginx + Uvicorn + systemd)

**Требования ТЗ, которые были выполнены:**

| Требование | Статус |
|---|---|
| Трекер доходов/расходов (CRUD + фильтрация + экспорт) | ✅ выполнено |
| QR-генератор (одиночный + пакетный) | ✅ выполнено |
| Калькулятор бюджета с конвертацией валют | ✅ выполнено |
| Email-отправщик с планировщиком | ✅ выполнено |
| Единый веб-интерфейс (Dashboard) | ✅ выполнено |
| Тесты pytest, покрытие ≥ 80% | ✅ выполнено (96%) |
| Деплой на сервер с HTTPS | ✅ выполнено |
| Без хардкода (конфиг через .env) | ✅ выполнено |

---

## 2. Архитектура и стек

**Язык и версия:** Python 3.12

**Ключевые библиотеки:**

| Библиотека | Версия | Назначение |
|---|---|---|
| `fastapi` | 0.136.3 | Веб-фреймворк, роутинг, автодокументация |
| `uvicorn[standard]` | 0.48.0 | ASGI-сервер |
| `jinja2` | 3.1.6 | HTML-шаблонизатор |
| `qrcode` | 8.2 | Генерация QR-кодов |
| `pillow` | 12.2.0 | Работа с изображениями (подписи на QR) |
| `python-dotenv` | 1.2.2 | Загрузка `.env` |
| `apscheduler` | 3.11.2 | Планировщик отложенных email |
| `httpx` | 0.28.1 | Асинхронный HTTP-клиент (API конвертации) |
| `python-multipart` | 0.0.29 | Обработка HTML-форм |
| `pytest` | 9.0.3 | Автоматические тесты |

Стандартная библиотека: `smtplib`, `email`, `json`, `os`, `uuid`, `dataclasses`, `logging`, `zipfile`, `io`.

**Структура модулей:**

```
quadra/
├── main.py                     # FastAPI: монтирование роутеров, dashboard
├── src/
│   ├── tracker/
│   │   ├── models.py           # Transaction (dataclass)
│   │   ├── storage.py          # JsonStorage: load() / save()
│   │   └── services.py         # FinanceService: вся бизнес-логика
│   ├── qr_module/
│   │   └── qr_utils.py         # create_qr_image, qr_to_bytes, batch_qr_zip
│   ├── budget/
│   │   └── service.py          # TripProfile (dataclass) + BudgetService
│   ├── email_module/
│   │   ├── mailer.py           # Mailer: SMTP_SSL через smtplib
│   │   └── queue_manager.py    # EmailQueueManager + APScheduler
│   └── api/                    # FastAPI-роутеры (HTTP-слой)
│       ├── tracker_routes.py
│       ├── qr_routes.py
│       ├── budget_routes.py
│       └── email_routes.py
├── templates/                  # Jinja2 HTML (6 шаблонов)
├── data/                       # JSON-файлы с данными
└── tests/                      # 38 тест-кейсов
```

**Схема взаимодействия компонентов:**

```
Браузер (HTML + Tailwind CSS)
         │  HTTP
         ▼
     main.py (FastAPI)
         │
         ├── /tracker ──► FinanceService ──► JsonStorage ──► transactions.json
         │
         ├── /qr      ──► qr_utils (qrcode + Pillow)
         │                   PNG / ZIP → Response
         │
         ├── /budget  ──► BudgetService ──► budgets.json
         │                   └── httpx → frankfurter.app → курс валюты
         │
         └── /email   ──► EmailQueueManager ──► Mailer ──► SMTP Timeweb
                              └── APScheduler (фоновые задания)
```

**Ключевое архитектурное решение — разделение слоёв:**
- Сервисный слой (бизнес-логика) не знает о HTTP
- Роутер (HTTP-слой) не знает о деталях хранилища
- Хранилище (JsonStorage) — отдельный класс, его можно заменить на SQLite без правки сервиса

---

## 3. Реализация ключевых функций

### 3.1 Трекер доходов и расходов (`services.py`)

Центральный компонент — `FinanceService`. Транзакции хранятся в памяти как список датаклассов, синхронизируются с JSON-файлом при каждом изменении.

```python
def add_transaction(self, t_type: str, category: str, amount: float, date: str, description: str):
    new_id = max((t.id for t in self.transactions), default=0) + 1
    new_t = Transaction(new_id, t_type, category, amount, date, description)
    self.transactions.append(new_t)
    self._sync()  # сразу сохраняет в JSON

def get_balance(self) -> float:
    incomes  = sum(t.amount for t in self.transactions if t.type == "income")
    expenses = sum(t.amount for t in self.transactions if t.type == "expense")
    return incomes - expenses
```

Метод `get_chart_data()` возвращает словарь `{категория: сумма}` для расходов — он напрямую передаётся в Chart.js через Jinja2-шаблон как JSON.

### 3.2 Генератор QR-кодов (`qr_utils.py`)

Модуль работает без tkinter — только `qrcode` и `Pillow`. Подпись рисуется под QR-кодом путём создания нового холста большей высоты и вставки текста через `ImageDraw`.

```python
def create_qr_image(data: str, caption: str = "", box_size: int = 10) -> Image.Image:
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M,
                       box_size=box_size, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    if caption.strip():
        # создаём холст выше на высоту текста + отступ
        new_img = Image.new("RGB", (img.width, img.height + text_height + 20), "white")
        new_img.paste(img, (0, 0))
        draw.text((...), caption, fill="black", font=font)
        img = new_img
    return img
```

`batch_qr_zip()` собирает ZIP в памяти через `io.BytesIO` + `zipfile.ZipFile` — файл на диск не пишется, сразу отдаётся клиенту.

### 3.3 Калькулятор бюджета поездки (`service.py` + `budget_routes.py`)

Уникальный ID поездки генерируется через `uuid.uuid4()`. Конвертация валют выполняется асинхронно через `httpx` + бесплатный API `frankfurter.app`. Если API недоступен, `rate=1.0` и приложение не падает.

```python
async with httpx.AsyncClient(timeout=5) as client:
    resp = await client.get(
        f"https://api.frankfurter.app/latest?from={currency}&to={target_currency}"
    )
    data = resp.json()
    rate = data["rates"].get(target_currency, 1.0)  # .get() — защита от KeyError
```

### 3.4 Email-отправщик (`mailer.py` + `queue_manager.py`)

`Mailer` использует `smtplib.SMTP_SSL` со встроенным `timeout=10` чтобы не зависать при недоступном сервере. `EmailQueueManager` управляет фоновыми задачами через `APScheduler.BackgroundScheduler`.

```python
def send(self, to: str, subject: str, html_body: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{self.sender_name} <{self.sender_email}>"
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    with smtplib.SMTP_SSL(self.host, self.port, timeout=10) as server:
        server.login(self.username, self.password)
        server.sendmail(self.sender_email, to, msg.as_string())
```

---

## 4. Тестирование и отладка

### Автоматические тесты

Тесты написаны на `pytest`. SMTP не вызывается — `smtplib.SMTP_SSL` мокируется через `unittest.mock.patch`. Для трекера используется `MemoryStorage` (хранилище в памяти вместо файла). Для бюджета — `tmp_path` из pytest (временная папка).

Итого: **38 тест-кейсов, покрытие 96%**.

```
Name                              Stmts   Miss  Cover
-----------------------------------------------------
src/tracker/models.py                 8      0   100%
src/tracker/services.py              32      1    97%
src/tracker/storage.py               14      0   100%
src/qr_module/qr_utils.py            28      2    93%
src/budget/service.py                42      1    98%
src/email_module/mailer.py           16      0   100%
src/email_module/queue_manager.py    28      3    89%
-----------------------------------------------------
TOTAL                               168      7    96%
```

Запуск:
```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

### Ошибки, найденные при отладке

| # | Модуль | Ошибка | Причина | Исправление |
|---|---|---|---|---|
| 1 | `qr_utils.py` | `NameError: name 'box_size' is not defined` | Переменная не определена в области видимости batch_generate | Добавлен параметр `box_size=10` в сигнатуры всех функций |
| 2 | `services.py` | `AttributeError: 'NoneType' object has no attribute 'strip'` | Пустая строка из GET-запроса не приводилась к None | В роутере добавлена конвертация: `date_filter or None` |
| 3 | `storage.py` | `FileNotFoundError` при `dirname=""` | `os.makedirs("")` — невалидный путь | Вызов makedirs только если dirname непустой |
| 4 | `tracker_routes.py` | HTTP 422 без понятного сообщения при "1500,50" | Запятая вместо точки в числе — FastAPI не парсит float | Добавлен атрибут `pattern` на input + try/except в роутере |
| 5 | `budget_routes.py` | `KeyError` при запросе с `from=RUB` | frankfurter.app не поддерживает RUB | Использован `.get(key, 1.0)` + предупреждение в UI |
| 6 | `qr_routes.py` | `DataOverflowError` при пустом data | qrcode не может создать QR для пустой строки | Добавлена проверка `if not data.strip()` перед вызовом |
| 7 | `mailer.py` | Зависание при недоступном SMTP | `SMTP_SSL()` без таймаута блокирует поток | Добавлен `timeout=10` в `smtplib.SMTP_SSL()` |
| 8 | `budget/service.py` | `total_converted = 0` при отсутствии amount | Элементы без ключа "amount" давали 0 без предупреждения | Поле amount обязательное в форме + серверная проверка |
| 9 | `queue_manager.py` | Журнал писем пропадает после перезапуска | `self.jobs` — список в памяти, не персистентный | Дублирование журнала в `data/email_jobs.json` |
| 10 | `main.py` | `email_jobs` всегда пустой на dashboard | Импорт переменной `_queue` захватывал None при старте | Заменён на вызов функции `_get_queue()` в момент запроса |

### Ручная проверка

```bash
# Запустить сервер
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Проверить трекер через curl
curl -X POST http://localhost:8000/tracker/add \
  -d "type=income&category=Зарплата&amount=50000&date=2026-05-24&description=Аванс"

# Проверить конвертацию валют
curl "http://localhost:8000/budget/convert?from_currency=USD&to_currency=EUR&amount=100"
# → {"from":"USD","to":"EUR","rate":0.924,"result":92.4}

# Проверить генерацию QR
curl -X POST http://localhost:8000/qr/generate \
  -F "data=https://redsgames.ru" -F "caption=Quadra" --output qr.png
```

---

## 5. Результаты и выводы

### Что реализовано в полном объёме

- Трекер доходов и расходов: CRUD, фильтрация по дате и категории, Chart.js диаграмма, TXT-экспорт
- QR-генератор: одиночный QR с подписью (PNG), пакетная генерация из TXT в ZIP-архив, без tkinter
- Калькулятор бюджета: профили поездок, расчёт итога, конвертация валют через frankfurter.app, сохранение
- Email: немедленная и отложенная отправка через SMTP_SSL Timeweb, APScheduler, журнал задач
- Dashboard: сводная страница с виджетами всех четырёх модулей, анимированные счётчики
- 38 автоматических тестов, покрытие 96%, без единого теста с реальной сетью или реальным SMTP
- Деплой на redsgames.ru: Nginx → Uvicorn, SSL через Let's Encrypt, systemd-сервис

### Что можно доработать

- Кэширование курсов валют (сейчас каждый расчёт → запрос к API)
- Валидация email-адреса перед отправкой
- Пагинация в трекере (при большом числе транзакций таблица длинная)
- Ограничение длины QR-данных (версия 1 вмещает до 41 символа ASCII)
- Dependency injection через `fastapi.Depends()` вместо глобальных переменных

### Навыки, полученные за практику

- Проектирование многомодульного Python-приложения с разделением сервисного и HTTP-слоёв
- Разработка REST API на FastAPI: роутеры, Form-данные, файловые загрузки, стриминг ответов
- Генерация изображений из кода (qrcode + Pillow), работа с ZIP в памяти (io.BytesIO)
- Асинхронная работа с внешними API через httpx в async-роутерах FastAPI
- Планирование фоновых задач через APScheduler внутри ASGI-приложения
- Отправка HTML-писем через smtplib.SMTP_SSL без сторонних клиентов
- Написание pytest-тестов с мокированием SMTP, файловой системы (tmp_path) и сети
- Деплой на Linux-сервер: systemd, Nginx reverse proxy, SSL/TLS через certbot

---

## Приложения

- **Живой сайт:** [https://redsgames.ru](https://redsgames.ru)
- **Репозиторий:** [https://github.com/RedsGames/quadra](https://github.com/RedsGames/quadra)
