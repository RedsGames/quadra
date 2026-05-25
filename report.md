# ОТЧЁТ ПО УЧЕБНОЙ ПРАКТИКЕ

**ФИО:** [Анисько Павел Владимирович] | **Группа:** [ИС-31] | **Вариант №:** 18
**Тема:** Автоотправщик email-отчётов
**Сроки:** 21.05.2026 – 25.05.2026
**Руководитель:** [Копосов Андрей Сергеевич]

---

## 1. Цель и задачи

**Цель:** разработать консольный инструмент на Python для автоматической отправки HTML-отчётов по электронной почте с поддержкой очереди, шаблонизации и журналирования.

**Задачи, которые ставились:**

- Реализовать отправку писем через протокол SMTP с поддержкой STARTTLS и SSL
- Создать систему HTML-шаблонов на базе Jinja2 для формирования тела письма
- Разработать персистентную очередь отправки с автоматическими повторными попытками
- Вынести все настройки (хост, порт, пароль) в конфигурационный файл без хардкода
- Настроить журналирование с ротацией лог-файла
- Покрыть основную логику автоматическими тестами (pytest)

**Требования ТЗ, которые были выполнены:**

| Требование | Статус |
|---|---|
| Отправка через smtplib | ✅ выполнено |
| HTML-шаблонизатор (Jinja2) | ✅ выполнено |
| Очередь отправки с повторами | ✅ выполнено |
| Лог отправок | ✅ выполнено |
| Конфиг без хардкода | ✅ выполнено |
| Тесты pytest | ✅ выполнено |

---

## 2. Архитектура и стек

**Язык и версия:** Python 3.11

**Ключевые библиотеки:**

| Библиотека | Версия | Назначение |
|---|---|---|
| `jinja2` | 3.1.6 | HTML-шаблонизатор с автоэкранированием |
| `smtplib` | stdlib | SMTP-отправка (STARTTLS / SSL) |
| `email` | stdlib | Формирование MIME-сообщений |
| `configparser` | stdlib | Чтение config.ini |
| `logging` | stdlib | Журналирование с RotatingFileHandler |
| `pytest` | 9.0.3 | Автоматические тесты |
| `pytest-cov` | 7.1.0 | Отчёт о покрытии кода |
| `flake8` | 7.3.0 | Проверка стиля кода (PEP 8) |

**Структура модулей:**

```
Email/
├── src/
│   ├── models.py           # Датаклассы: EmailMessage, QueueItem, EmailStatus
│   ├── config.py           # Загрузка конфигурации (configparser + env)
│   ├── logger.py           # RotatingFileHandler, консольный хендлер
│   ├── template_engine.py  # Обёртка над Jinja2
│   ├── mailer.py           # SMTP-отправка
│   └── queue_manager.py    # JSON-очередь с персистентностью
├── templates/
│   ├── base.html           # Базовый шаблон (наследование)
│   ├── daily_report.html   # Ежедневный отчёт
│   └── weekly_report.html  # Еженедельный отчёт
├── tests/                  # 65 тест-кейсов
├── data/                   # queue.json (создаётся автоматически)
├── logs/                   # app.log (создаётся автоматически)
├── main.py                 # CLI-точка входа (argparse)
└── config.ini              # Настройки SMTP и приложения
```

**Схема взаимодействия компонентов:**

```
 CLI (main.py / argparse)
         │
         ├─── [send / queue] ──► TemplateEngine.render(template, context)
         │                               │ Jinja2 → HTML-строка
         │                               ▼
         │                        EmailMessage(to, subject, body_html)
         │                               │
         │              ┌────────────────┴────────────────┐
         │           [send]                            [queue]
         │              │                                  │
         │        Mailer.send()                  QueueManager.add()
         │         SMTP-сервер                      queue.json
         │
         └─── [process] ──► QueueManager.get_pending()
                                     │
                             for item: Mailer.send()
                                  ├── OK  → mark_sent()
                                  └── ERR → mark_failed() → retrying / failed

         └─── [status]  ──► QueueManager.stats() → вывод в консоль
```

---

## 3. Реализация ключевых функций

### 3.1 Отправка письма через SMTP (`mailer.py`)

Ключевой момент — поддержка двух режимов TLS. При `use_tls = true` используется STARTTLS (порт 587), иначе — implicit SSL (порт 465). Все исключения smtplib перехватываются и оборачиваются в `MailerError`, чтобы вызывающий код не зависел от деталей SMTP.

```python
def send(self, message: EmailMessage) -> None:
    mime = self._build_mime(message)
    recipients = self._all_recipients(message)
    try:
        if self._config.use_tls:
            smtp = smtplib.SMTP(self._config.host, self._config.port, timeout=30)
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
        else:
            smtp = smtplib.SMTP_SSL(self._config.host, self._config.port, timeout=30)
        with smtp:
            smtp.login(self._config.username, self._config.password)
            smtp.sendmail(self._config.sender_email, recipients, mime.as_bytes())
    except smtplib.SMTPAuthenticationError as exc:
        raise MailerError("SMTP authentication failed — check username/password") from exc
    except smtplib.SMTPException as exc:
        raise MailerError(f"SMTP error: {exc}") from exc
```

### 3.2 Персистентная очередь с повторными попытками (`queue_manager.py`)

