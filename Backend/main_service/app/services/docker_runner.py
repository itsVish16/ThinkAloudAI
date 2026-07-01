import json
import os
import time
import re
from e2b_code_interpreter import Sandbox
from app.config import settings

def parse_traceback(tb_str: str) -> str:
    """Subtracts 6 from line numbers in runner.py traceback to match user code."""
    if not tb_str:
        return ""
    
    def replace_line(match):
        line_num = int(match.group(1))
        # Don't go below line 1 just in case
        return f"line {max(1, line_num - 6)}"
        
    return re.sub(r'line (\d+)', replace_line, tb_str)

def parse_cpp_error(err_msg: str, test_harness: str) -> str:
    """Subtracts the dynamic offset from main.cpp line numbers."""
    if not err_msg or not test_harness:
        return err_msg
        
    # Find the line number of // USER_CODE_START
    # Add 1 because we prepend `#include <bits/stdc++.h>\n` to the runner_script
    offset = test_harness.split("// USER_CODE_START")[0].count("\\n") + 1
    
    def replace_cpp_line(match):
        line_num = int(match.group(1))
        # Subtract the offset so line numbers match the user's editor
        return f"/home/user/main.cpp:{max(1, line_num - offset)}"
        
    return re.sub(r'/home/user/main.cpp:(\d+)', replace_cpp_line, err_msg)

def run_code_in_docker(code: str, function_name: str, test_cases_json: str, language: str = "python", test_harness: str = None) -> dict:
    """
    Executes user-submitted code in an E2B cloud sandbox.
    Keeps the function name 'run_code_in_docker' for backward compatibility.
    """
    if language not in ["python", "cpp"]:
        return {
            "status": "Unsupported Language",
            "passed_tests": 0,
            "total_tests": 0,
            "error_message": f"Language {language} is not supported.",
            "execution_time_ms": 0.0
        }

    test_cases = json.loads(test_cases_json)
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

test_cases_json = '''{test_cases_json}'''
test_cases = json.loads(test_cases_json)
function_name = "{function_name}"

solution_instance = None
if 'Solution' in locals():
    solution_instance = locals()['Solution']()

passed = 0
start_time = time.perf_counter()

try:
    for tc in test_cases:
        input_data = tc['input']
        expected = tc['expected']
        
        kwargs = input_data
        
        if solution_instance and hasattr(solution_instance, function_name):
            func = getattr(solution_instance, function_name)
        elif function_name in locals():
            func = locals()[function_name]
        else:
            print(json.dumps({{"error": f"Function '{{function_name}}' not found."}}))
            sys.exit(1)
            
        result = func(**kwargs)
        if result != expected:
            print(json.dumps({{"error": f"Test failed. Input: {{kwargs}}, Expected: {{expected}}, Got: {{result}}", "passed": passed}}))
            sys.exit(1)
            
        passed += 1
        
    execution_time_ms = (time.perf_counter() - start_time) * 1000
    print(json.dumps({{"success": True, "passed": passed, "time_ms": execution_time_ms}}))
    
except Exception as e:
    print(json.dumps({{"error": str(e), "traceback": traceback.format_exc(), "passed": passed}}))
    sys.exit(1)
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
            
        # Inject all standard C++ libraries to prevent "unordered_map not declared" errors
        runner_script = "#include <bits/stdc++.h>\n" + test_harness.replace("// USER_CODE_START\n// USER_CODE_END", code)
        filename = "/home/user/main.cpp"
        cmd = "g++ -O2 /home/user/main.cpp -o /home/user/sol && /home/user/sol"

    try:
        # E2B SDK reads E2B_API_KEY from the environment
        os.environ["E2B_API_KEY"] = settings.E2B_API_KEY
        
        # Start the E2B Sandbox
        with Sandbox.create() as sandbox:
            sandbox.files.write(filename, runner_script)
            
            execution = sandbox.commands.run(cmd, timeout=15)
            
            err_msg = execution.stderr.strip() or execution.stdout.strip()
            
            if execution.exit_code != 0 or execution.error:
                # Execution failed
                
                if execution.is_timeout:
                     return {
                        "status": "Time Limit Exceeded",
                        "passed_tests": 0,
                        "total_tests": total_tests,
                        "error_message": "Code execution exceeded 15 seconds.",
                        "execution_time_ms": 15000.0
                    }
                
                if language == "cpp" and "error:" in err_msg.lower():
                     return {
                        "status": "Compilation Error",
                        "passed_tests": 0,
                        "total_tests": total_tests,
                        "error_message": parse_cpp_error(err_msg, test_harness),
                        "execution_time_ms": 0.0
                    }
                    
                try:
                    # For C++, find the JSON summary line in stdout
                    stdout_lines = execution.stdout.strip().split("\n")
                    out_data = None
                    for line in reversed(stdout_lines):
                        line = line.strip()
                        if line.startswith("{"):
                            try:
                                out_data = json.loads(line)
                                break
                            except json.JSONDecodeError:
                                pass
                    if out_data is None:
                        out_data = json.loads(execution.stdout.strip())
                    
                    # C++ harness: test failures emit non-zero exit with stderr diagnostics
                    stderr_diag = execution.stderr.strip()
                    if language == "cpp":
                        passed_count = out_data.get("passed", 0)
                        real_total = out_data.get("total", total_tests)
                        return {
                            "status": "Wrong Answer",
                            "passed_tests": passed_count,
                            "total_tests": real_total,
                            "error_message": stderr_diag or f"{passed_count}/{real_total} tests passed.",
                            "execution_time_ms": out_data.get("time_ms", 0.0)
                        }
                    
                    # If it's a test failure, error string is fine. If it's a runtime error, use the corrected traceback.
                    if "Test failed" in out_data.get("error", ""):
                        final_err = out_data.get("error")
                    else:
                        raw_tb = out_data.get("traceback", "")
                        final_err = parse_traceback(raw_tb) or out_data.get("error")

                    return {
                        "status": "Wrong Answer" if "Test failed" in out_data.get("error", "") else "Runtime Error",
                        "passed_tests": out_data.get("passed", 0),
                        "total_tests": total_tests,
                        "error_message": final_err,
                        "execution_time_ms": 0.0
                    }
                except json.JSONDecodeError:
                    return {
                        "status": "Runtime Error",
                        "passed_tests": 0,
                        "total_tests": total_tests,
                        "error_message": err_msg,
                        "execution_time_ms": 0.0
                    }
                    
            stdout_lines = execution.stdout.strip().split("\n")
            # For C++, find the last line that looks like JSON (our summary line)
            out_data = None
            for line in reversed(stdout_lines):
                line = line.strip()
                if line.startswith("{"):
                    try:
                        out_data = json.loads(line)
                        break
                    except json.JSONDecodeError:
                        pass
            
            if out_data is None:
                out_data = json.loads(execution.stdout.strip())
            
            passed_count = out_data.get("passed", 0)
            real_total = out_data.get("total", total_tests)
            return {
                "status": "Accepted",
                "passed_tests": passed_count,
                "total_tests": real_total,
                "error_message": None,
                "execution_time_ms": out_data.get("time_ms", 0.0)
            }
            
    except Exception as e:
        return {
            "status": "Sandbox Error",
            "passed_tests": 0,
            "total_tests": total_tests,
            "error_message": str(e),
            "execution_time_ms": 0.0
        }
