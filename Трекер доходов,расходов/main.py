import os
from src.storage import JsonStorage
from src.services import FinanceService
from src.cli import ConsoleUI

def load_config():
    return {"status": "ok"}

def main(test_mode=False, filename=None):
    print("[START] Программа запущена")
    
    # Гарантируем наличие папки data
    db_dir = "data"
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    if not filename:
        user_input = input("Введите имя файла БД (напр. finance.json): ") or "finance.json"
        # Сохраняем файлы БД строго в папку data/
        filename = os.path.join(db_dir, user_input)
    
    storage = JsonStorage()
    service = FinanceService(storage, filename)
    ui = ConsoleUI(service)

    if not test_mode:
        ui.run()
    
    print("[DONE] Выполнение завершено")
    return 0

if __name__ == "__main__":
    main()