Очередь хранится в `data/queue.json`. При каждой операции файл читается, изменяется и записывается обратно. Метод `mark_failed()` увеличивает счётчик попыток: если счётчик меньше `max_retries` — статус `retrying`, иначе — `failed`.

```python
def mark_failed(self, item_id: str, error: str) -> None:
    items = self._load()
    for item in items:
        if item["item_id"] == item_id:
            item["retries"] += 1
            item["last_error"] = error
            if item["retries"] >= self._max_retries:
                item["status"] = EmailStatus.FAILED.value
            else:
                item["status"] = EmailStatus.RETRYING.value
            break
    self._save(items)
```

### 3.3 Шаблонизация писем через Jinja2 (`template_engine.py`)

Шаблоны наследуются от `base.html` через `{% extends %}`. Автоэкранирование HTML включено на уровне `Environment`, что защищает от XSS при подстановке пользовательских данных в тело письма.

```python
def __init__(self, templates_dir: Path) -> None:
    self._env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=True,          # экранирует < > & " ' в переменных
    )

def render(self, template_name: str, context: Dict[str, Any]) -> str:
    try:
        template = self._env.get_template(template_name)
    except TemplateNotFound as exc:
        raise FileNotFoundError(f"Template not found: {template_name}") from exc
    return template.render(**context)
```

---

## 4. Тестирование и отладка

### Автоматические тесты

Тесты написаны на `pytest`. SMTP не вызывается реально — `smtplib.SMTP` мокируется через `unittest.mock.patch`. Итого: **65 тест-кейсов, покрытие 99%**.

```
Name                     Stmts   Miss  Cover
--------------------------------------------
src/config.py               32      1    97%
src/logger.py               19      0   100%
src/mailer.py               48      0   100%
src/models.py               33      1    97%
src/queue_manager.py        70      0   100%
src/template_engine.py      15      0   100%
--------------------------------------------
TOTAL                      217      2    99%
```

Запуск:
```
pytest --cov=src --cov-report=term-missing
```

### Ошибки, найденные при отладке

| # | Модуль | Ошибка | Причина | Исправление |
|---|---|---|---|---|
| 1 | `config.py` | `UnicodeDecodeError: 'charmap'` | `configparser` читал UTF-8 файл как cp1252 на Windows | Добавлен `encoding="utf-8"` в `parser.read()` |
| 2 | `base.html` | `TemplateAssertionError: block 'title' defined twice` | Блок `{% block title %}` объявлен в `<title>` и в `<h1>` | Второй заменён на `{{ self.title() }}` |
| 3 | `queue_manager.py` | `FileNotFoundError` при первом запуске | Директория `data/` не создавалась | Добавлен `mkdir(parents=True, exist_ok=True)` |
| 4 | `logger.py` | `FileNotFoundError` при первом запуске | Директория `logs/` не создавалась | Добавлен `log_file.parent.mkdir(...)` |
| 5 | `mailer.py` | Пустой заголовок `Cc:` в письме | Заголовок добавлялся даже при пустом списке | Добавлена проверка `if message.cc:` |

### Ручная проверка

```
# Добавить письмо в очередь
python main.py queue --to test@example.com --subject "Тест" \
  --template daily_report.html --context '{"report_date":"2026-05-25",...}'

# Проверить статус очереди
python main.py status
# → pending: 1 / sent: 0 / failed: 0 / total: 1

# Запустить flake8 — 0 ошибок
flake8 src/ main.py --max-line-length=100
```

---

## 5. Результаты и выводы

### Что реализовано в полном объёме

- Отправка HTML-писем через SMTP (STARTTLS и SSL) без сторонних HTTP-клиентов
- Шаблонизатор на Jinja2 с наследованием шаблонов и автоэкранированием
- Персистентная JSON-очередь: статусы `pending → retrying → sent / failed`
- Журналирование: ротируемый файл (5 МБ × 3 копии) + консоль (WARNING+)
- CLI с четырьмя командами: `send`, `queue`, `process`, `status`
- Конфигурация через `config.ini` и переменные окружения (без хардкода)
- 65 автоматических тестов, покрытие 99%, линтер flake8 без замечаний

### Что можно доработать

- Встроенный планировщик (сейчас автозапуск только через внешний cron / Планировщик Windows)
- Валидация формата email-адресов на входе
- Команда `clear` для удаления писем со статусом `failed` из очереди
- Поддержка вложений (attachments) в письмах

### Навыки, полученные за практику

- Работа с сетевыми протоколами на уровне стандартной библиотеки (`smtplib`, `email`)
- Проектирование многомодульного Python-приложения с чёткими зонами ответственности
- Шаблонизация HTML-контента через Jinja2 и безопасная подстановка данных
- Написание тестов с мокированием внешних зависимостей (`unittest.mock`)
- Настройка CI-инструментов: покрытие (`pytest-cov`), стиль (`flake8`)
- Работа с конфигурацией через `configparser` и переменные окружения

---

## Приложения

- **Ссылка на репозиторий:** [https://github.com/RedsGames/quadra/tree/%D0%90%D0%B2%D1%82%D0%BE%D0%BE%D1%82%D0%BF%D1%80%D0%B0%D0%B2%D1%89%D0%B8%D0%BA-email-%D0%BE%D1%82%D1%87%D1%91%D1%82%D0%BE%D0%B2]
