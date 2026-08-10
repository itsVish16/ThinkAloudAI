import ast
import json
import logging
import re
import pandas as pd
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.database import DATABASE_URL, engine, Base
from app.models.dsa import DSAQuestion

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Subset of high-quality questions (Arrays, Strings, Math, DP) - No Linked Lists/Trees
TARGET_SLUGS = [
    "two-sum", "longest-palindromic-substring", "reverse-integer", "palindrome-number",
    "regular-expression-matching", "container-with-most-water", "integer-to-roman",
    "roman-to-integer", "longest-common-prefix", "3sum", "3sum-closest",
    "letter-combinations-of-a-phone-number", "4sum", "valid-parentheses", 
    "generate-parentheses", "remove-duplicates-from-sorted-array", "remove-element",
    "find-the-index-of-the-first-occurrence-in-a-string", "search-insert-position",
    "sudoku-solver", "count-and-say", "combination-sum", "combination-sum-ii",
    "first-missing-positive", "trapping-rain-water", "multiply-strings",
    "wildcard-matching", "jump-game-ii", "permutations", "permutations-ii",
    "rotate-image", "group-anagrams", "powx-n", "n-queens", "n-queens-ii",
    "maximum-subarray", "spiral-matrix", "jump-game", "merge-intervals",
    "insert-interval", "length-of-last-word", "spiral-matrix-ii",
    "permutation-sequence", "valid-number", "plus-one", "add-binary",
    "text-justification", "sqrtx", "climbing-stairs", "simplify-path",
    "edit-distance", "set-matrix-zeroes", "search-a-2d-matrix", "sort-colors"
]

def py_type_to_cpp(py_type):
    if py_type == "int": return "int"
    if py_type == "str": return "string"
    if py_type == "bool": return "bool"
    if py_type == "float": return "double"
    if py_type == "List[int]": return "vector<int>"
    if py_type == "List[str]": return "vector<string>"
    if py_type == "List[List[int]]": return "vector<vector<int>>"
    if py_type == "List[List[str]]": return "vector<vector<string>>"
    return "string" # fallback

def py_type_to_json(py_type):
    if py_type == "int": return "int"
    if py_type == "str": return "string"
    if py_type == "bool": return "boolean"
    if py_type == "float": return "float"
    if py_type == "List[int]": return "int[]"
    if py_type == "List[str]": return "string[]"
    if py_type == "List[List[int]]": return "int[][]"
    if py_type == "List[List[str]]": return "string[][]"
    return "string" # fallback

def extract_signature(py_code):
    try:
        tree = ast.parse(py_code + "\n        pass")
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_name = node.name
                params = []
                for arg in node.args.args:
                    if arg.arg == 'self':
                        continue
                    # Extract type hint
                    type_str = ast.unparse(arg.annotation) if arg.annotation else "str"
                    params.append({"name": arg.arg, "type_py": type_str, "type_cpp": py_type_to_cpp(type_str), "type_json": py_type_to_json(type_str)})
                ret_type = ast.unparse(node.returns) if node.returns else "None"
                return func_name, params, ret_type, py_type_to_json(ret_type), py_type_to_cpp(ret_type)
    except Exception as e:
        logger.error(f"AST Error on {py_code}: {e}")
    return None, None, None, None, None

def generate_cpp_harness(func_name, params, ret_type_cpp):
    cpp_code = "#include <iostream>\n#include <vector>\n#include <string>\n#include <sstream>\n#include <algorithm>\nusing namespace std;\n\n"
    
    # Helpers for parsing vectors
    cpp_code += """vector<int> parseVectorInt(const string& s) {
    vector<int> res;
    string temp = s;
    temp.erase(remove(temp.begin(), temp.end(), '['), temp.end());
    temp.erase(remove(temp.begin(), temp.end(), ']'), temp.end());
    temp.erase(remove(temp.begin(), temp.end(), ' '), temp.end());
    stringstream ss(temp);
    string item;
    while(getline(ss, item, ',')) {
        if(!item.empty()) res.push_back(stoi(item));
    }
    return res;
}

vector<string> parseVectorString(const string& s) {
    vector<string> res;
    string temp = s;
    temp.erase(remove(temp.begin(), temp.end(), '['), temp.end());
    temp.erase(remove(temp.begin(), temp.end(), ']'), temp.end());
    stringstream ss(temp);
    string item;
    while(getline(ss, item, ',')) {
        if(!item.empty()) {
            item.erase(remove(item.begin(), item.end(), '"'), item.end());
            item.erase(remove(item.begin(), item.end(), '\\''), item.end());
            item.erase(remove(item.begin(), item.end(), ' '), item.end()); // remove spaces
            res.push_back(item);
        }
    }
    return res;
}
\n"""
    
    cpp_code += "{{user_code}}\n\nint main() {\n"
    
    for p in params:
        if p["type_cpp"] == "int":
            cpp_code += f"    int {p['name']};\n"
            cpp_code += f"    if (!(cin >> {p['name']})) return 0;\n"
        elif p["type_cpp"] == "string":
            cpp_code += f"    string {p['name']};\n"
            cpp_code += f"    if (!(cin >> {p['name']})) return 0;\n"
        elif p["type_cpp"] == "vector<int>":
            cpp_code += f"    string {p['name']}_str;\n"
            cpp_code += f"    if (!getline(cin >> ws, {p['name']}_str)) return 0;\n"
            cpp_code += f"    vector<int> {p['name']} = parseVectorInt({p['name']}_str);\n"
        elif p["type_cpp"] == "vector<string>":
            cpp_code += f"    string {p['name']}_str;\n"
            cpp_code += f"    if (!getline(cin >> ws, {p['name']}_str)) return 0;\n"
            cpp_code += f"    vector<string> {p['name']} = parseVectorString({p['name']}_str);\n"
        else:
            # Fallback for complex types, treat as string to compile
            cpp_code += f"    string {p['name']};\n"
            cpp_code += f"    if (!getline(cin >> ws, {p['name']})) return 0;\n"
            
    cpp_code += f"    Solution sol;\n"
    call_args = ", ".join([p["name"] for p in params])
    cpp_code += f"    {ret_type_cpp} res = sol.{func_name}({call_args});\n"
    
    if ret_type_cpp == "vector<int>":
        cpp_code += '    cout << "[";\n'
        cpp_code += '    for(size_t i=0; i<res.size(); ++i) cout << res[i] << (i==res.size()-1 ? "" : ",");\n'
        cpp_code += '    cout << "]" << endl;\n'
    elif ret_type_cpp == "vector<vector<int>>":
        cpp_code += '    cout << "[";\n'
        cpp_code += '    for(size_t i=0; i<res.size(); ++i) {\n'
        cpp_code += '        cout << "[";\n'
        cpp_code += '        for(size_t j=0; j<res[i].size(); ++j) cout << res[i][j] << (j==res[i].size()-1 ? "" : ",");\n'
        cpp_code += '        cout << "]" << (i==res.size()-1 ? "" : ",");\n'
        cpp_code += '    }\n'
        cpp_code += '    cout << "]" << endl;\n'
    elif ret_type_cpp == "vector<string>":
        cpp_code += '    cout << "[";\n'
        cpp_code += '    for(size_t i=0; i<res.size(); ++i) cout << "\\"" << res[i] << "\\"" << (i==res.size()-1 ? "" : ",");\n'
        cpp_code += '    cout << "]" << endl;\n'
    elif ret_type_cpp == "bool":
        cpp_code += '    cout << (res ? "true" : "false") << endl;\n'
    else:
        cpp_code += '    cout << res << endl;\n'
        
    cpp_code += "    return 0;\n}\n"
    return cpp_code

