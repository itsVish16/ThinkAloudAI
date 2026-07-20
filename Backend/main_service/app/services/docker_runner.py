import json
import os
import time
import re
from e2b_code_interpreter import Sandbox
from app.config import settings

def parse_traceback(tb_str: str) -> str:
    """Subtracts line offset from python traceback."""
    if not tb_str:
        return ""
    def replace_line(match):
        line_num = int(match.group(1))
        return f"line {max(1, line_num - 5)}"
    return re.sub(r'line (\d+)', replace_line, tb_str)

def parse_cpp_error(err_msg: str, test_harness: str) -> str:
    """Subtracts the dynamic offset from main.cpp line numbers."""
    if not err_msg or not test_harness:
        return err_msg
    offset = test_harness.split("// USER_CODE_START")[0].count("\n") + 1
    def replace_cpp_line(match):
        line_num = int(match.group(1))
        return f"/home/user/main.cpp:{max(1, line_num - offset)}"
    return re.sub(r'/home/user/main.cpp:(\d+)', replace_cpp_line, err_msg)

def compare(actual, expected, mode):
    if mode == "exact":
        return actual == expected
    if mode == "unordered":
        if isinstance(actual, list) and isinstance(expected, list):
            return sorted(actual) == sorted(expected)
        return False
    if mode == "float_tolerance":
        try:
            return abs(float(actual) - float(expected)) < 1e-6
        except:
            return False
    if mode == "any_of":
        return actual in expected
    return actual == expected

