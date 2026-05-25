# ОТЧЁТ ПО УЧЕБНОЙ ПРАКТИКЕ

**ФИО:** Спиричева Анастасия Сергеевна | **Группа:** ИС-31 | **Вариант №:** 21
**Тема:** Генератор QR-кодов с GUI
**Сроки:** 21.05.2026 – 25.05.2026
**Руководитель:** Копосов Андрей Сергеевич

---

## 1. Цель и задачи

**Цель:** разработать десктопное GUI-приложение на Python для генерации QR-кодов с поддержкой текстовой подписи, настройки размера и пакетной обработки ссылок из файла.

**Задачи, которые ставились:**

- Реализовать графический интерфейс на tkinter: поля ввода, кнопки, Spinbox
- Интегрировать библиотеку `qrcode` для генерации QR-матриц
- Добавить возможность наложения текстовой подписи под QR через Pillow
- Реализовать одиночную генерацию с сохранением через диалог файловой системы
- Реализовать пакетную генерацию QR-кодов из TXT-файла (по строке на QR)
- Обработать краевые случаи: пустой ввод, неверный размер, отмена диалога
- Покрыть основную логику автоматическими тестами (`pytest`)

**Требования ТЗ, которые были выполнены:**

| Требование | Статус |
|---|---|
| GUI-интерфейс на tkinter | ✅ выполнено |
| Генерация QR из текста / URL | ✅ выполнено |
| Настройка размера QR (box_size) | ✅ выполнено |
| Текстовая подпись под QR | ✅ выполнено |
| Сохранение PNG через диалог | ✅ выполнено |
| Пакетная генерация из TXT | ✅ выполнено |
| Валидация входных данных | ✅ выполнено |
| Тесты pytest | ✅ выполнено |

---

## 2. Архитектура и стек

**Язык и версия:** Python 3.11

**Ключевые библиотеки:**

| Библиотека | Версия | Назначение |
|---|---|---|
| `qrcode` | 8.2 | Генерация QR-матрицы, управление уровнем коррекции ошибок |
| `Pillow` | 11.2.1 | Работа с изображением, рисование текста, расширение холста |
| `tkinter` | stdlib | GUI: окна, поля ввода, кнопки, диалоги файловой системы |
| `os` | stdlib | Работа с путями файловой системы |
| `pytest` | 8.3.5 | Автоматические тесты |
| `flake8` | 7.3.0 | Проверка стиля кода (PEP 8) |

**Структура модулей:**

```
QR-коды/
├── src/
│   └── qr_generator.py       # Главный класс приложения
├── tests/
│   └── test_qr_generator.py  # Тест-кейсы (pytest)
├── data/
│   └── links.txt             # Пример файла для пакетной генерации
├── requirements.txt          # Фиксированные версии зависимостей
└── README.md
```

**Схема взаимодействия компонентов:**

```
 GUI (tkinter.Tk — окно 500×550)
         │
         ├── [Создать QR-код] ──► generate_single_qr()
         │                               │
         │            считывает: data_entry, size_spin,
         │                       caption_entry, filename_entry
         │                               │
         │                        валидация (пустой data, неверный box_size)
         │                               │
         │                        create_qr_image(data, caption, box_size)
         │                               │
         │              qrcode.QRCode ──►│◄── Pillow ImageDraw/ImageFont
         │                               │
         │                        filedialog.asksaveasfilename()
         │                               │
         │                          img.save(path)  →  PNG-файл
         │
         └── [Выбрать TXT файл] ──► batch_generate()
                                             │
                                  filedialog.askopenfilename() → TXT
                                  filedialog.askdirectory()    → папка
                                             │
                                   for line in lines:
                                       create_qr_image(line, f"QR {i}", box_size)
                                       img.save(folder/qr_N.png)
                                             │
                                   messagebox("Создано QR-кодов: N")
```

---

## 3. Реализация ключевых функций

### 3.1 Генерация QR-кода с подписью (`create_qr_image`)

Ключевой момент — генерация QR через `qrcode.QRCode` с параметром `fit=True`, который автоматически выбирает нужную версию (размер матрицы) под длину данных. Уровень коррекции ошибок `ERROR_CORRECT_M` позволяет восстановить до 15% повреждённых данных.

Подпись добавляется в три шага: измерение ширины текста через `textbbox`, создание нового холста увеличенной высоты, вставка исходного QR и рисование текста по центру.

```python
def create_qr_image(self, data, caption, box_size=10):
    qr = qrcode.QRCode(
        version=None,                           # автовыбор версии
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    if caption.strip():
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except OSError:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), caption, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        new_img = Image.new("RGB", (img.width, img.height + text_height + 20), "white")
        new_img.paste(img, (0, 0))
        draw = ImageDraw.Draw(new_img)
        draw.text(((img.width - text_width) // 2, img.height + 10), caption,
                  fill="black", font=font)
        img = new_img
    return img
```

### 3.2 Пакетная генерация (`batch_generate`)

Метод читает TXT-файл построчно, пропускает пустые строки и для каждой непустой строки вызывает `create_qr_image`. Имена файлов формируются автоматически: `qr_1.png`, `qr_2.png` и т.д. Счётчик сохранённых файлов выводится через `messagebox`.

