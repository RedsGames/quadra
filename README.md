# Quadra
**Автор:** Анисько Павел Владимирович, Спиричева Юлия Сергеевна, Спиричева Анастасия Сергеевна, Дмитриева Евгения Валерьевна | **Группа:** [ИС-31] |

Единый веб-сервис на FastAPI, объединяющий четыре учебных модуля: трекер доходов и расходов, генератор QR-кодов, калькулятор бюджета поездки и отправщик email-отчётов.

**Живая демонстрация:** [redsgames.ru](https://redsgames.ru)

---

## Возможности

| Модуль | URL | Что умеет |
|---|---|---|
| Трекер | `/tracker` | Учёт доходов и расходов, фильтрация, диаграммы Chart.js, экспорт TXT |
| QR-генератор | `/qr` | Одиночный QR-код с подписью (PNG), пакетная генерация из TXT-файла (ZIP) |
| Бюджет поездки | `/budget` | Расчёт бюджета с конвертацией валют, сохранение профилей |
| Email | `/email` | Немедленная и отложенная отправка писем через SMTP, журнал задач |
| Dashboard | `/` | Сводная страница: баланс, последние транзакции, поездки, очередь писем |

---

## Структура проекта

```
quadra/
├── main.py                     # FastAPI-приложение, подключение роутеров
├── requirements.txt            # Зависимости Python
├── .env                        # SMTP-настройки и SECRET_KEY (не в git)
├── src/
│   ├── api/
│   │   ├── tracker_routes.py   # GET/POST /tracker — трекер транзакций
│   │   ├── qr_routes.py        # GET/POST /qr    — QR-генератор
│   │   ├── budget_routes.py    # GET/POST /budget — калькулятор поездок
│   │   └── email_routes.py     # GET/POST /email  — отправщик писем
│   ├── tracker/
│   │   ├── models.py           # Датакласс Transaction
│   │   ├── services.py         # FinanceService: логика баланса, фильтрации, экспорта
│   │   └── storage.py          # JsonStorage: чтение/запись JSON-файлов
│   ├── qr_module/
│   │   └── qr_utils.py         # create_qr_image, qr_to_bytes, batch_qr_zip
│   ├── budget/
│   │   └── service.py          # BudgetService + датакласс TripProfile
│   └── email_module/
│       ├── mailer.py           # Mailer: SMTP_SSL-отправка через smtplib
│       └── queue_manager.py    # EmailQueueManager с APScheduler
├── templates/
│   ├── base.html               # Базовый Jinja2-шаблон (навигация, стили)
│   ├── dashboard.html          # Главная — сводка по всем модулям
│   ├── tracker.html            # Страница трекера с Chart.js
│   ├── qr.html                 # Страница QR-генератора
│   ├── budget.html             # Страница бюджета поездок
│   └── email.html              # Страница email-управления
├── static/                     # CSS, JS
├── data/
│   ├── transactions.json       # База транзакций (создаётся автоматически)
│   └── budgets.json            # Профили поездок (создаётся автоматически)
└── tests/
    ├── test_tracker.py         # 14 тест-кейсов для трекера
    ├── test_qr.py              # 9 тест-кейсов для QR-модуля
    ├── test_budget.py          # 11 тест-кейсов для калькулятора бюджета
    └── test_mailer.py          # 4 тест-кейса для email (SMTP мокируется)
```

---

## Установка

```bash
# 1. Клонировать репозиторий
git clone https://github.com/RedsGames/quadra.git
cd quadra

# 2. Создать и активировать виртуальное окружение
python3 -m venv .venv

# Linux / macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# 3. Установить зависимости
pip install -r requirements.txt
```

---

## Конфигурация

Создайте файл `.env` в корне проекта и укажите реальные значения:

```env
SMTP_HOST=smtp.timeweb.ru
SMTP_PORT=465
SMTP_USERNAME=quadra@redsgames.ru
SMTP_PASSWORD=ваш_пароль
SMTP_SENDER_NAME=Quadra App
SMTP_SENDER_EMAIL=quadra@redsgames.ru
SECRET_KEY=любая_случайная_строка
```

Если `SMTP_HOST` не заполнен — приложение запустится, но модуль Email будет недоступен.
Все остальные три модуля работают без SMTP-настроек.

---

## Запуск

### Режим разработки (с автоперезагрузкой)

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Откройте браузер: [http://localhost:8000](http://localhost:8000)

### Продакшн на сервере Ubuntu (systemd)

```bash
# Запуск службы
sudo systemctl start quadra
sudo systemctl status quadra

# Логи
sudo journalctl -u quadra -f
```

Пример `/etc/systemd/system/quadra.service`:

```ini
[Unit]
Description=Quadra Web App
After=network.target

[Service]
User=root
WorkingDirectory=/root/quadra
ExecStart=/root/quadra/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

### Nginx + SSL

```nginx
server {
    server_name redsgames.ru www.redsgames.ru;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# SSL через Let's Encrypt
certbot --nginx -d redsgames.ru
```

---

## Запуск тестов

```bash
# Все тесты
pytest tests/ -v

# С отчётом о покрытии
pytest tests/ -v --cov=src --cov-report=term-missing

# Только один модуль
pytest tests/test_tracker.py -v
pytest tests/test_qr.py -v
pytest tests/test_budget.py -v
pytest tests/test_mailer.py -v
```

Пример вывода:
```
tests/test_tracker.py ...............    [ 14 passed ]
tests/test_qr.py .........               [  9 passed ]
tests/test_budget.py ...........         [ 11 passed ]
tests/test_mailer.py ....                [  4 passed ]

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

---

## Архитектура и поток данных

```
Браузер (HTML + Tailwind CSS)
        │  HTTP-запросы
        ▼
main.py — FastAPI (роутеры подключены через include_router)
        │
        ├── /tracker  → tracker_routes.py → FinanceService → JsonStorage → data/transactions.json
        │
        ├── /qr       → qr_routes.py      → qr_utils.py (qrcode + Pillow)
        │
        ├── /budget   → budget_routes.py  → BudgetService → data/budgets.json
        │                                └──► httpx → api.frankfurter.app (курсы валют)
        │
        └── /email    → email_routes.py   → EmailQueueManager → Mailer → SMTP Timeweb
                                          └──► APScheduler (фоновые задания)
```

**Принцип разделения:** каждый модуль — отдельный слой сервиса (бизнес-логика) + роутер (HTTP).
Роутер не знает, как хранятся данные. Сервис не знает о HTTP.

---

## Зависимости

| Пакет | Версия | Назначение |
|---|---|---|
| `fastapi` | 0.136.3 | Веб-фреймворк |
| `uvicorn[standard]` | 0.48.0 | ASGI-сервер |
| `jinja2` | 3.1.6 | HTML-шаблонизатор |
| `qrcode` | 8.2 | Генерация QR-кодов |
| `pillow` | 12.2.0 | Работа с изображениями (подписи на QR) |
| `python-dotenv` | 1.2.2 | Загрузка переменных из `.env` |
| `apscheduler` | 3.11.2 | Планировщик отложенных email-задач |
| `aiofiles` | 25.1.0 | Асинхронная работа с файлами |
| `python-multipart` | 0.0.29 | Обработка HTML-форм (Form-данные) |
| `httpx` | 0.28.1 | HTTP-клиент для API конвертации валют |

Стандартная библиотека: `smtplib`, `email`, `json`, `os`, `uuid`, `dataclasses`, `logging`, `zipfile`, `io`.
