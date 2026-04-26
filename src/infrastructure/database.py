import sqlite3
import sys
import os
from typing import List, Tuple
from datetime import date
from src.domain.interfaces import ITransactionRepository
from src.domain.types import Transaction, TransactionType, TransactionFilter

def _get_data_dir():
    """Return a writable directory for user data (database)."""
    if getattr(sys, 'frozen', False):
        app_data = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
        data_dir = os.path.join(app_data, 'PersonalBudgetDashboard')
        os.makedirs(data_dir, exist_ok=True)
        return data_dir
    return os.getcwd()

class SqliteTransactionRepo(ITransactionRepository):
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(_get_data_dir(), "finance.db")
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    date_added TEXT NOT NULL,
                    type TEXT NOT NULL,
                    description TEXT
                )
            """)
            conn.execute("CREATE TABLE IF NOT EXISTS categories (name TEXT PRIMARY KEY)")
            
            # Default categories
            defaults = ["Еда", "Транспорт", "Жильё", "Развлечения", "Зарплата", "Прочее"]
            for cat in defaults:
                try:
                    conn.execute("INSERT INTO categories (name) VALUES (?)", (cat,))
                except sqlite3.IntegrityError:
                    pass

    def add(self, t: Transaction) -> None:
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO transactions (amount, category, date_added, type, description) VALUES (?, ?, ?, ?, ?)",
                (t.amount, t.category, t.date_added.isoformat(), t.type.value, t.description)
            )

    def update(self, t: Transaction) -> None:
        if t.id is None: return
        with self._get_conn() as conn:
            conn.execute(
                """UPDATE transactions 
                   SET amount=?, category=?, date_added=?, type=?, description=? 
                   WHERE id=?""",
                (t.amount, t.category, t.date_added.isoformat(), t.type.value, t.description, t.id)
            )

    def delete(self, t_id: int) -> None:
        with self._get_conn() as conn:
            conn.execute("DELETE FROM transactions WHERE id=?", (t_id,))

    def get_filtered(self, filters: TransactionFilter) -> List[Transaction]:
        query = "SELECT id, amount, category, date_added, type, description FROM transactions WHERE 1=1"
        params = []

        if filters.date_from:
            query += " AND date_added >= ?"
            params.append(filters.date_from.isoformat())
        if filters.date_to:
            query += " AND date_added <= ?"
            params.append(filters.date_to.isoformat())
        if filters.category and filters.category != "Все":
            query += " AND category = ?"
            params.append(filters.category)
        if filters.type:
            query += " AND type = ?"
            params.append(filters.type.value)

        query += " ORDER BY date_added DESC"

        with self._get_conn() as conn:
            cursor = conn.execute(query, params)
            return [self._map_row(row) for row in cursor.fetchall()]

    def get_categories(self) -> List[str]:
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT name FROM categories ORDER BY name")
            return [row[0] for row in cursor.fetchall()]

    def get_categories_by_type(self, tx_type: TransactionType) -> List[str]:
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT DISTINCT category FROM transactions WHERE type=? ORDER BY category",
                (tx_type.value,)
            )
            return [row[0] for row in cursor.fetchall()]
            
    def add_category(self, name: str) -> None:
        with self._get_conn() as conn:
            try:
                conn.execute("INSERT INTO categories (name) VALUES (?)", (name,))
            except sqlite3.IntegrityError:
                pass

    def _map_row(self, row: Tuple) -> Transaction:
        return Transaction(
            id=row[0],
            amount=row[1],
            category=row[2],
            date_added=date.fromisoformat(row[3]),
            type=TransactionType(row[4]),
            description=row[5]
        )