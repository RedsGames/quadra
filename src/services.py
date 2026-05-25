from src.models import Transaction

class FinanceService:
    def __init__(self, storage, filename):
        self.storage = storage
        self.filename = filename
        self.transactions = [Transaction(**t) for t in self.storage.load(filename)]

    def add_transaction(self, t_type, category, amount, date, description):
        new_id = max([t.id for t in self.transactions], default=0) + 1
        new_t = Transaction(new_id, t_type, category, amount, date, description)
        self.transactions.append(new_t)
        self._sync()

    def delete_transaction(self, t_id):
        initial_len = len(self.transactions)
        self.transactions = [t for t in self.transactions if t.id != t_id]
        self._sync()
        return len(self.transactions) != initial_len

    def get_balance(self):
        incomes = sum(t.amount for t in self.transactions if t.type == 'income')
        expenses = sum(t.amount for t in self.transactions if t.type == 'expense')
        return incomes - expenses

    def filter_transactions(self, date=None, category=None):
        result = self.transactions
        if date:
            # Поиск по подстроке позволяет искать по году (2024) или месяцу (2024-05)
            target_date = date.strip()
            result = [t for t in result if target_date in t.date]
        if category:
            target_cat = category.strip().lower()
            result = [t for t in result if t.category.strip().lower() == target_cat]
        return result

    def export_summary(self, export_path):
        balance = self.get_balance()
        # Использование utf-8-sig гарантирует корректное чтение кириллицы в Windows Блокноте
        with open(export_path, 'w', encoding='utf-8-sig') as f:
            f.write(f"ФИНАНСОВЫЙ ОТЧЕТ\n")
            f.write(f"{'='*85}\n")
            f.write(f"Текущий баланс: {balance:>10.2f}\n")
            f.write(f"{'='*85}\n\n")
            
            # Формирование заголовков таблицы с фиксированной шириной
            header = f"{'ID':<4} | {'Дата':<12} | {'Тип':<10} | {'Категория':<20} | {'Сумма':<12} | {'Описание'}"
            f.write(header + "\n")
            f.write("-" * 85 + "\n")
            
            for t in self.transactions:
                t_type_display = "Доход" if t.type == "income" else "Расход"
                line = (f"{t.id:<4} | {t.date:<12} | {t_type_display:<10} | "
                        f"{t.category:<20} | {t.amount:<12.2f} | {t.description}")
                f.write(line + "\n")

    def _sync(self):
        self.storage.save(self.filename, [t.to_dict() for t in self.transactions])