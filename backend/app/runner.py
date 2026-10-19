"""Subprocess-based safe code execution engine and automated unit tester."""

import base64
import json
import os
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from backend.app.config import DEFAULT_TIMEOUT_SECONDS, MAX_OUTPUT_LENGTH


class ExecutionResult(BaseModel):
    """Result of running arbitrary user Python code."""
    success: bool
    stdout: str
    stderr: str
    execution_time_ms: float
    exit_code: int


class TestCaseResult(BaseModel):
    """Result of an individual test case."""
    test_name: str
    passed: bool
    expected: Any = None
    actual: Any = None
    message: str = ""


class TestSuiteResult(BaseModel):
    """Aggregated test suite results for a task submission."""
    passed: bool
    score: int
    total_tests: int
    passed_tests: int
    test_results: List[TestCaseResult] = Field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    all_completed: bool = False


# Template for the isolated test evaluation harness
TEST_HARNESS_TEMPLATE = """# -*- coding: utf-8 -*-
import sys
import io
import json
import math
import base64
import traceback

def safe_serialize(val):
    if val is None:
        return None
    if isinstance(val, (bool, int, float, str, list, dict)):
        try:
            json.dumps(val)
            return val
        except Exception:
            return repr(val)
    return repr(val)

def run_suite():
    user_code_raw = base64.b64decode({user_code_b64}).decode("utf-8")
    test_cases = json.loads(base64.b64decode({test_cases_b64}).decode("utf-8"))

    results = []
    global_stdout_io = io.StringIO()
    global_stderr_io = io.StringIO()

    # Compile user code first to check for syntax errors
    compiled_code = None
    compile_error = None
    try:
        compiled_code = compile(user_code_raw, "<user_code>", "exec")
    except Exception:
        compile_error = traceback.format_exc()

    if compile_error is not None:
        for tc in test_cases:
            name = tc.get("description") or tc.get("name") or tc.get("test_name") or "Тест"
            results.append({
                "test_name": name,
                "passed": False,
                "expected": safe_serialize(tc.get("expected", tc.get("expected_output"))),
                "actual": "<Синтаксическая ошибка>",
                "message": compile_error.strip(),
            })
        report = {
            "passed": False,
            "score": 0,
            "total_tests": len(test_cases),
            "passed_tests": 0,
            "test_results": results,
            "stdout": "",
            "stderr": compile_error.strip(),
        }
        print("\\n__PYTHON_TRAINER_TEST_RESULT_START__")
        print(json.dumps(report, ensure_ascii=False))
        print("__PYTHON_TRAINER_TEST_RESULT_END__")
        return

    # Prepare shared environment for function/class definitions
    shared_env = {
        "__name__": "__main__",
        "__doc__": None,
    }

    # Safe default mock input during top-level execution
    def noop_input(prompt=""):
        return ""
    shared_env["input"] = noop_input

    initial_exec_failed = False
    initial_error = None

    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = global_stdout_io
    sys.stderr = global_stderr_io

    try:
        exec(compiled_code, shared_env)
    except Exception:
        initial_exec_failed = True
        initial_error = traceback.format_exc()
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    top_stdout = global_stdout_io.getvalue()
    top_stderr = global_stderr_io.getvalue()

    for idx, tc in enumerate(test_cases):
        name = tc.get("description") or tc.get("name") or tc.get("test_name") or f"Тест #{idx + 1}"
        expected = tc.get("expected")
        expected_output = tc.get("expected_output")
        call = tc.get("call") or tc.get("expression")
        test_code = tc.get("test_code") or tc.get("code") or tc.get("assertion")
        inputs = tc.get("inputs")
        if inputs is None and "input" in tc:
            inputs = [tc["input"]] if tc["input"] is not None else []

        # If initial execution failed and this test needs defined functions/classes
        if initial_exec_failed and (call or test_code or inputs is None):
            results.append({
                "test_name": name,
                "passed": False,
                "expected": safe_serialize(expected if expected is not None else expected_output),
                "actual": "<Ошибка выполнения кода>",
                "message": initial_error.strip() if initial_error else "Ошибка при выполнении кода",
            })
            continue

        # Case A: Console I/O test with inputs or pure output test
        if inputs is not None or expected_output is not None:
            input_list = [str(x) for x in (inputs or [])]
            input_queue = list(input_list)

            def mock_input(prompt=""):
                if input_queue:
                    return input_queue.pop(0)
                return ""

            run_env = {
                "__name__": "__main__",
                "__doc__": None,
                "input": mock_input,
            }
            sub_stdout = io.StringIO()
            sub_stderr = io.StringIO()
            sys.stdout = sub_stdout
            sys.stderr = sub_stderr
            sub_error = None
            try:
                exec(compiled_code, run_env)
            except Exception:
                sub_error = traceback.format_exc()
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

            actual_out = sub_stdout.getvalue()
            actual_err = sub_stderr.getvalue()
            target_out = expected_output if expected_output is not None else expected

            passed = False
            msg = ""
            if sub_error:
                passed = False
                actual_val = f"<Ошибка: {sub_error.strip().splitlines()[-1]}>"
                msg = sub_error.strip()
            else:
                passed = (actual_out.strip() == str(target_out).strip())
                actual_val = actual_out.strip()
                if not passed:
                    msg = f"Ожидался вывод:\\n{str(target_out).strip()}\\n\\nПолучен вывод:\\n{actual_out.strip()}"

            results.append({
                "test_name": name,
                "passed": passed,
                "expected": str(target_out).strip() if target_out is not None else "",
                "actual": actual_val,
                "message": msg,
            })
            continue

        # Case B: Expression / Function Call
        if call:
            test_env = dict(shared_env)
            passed = False
            actual_val = None
            msg = ""
            try:
                actual = eval(call, test_env)
                actual_val = safe_serialize(actual)

                if expected is not None:
                    if isinstance(actual, float) and isinstance(expected, (int, float)):
                        passed = math.isclose(actual, float(expected), rel_tol=1e-6, abs_tol=1e-6)
                    else:
                        passed = (actual == expected)
                    if not passed:
                        msg = f"Ожидалось: {expected!r}, получено: {actual!r}"
                else:
                    passed = True
            except AssertionError as ae:
                passed = False
                actual_val = "<AssertionError>"
                msg = str(ae) if str(ae) else "Утверждение не выполнено"
            except Exception as e:
                passed = False
                actual_val = f"<{type(e).__name__}>"
                msg = f"{type(e).__name__}: {str(e)}"

            results.append({
                "test_name": name,
                "passed": passed,
                "expected": safe_serialize(expected),
                "actual": actual_val,
                "message": msg,
            })
            continue

        # Case C: Custom Assertion Script
        if test_code:
            test_env = dict(shared_env)
            passed = False
            actual_val = None
            msg = ""
            try:
                exec(test_code, test_env)
                passed = True
                actual_val = "Успешно"
            except AssertionError as ae:
                passed = False
                actual_val = "<AssertionError>"
                msg = str(ae) if str(ae) else "Утверждение не выполнено (AssertionError)"
            except Exception as e:
                passed = False
                actual_val = f"<{type(e).__name__}>"
                msg = f"{type(e).__name__}: {str(e)}"

            results.append({
                "test_name": name,
                "passed": passed,
                "expected": safe_serialize(expected if expected is not None else "Успешное выполнение"),
                "actual": actual_val,
                "message": msg,
            })
            continue

        # Fallback if no specific trigger
        results.append({
            "test_name": name,
            "passed": True,
            "expected": safe_serialize(expected),
            "actual": "OK",
            "message": "",
        })

    passed_count = sum(1 for t in results if t["passed"])
    total_count = len(results)
    score = int(round((passed_count / total_count) * 100)) if total_count > 0 else 100
    all_passed = (passed_count == total_count) if total_count > 0 else False

    full_stdout = top_stdout
    full_stderr = top_stderr or (initial_error or "")

    report = {
        "passed": all_passed,
        "score": score,
        "total_tests": total_count,
        "passed_tests": passed_count,
        "test_results": results,
        "stdout": full_stdout,
        "stderr": full_stderr.strip(),
    }

    print("\\n__PYTHON_TRAINER_TEST_RESULT_START__")
    print(json.dumps(report, ensure_ascii=False))
    print("__PYTHON_TRAINER_TEST_RESULT_END__")

if __name__ == "__main__":
    run_suite()
"""


