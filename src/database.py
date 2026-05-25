import sqlite3
from typing import List
from src.models import Transaction

class SQLiteRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    amount REAL NOT NULL,
                    date TEXT NOT NULL,
                    description TEXT
                )
            """)

    def add_transaction(self, t: Transaction) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO transactions (type, category, amount, date, description) VALUES (?, ?, ?, ?, ?)",
                (t.type, t.category, t.amount, t.date, t.description)
            )

    def get_all(self) -> List[Transaction]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT id, type, category, amount, date, description FROM transactions")
            return [Transaction(id=r[0], type=r[1], category=r[2], amount=r[3], date=r[4], description=r[5]) for r in cursor.fetchall()]

    def get_by_period(self, year: int, month: int) -> List[Transaction]:
        period = f"{year}-{month:02d}%"
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id, type, category, amount, date, description FROM transactions WHERE date LIKE ?",
                (period,)
            )
            return [Transaction(id=r[0], type=r[1], category=r[2], amount=r[3], date=r[4], description=r[5]) for r in cursor.fetchall()]

    def delete_by_id(self, transaction_id: int) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
            return cursor.rowcount > 0