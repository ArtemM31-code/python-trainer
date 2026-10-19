"""Reference solutions for all Python Trainer educational tasks.
Used by test_integration.py to verify that all test suites are solvable and accurate.
"""

REFERENCE_SOLUTIONS = {
    # 01 Basics
    "basics-01-format-greeting": """
def format_greeting(name: str, age: int) -> str:
    cleaned = name.strip().capitalize()
    return f"Привет, {cleaned}! Тебе {age} лет."
""",

    "basics-02-temperature-converter": """
def convert_celsius(celsius: float) -> tuple[float, float]:
    f = round(celsius * 9 / 5 + 32, 2)
    k = round(celsius + 273.15, 2)
    return (f, k)
""",

    "basics-03-palindrome-slice": """
def is_palindrome(text: str) -> bool:
    clean = "".join(ch.lower() for ch in text if ch.isalnum())
    return clean == clean[::-1]
""",

    "basics-04-card-masking": """
def mask_card_number(card: str) -> str:
    digits = card.replace(" ", "").replace("-", "")
    if len(digits) != 16 or not digits.isdigit():
        return "Invalid Card"
    return f"{digits[:4]}-****-****-{digits[-4:]}"
""",

    # 02 Data Structures
    "ds-01-even-squares": """
def get_even_squares(numbers: list[int]) -> list[int]:
    return [x ** 2 for x in numbers if x % 2 == 0]
""",

    "ds-02-word-frequencies": """
def count_words(text: str) -> dict[str, int]:
    cleaned = text.lower()
    for p in ",.!?;:":
        cleaned = cleaned.replace(p, " ")
    words = cleaned.split()
    counts = {}
    for w in words:
        counts[w] = counts.get(w, 0) + 1
    return counts
""",

    "ds-03-set-operations": """
def analyze_tags(tags_a: list[str], tags_b: list[str]) -> dict[str, set[str]]:
    sa = {t.lower() for t in tags_a}
    sb = {t.lower() for t in tags_b}
    return {
        "common": sa & sb,
        "only_a": sa - sb,
        "only_b": sb - sa,
    }
""",

    "ds-04-aggregate-inventory": """
def aggregate_inventory(batches: list[dict[str, int]]) -> dict[str, int]:
    totals = {}
    for batch in batches:
        for item, qty in batch.items():
            totals[item] = totals.get(item, 0) + qty
    return {k: totals[k] for k in sorted(totals) if totals[k] > 0}
""",

    # 03 Functions
    "func-01-power": """
def power(base: float, exponent: int = 2) -> float:
    return float(base ** exponent)
""",

    "func-02-clamp-docstring": '''
def clamp(value: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
    """Clamps a numeric value between min_val and max_val."""
    if min_val > max_val:
        min_val, max_val = max_val, min_val
    return float(max(min_val, min(value, max_val)))
''',

    "func-03-pipeline-first-class": """
from typing import Callable

def apply_pipeline(initial_value: float, functions: list[Callable[[float], float]]) -> float:
    current = initial_value
    for fn in functions:
        current = fn(current)
    return current
""",

    "func-04-flatten-recursion": """
def deep_flatten(nested_list: list) -> list:
    flat = []
    for item in nested_list:
        if isinstance(item, list):
            flat.extend(deep_flatten(item))
        else:
            flat.append(item)
    return flat
""",

    # 04 Args & Kwargs
    "args-01-multiply-all": """
def multiply_all(*args: int | float) -> float:
    prod = 1.0
    for num in args:
        prod *= num
    return float(prod)
""",

    "args-02-html-tag-builder": """
def build_html_tag(tag: str, content: str = "", **attributes) -> str:
    if attributes:
        attrs_str = " " + " ".join(f'{k}="{v}"' for k, v in sorted(attributes.items()))
    else:
        attrs_str = ""
    return f"<{tag}{attrs_str}>{content}</{tag}>"
""",

    "args-03-forwarding-wrapper": """
from typing import Callable, Any

def call_with_log(target_func: Callable, *args, **kwargs) -> dict[str, Any]:
    res = target_func(*args, **kwargs)
    return {
        "args": args,
        "kwargs": kwargs,
        "result": res,
    }
""",

    "args-04-merge-configs": """
def merge_configs(defaults: dict, *overrides: dict, **kwargs) -> dict:
    config = dict(defaults)
    for ovr in overrides:
        config.update(ovr)
    config.update(kwargs)
    return config
""",

    # 05 Closures & LEGB
    "scope-01-make-multiplier": """
from typing import Callable

def make_multiplier(factor: float) -> Callable[[float], float]:
    def multiplier(x: float) -> float:
        return x * factor
    return multiplier
""",

    "scope-02-stateful-counter": """
from typing import Callable

def make_counter(start: int = 0, step: int = 1) -> Callable[[], int]:
    current = start
    def counter() -> int:
        nonlocal current
        val = current
        current += step
        return val
    return counter
""",

    "scope-03-running-average": """
from typing import Callable

def make_averager() -> Callable[[float], float]:
    total = 0.0
    count = 0
    def averager(val: float) -> float:
        nonlocal total, count
        total += val
        count += 1
        return total / count
    return averager
""",

    "scope-04-memoize-cache": """
from typing import Callable

def memoize(func: Callable) -> Callable:
    cache = {}
    hits = 0
    misses = 0

    def wrapper(*args):
        nonlocal hits, misses
        if args in cache:
            hits += 1
            return cache[args]
        misses += 1
        result = func(*args)
        cache[args] = result
        return result

    def cache_info():
        return {"hits": hits, "misses": misses, "size": len(cache)}

    wrapper.cache_info = cache_info
    return wrapper
""",

    # 06 Decorators
    "dec-01-call-counter": """
import functools

def count_calls(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        wrapper.calls += 1
        return func(*args, **kwargs)
    wrapper.calls = 0
    return wrapper
""",

    "dec-02-api-envelope": """
import functools

def api_response(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            data = func(*args, **kwargs)
            return {"status": "success", "function": func.__name__, "data": data}
        except Exception as e:
            return {"status": "error", "function": func.__name__, "error": str(e)}
    return wrapper
""",

    "dec-03-repeat-decorator": """
import functools

def repeat(num_times: int = 1):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if num_times <= 0:
                return None
            res = None
            for _ in range(num_times):
                res = func(*args, **kwargs)
            return res
        return wrapper
    return decorator
""",

    "dec-04-type-enforcer": """
import functools
import inspect

def enforce_types(func):
    sig = inspect.signature(func)
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        for name, val in bound.arguments.items():
            expected = func.__annotations__.get(name)
            if expected is not None and not isinstance(val, expected):
                raise TypeError(f"Argument '{name}' must be of type {expected.__name__}, got {type(val).__name__}")
        res = func(*args, **kwargs)
        ret_type = func.__annotations__.get("return")
        if ret_type is not None and not isinstance(res, ret_type):
            raise TypeError(f"Return value must be of type {ret_type.__name__}, got {type(res).__name__}")
        return res
    return wrapper
""",

    # 07 Exceptions
    "exc-01-safe-converter": """
def safe_int(val, default: int = 0) -> int:
    try:
        return int(val)
    except (ValueError, TypeError):
        return default
""",

    "exc-02-dict-lookup": """
def deep_get(data: dict, keys_path: str, default=None):
    current = data
    for key in keys_path.split("."):
        try:
            current = current[key]
        except (KeyError, TypeError):
            return default
    return current
""",

    "exc-03-custom-exception": """
class InvalidPasswordError(Exception):
    pass

def validate_password(password: str) -> bool:
    if len(password) < 8:
        raise InvalidPasswordError("Пароль должен содержать не менее 8 символов")
    if not any(c.isupper() for c in password):
        raise InvalidPasswordError("Пароль должен содержать хотя бы одну заглавную букву")
    if not any(c.islower() for c in password):
        raise InvalidPasswordError("Пароль должен содержать хотя бы одну строчную букву")
    if not any(c.isdigit() for c in password):
        raise InvalidPasswordError("Пароль должен содержать хотя бы одну цифру")
    return True
""",

    "exc-04-retry-handler": """
from typing import Callable, Any

def retry_operation(func: Callable, max_attempts: int = 3, default=None) -> tuple[Any, dict]:
    attempts = 0
    success = False
    last_error = None
    res = default
    for attempt in range(1, max_attempts + 1):
        attempts = attempt
        try:
            res = func()
        except Exception as e:
            last_error = str(e)
        else:
            success = True
            last_error = None
            break
    return (res, {"attempts": attempts, "success": success, "last_error": last_error})
""",

    # 08 OOP
    "oop-01-bank-account": """
class BankAccount:
    def __init__(self, owner: str, balance: float = 0.0):
        if balance < 0:
            raise ValueError("Начальный баланс не может быть отрицательным")
        self.owner = owner
        self._balance = float(balance)

    def deposit(self, amount: float) -> float:
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть больше нуля")
        self._balance += amount
        return self._balance

    def withdraw(self, amount: float) -> float:
        if amount <= 0 or amount > self._balance:
            raise ValueError("Некорректная сумма списания или недостаточно средств")
        self._balance -= amount
        return self._balance

    def get_balance(self) -> float:
        return self._balance
""",

    "oop-02-rectangle-properties": """
class Rectangle:
    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height

    @property
    def width(self) -> float:
        return self._width

    @width.setter
    def width(self, value: float):
        if value <= 0:
            raise ValueError("Ширина должна быть положительной")
        self._width = float(value)

    @property
    def height(self) -> float:
        return self._height

    @height.setter
    def height(self, value: float):
        if value <= 0:
            raise ValueError("Высота должна быть положительной")
        self._height = float(value)

    @property
    def area(self) -> float:
        return self._width * self._height

    @property
    def perimeter(self) -> float:
        return 2 * (self._width + self._height)

    @property
    def is_square(self) -> bool:
        return self._width == self._height
""",

    "oop-03-inheritance-hierarchy": """
class Employee:
    def __init__(self, name: str, base_salary: float):
        self.name = name
        self.base_salary = float(base_salary)

    def calculate_pay(self) -> float:
        return self.base_salary

class Manager(Employee):
    def __init__(self, name: str, base_salary: float, bonus: float):
        super().__init__(name, base_salary)
        self.bonus = float(bonus)

    def calculate_pay(self) -> float:
        return self.base_salary + self.bonus

class Developer(Employee):
    def __init__(self, name: str, base_salary: float, completed_tasks: int, task_rate: float = 100.0):
        super().__init__(name, base_salary)
        self.completed_tasks = completed_tasks
        self.task_rate = float(task_rate)

    def calculate_pay(self) -> float:
        return self.base_salary + (self.completed_tasks * self.task_rate)

def total_payroll(employees: list[Employee]) -> float:
    return float(sum(emp.calculate_pay() for emp in employees))
""",

    "oop-04-vector-magic": """
import math

class Vector2D:
    def __init__(self, x: float, y: float):
        self.x = float(x)
        self.y = float(y)

    def __repr__(self) -> str:
        return f"Vector2D({self.x}, {self.y})"

    def __add__(self, other: "Vector2D") -> "Vector2D":
        if not isinstance(other, Vector2D):
            return NotImplemented
        return Vector2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vector2D") -> "Vector2D":
        if not isinstance(other, Vector2D):
            return NotImplemented
        return Vector2D(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "Vector2D":
        if not isinstance(scalar, (int, float)):
            return NotImplemented
        return Vector2D(self.x * scalar, self.y * scalar)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Vector2D):
            return False
        return self.x == other.x and self.y == other.y

    def __abs__(self) -> float:
        return math.hypot(self.x, self.y)
""",
}
