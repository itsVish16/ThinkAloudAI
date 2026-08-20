# 📚 ThinkAloudAI — Admin Panel API Reference (`apisdocs.md`)

This document provides a comprehensive, production-ready specification of all **Admin Panel Endpoints** across the ThinkAloudAI microservice ecosystem.

---

## 🔐 Global Authentication & Authorization

All Admin endpoints require a valid **JWT Bearer Token** in the `Authorization` header:

```http
Authorization: Bearer <ADMIN_JWT_ACCESS_TOKEN>
```

> **Security Rule**: The JWT payload `email` (or resolved email from User Service) must match one of the comma-separated emails configured in the `ADMIN_EMAILS` environment variable. If unauthorized or non-admin, the API returns `403 Forbidden` (`"detail": "Admin access required"`).

---

## 📑 Table of Contents

1. [User Management & Gamification (`Scalable_User_Service`)](#1-user-management--gamification-scalable_user_service)
   - [GET /api/v1/admin/users/stats](#11-get-apiv1adminusersstats)
   - [GET /api/v1/admin/users](#12-get-apiv1adminusers)
   - [GET /api/v1/admin/users/{user_id}](#13-get-apiv1adminusersuser_id)
   - [PATCH /api/v1/admin/users/{user_id}/status](#14-patch-apiv1adminusersuser_idstatus)
   - [DELETE /api/v1/admin/users/{user_id}](#15-delete-apiv1adminusersuser_id)
   - [GET /api/v1/admin/achievements](#16-get-apiv1adminachievements)
   - [POST /api/v1/admin/achievements](#17-post-apiv1adminachievements)
2. [DSA & Content Management (`main_service`)](#2-dsa--content-management-main_service)
   - [GET /admin/coding/stats](#21-get-admincodingstats)
   - [GET /admin/roadmaps/stats](#22-get-adminroadmapsstats)
   - [GET /admin/dsa/questions](#23-get-admindsaquestions)
   - [POST /admin/dsa/questions](#24-post-admindsaquestions)
   - [GET /admin/dsa/questions/{question_id}](#25-get-admindsaquestionsquestion_id)
   - [PUT /admin/dsa/questions/{question_id}](#26-put-admindsaquestionsquestion_id)
   - [DELETE /admin/dsa/questions/{question_id}](#27-delete-admindsaquestionsquestion_id)
   - [GET /admin/dsa/submissions](#28-get-admindsasubmissions)
   - [GET /admin/dsa/submissions/{submission_id}](#29-get-admindsasubmissionssubmission_id)
3. [Interview Auditing & Moderation (`AI_Interviewer`)](#3-interview-auditing--moderation-ai_interviewer)
   - [GET /api/admin/stats](#31-get-apiadminstats)
   - [GET /api/admin/users](#32-get-apiadminusers)
   - [GET /api/admin/interviews](#33-get-apiadmininterviews)
   - [GET /api/admin/interviews/{session_id}](#34-get-apiadmininterviewssession_id)
   - [PATCH /api/admin/interviews/{session_id}/score](#35-patch-apiadmininterviewssession_idscore)
   - [DELETE /api/admin/interviews/{session_id}](#36-delete-apiadmininterviewssession_id)

---

# 1. User Management & Gamification (`Scalable_User_Service`)
**Base Gateway URL**: `https://api.thinkaloudai.tech/api/v1/admin`

---

### 1.1 `GET /api/v1/admin/users/stats`
Retrieves platform user counts and 30-day signup growth metrics.

* **Method**: `GET`
* **Path**: `/api/v1/admin/users/stats`
* **Auth Required**: `Bearer <admin_token>`

#### Response `200 OK`
```json
{
  "total_users": 1540,
  "verified_users": 1420,
  "unverified_users": 120,
  "growth": [
    {
      "date": "2026-08-01",
      "users": 42
    },
    {
      "date": "2026-08-02",
      "users": 58
    }
  ]
}
```

---

### 1.2 `GET /api/v1/admin/users`
Paginated directory of all registered users with optional username/email search and verification filtering.

* **Method**: `GET`
* **Path**: `/api/v1/admin/users`
* **Query Parameters**:
  - `page` *(int, optional, default: 1)*: Page number
  - `limit` *(int, optional, default: 20, max: 100)*: Items per page
  - `search` *(string, optional)*: Filter by partial username, email, or full name
  - `is_verified` *(bool, optional)*: Filter by email verification status (`true` / `false`)

#### Response `200 OK`
```json
{
  "items": [
    {
      "id": 1,
      "username": "alexdev",
      "email": "alex@example.com",
      "full_name": "Alex Mercer",
      "is_verified": true,
      "created_at": "2026-07-15T10:30:00Z",
      "updated_at": "2026-08-10T14:20:00Z",
      "last_login_at": "2026-08-19T18:45:12Z"
    }
  ],
  "total": 1420,
  "page": 1,
  "limit": 20,
  "pages": 71
}
```

---

### 1.3 `GET /api/v1/admin/users/{user_id}`
Returns complete user dossier including profile bio, social links, preferences, and awarded badges.

* **Method**: `GET`
* **Path**: `/api/v1/admin/users/{user_id}`
* **Path Parameters**:
  - `user_id` *(int, required)*: Target user ID

#### Response `200 OK`
```json
{
  "user": {
    "id": 1,
    "username": "alexdev",
    "email": "alex@example.com",
    "full_name": "Alex Mercer",
    "is_verified": true,
    "created_at": "2026-07-15T10:30:00Z",
    "updated_at": "2026-08-10T14:20:00Z",
    "last_login_at": "2026-08-19T18:45:12Z"
  },
  "profile": {
    "bio": "Software Engineer preparing for FAANG interviews.",
    "avatar_url": "https://avatars.example.com/alex.png",
    "github_url": "https://github.com/alexdev",
    "linkedin_url": "https://linkedin.com/in/alexdev",
    "target_role": "Senior Backend Engineer",
    "years_of_experience": 4
  },
  "preferences": {
    "theme": "dark",
    "preferred_language": "python",
    "email_notifications": true
  },
  "achievements": [
    {
      "id": 1,
      "title": "First Mock Cleared",
      "description": "Completed your first live AI technical interview.",
      "icon_url": "https://assets.thinkaloudai.tech/badges/first-interview.svg"
    }
  ]
}
```

---

### 1.4 `PATCH /api/v1/admin/users/{user_id}/status`
Updates moderation parameters or details for a given user. Automatically purges user cache.

* **Method**: `PATCH`
* **Path**: `/api/v1/admin/users/{user_id}/status`
* **Request Body**:
```json
{
  "is_verified": true,
  "full_name": "Alexander Mercer"
}
```

#### Response `200 OK`
```json
{
  "message": "User status updated successfully",
  "user_id": 1,
  "is_verified": true
}
```

---

### 1.5 `DELETE /api/v1/admin/users/{user_id}`
Permanently removes a user account and purges user Redis cache.

* **Method**: `DELETE`
* **Path**: `/api/v1/admin/users/{user_id}`

#### Response `200 OK`
```json
{
  "message": "User deleted successfully",
  "user_id": 1
}
```

---

### 1.6 `GET /api/v1/admin/achievements`
Lists all global system achievements and badges.

* **Method**: `GET`
* **Path**: `/api/v1/admin/achievements`

#### Response `200 OK`
```json
[
  {
    "id": 1,
    "title": "DSA Master",
    "description": "Solved 50 DSA coding challenges with optimal complexity.",
    "icon_url": "https://assets.thinkaloudai.tech/badges/dsa-master.svg"
  }
]
```

---

### 1.7 `POST /api/v1/admin/achievements`
Creates a new global achievement.

* **Method**: `POST`
* **Path**: `/api/v1/admin/achievements`
* **Request Body**:
```json
{
  "title": "System Architect",
  "description": "Scored 90+ in 5 System Design mock interviews.",
  "icon_url": "https://assets.thinkaloudai.tech/badges/system-architect.svg"
}
```

#### Response `201 Created`
```json
{
  "id": 2,
  "title": "System Architect",
  "description": "Scored 90+ in 5 System Design mock interviews.",
  "icon_url": "https://assets.thinkaloudai.tech/badges/system-architect.svg"
}
```

---

# 2. DSA & Content Management (`main_service`)
**Base Gateway URL**: `https://api.thinkaloudai.tech/admin`

---

### 2.1 `GET /admin/coding/stats`
Platform code execution and submission analytics.

* **Method**: `GET`
* **Path**: `/admin/coding/stats`

#### Response `200 OK`
```json
{
  "total_questions": 120,
  "runs": 4530,
  "submissions": 2180,
  "passed_submissions": 1490,
  "popular_problems": [
    {
      "title": "Two Sum",
      "attempts": 450
    },
    {
      "title": "LRU Cache",
      "attempts": 320
    }
  ]
}
```

---

### 2.2 `GET /admin/roadmaps/stats`
Returns roadmap creation statistics and 30-day growth trends.

* **Method**: `GET`
* **Path**: `/admin/roadmaps/stats`

#### Response `200 OK`
```json
{
  "total_roadmaps": 840,
  "growth": [
    {
      "date": "2026-08-18",
      "roadmaps": 24
    }
  ]
}
```

---

### 2.3 `GET /admin/dsa/questions`
Paginated listing of all DSA questions with search and difficulty filters.

* **Method**: `GET`
* **Path**: `/admin/dsa/questions`
* **Query Parameters**:
  - `page` *(int, default: 1)*
  - `limit` *(int, default: 20)*
  - `difficulty` *(string, optional)*: `Easy`, `Medium`, `Hard`
  - `search` *(string, optional)*: Title or description keyword search

#### Response `200 OK`
```json
{
  "items": [
    {
      "id": 1,
      "title": "Two Sum",
      "description": "Given an array of integers `nums` and an integer `target`...",
      "difficulty": "Easy",
      "test_cases": "[{\"args\": [[2,7,11,15], 9], \"expected\": [0,1]}]",
      "python_starter_code": "def twoSum(nums: list[int], target: int) -> list[int]:\n    pass",
      "cpp_starter_code": "vector<int> twoSum(vector<int>& nums, int target) {\n    \n}",
      "cpp_test_harness": null,
      "function_name": "twoSum",
      "hints": "Try using a hash map to store complements.",
      "optimal_time_complexity": "O(N)",
      "optimal_space_complexity": "O(N)",
      "created_at": "2026-06-01T00:00:00Z"
    }
  ],
  "total": 120,
  "page": 1,
  "limit": 20,
  "pages": 6
}
```

---

### 2.4 `POST /admin/dsa/questions`
Creates a new DSA problem and invalidates Redis question catalog caches.

* **Method**: `POST`
* **Path**: `/admin/dsa/questions`
* **Request Body**:
```json
{
  "title": "Valid Palindrome",
  "description": "A phrase is a palindrome if, after converting all uppercase letters into lowercase...",
  "difficulty": "Easy",
  "test_cases": "[{\"args\": [\"A man, a plan, a canal: Panama\"], \"expected\": true}, {\"args\": [\"race a car\"], \"expected\": false}]",
  "python_starter_code": "def isPalindrome(s: str) -> bool:\n    pass",
  "cpp_starter_code": "bool isPalindrome(string s) {\n    \n}",
  "cpp_test_harness": null,
  "function_name": "isPalindrome",
  "hints": "Two pointers approach from left and right.",
  "optimal_time_complexity": "O(N)",
  "optimal_space_complexity": "O(1)"
}
```

#### Response `201 Created`
```json
{
  "id": 121,
  "title": "Valid Palindrome",
  "description": "A phrase is a palindrome...",
  "difficulty": "Easy",
  "test_cases": "[{\"args\": [\"A man, a plan, a canal: Panama\"], \"expected\": true}]",
  "python_starter_code": "def isPalindrome(s: str) -> bool:\n    pass",
  "cpp_starter_code": "bool isPalindrome(string s) {\n    \n}",
  "function_name": "isPalindrome",
  "hints": "Two pointers approach from left and right.",
  "optimal_time_complexity": "O(N)",
  "optimal_space_complexity": "O(1)",
  "created_at": "2026-08-20T14:00:00Z"
}
```

---

### 2.5 `GET /admin/dsa/questions/{question_id}`
Fetches single problem definition including raw test cases.

* **Method**: `GET`
* **Path**: `/admin/dsa/questions/{question_id}`

#### Response `200 OK`
*(Same schema as `POST /admin/dsa/questions`)*

---

### 2.6 `PUT /admin/dsa/questions/{question_id}`
Updates problem content, code stubs, or test cases.

* **Method**: `PUT`
* **Path**: `/admin/dsa/questions/{question_id}`
* **Request Body**: Same schema as `POST /admin/dsa/questions`

#### Response `200 OK`
*(Returns updated problem object)*

---

### 2.7 `DELETE /admin/dsa/questions/{question_id}`
Deletes problem and clears cache.

* **Method**: `DELETE`
* **Path**: `/admin/dsa/questions/{question_id}`

#### Response `200 OK`
```json
{
  "message": "Question deleted successfully",
  "question_id": 121
}
```

---

### 2.8 `GET /admin/dsa/submissions`
Global paginated feed of all user code runs and submissions.

* **Method**: `GET`
* **Path**: `/admin/dsa/submissions`
* **Query Parameters**:
  - `page` *(int, default: 1)*
  - `limit` *(int, default: 20)*
  - `status` *(string, optional)*: `Accepted`, `Wrong Answer`, `Runtime Error`, `Time Limit Exceeded`
  - `question_id` *(int, optional)*
  - `session_id` *(string, optional)*

#### Response `200 OK`
```json
{
  "items": [
    {
      "id": 501,
      "session_id": "user_42",
      "question_id": 1,
      "code": "def twoSum(nums, target):\n    seen = {}\n    for i, n in enumerate(nums):\n        if target - n in seen:\n            return [seen[target - n], i]\n        seen[n] = i",
      "language": "python",
      "status": "Accepted",
      "error_message": null,
      "is_submission": true,
      "created_at": "2026-08-20T13:45:00Z"
    }
  ],
  "total": 2180,
  "page": 1,
  "limit": 20,
  "pages": 109
}
```

---

### 2.9 `GET /admin/dsa/submissions/{submission_id}`
Inspect full submission code and execution details.

* **Method**: `GET`
* **Path**: `/admin/dsa/submissions/{submission_id}`

#### Response `200 OK`
*(Returns single `CodeSubmissionOut` object)*

---

# 3. Interview Auditing & Moderation (`AI_Interviewer`)
**Base Gateway URL**: `https://api.thinkaloudai.tech/api/admin`

---

### 3.1 `GET /api/admin/stats`
Platform voice interview metrics and domain category breakdown.

* **Method**: `GET`
* **Path**: `/api/admin/stats`

#### Response `200 OK`
```json
{
  "total_users": 980,
  "total_interviews": 3420,
  "total_minutes": 51200.5,
  "categories": {
    "dsa": 1650,
    "system_design": 920,
    "behavioral": 540,
    "pm": 210,
    "aiml": 100
  },
  "growth": [
    {
      "date": "2026-08-19",
      "interviews": 85
    }
  ]
}
```

---

### 3.2 `GET /api/admin/users`
Lists users ranked by total interview sessions conducted.

* **Method**: `GET`
* **Path**: `/api/admin/users`
* **Query Parameters**:
  - `page` *(int, default: 1)*
  - `limit` *(int, default: 20)*
  - `search` *(string, optional)*

#### Response `200 OK`
```json
{
  "items": [
    {
      "id": 1,
      "username": "alexdev",
      "email": "alex@example.com",
      "total_interviews": 18
    }
  ],
  "total": 980,
  "page": 1,
  "limit": 20,
  "pages": 49
}
```

---

### 3.3 `GET /api/admin/interviews`
Paginated directory of mock interviews with filtering.

* **Method**: `GET`
* **Path**: `/api/admin/interviews`
* **Query Parameters**:
  - `page` *(int, default: 1)*
  - `limit` *(int, default: 20)*
  - `interview_type` *(string, optional)*: `dsa`, `system_design`, `behavioral`, `pm`, `aiml`
  - `status` *(string, optional)*: `completed`, `in_progress`, `abandoned`
  - `search` *(string, optional)*: Candidate name or session ID

#### Response `200 OK`
```json
{
  "items": [
    {
      "id": "mock_sess_894f2",
      "user_email": "alex@example.com",
      "candidate_name": "Alex Mercer",
      "type": "dsa",
      "stage": "completed",
      "duration_minutes": 28.5,
      "score": 88,
      "created_at": "2026-08-20T12:00:00Z"
    }
  ],
  "total": 3420,
  "page": 1,
  "limit": 20,
  "pages": 171
}
```

---

### 3.4 `GET /api/admin/interviews/{session_id}`
Comprehensive session audit: complete conversational transcript, AI radar scores, strengths, weaknesses, and LLM rubric metrics.

* **Method**: `GET`
* **Path**: `/api/admin/interviews/{session_id}`

#### Response `200 OK`
```json
{
  "id": "mock_sess_894f2",
  "candidate_name": "Alex Mercer",
  "interview_type": "dsa",
  "stage": "completed",
  "created_at": "2026-08-20T12:00:00Z",
  "updated_at": "2026-08-20T12:28:30Z",
  "user": {
    "id": 1,
    "email": "alex@example.com",
    "username": "alexdev"
  },
  "feedback": {
    "technical_score": 90,
    "communication_score": 85,
    "english_score": 88,
    "strengths": [
      "Quickly identified optimal O(N) hash map approach",
      "Clear articulation of edge cases"
    ],
    "weaknesses": [
      "Brief hesitation during space complexity trade-off explanation"
    ],
    "improvement_plan": [
      "Practice multi-threading and concurrency questions"
    ],
    "recommended_topics": [
      "Dynamic Programming",
      "Sliding Window"
    ],
    "detailed_metrics": {
      "problem_solving": 9.2,
      "code_quality": 8.8,
      "communication_clarity": 8.5
    }
  },
  "transcript": [
    {
      "role": "interviewer",
      "content": "Hello Alex! Welcome. Let's start with your approach for Two Sum.",
      "created_at": "2026-08-20T12:00:05Z"
    },
    {
      "role": "candidate",
      "content": "Hi! I will use a hash map to look up complements in O(1) time.",
      "created_at": "2026-08-20T12:00:20Z"
    }
  ]
}
```

---

### 3.5 `PATCH /api/admin/interviews/{session_id}/score`
Manual score override for technical, communication, or english marks.

* **Method**: `PATCH`
* **Path**: `/api/admin/interviews/{session_id}/score`
* **Request Body**:
```json
{
  "technical_score": 95,
  "communication_score": 90,
  "english_score": 92,
  "reason": "Candidate provided rigorous proof of optimality post-interview review."
}
```

#### Response `200 OK`
```json
{
  "message": "Interview score overridden successfully",
  "session_id": "mock_sess_894f2",
  "technical_score": 95,
  "communication_score": 90,
  "english_score": 92
}
```

---

### 3.6 `DELETE /api/admin/interviews/{session_id}`
Purges corrupt or abandoned session records.

* **Method**: `DELETE`
* **Path**: `/api/admin/interviews/{session_id}`

#### Response `200 OK`
```json
{
  "message": "Interview session deleted successfully",
  "session_id": "mock_sess_894f2"
}
```

---

## 🛑 Standard Error Status Codes

| Status Code | Meaning | Example Scenario |
| :--- | :--- | :--- |
| `401 Unauthorized` | Invalid or missing token | Expired JWT or missing Bearer header. |
| `403 Forbidden` | Access Denied | User is authenticated but their email is not in `ADMIN_EMAILS`. |
| `404 Not Found` | Entity missing | User, Problem, Submission, or Interview Session ID does not exist. |
| `422 Unprocessable` | Validation Error | Request body payload does not conform to required Pydantic schema. |
| `429 Too Many Requests`| Rate Limit / OTP Lockout | Exceeded 5 failed OTP attempts or API rate limits. |
| `500 Server Error` | Unhandled Server Error | Database failure or unhandled exception. |