def safe_eval_arg(val_str, py_type):
    val_str = str(val_str).strip()
    if py_type == "int": return int(val_str)
    if py_type == "str": return val_str.strip('"').strip("'")
    if py_type == "bool": return val_str.lower() == "true"
    if py_type == "float": return float(val_str)
    if py_type.startswith("List["):
        try:
            return json.loads(val_str.replace("'", '"'))
        except:
            return []
    return val_str

async def process_csv():
    df = pd.read_csv("/Users/vishal/Desktop/ThinkAloudAI/dsa_problems.csv")
    df = df[df['slug'].isin(TARGET_SLUGS)].copy()
    
    local_engine = create_async_engine(DATABASE_URL)
    LocalSession = sessionmaker(local_engine, class_=AsyncSession, expire_on_commit=False)
    
    logger.info(f"Processing {len(df)} questions...")
    
    questions = []
    
    count = 0
    for idx, row in df.iterrows():
        title = row["title"]
        py_code = row["starter_code_python"]
        cpp_code = row["starter_code_cpp"]
        
        func_name, params, ret_type_py, ret_type_json, ret_type_cpp = extract_signature(py_code)
        
        if not func_name or "List[List[str]]" in [p["type_py"] for p in params]:
            logger.warning(f"Skipping {title}: Could not parse signature or unsupported type.")
            continue
            
        cpp_test_harness = generate_cpp_harness(func_name, params, ret_type_cpp)
        
        raw_test_cases = json.loads(row.get("test_cases_json", "[]"))
        clean_cases = []
        
        for tc in raw_test_cases:
            input_data_str = str(tc["input_data"])
            if '\\n' in input_data_str:
                input_parts = input_data_str.split('\\n')
            else:
                input_parts = input_data_str.split('\n')
            
            if len(input_parts) < len(params):
                input_parts = input_data_str.split(',')
            
            if len(input_parts) < len(params):
                continue
                
            args_dict = {}
            for i, p in enumerate(params):
                args_dict[p["name"]] = safe_eval_arg(input_parts[i], p["type_py"])
                
            expected_val = safe_eval_arg(tc["expected_output"], ret_type_py)
            
            clean_cases.append({
                "args": args_dict,
                "expected": expected_val
            })
            
        if len(clean_cases) == 0:
            logger.warning(f"Skipping {title}: Could not parse test cases.")
            continue
            
        test_cases_json = {
            "function_name": func_name,
            "params": [{"name": p["name"], "type": p["type_json"]} for p in params],
            "return_type": ret_type_json,
            "comparison": "unordered" if "unordered" in title.lower() else "exact",
            "cases": clean_cases[:10]
        }
        
        desc = row.get("description", row.get("original_description", ""))
        
        questions.append({
            "title": title,
            "description": desc,
            "difficulty": row["difficulty"].capitalize(),
            "function_name": func_name,
            "python_starter_code": py_code,
            "cpp_starter_code": cpp_code,
            "cpp_test_harness": cpp_test_harness,
            "test_cases": json.dumps(test_cases_json),
            "hints": json.dumps(str(row.get("hints", "")).split('\\n')),
            "optimal_time_complexity": "O(N)",
            "optimal_space_complexity": "O(1)"
        })
        count += 1
        
    with open("clean_dsa_questions.json", "w") as f:
        json.dump(questions, f, indent=4)
        
    logger.info(f"Successfully exported {count} highly-curated DSA questions to clean_dsa_questions.json")

if __name__ == "__main__":
    asyncio.run(process_csv())
