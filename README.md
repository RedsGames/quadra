# Email Auto-Sender
**Автор:** [Анисько Павел Владимирович] | **Группа:** [ИС-31] | **Вариант №:** [18]
Консольный инструмент для автоматической отправки HTML email-отчётов с поддержкой очереди, шаблонизатора Jinja2 и журналирования.

---

## Возможности

| Функция | Описание |
|---|---|
| Шаблонизатор | Jinja2 с автоэкранированием HTML; поддержка наследования (`extends`) |
| Очередь отправки | Персистентная JSON-очередь; статусы `pending / retrying / sent / failed` |
| Повторные попытки | Настраиваемый `max_retries`; автоперевод в `failed` после исчерпания |
| Журналирование | Ротируемый лог-файл (5 МБ × 3 копии) + консоль (WARNING+) |
| Конфигурация | `config.ini` + переменные окружения (без хардкода) |
| Тесты | `pytest` + `pytest-cov`; 40+ тест-кейсов, мокирование SMTP |

---

## Структура проекта

```
Email/
├── src/
│   ├── config.py           # Загрузка конфигурации (configparser + env)
│   ├── models.py           # Датаклассы EmailMessage, QueueItem, EmailStatus
│   ├── template_engine.py  # Обёртка над Jinja2
│   ├── mailer.py           # SMTP-отправка (smtplib, STARTTLS / SSL)
│   ├── queue_manager.py    # JSON-очередь с персистентностью
│   └── logger.py           # Настройка logging с RotatingFileHandler
├── templates/
│   ├── base.html           # Базовый шаблон (наследование)
│   ├── daily_report.html   # Ежедневный отчёт
│   └── weekly_report.html  # Еженедельный отчёт
├── tests/
│   ├── test_models.py
│   ├── test_config.py
│   ├── test_template_engine.py
│   ├── test_queue_manager.py
│   └── test_mailer.py
├── data/                   # Файл очереди queue.json (создаётся автоматически)
├── logs/                   # Файл app.log (создаётся автоматически)
├── main.py                 # CLI-точка входа
├── config.ini.example      # Пример конфига — скопируйте в config.ini
└── requirements.txt
```

---

## Установка

```bash
# 1. Клонировать / распаковать проект
cd Email

# 2. Создать и активировать виртуальное окружение
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Создать конфиг
copy config.ini.example config.ini   # Windows
# cp config.ini.example config.ini   # Linux / macOS
# Заполните config.ini своими SMTP-настройками
```

---

## Конфигурация

Скопируйте `config.ini.example` → `config.ini` и укажите реальные значения.

```ini
[smtp]
host        = smtp.gmail.com
port        = 587
use_tls     = true
username    = your@gmail.com
password    = your_app_password   ; App Password, не основной пароль
sender_name = Auto Reporter
sender_email = your@gmail.com

[app]
queue_file    = data/queue.json
templates_dir = templates
log_file      = logs/app.log
max_retries   = 3
retry_delay   = 60
```

Любое поле можно переопределить переменной окружения:

```bash
set SMTP_PASSWORD=new_password   # Windows
export SMTP_PASSWORD=new_password # Linux / macOS
```

---

## Использование

### Немедленная отправка

```bash
python main.py send \
  --to recipient@example.com \
  --subject "Ежедневный отчёт 2026-05-24" \
  --template daily_report.html \
  --context '{"report_date":"2026-05-24","recipient_name":"Иван","metrics":[{"name":"Продажи","value":120,"delta":5},{"name":"Лиды","value":34,"delta":-2}],"generated_at":"2026-05-24 09:00"}'
```

### Добавление в очередь

```bash
python main.py queue \
  --to team@example.com \
  --subject "Еженедельный отчёт" \
  --template weekly_report.html \
  --context '{"week_number":21,"date_from":"2026-05-18","date_to":"2026-05-24","recipient_name":"Команда","summary":[{"name":"Доход","actual":500,"plan":450,"pct":111}],"top_items":["Запуск новой фичи","Обновление CI"],"generated_at":"2026-05-24 18:00"}'
```

### Обработка очереди

```bash
python main.py process
```

### Статистика очереди

```bash
python main.py status
```

Пример вывода:
```
Queue statistics:
  pending  : 2
  sent     : 5
  failed   : 1
  retrying : 0
  total    : 8
```

### Автоматизация (cron / Планировщик Windows)

```
# Обрабатывать очередь каждые 15 минут (Linux cron):
*/15 * * * * /path/to/.venv/bin/python /path/to/Email/main.py process
```

---

## Запуск тестов

```bash
# Все тесты
pytest

# С отчётом о покрытии
pytest --cov=src --cov-report=term-missing

# Только быстрые (без сети)
pytest tests/ -v
```

---

## Архитектура

```
main.py  (CLI / argparse)
    │
    ├── TemplateEngine   ←── Jinja2 + autoescape
    │       renders HTML body from template + context dict
    │
    ├── Mailer           ←── smtplib (SMTP / SMTP_SSL + STARTTLS)
    │       sends EmailMessage over SMTP
    │
    └── QueueManager     ←── JSON file (data/queue.json)
            add()         → enqueue with UUID
            get_pending() → PENDING + RETRYING items
            mark_sent()   → status = sent, sets sent_at
            mark_failed() → increment retries; FAILED when max_retries reached
            stats()       → counts per status
```

### Поток данных

```
 CLI args
    ↓
TemplateEngine.render(template, context)  →  HTML string
    ↓
EmailMessage(to, subject, body_html)
    ↓
  [send]──────────────→ Mailer.send()  →  SMTP server
  [queue]─────────────→ QueueManager.add()  →  queue.json
                                 ↓
                          process cmd
                                 ↓
                     QueueManager.get_pending()
                                 ↓
                     for each item: Mailer.send()
                          ↙           ↘
                 mark_sent()      mark_failed()
```

---

## Зависимости

| Пакет | Назначение |
|---|---|
| `jinja2` | HTML-шаблонизатор с автоэкранированием |
| `pytest` | Тестовый фреймворк |
| `pytest-cov` | Отчёт о покрытии кода |

Стандартная библиотека: `smtplib`, `email`, `configparser`, `logging`, `json`, `argparse`, `uuid`, `dataclasses`.