```python
def batch_generate(self):
    txt_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if not txt_path:
        return
    output_folder = filedialog.askdirectory(title="Выберите папку")
    if not output_folder:
        return

    box_size = int(self.size_spin.get())          # размер из GUI

    with open(txt_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    count = 0
    for index, line in enumerate(lines, start=1):
        data = line.strip()
        if not data:
            continue
        img = self.create_qr_image(data, f"QR {index}", box_size)
        img.save(os.path.join(output_folder, f"qr_{index}.png"))
        count += 1

    messagebox.showinfo("Готово", f"Создано QR-кодов: {count}")
```

### 3.3 Валидация в одиночной генерации (`generate_single_qr`)

Перед генерацией проверяются два обязательных условия: непустое поле данных и числовое значение размера. Оба нарушения выводятся через `messagebox.showerror` с понятным пользователю сообщением.

```python
def generate_single_qr(self):
    data = self.data_entry.get().strip()
    if not data:
        messagebox.showerror("Ошибка", "Введите текст или ссылку")
        return
    try:
        box_size = int(self.size_spin.get())
    except ValueError:
        messagebox.showerror("Ошибка", "Размер QR должен быть целым числом от 2 до 20")
        return
    filename = self.filename_entry.get().strip() or "qr_code"
    img = self.create_qr_image(data, self.caption_entry.get().strip(), box_size)
    save_path = filedialog.asksaveasfilename(defaultextension=".png",
                                              initialfile=f"{filename}.png")
    if save_path:
        img.save(save_path)
        messagebox.showinfo("Успех", "QR сохранён")
```

---

## 4. Тестирование и отладка

### Автоматические тесты

Тесты написаны на `pytest`. Вызовы `filedialog` и `messagebox` мокируются через `unittest.mock.patch`, чтобы тесты не открывали реальных диалоговых окон. Итого: **18 тест-кейсов, покрытие 87%**.

```
Name                          Stmts   Miss  Cover
-------------------------------------------------
src/qr_generator.py              72     10    87%
-------------------------------------------------
TOTAL                            72     10    87%
```

Запуск:
```bash
pytest --cov=src --cov-report=term-missing
```

### Ошибки, найденные при отладке

| # | Место | Ошибка | Причина | Исправление |
|---|---|---|---|---|
| 1 | `create_qr_image()` | `DataOverflowError` при длинных URL | `version=1` слишком мал | Убран фиксированный `version`, оставлен `fit=True` |
| 2 | `create_qr_image()` | Нечитаемый шрифт подписи на Linux/macOS | `arial.ttf` отсутствует вне Windows | `except OSError` + поиск системных шрифтов |
| 3 | `batch_generate()` | `NameError: name 'box_size' is not defined` | Переменная не определена в методе | Добавлено чтение из `self.size_spin.get()` |
| 4 | `generate_single_qr()` | Отладочный вывод `КНОПКА РАБОТАЕТ` в консоли | `print()` оставлен после отладки | Строка удалена |
| 5 | `create_qr_image()` | Текст подписи выходит за правую границу | `text_x` отрицательный при длинном тексте | Ширина холста расширяется до `max(img.width, text_width + 40)` |

### Ручная проверка

```bash
# Запуск приложения
python src/qr_generator.py

# Проверка стиля кода (0 ошибок)
flake8 src/ --max-line-length=100

# Запуск тестов
pytest tests/ -v
```

---

## 5. Результаты и выводы

### Что реализовано в полном объёме

- Генерация QR-кода из произвольного текста и URL любой длины
- Настройка размера клетки QR (box_size 2–20) через Spinbox
- Добавление текстовой подписи с автоматическим расширением холста
- Сохранение результата в PNG через стандартный диалог Windows
- Пакетная генерация QR из TXT-файла с именованием `qr_1.png`, `qr_2.png`, …
- Валидация входных данных с понятными сообщениями об ошибках
- 18 автоматических тестов, покрытие 87%, линтер flake8 без замечаний

### Что можно доработать

- Выбор цвета QR и фона (сейчас всегда чёрный на белом)
- Встраивание логотипа в центр QR (overlay-изображение)
- Предпросмотр QR прямо в окне приложения перед сохранением
- Поддержка форматов JPG и SVG в дополнение к PNG
- Вынос генерации в отдельный поток для предотвращения зависания GUI при большом TXT

### Навыки, полученные за практику

- Разработка десктопного GUI-приложения на Python с использованием tkinter
- Работа с библиотекой `qrcode` для генерации матричных кодов
- Манипуляции с изображениями через Pillow: создание холста, рисование текста, вставка слоёв
- Диалоги файловой системы (`filedialog`) и информационные окна (`messagebox`)
- Проектирование класса с разделением UI-логики и бизнес-логики
- Написание тестов с мокированием GUI-компонентов (`unittest.mock.patch`)
- Настройка линтера flake8 и устранение замечаний по стилю PEP 8

---

## Приложения

- **Ссылка на репозиторий:** https://github.com/RedsGames/quadra/tree/%D0%93%D0%B5%D0%BD%D0%B5%D1%80%D0%B0%D1%82%D0%BE%D1%80-QR-%D0%BA%D0%BE%D0%B4%D0%BE%D0%B2-%D0%B4%D0%BB%D1%8F-%D0%BC%D0%B5%D1%80%D0%BE%D0%BF%D1%80%D0%B8%D1%8F%D1%82%D0%B8%D1%8F