def run_code_in_docker(code: str, function_name: str, test_cases_json: str, language: str = "python", test_harness: str = None) -> dict:
    if language not in ["python", "cpp"]:
        return {
            "status": "Unsupported Language",
            "passed_tests": 0,
            "total_tests": 0,
            "error_message": f"Language {language} is not supported.",
            "execution_time_ms": 0.0
        }

    try:
        schema = json.loads(test_cases_json)
        test_cases = schema.get("cases", [])
        comparison_mode = schema.get("comparison", "exact")
    except json.JSONDecodeError:
        return {
            "status": "Configuration Error",
            "passed_tests": 0,
            "total_tests": 0,
            "error_message": "Invalid test cases format in database.",
            "execution_time_ms": 0.0
        }

    total_tests = len(test_cases)
    runner_script = ""
    cmd = ""
    filename = ""

    if language == "python":
        runner_script = f"""
import json
import time
import sys
import traceback

# User code
{code}

test_cases = {json.dumps(test_cases)}
function_name = "{function_name}"

solution_instance = None
if 'Solution' in locals():
    solution_instance = locals()['Solution']()

results = []
start_time = time.perf_counter()

for tc in test_cases:
    try:
        kwargs = tc.get('args', {{}})
        if solution_instance and hasattr(solution_instance, function_name):
            func = getattr(solution_instance, function_name)
        elif function_name in locals():
            func = locals()[function_name]
        else:
            results.append({{"output": None, "error": f"Function '{{function_name}}' not found."}})
            continue
            
        result = func(**kwargs)
        results.append({{"output": result, "error": None}})
    except Exception as e:
        results.append({{"output": None, "error": traceback.format_exc()}})

execution_time_ms = (time.perf_counter() - start_time) * 1000
print(json.dumps({{"results": results, "time_ms": execution_time_ms}}))
"""
        filename = "/home/user/runner.py"
        cmd = "python3 /home/user/runner.py"

    elif language == "cpp":
        if not test_harness:
            return {
                "status": "Runtime Error",
                "passed_tests": 0,
                "total_tests": total_tests,
                "error_message": "C++ test harness not found for this question.",
                "execution_time_ms": 0.0
            }
            
        cpp_headers = """#include <iostream>
#include <vector>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <map>
#include <set>
#include <queue>
#include <stack>
#include <algorithm>
#include <cmath>
#include <sstream>
"""
        cpp_code = cpp_headers + "\n" + test_harness.replace("// USER_CODE_START\n// USER_CODE_END", code).replace("{{user_code}}", code)
        
        runner_script = f"""
import json
import subprocess
import time
import sys

def log(msg):
    with open('/home/user/progress.log', 'a') as f:
        f.write(msg + '\\n')

log("Compiling")
compile_proc = subprocess.run(["g++", "/home/user/main.cpp", "-o", "/home/user/sol"], capture_output=True, text=True)
if compile_proc.returncode != 0:
    print(json.dumps({{"compile_error": compile_proc.stderr}}))
    sys.exit(0)

log("Compile success")
test_cases = {json.dumps(test_cases)}
results = []
start_time = time.perf_counter()

for tc in test_cases:
    stdin_data = ""
    for param_name, param_val in tc.get('args', {{}}).items():
        if isinstance(param_val, list):
            stdin_data += "[" + ",".join(map(str, param_val)) + "]\\n"
        elif isinstance(param_val, bool):
            stdin_data += ("true" if param_val else "false") + "\\n"
        else:
            stdin_data += str(param_val) + "\\n"
            
    try:
        proc = subprocess.run(["/home/user/sol"], input=stdin_data, capture_output=True, text=True, timeout=2)
        if proc.returncode != 0:
            results.append({{"output": None, "error": f"Exit code {{proc.returncode}}. Stderr: {{proc.stderr}}"}})
        else:
            out = proc.stdout.strip()
            try:
                if out == "true": parsed_out = True
                elif out == "false": parsed_out = False
                else: parsed_out = json.loads(out)
            except Exception:
                parsed_out = out
            results.append({{"output": parsed_out, "error": None}})
            
    except subprocess.TimeoutExpired:
        results.append({{"output": None, "error": "Time Limit Exceeded"}})

execution_time_ms = (time.perf_counter() - start_time) * 1000
print(json.dumps({{"results": results, "time_ms": execution_time_ms}}))
"""
        filename = "/home/user/runner.py"
        cmd = "python3 /home/user/runner.py"

    try:
        os.environ["E2B_API_KEY"] = settings.E2B_API_KEY
        with Sandbox.create() as sandbox:
            sandbox.files.write(filename, runner_script)
            if language == "cpp":
                sandbox.files.write("/home/user/main.cpp", cpp_code)
            
            try:
                execution = sandbox.commands.run(cmd, timeout=30)
                exit_code = execution.exit_code
                error = execution.error
                stdout = execution.stdout
                stderr = execution.stderr
                is_timeout = False
            except Exception as e:
                if hasattr(e, "exit_code"):
                    exit_code = e.exit_code
                    error = True
                    is_timeout = False
                    stdout = getattr(e, "stdout", "")
                    stderr = getattr(e, "stderr", "")
                elif "TimeoutException" in repr(e) or "timeout" in str(e).lower():
                    print("TIMEOUT EXCEPTION CAUGHT:", repr(e))
                    exit_code = 1
                    error = True
                    is_timeout = True
                    stdout = ""
                    stderr = ""
                else:
                    return {
                        "status": "Sandbox Error",
                        "passed_tests": 0,
                        "total_tests": total_tests,
                        "error_message": str(e),
                        "execution_time_ms": 0.0
                    }
                    
            if is_timeout:
                return {
                    "status": "Time Limit Exceeded",
                    "passed_tests": 0,
                    "total_tests": total_tests,
                    "error_message": "Code execution exceeded 30 seconds limit.",
                    "execution_time_ms": 30000.0
                }

            # Parse Orchestrator JSON
            out_data = None
            stdout_lines = stdout.strip().split("\n")
            for line in reversed(stdout_lines):
                line = line.strip()
                if line.startswith("{"):
                    try:
                        out_data = json.loads(line)
                        break
                    except json.JSONDecodeError:
                        pass
                        
            if not out_data:
                # Fallback if print statement failed
                err_msg = stderr.strip() or stdout.strip()
                if language == "cpp":
                    err_msg = parse_cpp_error(err_msg, cpp_code)
                return {
                    "status": "Runtime Error" if exit_code != 0 else "Sandbox Error",
                    "passed_tests": 0,
                    "total_tests": total_tests,
                    "error_message": err_msg or "Failed to parse test results from sandbox.",
                    "execution_time_ms": 0.0
                }
                
            if "compile_error" in out_data:
                return {
                    "status": "Compilation Error",
                    "passed_tests": 0,
                    "total_tests": total_tests,
                    "error_message": parse_cpp_error(out_data["compile_error"], cpp_code),
                    "execution_time_ms": 0.0
                }
                
            results = out_data.get("results", [])
            time_ms = out_data.get("time_ms", 0.0)
            
            passed = 0
            first_error = None
            
            for i, res in enumerate(results):
                tc = test_cases[i]
                if res.get("error"):
                    if not first_error:
                        if "Time Limit" in res["error"]:
                            first_error = f"Test {{i+1}} failed: {{res['error']}}"
                        elif language == "python":
                            first_error = parse_traceback(res["error"])
                        else:
                            first_error = f"Test {{i+1}} failed: {{res['error']}}"
                    continue
                    
                actual = res.get("output")
                expected = tc.get("expected")
                
                if compare(actual, expected, comparison_mode):
                    passed += 1
                else:
                    if not first_error:
                        first_error = f"Test {{i+1}} failed.\\nInput: {{tc.get('args')}}\\nExpected: {{expected}}\\nGot: {{actual}}"
                        
            status = "Accepted" if passed == total_tests else "Wrong Answer"
            if passed < total_tests and first_error and ("Exit code" in first_error or "Traceback" in first_error):
                status = "Runtime Error"
            if passed < total_tests and first_error and "Time Limit" in first_error:
                status = "Time Limit Exceeded"
                
            return {
                "status": status,
                "passed_tests": passed,
                "total_tests": total_tests,
                "error_message": first_error,
                "execution_time_ms": time_ms
            }

    except Exception as e:
        return {
            "status": "System Error",
            "passed_tests": 0,
            "total_tests": total_tests,
            "error_message": str(e),
            "execution_time_ms": 0.0
        }