def _truncate_output(text: str) -> str:
    """Safely truncate output if it exceeds maximum limit."""
    if len(text) > MAX_OUTPUT_LENGTH:
        return text[:MAX_OUTPUT_LENGTH] + "\n... [Вывод обрезан: превышен лимит символов]"
    return text


def execute_code(code: str, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> ExecutionResult:
    """
    Execute arbitrary Python code in an isolated subprocess with strict timeout.
    """
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    start_time = time.perf_counter()
    try:
        proc = subprocess.run(
            [sys.executable, "-u", "-"],
            input=code,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=timeout,
        )
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return ExecutionResult(
            success=(proc.returncode == 0),
            stdout=_truncate_output(proc.stdout),
            stderr=_truncate_output(proc.stderr),
            execution_time_ms=elapsed_ms,
            exit_code=proc.returncode,
        )
    except subprocess.TimeoutExpired:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return ExecutionResult(
            success=False,
            stdout="",
            stderr=f"Превышено максимальное время выполнения ({timeout:.1f} сек).\nВозможно, в коде присутствует бесконечный цикл.",
            execution_time_ms=elapsed_ms,
            exit_code=-1,
        )
    except Exception as e:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return ExecutionResult(
            success=False,
            stdout="",
            stderr=f"Ошибка системного запуска: {type(e).__name__}: {str(e)}",
            execution_time_ms=elapsed_ms,
            exit_code=-1,
        )


def run_tests(
    code: str,
    test_cases: List[Dict[str, Any]],
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> TestSuiteResult:
    """
    Execute user code against a suite of unit test cases in an isolated subprocess.
    """
    if not test_cases:
        # If there are no test cases, just run the code
        exec_res = execute_code(code, timeout=timeout)
        return TestSuiteResult(
            passed=exec_res.success,
            score=100 if exec_res.success else 0,
            total_tests=0,
            passed_tests=0,
            test_results=[],
            stdout=exec_res.stdout,
            stderr=exec_res.stderr,
            all_completed=False,
        )

    user_code_b64 = repr(base64.b64encode(code.encode("utf-8")).decode("ascii"))
    test_cases_b64 = repr(base64.b64encode(json.dumps(test_cases).encode("utf-8")).decode("ascii"))

    harness_code = TEST_HARNESS_TEMPLATE.replace("{user_code_b64}", user_code_b64).replace(
        "{test_cases_b64}", test_cases_b64
    )

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    try:
        proc = subprocess.run(
            [sys.executable, "-u", "-"],
            input=harness_code,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        # Create timeout results for each test
        timeout_results = [
            TestCaseResult(
                test_name=tc.get("description") or tc.get("name") or tc.get("test_name") or f"Тест #{idx + 1}",
                passed=False,
                expected=tc.get("expected", tc.get("expected_output")),
                actual="<Timeout>",
                message=f"Превышено максимальное время выполнения ({timeout:.1f} сек).",
            )
            for idx, tc in enumerate(test_cases)
        ]
        return TestSuiteResult(
            passed=False,
            score=0,
            total_tests=len(test_cases),
            passed_tests=0,
            test_results=timeout_results,
            stdout="",
            stderr=f"Превышено максимальное время выполнения ({timeout:.1f} сек).\nВозможно, в коде присутствует бесконечный цикл.",
            all_completed=False,
        )
    except Exception as e:
        return TestSuiteResult(
            passed=False,
            score=0,
            total_tests=len(test_cases),
            passed_tests=0,
            test_results=[],
            stdout="",
            stderr=f"Ошибка выполнения тестов: {type(e).__name__}: {str(e)}",
            all_completed=False,
        )

    # Extract JSON report between delimiters
    raw_output = proc.stdout
    start_tag = "__PYTHON_TRAINER_TEST_RESULT_START__"
    end_tag = "__PYTHON_TRAINER_TEST_RESULT_END__"

    start_idx = raw_output.find(start_tag)
    end_idx = raw_output.find(end_tag)

    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        json_str = raw_output[start_idx + len(start_tag):end_idx].strip()
        try:
            report_dict = json.loads(json_str)
            return TestSuiteResult(
                passed=report_dict.get("passed", False),
                score=report_dict.get("score", 0),
                total_tests=report_dict.get("total_tests", len(test_cases)),
                passed_tests=report_dict.get("passed_tests", 0),
                test_results=[
                    TestCaseResult(
                        test_name=t.get("test_name", "Тест"),
                        passed=t.get("passed", False),
                        expected=t.get("expected"),
                        actual=t.get("actual"),
                        message=t.get("message", ""),
                    )
                    for t in report_dict.get("test_results", [])
                ],
                stdout=_truncate_output(report_dict.get("stdout", "")),
                stderr=_truncate_output(report_dict.get("stderr", "") or proc.stderr),
                all_completed=False,
            )
        except json.JSONDecodeError:
            pass

    # Fallback if delimiter or json parsing failed
    err_msg = proc.stderr.strip() or proc.stdout.strip() or "Не удалось получить результат тестирования"
    failed_results = [
        TestCaseResult(
            test_name=tc.get("description") or tc.get("name") or tc.get("test_name") or f"Тест #{idx + 1}",
            passed=False,
            expected=tc.get("expected", tc.get("expected_output")),
            actual="<Крах процесса>",
            message=err_msg,
        )
        for idx, tc in enumerate(test_cases)
    ]
    return TestSuiteResult(
        passed=False,
        score=0,
        total_tests=len(test_cases),
        passed_tests=0,
        test_results=failed_results,
        stdout=_truncate_output(proc.stdout),
        stderr=_truncate_output(proc.stderr),
        all_completed=False,
    )
