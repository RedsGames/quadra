"""Тесты для модуля калькулятора бюджета поездки."""
import pytest
from src.budget.service import BudgetService


@pytest.fixture
def service(tmp_path):
    """Сервис с временным файлом — каждый тест начинает с чистого листа."""
    return BudgetService(str(tmp_path / "budgets.json"))


ITEMS = [
    {"name": "Авиабилеты", "amount": 30000},
    {"name": "Отель", "amount": 20000},
    {"name": "Питание", "amount": 10000},
]


def test_create_profile(service):
    profile = service.create_profile("Турция", "Анталья", "RUB", ITEMS)
    assert profile.name == "Турция"
    assert profile.destination == "Анталья"
    assert profile.total_base == 60000


def test_profile_id_is_string(service):
    profile = service.create_profile("Тест", "Москва", "RUB", [])
    assert isinstance(profile.id, str)
    assert len(profile.id) > 0


def test_get_profile(service):
    created = service.create_profile("Египет", "Хургада", "USD", ITEMS)
    found = service.get_profile(created.id)
    assert found is not None
    assert found.name == "Египет"


def test_get_profile_nonexistent(service):
    result = service.get_profile("does_not_exist")
    assert result is None


def test_list_profiles(service):
    service.create_profile("Поездка 1", "Сочи", "RUB", [])
    service.create_profile("Поездка 2", "Казань", "RUB", [])
    profiles = service.list_profiles()
    assert len(profiles) == 2


def test_list_profiles_empty(service):
    assert service.list_profiles() == []


def test_update_converted(service):
    profile = service.create_profile("Европа", "Париж", "EUR", ITEMS)
    service.update_converted(profile.id, 100.0)  # курс: 1 EUR = 100 RUB
    updated = service.get_profile(profile.id)
    assert updated.total_converted == 6_000_000.0


def test_total_base_calculated_correctly(service):
    items = [{"name": "A", "amount": 100}, {"name": "B", "amount": 250.5}]
    profile = service.create_profile("Тест", "Тест", "USD", items)
    assert profile.total_base == 350.5


def test_delete_profile(service):
    profile = service.create_profile("Удалить", "Нигде", "RUB", [])
    result = service.delete_profile(profile.id)
    assert result is True
    assert service.get_profile(profile.id) is None


def test_delete_nonexistent(service):
    result = service.delete_profile("fake_id")
    assert result is False


def test_profiles_persist_to_file(tmp_path):
    """Данные сохраняются и восстанавливаются из файла."""
    path = str(tmp_path / "budgets.json")
    svc1 = BudgetService(path)
    svc1.create_profile("Сохранённая", "Берлин", "EUR", ITEMS)

    svc2 = BudgetService(path)  # новый экземпляр, читает тот же файл
    profiles = svc2.list_profiles()
    assert len(profiles) == 1
    assert profiles[0].name == "Сохранённая"
