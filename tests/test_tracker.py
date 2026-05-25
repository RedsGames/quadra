"""Тесты для модуля трекера доходов и расходов."""
import pytest
from src.tracker.models import Transaction
from src.tracker.storage import JsonStorage
from src.tracker.services import FinanceService


# --- Вспомогательный класс хранилища в памяти (без файлов) ---

class MemoryStorage:
    """Хранилище в памяти — для тестов не нужен реальный файл."""
    def __init__(self):
        self._data = []

    def load(self, filename):
        return self._data

    def save(self, filename, data):
        self._data = data


@pytest.fixture
def service():
    """Создаёт чистый FinanceService перед каждым тестом."""
    return FinanceService(MemoryStorage(), "test.json")


# --- Тесты модели Transaction ---

def test_transaction_to_dict():
    t = Transaction(1, "income", "Зарплата", 50000.0, "2026-05-24", "Майская")
    d = t.to_dict()
    assert d["id"] == 1
    assert d["type"] == "income"
    assert d["amount"] == 50000.0


def test_transaction_optional_description():
    t = Transaction(1, "expense", "Еда", 500.0, "2026-05-24")
    assert t.description == ""


# --- Тесты сервиса ---

def test_add_income(service):
    service.add_transaction("income", "Зарплата", 50000, "2026-05-24", "Аванс")
    assert len(service.transactions) == 1
    assert service.transactions[0].type == "income"
    assert service.transactions[0].amount == 50000


def test_add_expense(service):
    service.add_transaction("expense", "Еда", 1500, "2026-05-24", "Продукты")
    assert service.transactions[0].type == "expense"


def test_ids_autoincrement(service):
    service.add_transaction("income", "A", 100, "2026-05-01", "")
    service.add_transaction("income", "B", 200, "2026-05-02", "")
    assert service.transactions[0].id == 1
    assert service.transactions[1].id == 2


def test_balance_positive(service):
    service.add_transaction("income", "Зарплата", 50000, "2026-05-24", "")
    service.add_transaction("expense", "Аренда", 20000, "2026-05-24", "")
    assert service.get_balance() == 30000


def test_balance_negative(service):
    service.add_transaction("expense", "Долг", 5000, "2026-05-24", "")
    assert service.get_balance() == -5000


def test_balance_empty(service):
    assert service.get_balance() == 0


def test_delete_transaction(service):
    service.add_transaction("income", "Бонус", 3000, "2026-05-24", "")
    t_id = service.transactions[0].id
    result = service.delete_transaction(t_id)
    assert result is True
    assert len(service.transactions) == 0


def test_delete_nonexistent(service):
    result = service.delete_transaction(999)
    assert result is False


def test_filter_by_date(service):
    service.add_transaction("income", "A", 100, "2026-05-01", "")
    service.add_transaction("income", "B", 200, "2026-06-01", "")
    result = service.filter_transactions(date="2026-05")
    assert len(result) == 1
    assert result[0].category == "A"


def test_filter_by_category(service):
    service.add_transaction("expense", "Еда", 500, "2026-05-01", "")
    service.add_transaction("expense", "Транспорт", 200, "2026-05-01", "")
    result = service.filter_transactions(category="еда")  # регистр не важен
    assert len(result) == 1
    assert result[0].category == "Еда"


def test_filter_no_match(service):
    service.add_transaction("income", "Зарплата", 1000, "2026-05-01", "")
    result = service.filter_transactions(category="Несуществующая")
    assert result == []


def test_chart_data(service):
    service.add_transaction("expense", "Еда", 1000, "2026-05-01", "")
    service.add_transaction("expense", "Еда", 500, "2026-05-02", "")
    service.add_transaction("income", "Зарплата", 5000, "2026-05-01", "")
    data = service.get_chart_data()
    assert "Еда" in data
    assert data["Еда"] == 1500
    assert "Зарплата" not in data  # доходы не включаются


def test_export_text_contains_balance(service):
    service.add_transaction("income", "Зарплата", 10000, "2026-05-01", "")
    service.add_transaction("expense", "Аренда", 3000, "2026-05-01", "")
    text = service.export_text()
    assert "7000.00" in text
    assert "ФИНАНСОВЫЙ ОТЧЕТ" in text


# --- Тесты хранилища (JsonStorage) ---

def test_json_storage_load_missing_file(tmp_path):
    storage = JsonStorage()
    result = storage.load(str(tmp_path / "nonexistent.json"))
    assert result == []


def test_json_storage_save_and_load(tmp_path):
    storage = JsonStorage()
    filepath = str(tmp_path / "data.json")
    data = [{"id": 1, "type": "income", "amount": 100}]
    storage.save(filepath, data)
    loaded = storage.load(filepath)
    assert loaded == data
