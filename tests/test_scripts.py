import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import main, load_config

def test_load_config_returns_dict():
    result = load_config()
    assert isinstance(result, dict)
    assert "status" in result

def test_main_exits_successfully(capsys):
    exit_code = main(test_mode=True)
    assert exit_code == 0
    
    captured = capsys.readouterr()
    assert "🟢 Программа запущена" in captured.out
    assert "✅ Выполнение завершено" in captured.out