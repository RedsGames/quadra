"""
ОТЧЕТ О ТЕСТИРОВАНИИ (Проект: Finance JSON Tracker)
Среда: Python 3.8+

ВЫПОЛНЕННЫЙ ЧЕК-ЛИСТ:
[x] Добавление транзакции со строгим выбором типа (1. Доход / 2. Расход)
[x] Отображение описаний в общем списке транзакций
[x] Табличное форматирование UI для улучшения читаемости
[x] Исправленная логика фильтрации (удаление пробелов и игнорирование регистра)
[x] Экспорт в TXT с выравниванием столбцов и заголовками
[x] Реализация паузы (нажатие Enter) перед возвратом в меню

ИСПРАВЛЕННЫЕ ОШИБКИ:
- Ошибка Logic: Функция max() вызывала ValueError при пустом списке транзакций. 
  Решение: Добавлен аргумент default=0.
- Ошибка Logic: Фильтрация не находила записи из-за лишних пробелов в вводе пользователя.
  Решение: Применен метод .strip() к входным данным.
- Ошибка UX: Информация сливалась в один блок, затрудняя поиск нужной записи.
  Решение: Внедрен табличный вывод с фиксированной шириной колонок через f-строки.
- Ошибка Data: Поле 'тип' принимало произвольный текст, что ломало расчет баланса.
  Решение: Введен строгий выбор через цифровые индексы (1/2).
- Ошибка Export: В текстовом отчете отсутствовали колонки ID и описания.
  Решение: Обновлен метод export_summary с расширенной структурой таблицы.
- Ошибка Encoding: В Windows Блокноте отображались некорректные символы.
  Решение: Кодировка изменена на utf-8-sig (BOM) для автоматического распознавания.
- Ошибка UX: Лишний ввод имени файла при экспорте.
  Решение: Экспорт теперь происходит мгновенно в файл finance_report.txt.
- Архитектура: Папка data/ не использовалась для хранения БД.
  Решение: В main.py внедрена логика, принудительно сохраняющая JSON-файлы в директорию data/.
- Улучшение UX: Фильтрация по дате требовала ввода полного значения YYYY-MM-DD.
  Решение: Реализован поиск по подстроке, позволяющий фильтровать записи по году или месяцу.
"""

import pytest
import os
import sys

# Добавление пути для импорта модулей из папки src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.storage import JsonStorage
from src.services import FinanceService

@pytest.fixture
def service_instance():
    """Инициализация чистого сервиса для каждого теста"""
    if not os.path.exists("data"):
        os.makedirs("data")
    test_file = os.path.join("data", "test_audit.json")
    if os.path.exists(test_file): 
        os.remove(test_file)
    storage = JsonStorage()
    svc = FinanceService(storage, test_file)
    yield svc
    if os.path.exists(test_file): 
        os.remove(test_file)

def test_balance_calculation(service_instance):
    """Проверка точности расчета баланса"""
    service_instance.add_transaction("income", "Зарплата", 5000, "2024-05-01", "Основная")
    service_instance.add_transaction("expense", "Кофе", 300, "2024-05-02", "Старбакс")
    assert service_instance.get_balance() == 4700

def test_filter_functionality(service_instance):
    """Проверка фильтрации по категории и части даты (год/месяц)"""
    service_instance.add_transaction("income", "Зарплата", 5000, "2024-05-01", "Тест")
    service_instance.add_transaction("expense", "Кофе", 300, "2024-06-15", "Обед")

    # Тест: фильтрация по году
    res_year = service_instance.filter_transactions(date="2024")
    assert len(res_year) == 2

    # Тест: фильтрация по месяцу
    res_month = service_instance.filter_transactions(date="2024-05")
    assert len(res_month) == 1
    assert res_month[0].category == "Зарплата"

    # Тест: фильтрация по категории
    res_cat = service_instance.filter_transactions(category="  ЗАРПЛАТА  ")
    assert len(res_cat) == 1

def test_export_existence(service_instance):
    """Проверка создания и содержимого файла экспорта"""
    export_file = "test_export.txt"
    service_instance.add_transaction("expense", "Налоги", 1000, "2024-05-01", "ФНС")
    service_instance.export_summary(export_file)
    assert os.path.exists(export_file)
    with open(export_file, 'r', encoding='utf-8') as f:
        content = f.read()
        assert "Налоги" in content
        assert "ФНС" in content
    os.remove(export_file)

if __name__ == "__main__":
    # Вывод текстового отчета в консоль перед запуском тестов
    print(__doc__)
    pytest.main([__file__])