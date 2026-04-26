import csv
from collections import defaultdict
from src.domain.interfaces import ITransactionRepository
from src.domain.types import Transaction, TransactionType, DashboardSummary, TransactionFilter

class FinanceService:
    def __init__(self, repo: ITransactionRepository):
        self.repo = repo

        self._income_categories = [
            "Зарплата", "Стипендия", "Премия", "Подработка", "Перевод",
            "Выплаты", "Дивиденды", "Проценты", "Подарки", "Возврат долга",
            "Продажа", "Прочее"
        ]
        self._expense_categories = [
            "Еда", "Ресторан", "Кафе", "Транспорт", "Жилье",
            "Коммунальные", "Связь", "Интернет", "Одежда", "Здоровье",
            "Развлечения", "Путешествия", "Образование", "Подарки",
            "Подписки", "Дом и быт", "Техника", "Такси", "Прочее"
        ]
        self._expense_set = set(self._expense_categories)

    def get_summary(self) -> DashboardSummary:
        transactions = self.repo.get_filtered(TransactionFilter())
        
        income = sum(t.amount for t in transactions if t.type == TransactionType.INCOME)
        expense = sum(t.amount for t in transactions if t.type == TransactionType.EXPENSE)
        
        # Categories (Expense only)
        cat_map = defaultdict(float)
        for t in transactions:
            if t.type == TransactionType.EXPENSE:
                cat_map[t.category] += t.amount
        
        # Balance History
        sorted_tx = sorted(transactions, key=lambda x: x.date_added)
        balance_history = {}
        
        # Changes by day
        daily_changes = defaultdict(float)
        for t in sorted_tx:
            impact = t.amount if t.type == TransactionType.INCOME else -t.amount
            daily_changes[t.date_added.isoformat()] += impact
            
        # Running total
        dates = sorted(daily_changes.keys())
        running_bal = 0.0
        for d in dates:
            running_bal += daily_changes[d]
            balance_history[d] = running_bal

        return DashboardSummary(
            total_income=income,
            total_expense=expense,
            balance=income - expense,
            expense_by_category=dict(cat_map),
            balance_history=balance_history
        )
        
    def export_csv(self, filename: str, filters: TransactionFilter):
        data = self.repo.get_filtered(filters)
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Дата", "Тип", "Категория", "Сумма", "Описание"])
            for t in data:
                writer.writerow([t.id, t.date_added, t.type.value, t.category, t.amount, t.description])

    def get_all_categories(self):
        return self.repo.get_categories()

    def get_categories_for_type(self, tx_type: TransactionType):
        defaults = self._income_categories if tx_type == TransactionType.INCOME else self._expense_categories
        existing = self.repo.get_categories_by_type(tx_type)
        deny = self._expense_set if tx_type == TransactionType.INCOME else set()
        return self._merge_categories(defaults, existing, deny)

    def add_category(self, name: str):
        if name: self.repo.add_category(name)

    @staticmethod
    def _merge_categories(defaults, existing, deny):
        merged = []
        seen = set()
        for item in defaults + existing:
            if item in deny:
                continue
            if item not in seen:
                merged.append(item)
                seen.add(item)
        return merged