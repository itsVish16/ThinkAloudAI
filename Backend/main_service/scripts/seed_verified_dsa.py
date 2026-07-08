import asyncio
import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal, Base, engine
from app.models.dsa import DSAQuestion, CodeSubmission

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def seed_verified_problems():
    logger.info("Dropping all existing low-quality DSA questions and Code Submissions...")
    
    async with SessionLocal() as session:
        # Cascade manually by deleting submissions first
        await session.execute(delete(CodeSubmission))
        await session.execute(delete(DSAQuestion))
        
        # 1. Two Sum
        two_sum = DSAQuestion(
            title="Two Sum",
            description="""Given an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to `target`.

You may assume that each input would have exactly one solution, and you may not use the same element twice.

You can return the answer in any order.

**Example 1:**
- **Input:** `nums = [2,7,11,15]`, `target = 9`
- **Output:** `[0,1]`
- **Explanation:** Because nums[0] + nums[1] == 9, we return [0, 1].

**Example 2:**
- **Input:** `nums = [3,2,4]`, `target = 6`
- **Output:** `[1,2]`

**Constraints:**
- `2 <= nums.length <= 10^4`
- `-10^9 <= nums[i] <= 10^9`
- `-10^9 <= target <= 10^9`
- **Only one valid answer exists.**""",
            difficulty="Easy",
            function_name="twoSum",
            python_starter_code="""class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        # Write your code here
        pass
""",
            cpp_starter_code="""class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        // Write your code here
        return {};
    }
};
""",
            cpp_test_harness="""#include <iostream>
#include <vector>
#include <string>
#include <unordered_map>
#include <sstream>

using namespace std;

{{user_code}}

vector<int> parseVector(const string& s) {
    vector<int> res;
    string temp = s;
    temp.erase(remove(temp.begin(), temp.end(), '['), temp.end());
    temp.erase(remove(temp.begin(), temp.end(), ']'), temp.end());
    stringstream ss(temp);
    string item;
    while(getline(ss, item, ',')) {
        res.push_back(stoi(item));
    }
    return res;
}

int main(int argc, char* argv[]) {
    if (argc < 3) return 1;
    vector<int> nums = parseVector(argv[1]);
    int target = stoi(argv[2]);
    Solution sol;
    vector<int> res = sol.twoSum(nums, target);
    cout << "[";
    for(size_t i=0; i<res.size(); ++i) {
        cout << res[i] << (i==res.size()-1 ? "" : ", ");
    }
    cout << "]" << endl;
    return 0;
}
""",
            test_cases=json.dumps([
                {"input": "[2,7,11,15] 9", "output": "[0, 1]"},
                {"input": "[3,2,4] 6", "output": "[1, 2]"},
                {"input": "[3,3] 6", "output": "[0, 1]"}
            ]),
            hints=json.dumps([
                "A really brute force way would be to search for all possible pairs of numbers but that would be too slow.",
                "Can you use a hash map to keep track of the elements you have seen so far?"
            ]),
            optimal_time_complexity="O(N)",
            optimal_space_complexity="O(N)"
        )

        # 2. Valid Parentheses
        valid_parens = DSAQuestion(
            title="Valid Parentheses",
            description="""Given a string `s` containing just the characters `'('`, `')'`, `'{'`, `'}'`, `'['` and `']'`, determine if the input string is valid.

An input string is valid if:
1. Open brackets must be closed by the same type of brackets.
2. Open brackets must be closed in the correct order.
3. Every close bracket has a corresponding open bracket of the same type.

**Example 1:**
- **Input:** `s = "()"`
- **Output:** `true`

**Example 2:**
- **Input:** `s = "()[]{}"`
- **Output:** `true`

**Example 3:**
- **Input:** `s = "(]"`
- **Output:** `false`

**Constraints:**
- `1 <= s.length <= 10^4`
- `s` consists of parentheses only `'()[]{}'`.
""",
            difficulty="Easy",
            function_name="isValid",
            python_starter_code="""class Solution:
    def isValid(self, s: str) -> bool:
        # Write your code here
        pass
""",
            cpp_starter_code="""class Solution {
public:
    bool isValid(string s) {
        // Write your code here
        return false;
    }
};
""",
            cpp_test_harness="""#include <iostream>
#include <string>
#include <stack>
#include <unordered_map>

using namespace std;

{{user_code}}

int main(int argc, char* argv[]) {
    if (argc < 2) return 1;
    string s = argv[1];
    Solution sol;
    bool res = sol.isValid(s);
    cout << (res ? "true" : "false") << endl;
    return 0;
}
""",
            test_cases=json.dumps([
                {"input": "()", "output": "true"},
                {"input": "()[]{}", "output": "true"},
                {"input": "(]", "output": "false"},
                {"input": "([)]", "output": "false"},
                {"input": "{[]}", "output": "true"}
            ]),
            hints=json.dumps([
                "Use a stack data structure to keep track of open brackets.",
                "When you see a close bracket, check if it matches the top of the stack."
            ]),
            optimal_time_complexity="O(N)",
            optimal_space_complexity="O(N)"
        )

        # 3. Longest Substring Without Repeating Characters
        longest_sub = DSAQuestion(
            title="Longest Substring Without Repeating Characters",
            description="""Given a string `s`, find the length of the longest substring without repeating characters.

**Example 1:**
- **Input:** `s = "abcabcbb"`
- **Output:** `3`
- **Explanation:** The answer is "abc", with the length of 3.

**Example 2:**
- **Input:** `s = "bbbbb"`
- **Output:** `1`
- **Explanation:** The answer is "b", with the length of 1.

**Example 3:**
- **Input:** `s = "pwwkew"`
- **Output:** `3`
- **Explanation:** The answer is "wke", with the length of 3. Notice that the answer must be a substring, "pwke" is a subsequence and not a substring.

**Constraints:**
- `0 <= s.length <= 5 * 10^4`
- `s` consists of English letters, digits, symbols and spaces.
""",
            difficulty="Medium",
            function_name="lengthOfLongestSubstring",
            python_starter_code="""class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        # Write your code here
        pass
""",
            cpp_starter_code="""class Solution {
public:
    int lengthOfLongestSubstring(string s) {
        // Write your code here
        return 0;
    }
};
""",
            cpp_test_harness="""#include <iostream>
#include <string>
#include <unordered_map>
#include <algorithm>

using namespace std;

{{user_code}}

int main(int argc, char* argv[]) {
    // Handling empty string arg
    string s = "";
    if (argc >= 2) s = argv[1];
    Solution sol;
    int res = sol.lengthOfLongestSubstring(s);
    cout << res << endl;
    return 0;
}
""",
            test_cases=json.dumps([
                {"input": "abcabcbb", "output": "3"},
                {"input": "bbbbb", "output": "1"},
                {"input": "pwwkew", "output": "3"},
                {"input": "", "output": "0"}
            ]),
            hints=json.dumps([
                "Can you optimize the brute force approach using a sliding window?",
                "Keep a hash set to store the characters in the current window [i, j)."
            ]),
            optimal_time_complexity="O(N)",
            optimal_space_complexity="O(min(M, N))"
        )
        
        # 4. Climbing Stairs
        climbing_stairs = DSAQuestion(
            title="Climbing Stairs",
            description="""You are climbing a staircase. It takes `n` steps to reach the top.

Each time you can either climb `1` or `2` steps. In how many distinct ways can you climb to the top?

**Example 1:**
- **Input:** `n = 2`
- **Output:** `2`
- **Explanation:** There are two ways to climb to the top.
1. 1 step + 1 step
2. 2 steps

**Example 2:**
- **Input:** `n = 3`
- **Output:** `3`
- **Explanation:** There are three ways to climb to the top.
1. 1 step + 1 step + 1 step
2. 1 step + 2 steps
3. 2 steps + 1 step

**Constraints:**
- `1 <= n <= 45`
""",
            difficulty="Easy",
            function_name="climbStairs",
            python_starter_code="""class Solution:
    def climbStairs(self, n: int) -> int:
        # Write your code here
        pass
""",
            cpp_starter_code="""class Solution {
public:
    int climbStairs(int n) {
        // Write your code here
        return 0;
    }
};
""",
            cpp_test_harness="""#include <iostream>
#include <string>

using namespace std;

{{user_code}}

int main(int argc, char* argv[]) {
    if (argc < 2) return 1;
    int n = stoi(argv[1]);
    Solution sol;
    int res = sol.climbStairs(n);
    cout << res << endl;
    return 0;
}
""",
            test_cases=json.dumps([
                {"input": "2", "output": "2"},
                {"input": "3", "output": "3"},
                {"input": "4", "output": "5"},
                {"input": "10", "output": "89"}
            ]),
            hints=json.dumps([
                "To reach nth step, what could have been your previous steps?",
                "You could have reached n from n-1 or n-2. Thus DP[n] = DP[n-1] + DP[n-2]."
            ]),
            optimal_time_complexity="O(N)",
            optimal_space_complexity="O(1)"
        )
        
        session.add_all([two_sum, valid_parens, longest_sub, climbing_stairs])
        await session.commit()
        
        logger.info("Successfully seeded curated verified DSA problems!")

if __name__ == "__main__":
    asyncio.run(init_db())
    asyncio.run(seed_verified_problems())
