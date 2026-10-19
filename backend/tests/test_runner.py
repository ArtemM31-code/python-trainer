"""Unit tests for code runner and test validation engine."""

import pytest
from backend.app.runner import execute_code, run_tests


def test_execute_code_success():
    code = "print('Hello, world!')\nprint(10 + 20)"
    res = execute_code(code, timeout=3.0)
    assert res.success is True
    assert res.exit_code == 0
    assert "Hello, world!" in res.stdout
    assert "30" in res.stdout
    assert res.stderr == ""
    assert res.execution_time_ms > 0


def test_execute_code_syntax_error():
    code = "def broken(\nprint('bad syntax')"
    res = execute_code(code, timeout=3.0)
    assert res.success is False
    assert res.exit_code != 0
    assert "SyntaxError" in res.stderr


def test_execute_code_cyrillic():
    code = "print('Привет, мир!')"
    res = execute_code(code, timeout=3.0)
    assert res.success is True
    assert "Привет, мир!" in res.stdout


def test_execute_code_timeout():
    code = "while True:\n    pass"
    res = execute_code(code, timeout=1.0)
    assert res.success is False
    assert res.exit_code == -1
    assert "Превышено максимальное время" in res.stderr


def test_run_tests_functions_success():
    user_code = (
        "def greet(name: str) -> str:\n"
        "    return f'Привет, {name}!'"
    )
    test_cases = [
        {"name": "greet('Алексей')", "call": "greet('Алексей')", "expected": "Привет, Алексей!"},
        {"name": "greet('Мир')", "call": "greet('Мир')", "expected": "Привет, Мир!"},
    ]
    res = run_tests(user_code, test_cases, timeout=3.0)
    assert res.passed is True
    assert res.score == 100
    assert res.total_tests == 2
    assert res.passed_tests == 2
    assert len(res.test_results) == 2
    assert res.test_results[0].passed is True
    assert res.test_results[0].actual == "Привет, Алексей!"
    assert res.test_results[1].passed is True


def test_run_tests_functions_failure():
    user_code = (
        "def add(a, b):\n"
        "    return a - b"
    )
    test_cases = [
        {"name": "add(2, 3)", "call": "add(2, 3)", "expected": 5},
        {"name": "add(10, 20)", "call": "add(10, 20)", "expected": 30},
    ]
    res = run_tests(user_code, test_cases, timeout=3.0)
    assert res.passed is False
    assert res.score == 0
    assert res.total_tests == 2
    assert res.passed_tests == 0
    assert res.test_results[0].passed is False
    assert res.test_results[0].actual == -1


def test_run_tests_runtime_exception():
    user_code = (
        "def divide(a, b):\n"
        "    return a / b"
    )
    test_cases = [
        {"name": "divide(10, 0)", "call": "divide(10, 0)", "expected": 0},
    ]
    res = run_tests(user_code, test_cases, timeout=3.0)
    assert res.passed is False
    assert res.score == 0
    assert "ZeroDivisionError" in res.test_results[0].message


def test_run_tests_console_io():
    user_code = (
        "name = input()\n"
        "print(f'Привет, {name}!')"
    )
    test_cases = [
        {"name": "Имя Анна", "inputs": ["Анна"], "expected_output": "Привет, Анна!"},
        {"name": "Имя Иван", "inputs": ["Иван"], "expected_output": "Привет, Иван!"},
    ]
    res = run_tests(user_code, test_cases, timeout=3.0)
    assert res.passed is True
    assert res.score == 100
    assert res.total_tests == 2
    assert res.passed_tests == 2


def test_run_tests_assertion_code():
    user_code = (
        "class Counter:\n"
        "    def __init__(self):\n"
        "        self.count = 0\n"
        "    def increment(self):\n"
        "        self.count += 1\n"
    )
    test_cases = [
        {
            "name": "Проверка счетчика",
            "test_code": "c = Counter()\nassert c.count == 0\nc.increment()\nassert c.count == 1",
            "expected": "Успешное выполнение",
        }
    ]
    res = run_tests(user_code, test_cases, timeout=3.0)
    assert res.passed is True
    assert res.score == 100
    assert res.passed_tests == 1


def test_run_tests_timeout():
    user_code = (
        "def endless():\n"
        "    while True:\n"
        "        pass\n"
    )
    test_cases = [
        {"name": "Бесконечный цикл", "call": "endless()", "expected": 1},
    ]
    res = run_tests(user_code, test_cases, timeout=1.0)
    assert res.passed is False
    assert res.score == 0
    assert "Превышено максимальное время" in res.stderr
