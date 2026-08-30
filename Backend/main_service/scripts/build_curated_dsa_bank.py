import json
import logging
import os
import sys
import copy
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def normalize_val(v):
    if isinstance(v, (list, tuple)):
        normalized_items = [normalize_val(x) for x in v]
        try:
            return sorted(normalized_items, key=lambda x: str(x))
        except Exception:
            return normalized_items
    if isinstance(v, set):
        try:
            return sorted([normalize_val(x) for x in v], key=lambda x: str(x))
        except Exception:
            return list(v)
    if isinstance(v, dict):
        return {k: normalize_val(val) for k, val in v.items()}
    return v

def verify_test_cases(func, cases, comparison="exact"):
    for i, tc in enumerate(cases):
        args = copy.deepcopy(tc["args"])
        expected = tc["expected"]
        result = func(**args)
        
        # Check in-place mutation if return is None
        if result is None:
            for key in ['nums', 'matrix', 'board', 'intervals']:
                if key in args:
                    result = args[key]
                    break
        
        if comparison in ("unordered", "unordered_nested"):
            passed = normalize_val(result) == normalize_val(expected)
        elif comparison == "float_tolerance" or isinstance(expected, float):
            passed = abs(float(result) - float(expected)) < 1e-5
        elif comparison == "any_of":
            passed = result in expected or normalize_val(result) in [normalize_val(e) for e in expected]
        else:
            passed = result == expected
            
        if not passed:
            raise AssertionError(f"Test {i+1} failed!\nInput: {tc['args']}\nExpected: {expected}\nGot: {result}")
    return True

# Reference solutions for verification
def sol_contains_duplicate(nums):
    return len(nums) != len(set(nums))

def sol_valid_anagram(s, t):
    return sorted(s) == sorted(t)

