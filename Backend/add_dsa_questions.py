import requests
import json

URL = "http://localhost:8001/dsa/questions"

q1 = {
    "title": "Merge Intervals",
    "description": "<p>Given an array of <code>intervals</code> where <code>intervals[i] = [start<sub>i</sub>, end<sub>i</sub>]</code>, merge all overlapping intervals, and return <em>an array of the non-overlapping intervals that cover all the intervals in the input</em>.</p>",
    "difficulty": "Medium",
    "test_cases": json.dumps([
      { "input": "intervals = [[1,3],[2,6],[8,10],[15,18]]", "expected": "[[1,6],[8,10],[15,18]]", "isPublic": True },
      { "input": "intervals = [[1,4],[4,5]]", "expected": "[[1,5]]", "isPublic": True }
    ]),
    "python_starter_code": "class Solution:\n    def merge(self, intervals: List[List[int]]) -> List[List[int]]:\n        pass",
    "cpp_starter_code": "#include <vector>\nclass Solution {\npublic:\n    std::vector<std::vector<int>> merge(std::vector<std::vector<int>>& intervals) {\n        \n    }\n};"
}

q2 = {
    "title": "Valid Parentheses",
    "description": "<p>Given a string <code>s</code> containing just the characters <code>'('</code>, <code>')'</code>, <code>'{'</code>, <code>'}'</code>, <code>'['</code> and <code>']'</code>, determine if the input string is valid.</p>",
    "difficulty": "Easy",
    "test_cases": json.dumps([
      { "input": "s = \"()\"", "expected": "true", "isPublic": True },
      { "input": "s = \"()[]{}\"", "expected": "true", "isPublic": True }
    ]),
    "python_starter_code": "class Solution:\n    def isValid(self, s: str) -> bool:\n        pass",
    "cpp_starter_code": "#include <string>\nclass Solution {\npublic:\n    bool isValid(std::string s) {\n        \n    }\n};"
}

r1 = requests.post(URL, json=q1)
print("Merge Intervals:", r1.status_code, r1.text)

r2 = requests.post(URL, json=q2)
print("Valid Parentheses:", r2.status_code, r2.text)
