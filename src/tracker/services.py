from src.tracker.models import Transaction


class FinanceService:
    def __init__(self, storage, filename: str):
        self.storage = storage
        self.filename = filename
        self.transactions = [Transaction(**t) for t in self.storage.load(filename)]

    def add_transaction(self, t_type: str, category: str, amount: float, date: str, description: str):
        new_id = max((t.id for t in self.transactions), default=0) + 1
        new_t = Transaction(new_id, t_type, category, amount, date, description)
        self.transactions.append(new_t)
        self._sync()

    def delete_transaction(self, t_id: int) -> bool:
        before = len(self.transactions)
        self.transactions = [t for t in self.transactions if t.id != t_id]
        self._sync()
        return len(self.transactions) != before

    def get_balance(self) -> float:
        incomes = sum(t.amount for t in self.transactions if t.type == "income")
        expenses = sum(t.amount for t in self.transactions if t.type == "expense")
        return incomes - expenses

    def filter_transactions(self, date: str = None, category: str = None) -> list:
        result = self.transactions
        if date:
            result = [t for t in result if date.strip() in t.date]
        if category:
            result = [t for t in result if t.category.strip().lower() == category.strip().lower()]
        return result

    def get_chart_data(self) -> dict:
        """Данные для Chart.js: расходы по категориям."""
        expense_by_cat: dict[str, float] = {}
        for t in self.transactions:
            if t.type == "expense":
                expense_by_cat[t.category] = expense_by_cat.get(t.category, 0) + t.amount
        return expense_by_cat

    def export_text(self) -> str:
        balance = self.get_balance()
        lines = [
            "ФИНАНСОВЫЙ ОТЧЕТ",
            "=" * 85,
            f"Текущий баланс: {balance:>10.2f}",
            "=" * 85,
            f"{'ID':<4} | {'Дата':<12} | {'Тип':<10} | {'Категория':<20} | {'Сумма':<12} | Описание",
            "-" * 85,
        ]
        for t in self.transactions:
            type_label = "Доход" if t.type == "income" else "Расход"
            lines.append(
                f"{t.id:<4} | {t.date:<12} | {type_label:<10} | "
                f"{t.category:<20} | {t.amount:<12.2f} | {t.description}"
            )
        return "\n".join(lines)

    def _sync(self):
        self.storage.save(self.filename, [t.to_dict() for t in self.transactions])