def sol_two_sum(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        diff = target - n
        if diff in seen:
            return [seen[diff], i]
        seen[n] = i
    return []

def sol_group_anagrams(strs):
    groups = {}
    for s in strs:
        key = "".join(sorted(s))
        groups.setdefault(key, []).append(s)
    return list(groups.values())

def sol_top_k_frequent(nums, k):
    from collections import Counter
    return [item for item, _ in Counter(nums).most_common(k)]

def sol_product_except_self(nums):
    n = len(nums)
    res = [1] * n
    prefix = 1
    for i in range(n):
        res[i] = prefix
        prefix *= nums[i]
    postfix = 1
    for i in range(n - 1, -1, -1):
        res[i] *= postfix
        postfix *= nums[i]
    return res

def sol_longest_consecutive(nums):
    num_set = set(nums)
    longest = 0
    for n in num_set:
        if n - 1 not in num_set:
            length = 1
            while n + length in num_set:
                length += 1
            longest = max(longest, length)
    return longest

def sol_valid_palindrome(s):
    clean = [c.lower() for c in s if c.isalnum()]
    return clean == clean[::-1]

def sol_two_sum_sorted(numbers, target):
    l, r = 0, len(numbers) - 1
    while l < r:
        total = numbers[l] + numbers[r]
        if total == target:
            return [l + 1, r + 1]
        elif total < target:
            l += 1
        else:
            r -= 1
    return []

def sol_3sum(nums):
    nums.sort()
    res = []
    for i in range(len(nums) - 2):
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        l, r = i + 1, len(nums) - 1
        while l < r:
            total = nums[i] + nums[l] + nums[r]
            if total == 0:
                res.append([nums[i], nums[l], nums[r]])
                while l < r and nums[l] == nums[l + 1]:
                    l += 1
                while l < r and nums[r] == nums[r - 1]:
                    r -= 1
                l += 1
                r -= 1
            elif total < 0:
                l += 1
            else:
                r -= 1
    return res

def sol_container_water(height):
    l, r = 0, len(height) - 1
    max_a = 0
    while l < r:
        max_a = max(max_a, min(height[l], height[r]) * (r - l))
        if height[l] < height[r]:
            l += 1
        else:
            r -= 1
    return max_a

def sol_trapping_rain_water(height):
    if not height:
        return 0
    l, r = 0, len(height) - 1
    left_max, right_max = height[l], height[r]
    water = 0
    while l < r:
        if left_max < right_max:
            l += 1
            left_max = max(left_max, height[l])
            water += left_max - height[l]
        else:
            r -= 1
            right_max = max(right_max, height[r])
            water += right_max - height[r]
    return water

def sol_best_time_stock(prices):
    min_p = float('inf')
    max_p = 0
    for p in prices:
        min_p = min(min_p, p)
        max_p = max(max_p, p - min_p)
    return max_p

def sol_longest_substring_without_repeating(s):
    seen = {}
    l = 0
    max_len = 0
    for r, c in enumerate(s):
        if c in seen and seen[c] >= l:
            l = seen[c] + 1
        seen[c] = r
        max_len = max(max_len, r - l + 1)
    return max_len

def sol_longest_repeating_char_replacement(s, k):
    count = {}
    l = 0
    max_freq = 0
    max_len = 0
    for r in range(len(s)):
        count[s[r]] = count.get(s[r], 0) + 1
        max_freq = max(max_freq, count[s[r]])
        while (r - l + 1) - max_freq > k:
            count[s[l]] -= 1
            l += 1
        max_len = max(max_len, r - l + 1)
    return max_len

def sol_valid_parentheses(s):
    stack = []
    mapping = {")": "(", "}": "{", "]": "["}
    for c in s:
        if c in mapping:
            if not stack or stack.pop() != mapping[c]:
                return False
        else:
            stack.append(c)
    return len(stack) == 0

def sol_eval_rpn(tokens):
    stack = []
    for t in tokens:
        if t in "+-*/":
            b, a = stack.pop(), stack.pop()
            if t == "+": stack.append(a + b)
            elif t == "-": stack.append(a - b)
            elif t == "*": stack.append(a * b)
            elif t == "/": stack.append(int(a / b))
        else:
            stack.append(int(t))
    return stack[0]

def sol_daily_temperatures(temperatures):
    res = [0] * len(temperatures)
    stack = []
    for i, t in enumerate(temperatures):
        while stack and t > stack[-1][0]:
            _, idx = stack.pop()
            res[idx] = i - idx
        stack.append((t, i))
    return res

def sol_binary_search(nums, target):
    l, r = 0, len(nums) - 1
    while l <= r:
        mid = (l + r) // 2
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            l = mid + 1
        else:
            r = mid - 1
    return -1

def sol_search_2d_matrix(matrix, target):
    if not matrix or not matrix[0]:
        return False
    m, n = len(matrix), len(matrix[0])
    l, r = 0, m * n - 1
    while l <= r:
        mid = (l + r) // 2
        val = matrix[mid // n][mid % n]
        if val == target:
            return True
        elif val < target:
            l = mid + 1
        else:
            r = mid - 1
    return False

def sol_find_min_rotated(nums):
    l, r = 0, len(nums) - 1
    while l < r:
        mid = (l + r) // 2
        if nums[mid] > nums[r]:
            l = mid + 1
        else:
            r = mid
    return nums[l]

def sol_search_rotated(nums, target):
    l, r = 0, len(nums) - 1
    while l <= r:
        mid = (l + r) // 2
        if nums[mid] == target:
            return mid
        if nums[l] <= nums[mid]:
            if nums[l] <= target < nums[mid]:
                r = mid - 1
            else:
                l = mid + 1
        else:
            if nums[mid] < target <= nums[r]:
                l = mid + 1
            else:
                r = mid - 1
    return -1

def sol_merge_intervals(intervals):
    intervals.sort(key=lambda x: x[0])
    merged = []
    for interval in intervals:
        if not merged or merged[-1][1] < interval[0]:
            merged.append(interval)
        else:
            merged[-1][1] = max(merged[-1][1], interval[1])
    return merged

def sol_insert_interval(intervals, newInterval):
    res = []
    i = 0
    n = len(intervals)
    while i < n and intervals[i][1] < newInterval[0]:
        res.append(intervals[i])
        i += 1
    while i < n and intervals[i][0] <= newInterval[1]:
        newInterval[0] = min(newInterval[0], intervals[i][0])
        newInterval[1] = max(newInterval[1], intervals[i][1])
        i += 1
    res.append(newInterval)
    while i < n:
        res.append(intervals[i])
        i += 1
    return res

def sol_climbing_stairs(n):
    a, b = 1, 1
    for _ in range(n - 1):
        a, b = b, a + b
    return b

def sol_house_robber(nums):
    rob1, rob2 = 0, 0
    for n in nums:
        temp = max(n + rob1, rob2)
        rob1 = rob2
        rob2 = temp
    return rob2

def sol_coin_change(coins, amount):
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0
    for c in coins:
        for i in range(c, amount + 1):
            dp[i] = min(dp[i], dp[i - c] + 1)
    return dp[amount] if dp[amount] != float('inf') else -1

def sol_unique_paths(m, n):
    row = [1] * n
    for _ in range(m - 1):
        new_row = [1] * n
        for j in range(n - 2, -1, -1):
            new_row[j] = new_row[j + 1] + row[j]
        row = new_row
    return row[0]

def sol_max_subarray(nums):
    cur_sum = 0
    max_sum = nums[0]
    for n in nums:
        cur_sum = max(n, cur_sum + n)
        max_sum = max(max_sum, cur_sum)
    return max_sum

def sol_jump_game(nums):
    reach = 0
    for i, n in enumerate(nums):
        if i > reach:
            return False
        reach = max(reach, i + n)
    return True

def sol_jump_game_ii(nums):
    jumps = 0
    cur_end = 0
    cur_farthest = 0
    for i in range(len(nums) - 1):
        cur_farthest = max(cur_farthest, i + nums[i])
        if i == cur_end:
            jumps += 1
            cur_end = cur_farthest
    return jumps

def sol_rotate_image(matrix):
    n = len(matrix)
    for i in range(n):
        for j in range(i + 1, n):
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
    for row in matrix:
        row.reverse()
    return None

def sol_spiral_matrix(matrix):
    res = []
    top, bottom = 0, len(matrix) - 1
    left, right = 0, len(matrix[0]) - 1
    while top <= bottom and left <= right:
        for c in range(left, right + 1):
            res.append(matrix[top][c])
        top += 1
        for r in range(top, bottom + 1):
            res.append(matrix[r][right])
        right -= 1
        if top <= bottom:
            for c in range(right, left - 1, -1):
                res.append(matrix[bottom][c])
            bottom -= 1
        if left <= right:
            for r in range(bottom, top - 1, -1):
                res.append(matrix[r][left])
            left += 1
    return res

def sol_single_number(nums):
    res = 0
    for n in nums:
        res ^= n
    return res

def sol_number_of_1_bits(n):
    return bin(n).count("1")

def sol_counting_bits(n):
    dp = [0] * (n + 1)
    offset = 1
    for i in range(1, n + 1):
        if offset * 2 == i:
            offset = i
        dp[i] = 1 + dp[i - offset]
    return dp

# Helper generator for C++ array harness
def cpp_vector_int_harness(func_call_snippet):
    return f"""#include <iostream>
#include <vector>
#include <string>
#include <sstream>
#include <algorithm>
using namespace std;

vector<int> parseVectorInt(const string& s) {{
    vector<int> res;
    string temp = s;
    temp.erase(remove(temp.begin(), temp.end(), '['), temp.end());
    temp.erase(remove(temp.begin(), temp.end(), ']'), temp.end());
    temp.erase(remove(temp.begin(), temp.end(), ' '), temp.end());
    stringstream ss(temp);
    string item;
    while(getline(ss, item, ',')) {{
        if(!item.empty()) res.push_back(stoi(item));
    }}
    return res;
}}

{{{{user_code}}}}

int main() {{
{func_call_snippet}
    return 0;
}}"""

# All 28 curated questions
QUESTIONS: List[Dict[str, Any]] = [
    {
        "title": "Contains Duplicate",
        "category": "Arrays & Hashing",
        "difficulty": "Easy",
        "function_name": "containsDuplicate",
        "description": """Given an integer array `nums`, return `true` if any value appears **at least twice** in the array, and return `false` if every element is distinct.

## Examples

**Example 1:**
- **Input:** `nums = [1,2,3,1]`
- **Output:** `true`

**Example 2:**
- **Input:** `nums = [1,2,3,4]`
- **Output:** `false`

**Example 3:**
- **Input:** `nums = [1,1,1,3,3,4,3,2,4,2]`
- **Output:** `true`

## Constraints
- `1 <= nums.length <= 10^5`
- `-10^9 <= nums[i] <= 10^9`""",
        "python_starter_code": """class Solution:
    def containsDuplicate(self, nums: List[int]) -> bool:
        # Implement your solution here
        pass""",
        "cpp_starter_code": """class Solution {
public:
    bool containsDuplicate(vector<int>& nums) {
        // Implement your solution here
        return false;
    }
};""",
        "cpp_test_harness": cpp_vector_int_harness("""    string nums_str;
    if (!getline(cin >> ws, nums_str)) return 0;
    vector<int> nums = parseVectorInt(nums_str);
    Solution sol;
    bool res = sol.containsDuplicate(nums);
    cout << (res ? "true" : "false") << endl;"""),
        "test_cases": {
            "function_name": "containsDuplicate",
            "params": [{"name": "nums", "type": "int[]"}],
            "return_type": "boolean",
            "comparison": "exact",
            "cases": [
                {"args": {"nums": [1, 2, 3, 1]}, "expected": True},
                {"args": {"nums": [1, 2, 3, 4]}, "expected": False},
                {"args": {"nums": [1, 1, 1, 3, 3, 4, 3, 2, 4, 2]}, "expected": True},
                {"args": {"nums": [0]}, "expected": False},
                {"args": {"nums": [99, 99]}, "expected": True},
                {"args": {"nums": [-1, -2, -3, -1]}, "expected": True},
                {"args": {"nums": [-1000000000, 1000000000, 0, -1000000000]}, "expected": True}
            ]
        },
        "hints": [
            "A brute force check compares all pairs in O(N^2) time.",
            "Can you use a Hash Set to track seen numbers in O(N) time and O(N) space?"
        ],
        "optimal_time_complexity": "O(N)",
        "optimal_space_complexity": "O(N)",
        "tags": ["Array", "Hash Table"],
        "solution_func": sol_contains_duplicate
    },
    {
        "title": "Valid Anagram",
        "category": "Arrays & Hashing",
        "difficulty": "Easy",
        "function_name": "isAnagram",
        "description": """Given two strings `s` and `t`, return `true` if `t` is an **anagram** of `s`, and `false` otherwise.

## Examples

**Example 1:**
- **Input:** `s = "anagram"`, `t = "nagaram"`
- **Output:** `true`

**Example 2:**
- **Input:** `s = "rat"`, `t = "car"`
- **Output:** `false`

## Constraints
- `1 <= s.length, t.length <= 5 * 10^4`
- `s` and `t` consist of lowercase English letters.""",
        "python_starter_code": """class Solution:
    def isAnagram(self, s: str, t: str) -> bool:
        # Implement your solution here
        pass""",
        "cpp_starter_code": """class Solution {
public:
    bool isAnagram(string s, string t) {
        // Implement your solution here
        return false;
    }
};""",
        "cpp_test_harness": """#include <iostream>
#include <string>
#include <vector>
#include <algorithm>
using namespace std;

{{user_code}}

int main() {
    string s, t;
    if (!(cin >> s >> t)) return 0;
    Solution sol;
    bool res = sol.isAnagram(s, t);
    cout << (res ? "true" : "false") << endl;
    return 0;
}""",
        "test_cases": {
            "function_name": "isAnagram",
            "params": [{"name": "s", "type": "string"}, {"name": "t", "type": "string"}],
            "return_type": "boolean",
            "comparison": "exact",
            "cases": [
                {"args": {"s": "anagram", "t": "nagaram"}, "expected": True},
                {"args": {"s": "rat", "t": "car"}, "expected": False},
                {"args": {"s": "a", "t": "a"}, "expected": True},
                {"args": {"s": "ab", "t": "a"}, "expected": False},
                {"args": {"s": "listen", "t": "silent"}, "expected": True},
                {"args": {"s": "triangle", "t": "integral"}, "expected": True},
                {"args": {"s": "aabbcc", "t": "abcabc"}, "expected": True}
            ]
        },
        "hints": [
            "If lengths of s and t differ, they cannot be anagrams.",
            "Count frequencies of each character using a hash map or array of size 26."
        ],
        "optimal_time_complexity": "O(N)",
        "optimal_space_complexity": "O(1)",
        "tags": ["Hash Table", "String", "Sorting"],
        "solution_func": sol_valid_anagram
    },
    {
        "title": "Two Sum",
        "category": "Arrays & Hashing",
        "difficulty": "Easy",
        "function_name": "twoSum",
        "description": """Given an array of integers `nums` and an integer `target`, return *indices of the two numbers such that they add up to `target`*.

You may assume that each input would have ***exactly one solution***, and you may not use the *same* element twice.

## Examples

**Example 1:**
- **Input:** `nums = [2,7,11,15]`, `target = 9`
- **Output:** `[0,1]`

**Example 2:**
- **Input:** `nums = [3,2,4]`, `target = 6`
- **Output:** `[1,2]`

**Example 3:**
- **Input:** `nums = [3,3]`, `target = 6`
- **Output:** `[0,1]`

## Constraints
- `2 <= nums.length <= 10^4`
- `-10^9 <= nums[i] <= 10^9`
- `-10^9 <= target <= 10^9`""",
        "python_starter_code": """class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        # Implement your solution here
        pass""",
        "cpp_starter_code": """class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        // Implement your solution here
        return {};
    }
};""",
        "cpp_test_harness": cpp_vector_int_harness("""    string nums_str;
    if (!getline(cin >> ws, nums_str)) return 0;
    vector<int> nums = parseVectorInt(nums_str);
    int target;
    if (!(cin >> target)) return 0;
    Solution sol;
    vector<int> res = sol.twoSum(nums, target);
    cout << "[";
    for(size_t i = 0; i < res.size(); ++i) {
        cout << res[i] << (i == res.size() - 1 ? "" : ",");
    }
    cout << "]" << endl;"""),
        "test_cases": {
            "function_name": "twoSum",
            "params": [{"name": "nums", "type": "int[]"}, {"name": "target", "type": "int"}],
            "return_type": "int[]",
            "comparison": "unordered",
            "cases": [
                {"args": {"nums": [2, 7, 11, 15], "target": 9}, "expected": [0, 1]},
                {"args": {"nums": [3, 2, 4], "target": 6}, "expected": [1, 2]},
                {"args": {"nums": [3, 3], "target": 6}, "expected": [0, 1]},
                {"args": {"nums": [-1, -2, -3, -4, -5], "target": -8}, "expected": [2, 4]},
                {"args": {"nums": [0, 4, 3, 0], "target": 0}, "expected": [0, 3]},
                {"args": {"nums": [1000000000, -1000000000, 5], "target": 0}, "expected": [0, 1]}
            ]
        },
        "hints": [
            "Store elements in a hash map: for each element x, check if (target - x) is already in the map."
        ],
        "optimal_time_complexity": "O(N)",
        "optimal_space_complexity": "O(N)",
        "tags": ["Array", "Hash Table"],
        "solution_func": sol_two_sum
    },
    {
        "title": "Group Anagrams",
        "category": "Arrays & Hashing",
        "difficulty": "Medium",
        "function_name": "groupAnagrams",
        "description": """Given an array of strings `strs`, group **the anagrams** together. You can return the answer in **any order**.

## Examples

**Example 1:**
- **Input:** `strs = ["eat","tea","tan","ate","nat","bat"]`
- **Output:** `[["bat"],["nat","tan"],["ate","eat","tea"]]`

**Example 2:**
- **Input:** `strs = [""]`
- **Output:** `[[""]]`

**Example 3:**
- **Input:** `strs = ["a"]`
- **Output:** `[["a"]]`

## Constraints
- `1 <= strs.length <= 10^4`
- `0 <= strs[i].length <= 100`""",
        "python_starter_code": """class Solution:
    def groupAnagrams(self, strs: List[str]) -> List[List[str]]:
        # Implement your solution here
        pass""",
        "cpp_starter_code": """class Solution {
public:
    vector<vector<string>> groupAnagrams(vector<string>& strs) {
        // Implement your solution here
        return {};
    }
};""",
        "cpp_test_harness": """#include <iostream>
#include <vector>
#include <string>
#include <sstream>
#include <algorithm>
using namespace std;

vector<string> parseVectorString(const string& s) {
    vector<string> res;
    string temp = s;
    temp.erase(remove(temp.begin(), temp.end(), '['), temp.end());
    temp.erase(remove(temp.begin(), temp.end(), ']'), temp.end());
    stringstream ss(temp);
    string item;
    while(getline(ss, item, ',')) {
        if(!item.empty()) {
            item.erase(remove(item.begin(), item.end(), '\"'), item.end());
            item.erase(remove(item.begin(), item.end(), '\\''), item.end());
            item.erase(remove(item.begin(), item.end(), ' '), item.end());
            res.push_back(item);
        }
    }
    return res;
}

{{user_code}}

int main() {
    string strs_line;
    if (!getline(cin >> ws, strs_line)) return 0;
    vector<string> strs = parseVectorString(strs_line);
    Solution sol;
    vector<vector<string>> res = sol.groupAnagrams(strs);
    cout << "[";
    for(size_t i = 0; i < res.size(); ++i) {
        cout << "[";
        for(size_t j = 0; j < res[i].size(); ++j) {
            cout << "\\\"" << res[i][j] << "\\\"" << (j == res[i].size() - 1 ? "" : ",");
        }
        cout << "]" << (i == res.size() - 1 ? "" : ",");
    }
    cout << "]" << endl;
    return 0;
}""",
        "test_cases": {
            "function_name": "groupAnagrams",
            "params": [{"name": "strs", "type": "string[]"}],
            "return_type": "string[][]",
            "comparison": "unordered_nested",
            "cases": [
                {"args": {"strs": ["eat", "tea", "tan", "ate", "nat", "bat"]}, "expected": [["bat"], ["nat", "tan"], ["ate", "eat", "tea"]]},
                {"args": {"strs": [""]}, "expected": [[""]]},
                {"args": {"strs": ["a"]}, "expected": [["a"]]},
                {"args": {"strs": ["a", "b", "a"]}, "expected": [["a", "a"], ["b"]]}
            ]
        },
        "hints": [
            "Use the sorted string as the key in a hash map to group words."
        ],
        "optimal_time_complexity": "O(N * K log K)",
        "optimal_space_complexity": "O(N * K)",
        "tags": ["Array", "Hash Table", "String", "Sorting"],
        "solution_func": sol_group_anagrams
    },
    {
        "title": "Top K Frequent Elements",
        "category": "Arrays & Hashing",
        "difficulty": "Medium",
        "function_name": "topKFrequent",
        "description": """Given an integer array `nums` and an integer `k`, return *the* `k` *most frequent elements*. You may return the answer in **any order**.

## Examples

**Example 1:**
- **Input:** `nums = [1,1,1,2,2,3]`, `k = 2`
- **Output:** `[1,2]`

**Example 2:**
- **Input:** `nums = [1]`, `k = 1`
- **Output:** `[1]`

## Constraints
- `1 <= nums.length <= 10^5`
- `-10^4 <= nums[i] <= 10^4`
- `k` is in the range `[1, the number of unique elements in the array]`.
- It is **guaranteed** that the answer is **unique**.""",
        "python_starter_code": """class Solution:
    def topKFrequent(self, nums: List[int], k: int) -> List[int]:
        # Implement your solution here
        pass""",
        "cpp_starter_code": """class Solution {
public:
    vector<int> topKFrequent(vector<int>& nums, int k) {
        // Implement your solution here
        return {};
    }
};""",
        "cpp_test_harness": cpp_vector_int_harness("""    string nums_str;
    if (!getline(cin >> ws, nums_str)) return 0;
    vector<int> nums = parseVectorInt(nums_str);
    int k;
    if (!(cin >> k)) return 0;
    Solution sol;
    vector<int> res = sol.topKFrequent(nums, k);
    cout << "[";
    for(size_t i = 0; i < res.size(); ++i) {
        cout << res[i] << (i == res.size() - 1 ? "" : ",");
    }
    cout << "]" << endl;"""),
        "test_cases": {
            "function_name": "topKFrequent",
            "params": [{"name": "nums", "type": "int[]"}, {"name": "k", "type": "int"}],
            "return_type": "int[]",
            "comparison": "unordered",
            "cases": [
                {"args": {"nums": [1, 1, 1, 2, 2, 3], "k": 2}, "expected": [1, 2]},
                {"args": {"nums": [1], "k": 1}, "expected": [1]},
                {"args": {"nums": [4, 1, -1, 2, -1, 2, 3], "k": 2}, "expected": [-1, 2]},
                {"args": {"nums": [3, 0, 1, 0], "k": 1}, "expected": [0]}
            ]
        },
        "hints": [
            "Use Bucket Sort or a Min-Heap of size k to find the top k frequent elements in O(N) time."
        ],
        "optimal_time_complexity": "O(N)",
        "optimal_space_complexity": "O(N)",
        "tags": ["Array", "Hash Table", "Heap", "Bucket Sort"],
        "solution_func": sol_top_k_frequent
    },
    {
        "title": "Product of Array Except Self",
        "category": "Arrays & Hashing",
        "difficulty": "Medium",
        "function_name": "productExceptSelf",
        "description": """Given an integer array `nums`, return *an array* `answer` *such that* `answer[i]` *is equal to the product of all the elements of* `nums` *except* `nums[i]`.

You must write an algorithm that runs in `O(n)` time and without using the division operation.

## Examples

**Example 1:**
- **Input:** `nums = [1,2,3,4]`
- **Output:** `[24,12,8,6]`

**Example 2:**
- **Input:** `nums = [-1,1,0,-3,3]`
- **Output:** `[0,0,9,0,0]`

## Constraints
- `2 <= nums.length <= 10^5`
- `-30 <= nums[i] <= 30`""",
        "python_starter_code": """class Solution:
    def productExceptSelf(self, nums: List[int]) -> List[int]:
        # Implement your solution here
        pass""",
        "cpp_starter_code": """class Solution {
public:
    vector<int> productExceptSelf(vector<int>& nums) {
        // Implement your solution here
        return {};
    }
};""",
        "cpp_test_harness": cpp_vector_int_harness("""    string nums_str;
    if (!getline(cin >> ws, nums_str)) return 0;
    vector<int> nums = parseVectorInt(nums_str);
    Solution sol;
    vector<int> res = sol.productExceptSelf(nums);
    cout << "[";
    for(size_t i = 0; i < res.size(); ++i) {
        cout << res[i] << (i == res.size() - 1 ? "" : ",");
    }
    cout << "]" << endl;"""),
        "test_cases": {
            "function_name": "productExceptSelf",
            "params": [{"name": "nums", "type": "int[]"}],
            "return_type": "int[]",
            "comparison": "exact",
            "cases": [
                {"args": {"nums": [1, 2, 3, 4]}, "expected": [24, 12, 8, 6]},
                {"args": {"nums": [-1, 1, 0, -3, 3]}, "expected": [0, 0, 9, 0, 0]},
                {"args": {"nums": [2, 3]}, "expected": [3, 2]},
                {"args": {"nums": [0, 0]}, "expected": [0, 0]},
                {"args": {"nums": [1, 1, 1, 1]}, "expected": [1, 1, 1, 1]}
            ]
        },
        "hints": [
            "Compute prefix products in one forward pass and suffix products in a backward pass."
        ],
        "optimal_time_complexity": "O(N)",
        "optimal_space_complexity": "O(1)",
        "tags": ["Array", "Prefix Sum"],
        "solution_func": sol_product_except_self
    },
    {
        "title": "Longest Consecutive Sequence",
        "category": "Arrays & Hashing",
        "difficulty": "Medium",
        "function_name": "longestConsecutive",
        "description": """Given an unsorted array of integers `nums`, return *the length of the longest consecutive elements sequence.*

You must write an algorithm that runs in `O(n)` time.

## Examples

**Example 1:**
- **Input:** `nums = [100,4,200,1,3,2]`
- **Output:** `4`
- **Explanation:** The longest consecutive elements sequence is `[1, 2, 3, 4]`. Its length is 4.

**Example 2:**
- **Input:** `nums = [0,3,7,2,5,8,4,6,0,1]`
- **Output:** `9`

## Constraints
- `0 <= nums.length <= 10^5`
- `-10^9 <= nums[i] <= 10^9`""",
        "python_starter_code": """class Solution:
    def longestConsecutive(self, nums: List[int]) -> int:
        # Implement your solution here
        pass""",
        "cpp_starter_code": """class Solution {
public:
    int longestConsecutive(vector<int>& nums) {
        // Implement your solution here
        return 0;
    }
};""",
        "cpp_test_harness": cpp_vector_int_harness("""    string nums_str;
    if (!getline(cin >> ws, nums_str)) return 0;
    vector<int> nums = parseVectorInt(nums_str);
    Solution sol;
    int res = sol.longestConsecutive(nums);
    cout << res << endl;"""),
        "test_cases": {
            "function_name": "longestConsecutive",
            "params": [{"name": "nums", "type": "int[]"}],
            "return_type": "int",
            "comparison": "exact",
            "cases": [
                {"args": {"nums": [100, 4, 200, 1, 3, 2]}, "expected": 4},
                {"args": {"nums": [0, 3, 7, 2, 5, 8, 4, 6, 0, 1]}, "expected": 9},
                {"args": {"nums": []}, "expected": 0},
                {"args": {"nums": [9, 1, 4, 7, 3, -1, 0, 5, 8, -1, 6]}, "expected": 7},
                {"args": {"nums": [1, 2, 0, 1]}, "expected": 3}
            ]
        },
        "hints": [
            "Store all numbers in a HashSet.",
            "Only start counting sequence length from numbers that are sequence starts (i.e. `n - 1` is not in the set)."
        ],
        "optimal_time_complexity": "O(N)",
        "optimal_space_complexity": "O(N)",
        "tags": ["Array", "Hash Table", "Union Find"],
        "solution_func": sol_longest_consecutive
    },
    {
        "title": "Valid Palindrome",
        "category": "Two Pointers",
        "difficulty": "Easy",
        "function_name": "isPalindrome",
        "description": """A phrase is a **palindrome** if, after converting all uppercase letters into lowercase letters and removing all non-alphanumeric characters, it reads the same forward and backward.

Given a string `s`, return `true` *if it is a **palindrome**, or* `false` *otherwise*.

## Examples

**Example 1:**
- **Input:** `s = "A man, a plan, a canal: Panama"`
- **Output:** `true`

**Example 2:**
- **Input:** `s = "race a car"`
- **Output:** `false`

**Example 3:**
- **Input:** `s = " "`
- **Output:** `true`

## Constraints
- `1 <= s.length <= 2 * 10^5`""",
        "python_starter_code": """class Solution:
    def isPalindrome(self, s: str) -> bool:
        # Implement your solution here
        pass""",
        "cpp_starter_code": """class Solution {
public:
    bool isPalindrome(string s) {
        // Implement your solution here
        return false;
    }
};""",
        "cpp_test_harness": """#include <iostream>
#include <string>
#include <cctype>
#include <algorithm>
using namespace std;

{{user_code}}

int main() {
    string s;
    if (!getline(cin, s)) return 0;
    Solution sol;
    bool res = sol.isPalindrome(s);
    cout << (res ? "true" : "false") << endl;
    return 0;
}""",
        "test_cases": {
            "function_name": "isPalindrome",
            "params": [{"name": "s", "type": "string"}],
            "return_type": "boolean",
            "comparison": "exact",
            "cases": [
                {"args": {"s": "A man, a plan, a canal: Panama"}, "expected": True},
                {"args": {"s": "race a car"}, "expected": False},
                {"args": {"s": " "}, "expected": True},
                {"args": {"s": "0P"}, "expected": False},
                {"args": {"s": "a."}, "expected": True},
                {"args": {"s": "Madam, I'm Adam."}, "expected": True}
            ]
        },
        "hints": [
            "Use two pointers, skipping non-alphanumeric characters with `isalnum()`."
        ],
        "optimal_time_complexity": "O(N)",
        "optimal_space_complexity": "O(1)",
        "tags": ["Two Pointers", "String"],
        "solution_func": sol_valid_palindrome
    },
    {
        "title": "3Sum",
        "category": "Two Pointers",
        "difficulty": "Medium",
        "function_name": "threeSum",
        "description": """Given an integer array `nums`, return all the triplets `[nums[i], nums[j], nums[k]]` such that `i != j`, `i != k`, and `j != k`, and `nums[i] + nums[j] + nums[k] == 0`.

The solution set must not contain duplicate triplets.

## Examples

**Example 1:**
- **Input:** `nums = [-1,0,1,2,-1,-4]`
- **Output:** `[[-1,-1,2],[-1,0,1]]`

**Example 2:**
- **Input:** `nums = [0,1,1]`
- **Output:** `[]`

**Example 3:**
- **Input:** `nums = [0,0,0]`
- **Output:** `[[0,0,0]]`

## Constraints
- `3 <= nums.length <= 3000`
- `-10^5 <= nums[i] <= 10^5`""",
        "python_starter_code": """class Solution:
    def threeSum(self, nums: List[int]) -> List[List[int]]:
        # Implement your solution here
        pass""",
        "cpp_starter_code": """class Solution {
public:
    vector<vector<int>> threeSum(vector<int>& nums) {
        // Implement your solution here
        return {};
    }
};""",
        "cpp_test_harness": cpp_vector_int_harness("""    string nums_str;
    if (!getline(cin >> ws, nums_str)) return 0;
    vector<int> nums = parseVectorInt(nums_str);
    Solution sol;
    vector<vector<int>> res = sol.threeSum(nums);
    cout << "[";
    for(size_t i=0; i<res.size(); ++i) {
        cout << "[";
        for(size_t j=0; j<res[i].size(); ++j) cout << res[i][j] << (j==res[i].size()-1 ? "" : ",");
        cout << "]" << (i==res.size()-1 ? "" : ",");
    }
    cout << "]" << endl;"""),
        "test_cases": {
            "function_name": "threeSum",
            "params": [{"name": "nums", "type": "int[]"}],
            "return_type": "int[][]",
            "comparison": "unordered_nested",
            "cases": [
                {"args": {"nums": [-1, 0, 1, 2, -1, -4]}, "expected": [[-1, -1, 2], [-1, 0, 1]]},
                {"args": {"nums": [0, 1, 1]}, "expected": []},
                {"args": {"nums": [0, 0, 0]}, "expected": [[0, 0, 0]]},
                {"args": {"nums": [-2, 0, 1, 1, 2]}, "expected": [[-2, 0, 2], [-2, 1, 1]]},
                {"args": {"nums": [-1, 0, 1]}, "expected": [[-1, 0, 1]]},
                {"args": {"nums": [1, 2, -2, -1]}, "expected": []}
            ]
        },
        "hints": [
            "Sort the array first to easily bypass duplicates and apply two pointers."
        ],
        "optimal_time_complexity": "O(N^2)",
        "optimal_space_complexity": "O(1)",
        "tags": ["Array", "Two Pointers", "Sorting"],
        "solution_func": sol_3sum
    },
    {
        "title": "Container With Most Water",
        "category": "Two Pointers",
        "difficulty": "Medium",
        "function_name": "maxArea",
        "description": """You are given an integer array `height` of length `n`. There are `n` vertical lines drawn such that the two endpoints of the `i`th line are `(i, 0)` and `(i, height[i])`.

Find two lines that together with the x-axis form a container, such that the container contains the most water.

Return *the maximum amount of water a container can store*.

## Examples

**Example 1:**
- **Input:** `height = [1,8,6,2,5,4,8,3,7]`
- **Output:** `49`

**Example 2:**
- **Input:** `height = [1,1]`
- **Output:** `1`

## Constraints
- `n == height.length`
- `2 <= n <= 10^5`
- `0 <= height[i] <= 10^4`""",
        "python_starter_code": """class Solution:
    def maxArea(self, height: List[int]) -> int:
        # Implement your solution here
        pass""",
        "cpp_starter_code": """class Solution {
public:
    int maxArea(vector<int>& height) {
        // Implement your solution here
        return 0;
    }
};""",
        "cpp_test_harness": cpp_vector_int_harness("""    string height_str;
    if (!getline(cin >> ws, height_str)) return 0;
    vector<int> height = parseVectorInt(height_str);
    Solution sol;
    int res = sol.maxArea(height);
    cout << res << endl;"""),
        "test_cases": {
            "function_name": "maxArea",
            "params": [{"name": "height", "type": "int[]"}],
            "return_type": "int",
            "comparison": "exact",
            "cases": [
                {"args": {"height": [1, 8, 6, 2, 5, 4, 8, 3, 7]}, "expected": 49},
                {"args": {"height": [1, 1]}, "expected": 1},
                {"args": {"height": [4, 3, 2, 1, 4]}, "expected": 16},
                {"args": {"height": [1, 2, 1]}, "expected": 2},
                {"args": {"height": [1, 2, 4, 3]}, "expected": 4}
            ]
        },
        "hints": [
            "Start with the widest container and greedily move the shorter line inward."
        ],
        "optimal_time_complexity": "O(N)",
        "optimal_space_complexity": "O(1)",
        "tags": ["Array", "Two Pointers", "Greedy"],
        "solution_func": sol_container_water
    },
    {
        "title": "Trapping Rain Water",
        "category": "Two Pointers",
        "difficulty": "Hard",
        "function_name": "trap",
        "description": """Given `n` non-negative integers representing an elevation map where the width of each bar is `1`, compute how much water it can trap after raining.

## Examples

**Example 1:**
- **Input:** `height = [0,1,0,2,1,0,1,3,2,1,2,1]`
- **Output:** `6`

**Example 2:**
- **Input:** `height = [4,2,0,3,2,5]`
- **Output:** `9`

## Constraints
- `n == height.length`
- `1 <= n <= 2 * 10^4`
- `0 <= height[i] <= 10^5`""",
        "python_starter_code": """class Solution:
    def trap(self, height: List[int]) -> int:
        # Implement your solution here
        pass""",
        "cpp_starter_code": """class Solution {
public:
    int trap(vector<int>& height) {
        // Implement your solution here
        return 0;
    }
};""",
        "cpp_test_harness": cpp_vector_int_harness("""    string height_str;
    if (!getline(cin >> ws, height_str)) return 0;
    vector<int> height = parseVectorInt(height_str);
    Solution sol;
    int res = sol.trap(height);
    cout << res << endl;"""),
        "test_cases": {
            "function_name": "trap",
            "params": [{"name": "height", "type": "int[]"}],
            "return_type": "int",
            "comparison": "exact",
            "cases": [
                {"args": {"height": [0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]}, "expected": 6},
                {"args": {"height": [4, 2, 0, 3, 2, 5]}, "expected": 9},
                {"args": {"height": [4, 2, 3]}, "expected": 1},
                {"args": {"height": [1]}, "expected": 0},
                {"args": {"height": []}, "expected": 0}
            ]
        },
        "hints": [
            "Use two pointers with `left_max` and `right_max` boundaries to calculate trapped water in O(1) space."
        ],
        "optimal_time_complexity": "O(N)",
        "optimal_space_complexity": "O(1)",
        "tags": ["Array", "Two Pointers", "Dynamic Programming", "Stack"],
        "solution_func": sol_trapping_rain_water
    },
    {
        "title": "Best Time to Buy and Sell Stock",
        "category": "Sliding Window",
        "difficulty": "Easy",
        "function_name": "maxProfit",
        "description": """You are given an array `prices` where `prices[i]` is the price of a given stock on the `i`th day.

Maximize your profit by choosing a single day to buy and a future day to sell. Return the maximum profit, or `0` if no profit is possible.

## Examples

**Example 1:**
- **Input:** `prices = [7,1,5,3,6,4]`
- **Output:** `5`

**Example 2:**
- **Input:** `prices = [7,6,4,3,1]`
- **Output:** `0`

## Constraints
- `1 <= prices.length <= 10^5`
- `0 <= prices[i] <= 10^4`""",
        "python_starter_code": """class Solution:
    def maxProfit(self, prices: List[int]) -> int:
        # Implement your solution here
        pass""",
        "cpp_starter_code": """class Solution {
public:
    int maxProfit(vector<int>& prices) {
        // Implement your solution here
        return 0;
    }
};""",
        "cpp_test_harness": cpp_vector_int_harness("""    string prices_str;
    if (!getline(cin >> ws, prices_str)) return 0;
    vector<int> prices = parseVectorInt(prices_str);
    Solution sol;
    int res = sol.maxProfit(prices);
    cout << res << endl;"""),
        "test_cases": {
            "function_name": "maxProfit",
            "params": [{"name": "prices", "type": "int[]"}],
            "return_type": "int",
            "comparison": "exact",
            "cases": [
                {"args": {"prices": [7, 1, 5, 3, 6, 4]}, "expected": 5},
                {"args": {"prices": [7, 6, 4, 3, 1]}, "expected": 0},
                {"args": {"prices": [1, 2]}, "expected": 1},
                {"args": {"prices": [2, 4, 1]}, "expected": 2},
                {"args": {"prices": [3, 2, 6, 5, 0, 3]}, "expected": 4}
            ]
        },
        "hints": [
            "Track min price so far and compute profit at every step."
        ],
        "optimal_time_complexity": "O(N)",
        "optimal_space_complexity": "O(1)",
        "tags": ["Array", "Dynamic Programming"],
        "solution_func": sol_best_time_stock
    },
    {
        "title": "Longest Substring Without Repeating Characters",
        "category": "Sliding Window",
        "difficulty": "Medium",
        "function_name": "lengthOfLongestSubstring",
        "description": """Given a string `s`, find the length of the **longest substring** without duplicate characters.

## Examples

**Example 1:**
- **Input:** `s = "abcabcbb"`
- **Output:** `3`

**Example 2:**
- **Input:** `s = "bbbbb"`
- **Output:** `1`

**Example 3:**
- **Input:** `s = "pwwkew"`
- **Output:** `3`

## Constraints
- `0 <= s.length <= 5 * 10^4`""",
        "python_starter_code": """class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        # Implement your solution here
        pass""",
        "cpp_starter_code": """class Solution {
public:
    int lengthOfLongestSubstring(string s) {
        // Implement your solution here
        return 0;
    }
};""",
        "cpp_test_harness": """#include <iostream>
#include <string>
#include <unordered_map>
#include <algorithm>
using namespace std;

{{user_code}}

int main() {
    string s;
    getline(cin, s);
    Solution sol;
    int res = sol.lengthOfLongestSubstring(s);
    cout << res << endl;
    return 0;
}""",
        "test_cases": {
            "function_name": "lengthOfLongestSubstring",
            "params": [{"name": "s", "type": "string"}],
            "return_type": "int",
            "comparison": "exact",
            "cases": [
                {"args": {"s": "abcabcbb"}, "expected": 3},
                {"args": {"s": "bbbbb"}, "expected": 1},
                {"args": {"s": "pwwkew"}, "expected": 3},
                {"args": {"s": ""}, "expected": 0},
                {"args": {"s": " "}, "expected": 1},
                {"args": {"s": "au"}, "expected": 2},
                {"args": {"s": "dvdf"}, "expected": 3}
            ]
        },
        "hints": [
            "Use a sliding window with a hash map of last seen indices."
        ],
        "optimal_time_complexity": "O(N)",
        "optimal_space_complexity": "O(min(M, N))",
        "tags": ["Hash Table", "String", "Sliding Window"],
        "solution_func": sol_longest_substring_without_repeating
    },
    {
        "title": "Valid Parentheses",
        "category": "Stack",
        "difficulty": "Easy",
        "function_name": "isValid",
        "description": """Given a string `s` containing just the characters `'('`, `')'`, `'{'`, `'}'`, `'['` and `']'`, determine if the input string is valid.

## Examples

**Example 1:**
- **Input:** `s = "()"`
- **Output:** `true`

**Example 2:**
- **Input:** `s = "()[]{}"`
- **Output:** `true`

**Example 3:**
- **Input:** `s = "(]"`
- **Output:** `false`

## Constraints
- `1 <= s.length <= 10^4`""",
        "python_starter_code": """class Solution:
    def isValid(self, s: str) -> bool:
        # Implement your solution here
        pass""",
        "cpp_starter_code": """class Solution {
public:
    bool isValid(string s) {
        // Implement your solution here
        return false;
    }
};""",
        "cpp_test_harness": """#include <iostream>
#include <string>
#include <stack>
#include <unordered_map>
using namespace std;

{{user_code}}

int main() {
    string s;
    if (!getline(cin, s)) return 0;
    Solution sol;
    bool res = sol.isValid(s);
    cout << (res ? "true" : "false") << endl;
    return 0;
}""",
        "test_cases": {
            "function_name": "isValid",
            "params": [{"name": "s", "type": "string"}],
            "return_type": "boolean",
            "comparison": "exact",
            "cases": [
                {"args": {"s": "()"}, "expected": True},
                {"args": {"s": "()[]{}"}, "expected": True},
                {"args": {"s": "(]"}, "expected": False},
                {"args": {"s": "([])"}, "expected": True},
                {"args": {"s": "([)]"}, "expected": False},
                {"args": {"s": "{"}, "expected": False}
            ]
        },
        "hints": [
            "Use a stack to push open brackets and pop on matching closed brackets."
        ],
        "optimal_time_complexity": "O(N)",
        "optimal_space_complexity": "O(N)",
        "tags": ["String", "Stack"],
        "solution_func": sol_valid_parentheses
    },
    {
        "title": "Evaluate Reverse Polish Notation",
        "category": "Stack",
        "difficulty": "Medium",
        "function_name": "evalRPN",
        "description": """You are given an array of strings `tokens` that represents an arithmetic expression in a Reverse Polish Notation.

Evaluate the expression and return an integer that represents its value.

## Examples

**Example 1:**
- **Input:** `tokens = ["2","1","+","3","*"]`
- **Output:** `9`

**Example 2:**
- **Input:** `tokens = ["4","13","5","/","+"]`
- **Output:** `6`

## Constraints
- `1 <= tokens.length <= 10^4`""",
        "python_starter_code": """class Solution:
    def evalRPN(self, tokens: List[str]) -> int:
        # Implement your solution here
        pass""",
        "cpp_starter_code": """class Solution {
public:
    int evalRPN(vector<string>& tokens) {
        // Implement your solution here
        return 0;
    }
};""",
        "cpp_test_harness": """#include <iostream>
#include <vector>
#include <string>
#include <sstream>
#include <stack>
#include <algorithm>
using namespace std;

vector<string> parseVectorString(const string& s) {
    vector<string> res;
    string temp = s;
    temp.erase(remove(temp.begin(), temp.end(), '['), temp.end());
    temp.erase(remove(temp.begin(), temp.end(), ']'), temp.end());
    stringstream ss(temp);
    string item;
    while(getline(ss, item, ',')) {
        if(!item.empty()) {
            item.erase(remove(item.begin(), item.end(), '\"'), item.end());
            item.erase(remove(item.begin(), item.end(), '\\''), item.end());
            item.erase(remove(item.begin(), item.end(), ' '), item.end());
            res.push_back(item);
        }
    }
    return res;
}

{{user_code}}

int main() {
    string tokens_line;
    if (!getline(cin >> ws, tokens_line)) return 0;
    vector<string> tokens = parseVectorString(tokens_line);
    Solution sol;
    int res = sol.evalRPN(tokens);
    cout << res << endl;
    return 0;
}""",
        "test_cases": {
            "function_name": "evalRPN",
            "params": [{"name": "tokens", "type": "string[]"}],
            "return_type": "int",
            "comparison": "exact",
            "cases": [
                {"args": {"tokens": ["2", "1", "+", "3", "*"]}, "expected": 9},
                {"args": {"tokens": ["4", "13", "5", "/", "+"]}, "expected": 6},
                {"args": {"tokens": ["10", "6", "9", "3", "+", "-11", "*", "/", "*", "17", "+", "5", "+"]}, "expected": 22},
                {"args": {"tokens": ["18"]}, "expected": 18}
            ]
        },
        "hints": [
            "Use a stack: push numbers, pop two numbers on operators, evaluate, and push result."
        ],
        "optimal_time_complexity": "O(N)",
        "optimal_space_complexity": "O(N)",
        "tags": ["Array", "Math", "Stack"],
        "solution_func": sol_eval_rpn
    },
    {
        "title": "Daily Temperatures",
        "category": "Stack",
        "difficulty": "Medium",
        "function_name": "dailyTemperatures",
        "description": """Given an array of integers `temperatures` represents the daily temperatures, return *an array* `answer` *such that* `answer[i]` *is the number of days you have to wait after the* `i`th *day to get a warmer temperature*. If there is no future day for which this is possible, keep `answer[i] == 0` instead.

## Examples

**Example 1:**
- **Input:** `temperatures = [73,74,75,71,69,72,76,73]`
- **Output:** `[1,1,4,2,1,1,0,0]`

**Example 2:**
- **Input:** `temperatures = [30,40,50,60]`
- **Output:** `[1,1,1,0]`

**Example 3:**
- **Input:** `temperatures = [30,60,90]`
- **Output:** `[1,1,0]`

## Constraints
- `1 <= temperatures.length <= 10^5`
- `30 <= temperatures[i] <= 100`""",
        "python_starter_code": """class Solution:
    def dailyTemperatures(self, temperatures: List[int]) -> List[int]:
        # Implement your solution here
        pass""",
        "cpp_starter_code": """class Solution {
public:
    vector<int> dailyTemperatures(vector<int>& temperatures) {
        // Implement your solution here
        return {};
    }
};""",
        "cpp_test_harness": cpp_vector_int_harness("""    string temps_str;
    if (!getline(cin >> ws, temps_str)) return 0;
    vector<int> temperatures = parseVectorInt(temps_str);
    Solution sol;
    vector<int> res = sol.dailyTemperatures(temperatures);
    cout << "[";
    for(size_t i = 0; i < res.size(); ++i) {
        cout << res[i] << (i == res.size() - 1 ? "" : ",");
    }
    cout << "]" << endl;"""),
        "test_cases": {
            "function_name": "dailyTemperatures",
            "params": [{"name": "temperatures", "type": "int[]"}],
            "return_type": "int[]",
            "comparison": "exact",
            "cases": [
                {"args": {"temperatures": [73, 74, 75, 71, 69, 72, 76, 73]}, "expected": [1, 1, 4, 2, 1, 1, 0, 0]},
                {"args": {"temperatures": [30, 40, 50, 60]}, "expected": [1, 1, 1, 0]},
                {"args": {"temperatures": [30, 60, 90]}, "expected": [1, 1, 0]},
                {"args": {"temperatures": [90]}, "expected": [0]}
            ]
        },
        "hints": [
            "Use a monotonic decreasing stack storing pairs of (temperature, index)."
        ],
        "optimal_time_complexity": "O(N)",
        "optimal_space_complexity": "O(N)",
        "tags": ["Array", "Stack", "Monotonic Stack"],
        "solution_func": sol_daily_temperatures
    },
    {
        "title": "Binary Search",
        "category": "Binary Search",
        "difficulty": "Easy",
        "function_name": "search",
        "description": """Given an array of integers `nums` which is sorted in ascending order, and an integer `target`, write a function to search `target` in `nums`. If `target` exists, then return its index. Otherwise, return `-1`.

## Examples

**Example 1:**
- **Input:** `nums = [-1,0,3,5,9,12]`, `target = 9`
- **Output:** `4`

**Example 2:**
- **Input:** `nums = [-1,0,3,5,9,12]`, `target = 2`
- **Output:** `-1`

## Constraints
- `1 <= nums.length <= 10^4`
- All the integers in `nums` are **unique**.""",
        "python_starter_code": """class Solution:
    def search(self, nums: List[int], target: int) -> int:
        # Implement your solution here
        pass""",
        "cpp_starter_code": """class Solution {
public:
    int search(vector<int>& nums, int target) {
        // Implement your solution here
        return -1;
    }
};""",
        "cpp_test_harness": cpp_vector_int_harness("""    string nums_str;
    if (!getline(cin >> ws, nums_str)) return 0;
    vector<int> nums = parseVectorInt(nums_str);
    int target;
    if (!(cin >> target)) return 0;
    Solution sol;
    int res = sol.search(nums, target);
    cout << res << endl;"""),
        "test_cases": {
            "function_name": "search",
            "params": [{"name": "nums", "type": "int[]"}, {"name": "target", "type": "int"}],
            "return_type": "int",
            "comparison": "exact",
            "cases": [
                {"args": {"nums": [-1, 0, 3, 5, 9, 12], "target": 9}, "expected": 4},
                {"args": {"nums": [-1, 0, 3, 5, 9, 12], "target": 2}, "expected": -1},
                {"args": {"nums": [5], "target": 5}, "expected": 0},
                {"args": {"nums": [5], "target": -5}, "expected": -1}
            ]
        },
        "hints": [
            "Use two pointers `left` and `right`, comparing `nums[mid]` against `target`."
        ],
        "optimal_time_complexity": "O(log N)",
        "optimal_space_complexity": "O(1)",
        "tags": ["Array", "Binary Search"],
        "solution_func": sol_binary_search
    },
    {
        "title": "Find Minimum in Rotated Sorted Array",
        "category": "Binary Search",
        "difficulty": "Medium",
        "function_name": "findMin",
        "description": """Suppose an array of length `n` sorted in ascending order is rotated between `1` and `n` times.

Given the sorted rotated array `nums` of **unique** elements, return *the minimum element of this array*.

You must write an algorithm that runs in `O(log n)` time.

## Examples

**Example 1:**
- **Input:** `nums = [3,4,5,1,2]`
- **Output:** `1`

**Example 2:**
- **Input:** `nums = [4,5,6,7,0,1,2]`
- **Output:** `0`

**Example 3:**
- **Input:** `nums = [11,13,15,17]`
- **Output:** `11`

## Constraints
- `n == nums.length`
- `1 <= n <= 5000`
- All values are **unique**.""",
        "python_starter_code": """class Solution:
    def findMin(self, nums: List[int]) -> int:
        # Implement your solution here
        pass""",
        "cpp_starter_code": """class Solution {
public:
    int findMin(vector<int>& nums) {
        // Implement your solution here
        return 0;
    }
};""",
        "cpp_test_harness": cpp_vector_int_harness("""    string nums_str;
    if (!getline(cin >> ws, nums_str)) return 0;
    vector<int> nums = parseVectorInt(nums_str);
    Solution sol;
    int res = sol.findMin(nums);
    cout << res << endl;"""),
        "test_cases": {
            "function_name": "findMin",
            "params": [{"name": "nums", "type": "int[]"}],
            "return_type": "int",
            "comparison": "exact",
            "cases": [
                {"args": {"nums": [3, 4, 5, 1, 2]}, "expected": 1},
                {"args": {"nums": [4, 5, 6, 7, 0, 1, 2]}, "expected": 0},
                {"args": {"nums": [11, 13, 15, 17]}, "expected": 11},
                {"args": {"nums": [2, 1]}, "expected": 1},
                {"args": {"nums": [1]}, "expected": 1}
            ]
        },
        "hints": [
            "Compare `nums[mid]` with `nums[right]`. If `nums[mid] > nums[right]`, the minimum is in the right half."
        ],
        "optimal_time_complexity": "O(log N)",
        "optimal_space_complexity": "O(1)",
        "tags": ["Array", "Binary Search"],
        "solution_func": sol_find_min_rotated
    },
    {
        "title": "Search in Rotated Sorted Array",
        "category": "Binary Search",
        "difficulty": "Medium",
        "function_name": "search",
        "description": """Given the array `nums` after a possible rotation and an integer `target`, return *the index of* `target` *if it is in* `nums`*, or* `-1` *if it is not in* `nums`.

You must write an algorithm with `O(log n)` runtime complexity.

## Examples

**Example 1:**
- **Input:** `nums = [4,5,6,7,0,1,2]`, `target = 0`
- **Output:** `4`

**Example 2:**
- **Input:** `nums = [4,5,6,7,0,1,2]`, `target = 3`
- **Output:** `-1`

**Example 3:**
- **Input:** `nums = [1]`, `target = 0`
- **Output:** `-1`

## Constraints
- `1 <= nums.length <= 5000`
- All values of `nums` are **unique**.""",
        "python_starter_code": """class Solution:
    def search(self, nums: List[int], target: int) -> int:
        # Implement your solution here
        pass""",
        "cpp_starter_code": """class Solution {
public:
    int search(vector<int>& nums, int target) {
        // Implement your solution here
        return -1;
    }
};""",
        "cpp_test_harness": cpp_vector_int_harness("""    string nums_str;
    if (!getline(cin >> ws, nums_str)) return 0;
    vector<int> nums = parseVectorInt(nums_str);
    int target;
    if (!(cin >> target)) return 0;
    Solution sol;
    int res = sol.search(nums, target);
    cout << res << endl;"""),
        "test_cases": {
            "function_name": "search",
            "params": [{"name": "nums", "type": "int[]"}, {"name": "target", "type": "int"}],
            "return_type": "int",
            "comparison": "exact",
            "cases": [
                {"args": {"nums": [4, 5, 6, 7, 0, 1, 2], "target": 0}, "expected": 4},
                {"args": {"nums": [4, 5, 6, 7, 0, 1, 2], "target": 3}, "expected": -1},
                {"args": {"nums": [1], "target": 0}, "expected": -1},
                {"args": {"nums": [1, 3], "target": 3}, "expected": 1},
                {"args": {"nums": [5, 1, 3], "target": 5}, "expected": 0}
            ]
        },
        "hints": [
            "Check which half of the array `[l, mid]` or `[mid, r]` is sorted."
        ],
        "optimal_time_complexity": "O(log N)",
        "optimal_space_complexity": "O(1)",
        "tags": ["Array", "Binary Search"],
        "solution_func": sol_search_rotated
    },
    {
        "title": "Merge Intervals",
        "category": "Intervals",
        "difficulty": "Medium",
        "function_name": "merge",
        "description": """Given an array of `intervals` where `intervals[i] = [start_i, end_i]`, merge all overlapping intervals, and return *an array of the non-overlapping intervals that cover all the intervals in the input*.

## Examples

**Example 1:**
- **Input:** `intervals = [[1,3],[2,6],[8,10],[15,18]]`
- **Output:** `[[1,6],[8,10],[15,18]]`

**Example 2:**
- **Input:** `intervals = [[1,4],[4,5]]`
- **Output:** `[[1,5]]`

## Constraints
- `1 <= intervals.length <= 10^4`
- `intervals[i].length == 2`""",
        "python_starter_code": """class Solution:
    def merge(self, intervals: List[List[int]]) -> List[List[int]]:
        # Implement your solution here
        pass""",
        "cpp_starter_code": """class Solution {
public:
    vector<vector<int>> merge(vector<vector<int>>& intervals) {
        // Implement your solution here
        return {};
    }
};""",
        "cpp_test_harness": """#include <iostream>
#include <vector>
#include <string>
#include <sstream>
#include <algorithm>
using namespace std;

vector<vector<int>> parseVectorVectorInt(const string& s) {
    vector<vector<int>> res;
    size_t i = 0;
    while (i < s.size()) {
        if (s[i] == '[') {
            size_t end = s.find(']', i);
            if (end != string::npos) {
                string sub = s.substr(i + 1, end - i - 1);
                if (!sub.empty() && sub.find('[') == string::npos) {
                    vector<int> row;
                    stringstream ss(sub);
                    string item;
                    while (getline(ss, item, ',')) {
                        if (!item.empty()) row.push_back(stoi(item));
                    }
                    if(!row.empty()) res.push_back(row);
                }
            }
        }
        i++;
    }
    return res;
}

{{user_code}}

int main() {
    string intervals_str;
    if (!getline(cin >> ws, intervals_str)) return 0;
    vector<vector<int>> intervals = parseVectorVectorInt(intervals_str);
    Solution sol;
    vector<vector<int>> res = sol.merge(intervals);
    cout << "[";
    for (size_t i = 0; i < res.size(); ++i) {
        cout << "[";
        for (size_t j = 0; j < res[i].size(); ++j) {
            cout << res[i][j] << (j == res[i].size() - 1 ? "" : ",");
        }
        cout << "]" << (i == res.size() - 1 ? "" : ",");
    }
    cout << "]" << endl;
    return 0;
}""",
        "test_cases": {
            "function_name": "merge",
            "params": [{"name": "intervals", "type": "int[][]"}],
            "return_type": "int[][]",
            "comparison": "exact",
            "cases": [
                {"args": {"intervals": [[1, 3], [2, 6], [8, 10], [15, 18]]}, "expected": [[1, 6], [8, 10], [15, 18]]},
                {"args": {"intervals": [[1, 4], [4, 5]]}, "expected": [[1, 5]]},
                {"args": {"intervals": [[1, 4], [0, 4]]}, "expected": [[0, 4]]},
                {"args": {"intervals": [[1, 4], [2, 3]]}, "expected": [[1, 4]]},
                {"args": {"intervals": [[1, 10], [2, 3], [4, 5], [6, 7], [8, 9]]}, "expected": [[1, 10]]}
            ]
        },
        "hints": [
            "Sort intervals by start time, then merge consecutively overlapping intervals."
        ],
        "optimal_time_complexity": "O(N log N)",
        "optimal_space_complexity": "O(N)",
        "tags": ["Array", "Sorting"],
        "solution_func": sol_merge_intervals
    },
    {
        "title": "Insert Interval",
        "category": "Intervals",
        "difficulty": "Medium",
        "function_name": "insert",
        "description": """You are given an array of non-overlapping intervals `intervals` where `intervals[i] = [start_i, end_i]` sorted in ascending order by `start_i`. You are also given an interval `newInterval = [start, end]`.

Insert `newInterval` into `intervals` such that `intervals` is still sorted and non-overlapping.

## Examples

**Example 1:**
- **Input:** `intervals = [[1,3],[6,9]]`, `newInterval = [2,5]`
- **Output:** `[[1,5],[6,9]]`

**Example 2:**
- **Input:** `intervals = [[1,2],[3,5],[6,7],[8,10],[12,16]]`, `newInterval = [4,8]`
- **Output:** `[[1,2],[3,10],[12,16]]`

## Constraints
- `0 <= intervals.length <= 10^4`
- `intervals[i].length == 2`""",
        "python_starter_code": """class Solution:
    def insert(self, intervals: List[List[int]], newInterval: List[int]) -> List[List[int]]:
        # Implement your solution here
        pass""",
        "cpp_starter_code": """class Solution {
public:
    vector<vector<int>> insert(vector<vector<int>>& intervals, vector<int>& newInterval) {
        // Implement your solution here
        return {};
    }
};""",
        "cpp_test_harness": """#include <iostream>
#include <vector>
#include <string>
#include <sstream>
#include <algorithm>
using namespace std;

vector<vector<int>> parseVectorVectorInt(const string& s) {
    vector<vector<int>> res;
    size_t i = 0;
    while (i < s.size()) {
        if (s[i] == '[') {
            size_t end = s.find(']', i);
            if (end != string::npos) {
                string sub = s.substr(i + 1, end - i - 1);
                if (!sub.empty() && sub.find('[') == string::npos) {
                    vector<int> row;
                    stringstream ss(sub);
                    string item;
                    while (getline(ss, item, ',')) {
                        if (!item.empty()) row.push_back(stoi(item));
                    }
                    if(!row.empty()) res.push_back(row);
                }
            }
        }
        i++;
    }
    return res;
}

vector<int> parseVectorInt(const string& s) {
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

{{user_code}}

int main() {
    string intervals_str, new_str;
    if (!getline(cin >> ws, intervals_str)) return 0;
    if (!getline(cin >> ws, new_str)) return 0;
    vector<vector<int>> intervals = parseVectorVectorInt(intervals_str);
    vector<int> newInterval = parseVectorInt(new_str);
    Solution sol;
    vector<vector<int>> res = sol.insert(intervals, newInterval);
    cout << "[";
    for (size_t i = 0; i < res.size(); ++i) {
        cout << "[";
        for (size_t j = 0; j < res[i].size(); ++j) {
            cout << res[i][j] << (j == res[i].size() - 1 ? "" : ",");
        }
        cout << "]" << (i == res.size() - 1 ? "" : ",");
    }
    cout << "]" << endl;
    return 0;
}""",
        "test_cases": {
            "function_name": "insert",
            "params": [{"name": "intervals", "type": "int[][]"}, {"name": "newInterval", "type": "int[]"}],
            "return_type": "int[][]",
            "comparison": "exact",
            "cases": [
                {"args": {"intervals": [[1, 3], [6, 9]], "newInterval": [2, 5]}, "expected": [[1, 5], [6, 9]]},
                {"args": {"intervals": [[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]], "newInterval": [4, 8]}, "expected": [[1, 2], [3, 10], [12, 16]]},
                {"args": {"intervals": [], "newInterval": [5, 7]}, "expected": [[5, 7]]},
                {"args": {"intervals": [[1, 5]], "newInterval": [2, 3]}, "expected": [[1, 5]]},
                {"args": {"intervals": [[1, 5]], "newInterval": [2, 7]}, "expected": [[1, 7]]}
            ]
        },
        "hints": [
            "Add all intervals ending before newInterval starts.",
            "Merge all overlapping intervals with newInterval, then append the rest."
        ],
        "optimal_time_complexity": "O(N)",
        "optimal_space_complexity": "O(N)",
        "tags": ["Array"],
        "solution_func": sol_insert_interval
    },
    {
        "title": "Climbing Stairs",
        "category": "1-D Dynamic Programming",
        "difficulty": "Easy",
        "function_name": "climbStairs",
        "description": """You are climbing a staircase. It takes `n` steps to reach the top.

Each time you can either climb `1` or `2` steps. In how many distinct ways can you climb to the top?

## Examples

**Example 1:**
- **Input:** `n = 2`
- **Output:** `2`

**Example 2:**
- **Input:** `n = 3`
- **Output:** `3`

## Constraints
- `1 <= n <= 45`""",
        "python_starter_code": """class Solution:
    def climbStairs(self, n: int) -> int:
        # Implement your solution here
        pass""",
        "cpp_starter_code": """class Solution {
public:
    int climbStairs(int n) {
        // Implement your solution here
        return 0;
    }
};""",
        "cpp_test_harness": """#include <iostream>
using namespace std;

{{user_code}}

int main() {
    int n;
    if (!(cin >> n)) return 0;
    Solution sol;
    int res = sol.climbStairs(n);
    cout << res << endl;
    return 0;
}""",
        "test_cases": {
            "function_name": "climbStairs",
            "params": [{"name": "n", "type": "int"}],
            "return_type": "int",
            "comparison": "exact",
            "cases": [
                {"args": {"n": 1}, "expected": 1},
                {"args": {"n": 2}, "expected": 2},
                {"args": {"n": 3}, "expected": 3},
                {"args": {"n": 4}, "expected": 5},
                {"args": {"n": 5}, "expected": 8},
                {"args": {"n": 10}, "expected": 89},
                {"args": {"n": 20}, "expected": 10946}
            ]
        },
        "hints": [
            "Use Fibonacci recurrence: `dp[n] = dp[n-1] + dp[n-2]`."
        ],
        "optimal_time_complexity": "O(N)",
        "optimal_space_complexity": "O(1)",
        "tags": ["Math", "Dynamic Programming", "Memoization"],
        "solution_func": sol_climbing_stairs
    },
    {
        "title": "House Robber",
        "category": "1-D Dynamic Programming",
        "difficulty": "Medium",
        "function_name": "rob",
        "description": """You are a professional robber planning to rob houses along a street. Each house has a certain amount of money stashed. Adjacent houses have security systems connected, which will automatically contact the police if two adjacent houses were broken into on the same night.

Given an integer array `nums` representing the amount of money of each house, return *the maximum amount of money you can rob tonight without alerting the police*.

## Examples

**Example 1:**
- **Input:** `nums = [1,2,3,1]`
- **Output:** `4`

**Example 2:**
- **Input:** `nums = [2,7,9,3,1]`
- **Output:** `12`

## Constraints
- `1 <= nums.length <= 100`
- `0 <= nums[i] <= 400`""",
        "python_starter_code": """class Solution:
    def rob(self, nums: List[int]) -> int:
        # Implement your solution here
        pass""",
        "cpp_starter_code": """class Solution {
public:
    int rob(vector<int>& nums) {
        // Implement your solution here
        return 0;
    }
};""",
        "cpp_test_harness": cpp_vector_int_harness("""    string nums_str;
    if (!getline(cin >> ws, nums_str)) return 0;
    vector<int> nums = parseVectorInt(nums_str);
    Solution sol;
    int res = sol.rob(nums);
    cout << res << endl;"""),
        "test_cases": {
            "function_name": "rob",
            "params": [{"name": "nums", "type": "int[]"}],
            "return_type": "int",
            "comparison": "exact",
            "cases": [
                {"args": {"nums": [1, 2, 3, 1]}, "expected": 4},
                {"args": {"nums": [2, 7, 9, 3, 1]}, "expected": 12},
                {"args": {"nums": [0]}, "expected": 0},
                {"args": {"nums": [2, 1, 1, 2]}, "expected": 4}
            ]
        },
        "hints": [
            "At house i, choose `max(rob[i-1], rob[i-2] + nums[i])`."
        ],
        "optimal_time_complexity": "O(N)",
        "optimal_space_complexity": "O(1)",
        "tags": ["Array", "Dynamic Programming"],
        "solution_func": sol_house_robber
    },
    {
        "title": "Coin Change",
        "category": "1-D Dynamic Programming",
        "difficulty": "Medium",
        "function_name": "coinChange",
        "description": """You are given an integer array `coins` representing coins of different denominations and an integer `amount` representing a total amount of money.

Return *the fewest number of coins that you need to make up that amount*. If that amount cannot be made up, return `-1`.

## Examples

**Example 1:**
- **Input:** `coins = [1,2,5]`, `amount = 11`
- **Output:** `3`

**Example 2:**
- **Input:** `coins = [2]`, `amount = 3`
- **Output:** `-1`

**Example 3:**
- **Input:** `coins = [1]`, `amount = 0`
- **Output:** `0`

## Constraints
- `1 <= coins.length <= 12`
- `0 <= amount <= 10^4`""",
        "python_starter_code": """class Solution:
    def coinChange(self, coins: List[int], amount: int) -> int:
        # Implement your solution here
        pass""",
        "cpp_starter_code": """class Solution {
public:
    int coinChange(vector<int>& coins, int amount) {
        // Implement your solution here
        return -1;
    }
};""",
        "cpp_test_harness": cpp_vector_int_harness("""    string coins_str;
    if (!getline(cin >> ws, coins_str)) return 0;
    vector<int> coins = parseVectorInt(coins_str);
    int amount;
    if (!(cin >> amount)) return 0;
    Solution sol;
    int res = sol.coinChange(coins, amount);
    cout << res << endl;"""),
        "test_cases": {
            "function_name": "coinChange",
            "params": [{"name": "coins", "type": "int[]"}, {"name": "amount", "type": "int"}],
            "return_type": "int",
            "comparison": "exact",
            "cases": [
                {"args": {"coins": [1, 2, 5], "amount": 11}, "expected": 3},
                {"args": {"coins": [2], "amount": 3}, "expected": -1},
                {"args": {"coins": [1], "amount": 0}, "expected": 0},
                {"args": {"coins": [1], "amount": 1}, "expected": 1},
                {"args": {"coins": [1], "amount": 2}, "expected": 2}
            ]
        },
        "hints": [
            "Use bottom-up DP: `dp[i] = min(dp[i], dp[i - c] + 1)` for each coin `c`."
        ],
        "optimal_time_complexity": "O(amount * len(coins))",
        "optimal_space_complexity": "O(amount)",
        "tags": ["Array", "Dynamic Programming"],
        "solution_func": sol_coin_change
    },
    {
        "title": "Unique Paths",
        "category": "2-D Dynamic Programming",
        "difficulty": "Medium",
        "function_name": "uniquePaths",
        "description": """There is a robot on an `m x n` grid. The robot is initially located at the **top-left corner** (`grid[0][0]`). The robot tries to move to the **bottom-right corner** (`grid[m - 1][n - 1]`). The robot can only move either down or right at any point in time.

Given the two integers `m` and `n`, return *the number of possible unique paths that the robot can take to reach the bottom-right corner*.

## Examples

**Example 1:**
- **Input:** `m = 3, n = 7`
- **Output:** `28`

**Example 2:**
- **Input:** `m = 3, n = 2`
- **Output:** `3`

## Constraints
- `1 <= m, n <= 100`""",
        "python_starter_code": """class Solution:
    def uniquePaths(self, m: int, n: int) -> int:
        # Implement your solution here
        pass""",
        "cpp_starter_code": """class Solution {
public:
    int uniquePaths(int m, int n) {
        // Implement your solution here
        return 0;
    }
};""",
        "cpp_test_harness": """#include <iostream>
using namespace std;

{{user_code}}

int main() {
    int m, n;
    if (!(cin >> m >> n)) return 0;
    Solution sol;
    int res = sol.uniquePaths(m, n);
    cout << res << endl;
    return 0;
}""",
        "test_cases": {
            "function_name": "uniquePaths",
            "params": [{"name": "m", "type": "int"}, {"name": "n", "type": "int"}],
            "return_type": "int",
            "comparison": "exact",
            "cases": [
                {"args": {"m": 3, "n": 7}, "expected": 28},
                {"args": {"m": 3, "n": 2}, "expected": 3},
                {"args": {"m": 1, "n": 1}, "expected": 1},
                {"args": {"m": 7, "n": 3}, "expected": 28}
            ]
        },
        "hints": [
            "`dp[i][j] = dp[i-1][j] + dp[i][j-1]`."
        ],
        "optimal_time_complexity": "O(M * N)",
        "optimal_space_complexity": "O(N)",
        "tags": ["Math", "Dynamic Programming", "Combinatorics"],
        "solution_func": sol_unique_paths
    },
    {
        "title": "Maximum Subarray",
        "category": "Greedy",
        "difficulty": "Medium",
        "function_name": "maxSubArray",
        "description": """Given an integer array `nums`, find the subarray with the largest sum, and return *its sum*.

## Examples

**Example 1:**
- **Input:** `nums = [-2,1,-3,4,-1,2,1,-5,4]`
- **Output:** `6`

**Example 2:**
- **Input:** `nums = [1]`
- **Output:** `1`

**Example 3:**
- **Input:** `nums = [5,4,-1,7,8]`
- **Output:** `23`

## Constraints
- `1 <= nums.length <= 10^5`
- `-10^4 <= nums[i] <= 10^4`""",
        "python_starter_code": """class Solution:
    def maxSubArray(self, nums: List[int]) -> int:
        # Implement your solution here
        pass""",
        "cpp_starter_code": """class Solution {
public:
    int maxSubArray(vector<int>& nums) {
        // Implement your solution here
        return 0;
    }
};""",
        "cpp_test_harness": cpp_vector_int_harness("""    string nums_str;
    if (!getline(cin >> ws, nums_str)) return 0;
    vector<int> nums = parseVectorInt(nums_str);
    Solution sol;
    int res = sol.maxSubArray(nums);
    cout << res << endl;"""),
        "test_cases": {
            "function_name": "maxSubArray",
            "params": [{"name": "nums", "type": "int[]"}],
            "return_type": "int",
            "comparison": "exact",
            "cases": [
                {"args": {"nums": [-2, 1, -3, 4, -1, 2, 1, -5, 4]}, "expected": 6},
                {"args": {"nums": [1]}, "expected": 1},
                {"args": {"nums": [5, 4, -1, 7, 8]}, "expected": 23},
                {"args": {"nums": [-1]}, "expected": -1},
                {"args": {"nums": [-2, -1]}, "expected": -1}
            ]
        },
        "hints": [
            "Kadane's Algorithm: `cur_sum = max(x, cur_sum + x)`."
        ],
        "optimal_time_complexity": "O(N)",
        "optimal_space_complexity": "O(1)",
        "tags": ["Array", "Divide and Conquer", "Dynamic Programming"],
        "solution_func": sol_max_subarray
    },
    {
        "title": "Jump Game",
        "category": "Greedy",
        "difficulty": "Medium",
        "function_name": "canJump",
        "description": """You are given an integer array `nums`. You are initially positioned at the array's **first index**, and each element in the array represents your maximum jump length at that position.

Return `true` *if you can reach the last index, or* `false` *otherwise*.

## Examples

**Example 1:**
- **Input:** `nums = [2,3,1,1,4]`
- **Output:** `true`

**Example 2:**
- **Input:** `nums = [3,2,1,0,4]`
- **Output:** `false`

## Constraints
- `1 <= nums.length <= 10^4`""",
        "python_starter_code": """class Solution:
    def canJump(self, nums: List[int]) -> bool:
        # Implement your solution here
        pass""",
        "cpp_starter_code": """class Solution {
public:
    bool canJump(vector<int>& nums) {
        // Implement your solution here
        return false;
    }
};""",
        "cpp_test_harness": cpp_vector_int_harness("""    string nums_str;
    if (!getline(cin >> ws, nums_str)) return 0;
    vector<int> nums = parseVectorInt(nums_str);
    Solution sol;
    bool res = sol.canJump(nums);
    cout << (res ? "true" : "false") << endl;"""),
        "test_cases": {
            "function_name": "canJump",
            "params": [{"name": "nums", "type": "int[]"}],
            "return_type": "boolean",
            "comparison": "exact",
            "cases": [
                {"args": {"nums": [2, 3, 1, 1, 4]}, "expected": True},
                {"args": {"nums": [3, 2, 1, 0, 4]}, "expected": False},
                {"args": {"nums": [0]}, "expected": True},
                {"args": {"nums": [2, 0, 0]}, "expected": True},
                {"args": {"nums": [1, 0, 1, 0]}, "expected": False}
            ]
        },
        "hints": [
            "Track the max reachable index at every step."
        ],
        "optimal_time_complexity": "O(N)",
        "optimal_space_complexity": "O(1)",
        "tags": ["Array", "Dynamic Programming", "Greedy"],
        "solution_func": sol_jump_game
    },
    {
        "title": "Jump Game II",
        "category": "Greedy",
        "difficulty": "Medium",
        "function_name": "jump",
        "description": """You are given a **0-indexed** array of integers `nums` of length `n`. You are initially positioned at `nums[0]`.

Each element `nums[i]` represents the maximum length of a forward jump from index `i`.

Return *the minimum number of jumps to reach* `nums[n - 1]`.

## Examples

**Example 1:**
- **Input:** `nums = [2,3,1,1,4]`
- **Output:** `2`

**Example 2:**
- **Input:** `nums = [2,3,0,1,4]`
- **Output:** `2`

## Constraints
- `1 <= nums.length <= 10^4`""",
        "python_starter_code": """class Solution:
    def jump(self, nums: List[int]) -> int:
        # Implement your solution here
        pass""",
        "cpp_starter_code": """class Solution {
public:
    int jump(vector<int>& nums) {
        // Implement your solution here
        return 0;
    }
};""",
        "cpp_test_harness": cpp_vector_int_harness("""    string nums_str;
    if (!getline(cin >> ws, nums_str)) return 0;
    vector<int> nums = parseVectorInt(nums_str);
    Solution sol;
    int res = sol.jump(nums);
    cout << res << endl;"""),
        "test_cases": {
            "function_name": "jump",
            "params": [{"name": "nums", "type": "int[]"}],
            "return_type": "int",
            "comparison": "exact",
            "cases": [
                {"args": {"nums": [2, 3, 1, 1, 4]}, "expected": 2},
                {"args": {"nums": [2, 3, 0, 1, 4]}, "expected": 2},
                {"args": {"nums": [0]}, "expected": 0},
                {"args": {"nums": [1, 2, 3]}, "expected": 2}
            ]
        },
        "hints": [
            "Use BFS / Greedy window: whenever `i == cur_end`, increment jumps and update `cur_end = cur_farthest`."
        ],
        "optimal_time_complexity": "O(N)",
        "optimal_space_complexity": "O(1)",
        "tags": ["Array", "Dynamic Programming", "Greedy"],
        "solution_func": sol_jump_game_ii
    },
    {
        "title": "Rotate Image",
        "category": "Math & Geometry",
        "difficulty": "Medium",
        "function_name": "rotate",
        "description": """You are given an `n x n` 2D `matrix` representing an image, rotate the image by **90 degrees (clockwise)** in-place.

## Examples

**Example 1:**
- **Input:** `matrix = [[1,2,3],[4,5,6],[7,8,9]]`
- **Output:** `[[7,4,1],[8,5,2],[9,6,3]]`

**Example 2:**
- **Input:** `matrix = [[5,1,9,11],[2,4,8,10],[13,3,6,7],[15,14,12,16]]`
- **Output:** `[[15,13,2,5],[14,3,4,1],[12,6,8,9],[16,7,10,11]]`

## Constraints
- `n == matrix.length == matrix[i].length`
- `1 <= n <= 20`""",
        "python_starter_code": """class Solution:
    def rotate(self, matrix: List[List[int]]) -> None:
        # Modify matrix in-place instead.
        pass""",
        "cpp_starter_code": """class Solution {
public:
    void rotate(vector<vector<int>>& matrix) {
        // Modify matrix in-place instead.
    }
};""",
        "cpp_test_harness": """#include <iostream>
#include <vector>
#include <string>
#include <sstream>
#include <algorithm>
using namespace std;

vector<vector<int>> parseVectorVectorInt(const string& s) {
    vector<vector<int>> res;
    size_t i = 0;
    while (i < s.size()) {
        if (s[i] == '[') {
            size_t end = s.find(']', i);
            if (end != string::npos) {
                string sub = s.substr(i + 1, end - i - 1);
                if (!sub.empty() && sub.find('[') == string::npos) {
                    vector<int> row;
                    stringstream ss(sub);
                    string item;
                    while (getline(ss, item, ',')) {
                        if (!item.empty()) row.push_back(stoi(item));
                    }
                    if(!row.empty()) res.push_back(row);
                }
            }
        }
        i++;
    }
    return res;
}

{{user_code}}

int main() {
    string matrix_str;
    if (!getline(cin >> ws, matrix_str)) return 0;
    vector<vector<int>> matrix = parseVectorVectorInt(matrix_str);
    Solution sol;
    sol.rotate(matrix);
    cout << "[";
    for (size_t i = 0; i < matrix.size(); ++i) {
        cout << "[";
        for (size_t j = 0; j < matrix[i].size(); ++j) {
            cout << matrix[i][j] << (j == matrix[i].size() - 1 ? "" : ",");
        }
        cout << "]" << (i == matrix.size() - 1 ? "" : ",");
    }
    cout << "]" << endl;
    return 0;
}""",
        "test_cases": {
            "function_name": "rotate",
            "params": [{"name": "matrix", "type": "int[][]"}],
            "return_type": "void",
            "comparison": "exact",
            "cases": [
                {"args": {"matrix": [[1, 2, 3], [4, 5, 6], [7, 8, 9]]}, "expected": [[7, 4, 1], [8, 5, 2], [9, 6, 3]]},
                {"args": {"matrix": [[5, 1, 9, 11], [2, 4, 8, 10], [13, 3, 6, 7], [15, 14, 12, 16]]}, "expected": [[15, 13, 2, 5], [14, 3, 4, 1], [12, 6, 8, 9], [16, 7, 10, 11]]},
                {"args": {"matrix": [[1]]}, "expected": [[1]]},
                {"args": {"matrix": [[1, 2], [3, 4]]}, "expected": [[3, 1], [4, 2]]}
            ]
        },
        "hints": [
            "Transpose the matrix, then reverse each row."
        ],
        "optimal_time_complexity": "O(N^2)",
        "optimal_space_complexity": "O(1)",
        "tags": ["Array", "Math", "Matrix"],
        "solution_func": sol_rotate_image
    },
    {
        "title": "Spiral Matrix",
        "category": "Math & Geometry",
        "difficulty": "Medium",
        "function_name": "spiralOrder",
        "description": """Given an `m x n` `matrix`, return *all elements of the* `matrix` *in spiral order*.

## Examples

**Example 1:**
- **Input:** `matrix = [[1,2,3],[4,5,6],[7,8,9]]`
- **Output:** `[1,2,3,6,9,8,7,4,5]`

**Example 2:**
- **Input:** `matrix = [[1,2,3,4],[5,6,7,8],[9,10,11,12]]`
- **Output:** `[1,2,3,4,8,12,11,10,9,5,6,7]`

## Constraints
- `1 <= m, n <= 10`""",
        "python_starter_code": """class Solution:
    def spiralOrder(self, matrix: List[List[int]]) -> List[int]:
        # Implement your solution here
        pass""",
        "cpp_starter_code": """class Solution {
public:
    vector<int> spiralOrder(vector<vector<int>>& matrix) {
        // Implement your solution here
        return {};
    }
};""",
        "cpp_test_harness": """#include <iostream>
#include <vector>
#include <string>
#include <sstream>
#include <algorithm>
using namespace std;

vector<vector<int>> parseVectorVectorInt(const string& s) {
    vector<vector<int>> res;
    size_t i = 0;
    while (i < s.size()) {
        if (s[i] == '[') {
            size_t end = s.find(']', i);
            if (end != string::npos) {
                string sub = s.substr(i + 1, end - i - 1);
                if (!sub.empty() && sub.find('[') == string::npos) {
                    vector<int> row;
                    stringstream ss(sub);
                    string item;
                    while (getline(ss, item, ',')) {
                        if (!item.empty()) row.push_back(stoi(item));
                    }
                    if(!row.empty()) res.push_back(row);
                }
            }
        }
        i++;
    }
    return res;
}

{{user_code}}

int main() {
    string matrix_str;
    if (!getline(cin >> ws, matrix_str)) return 0;
    vector<vector<int>> matrix = parseVectorVectorInt(matrix_str);
    Solution sol;
    vector<int> res = sol.spiralOrder(matrix);
    cout << "[";
    for (size_t i = 0; i < res.size(); ++i) {
        cout << res[i] << (i == res.size() - 1 ? "" : ",");
    }
    cout << "]" << endl;
    return 0;
}""",
        "test_cases": {
            "function_name": "spiralOrder",
            "params": [{"name": "matrix", "type": "int[][]"}],
            "return_type": "int[]",
            "comparison": "exact",
            "cases": [
                {"args": {"matrix": [[1, 2, 3], [4, 5, 6], [7, 8, 9]]}, "expected": [1, 2, 3, 6, 9, 8, 7, 4, 5]},
                {"args": {"matrix": [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]}, "expected": [1, 2, 3, 4, 8, 12, 11, 10, 9, 5, 6, 7]},
                {"args": {"matrix": [[7]]}, "expected": [7]},
                {"args": {"matrix": [[1, 2], [3, 4]]}, "expected": [1, 2, 4, 3]}
            ]
        },
        "hints": [
            "Maintain four boundaries (top, bottom, left, right) and shrink them sequentially."
        ],
        "optimal_time_complexity": "O(M * N)",
        "optimal_space_complexity": "O(1)",
        "tags": ["Array", "Matrix", "Simulation"],
        "solution_func": sol_spiral_matrix
    },
    {
        "title": "Single Number",
        "category": "Bit Manipulation",
        "difficulty": "Easy",
        "function_name": "singleNumber",
        "description": """Given a **non-empty** array of integers `nums`, every element appears *twice* except for one. Find that single one in linear time and O(1) space.

## Examples

**Example 1:**
- **Input:** `nums = [2,2,1]`
- **Output:** `1`

**Example 2:**
- **Input:** `nums = [4,1,2,1,2]`
- **Output:** `4`

## Constraints
- `1 <= nums.length <= 3 * 10^4`""",
        "python_starter_code": """class Solution:
    def singleNumber(self, nums: List[int]) -> int:
        # Implement your solution here
        pass""",
        "cpp_starter_code": """class Solution {
public:
    int singleNumber(vector<int>& nums) {
        // Implement your solution here
        return 0;
    }
};""",
        "cpp_test_harness": cpp_vector_int_harness("""    string nums_str;
    if (!getline(cin >> ws, nums_str)) return 0;
    vector<int> nums = parseVectorInt(nums_str);
    Solution sol;
    int res = sol.singleNumber(nums);
    cout << res << endl;"""),
        "test_cases": {
            "function_name": "singleNumber",
            "params": [{"name": "nums", "type": "int[]"}],
            "return_type": "int",
            "comparison": "exact",
            "cases": [
                {"args": {"nums": [2, 2, 1]}, "expected": 1},
                {"args": {"nums": [4, 1, 2, 1, 2]}, "expected": 4},
                {"args": {"nums": [1]}, "expected": 1},
                {"args": {"nums": [-1, -1, -2]}, "expected": -2}
            ]
        },
        "hints": [
            "XORing all elements together cancels duplicates: `x ^ x = 0`."
        ],
        "optimal_time_complexity": "O(N)",
        "optimal_space_complexity": "O(1)",
        "tags": ["Array", "Bit Manipulation"],
        "solution_func": sol_single_number
    },
    {
        "title": "Number of 1 Bits",
        "category": "Bit Manipulation",
        "difficulty": "Easy",
        "function_name": "hammingWeight",
        "description": """Given a positive integer `n`, write a function that returns the number of set bits it has (also known as the Hamming weight).

## Examples

**Example 1:**
- **Input:** `n = 11`
- **Output:** `3`

**Example 2:**
- **Input:** `n = 128`
- **Output:** `1`

## Constraints
- `1 <= n <= 2^31 - 1`""",
        "python_starter_code": """class Solution:
    def hammingWeight(self, n: int) -> int:
        # Implement your solution here
        pass""",
        "cpp_starter_code": """class Solution {
public:
    int hammingWeight(int n) {
        // Implement your solution here
        return 0;
    }
};""",
        "cpp_test_harness": """#include <iostream>
using namespace std;

{{user_code}}

int main() {
    int n;
    if (!(cin >> n)) return 0;
    Solution sol;
    int res = sol.hammingWeight(n);
    cout << res << endl;
    return 0;
}""",
        "test_cases": {
            "function_name": "hammingWeight",
            "params": [{"name": "n", "type": "int"}],
            "return_type": "int",
            "comparison": "exact",
            "cases": [
                {"args": {"n": 11}, "expected": 3},
                {"args": {"n": 128}, "expected": 1},
                {"args": {"n": 2147483645}, "expected": 30},
                {"args": {"n": 1}, "expected": 1},
                {"args": {"n": 0}, "expected": 0}
            ]
        },
        "hints": [
            "Use `n & (n - 1)` to clear the lowest set bit in each step."
        ],
        "optimal_time_complexity": "O(1)",
        "optimal_space_complexity": "O(1)",
        "tags": ["Divide and Conquer", "Bit Manipulation"],
        "solution_func": sol_number_of_1_bits
    },
    {
        "title": "Counting Bits",
        "category": "Bit Manipulation",
        "difficulty": "Easy",
        "function_name": "countBits",
        "description": """Given an integer `n`, return an array `ans` of length `n + 1` such that for each `i` (`0 <= i <= n`), `ans[i]` is the **number of** `1`**'s** in the binary representation of `i`.

## Examples

**Example 1:**
- **Input:** `n = 2`
- **Output:** `[0,1,1]`

**Example 2:**
- **Input:** `n = 5`
- **Output:** `[0,1,1,2,1,2]`

## Constraints
- `0 <= n <= 10^5`""",
        "python_starter_code": """class Solution:
    def countBits(self, n: int) -> List[int]:
        # Implement your solution here
        pass""",
        "cpp_starter_code": """class Solution {
public:
    vector<int> countBits(int n) {
        // Implement your solution here
        return {};
    }
};""",
        "cpp_test_harness": """#include <iostream>
#include <vector>
using namespace std;

{{user_code}}

int main() {
    int n;
    if (!(cin >> n)) return 0;
    Solution sol;
    vector<int> res = sol.countBits(n);
    cout << "[";
    for(size_t i = 0; i < res.size(); ++i) {
        cout << res[i] << (i == res.size() - 1 ? "" : ",");
    }
    cout << "]" << endl;
    return 0;
}""",
        "test_cases": {
            "function_name": "countBits",
            "params": [{"name": "n", "type": "int"}],
            "return_type": "int[]",
            "comparison": "exact",
            "cases": [
                {"args": {"n": 2}, "expected": [0, 1, 1]},
                {"args": {"n": 5}, "expected": [0, 1, 1, 2, 1, 2]},
                {"args": {"n": 0}, "expected": [0]},
                {"args": {"n": 1}, "expected": [0, 1]}
            ]
        },
        "hints": [
            "Use DP: `dp[i] = dp[i >> 1] + (i & 1)`."
        ],
        "optimal_time_complexity": "O(N)",
        "optimal_space_complexity": "O(1)",
        "tags": ["Dynamic Programming", "Bit Manipulation"],
        "solution_func": sol_counting_bits
    }
]

def main():
    logger.info(f"Starting verification of {len(QUESTIONS)} curated DSA questions...")
    
    verified_questions = []
    
    for q in QUESTIONS:
        title = q["title"]
        test_cases_dict = q["test_cases"]
        solution_func = q["solution_func"]
        comparison = test_cases_dict.get("comparison", "exact")
        
        try:
            verify_test_cases(solution_func, test_cases_dict["cases"], comparison=comparison)
            logger.info(f"✅ Verified: {title} ({len(test_cases_dict['cases'])} test cases passed)")
            
            record = {
                "title": q["title"],
                "description": q["description"],
                "difficulty": q["difficulty"],
                "function_name": q["function_name"],
                "python_starter_code": q["python_starter_code"],
                "cpp_starter_code": q["cpp_starter_code"],
                "cpp_test_harness": q["cpp_test_harness"],
                "test_cases": json.dumps(test_cases_dict),
                "hints": json.dumps(q["hints"]),
                "optimal_time_complexity": q["optimal_time_complexity"],
                "optimal_space_complexity": q["optimal_space_complexity"],
                "tags": q["tags"]
            }
            verified_questions.append(record)
        except Exception as e:
            logger.error(f"❌ Verification failed for {title}: {e}")
            raise

    output_path = os.path.join(os.path.dirname(__file__), "..", "canonical_dsa_questions.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(verified_questions, f, indent=2)
        
    logger.info(f"🎉 Successfully exported {len(verified_questions)} 100% verified DSA questions to canonical_dsa_questions.json")

if __name__ == "__main__":
    main()
