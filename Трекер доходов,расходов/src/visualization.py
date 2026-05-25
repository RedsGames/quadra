import matplotlib.pyplot as plt
import os
from typing import List
from src.models import Transaction

class ChartGenerator:
    def generate_expense_pie_chart(self, transactions: List[Transaction], output_path: str) -> None:
        expenses = [t for t in transactions if t.type == 'expense']
        if not expenses:
            return

        data = {}
        for t in expenses:
            data[t.category] = data.get(t.category, 0) + t.amount

        plt.figure(figsize=(10, 7))
        plt.pie(data.values(), labels=data.keys(), autopct='%1.1f%%')
        plt.title("Expenses by Category")
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path)
        plt.close()