# ThinkAloudAI — Backend Microservices API Documentation

Welcome to the comprehensive API documentation for the **ThinkAloudAI** backend platform. This document covers the specifications, request/response schemas, authentication mechanisms, background workers, and error codes across all backend microservices:

1. [Scalable User Service (`:8000`)](#1-scalable-user-service-port-8000)
2. [Main Service (`:8001`)](#2-main-service-port-8001)
3. [AI Interviewer Service (`:8002`)](#3-ai-interviewer-service-port-8002)
4. [Standard Error Responses & Status Codes](#4-standard-error-responses--status-codes)

---

# Architecture & Common Authentication Standards

- **Gateway / Caddy Reverse Proxy**:
  - User Service: `http://localhost/api/v1/users` $\to$ `http://user-service:8000`
  - Main Service: `http://localhost/api/v1` $\to$ `http://main-service:8001`
  - AI Interviewer: `http://localhost/api/v1/interviews` $\to$ `http://ai-interviewer-api:8000`
- **Stateless JWT Authentication**:
  - Header: `Authorization: Bearer <access_token>`
  - Algorithm: `HS256`
  - Claims: `sub` (User ID / UUID), `email`, `username`, `exp`, `jti` (JWT ID for Redis blacklist).
- **Service-to-Service Communication**:
  - Header: `X-Internal-Service: ai_interviewer|user_service|main_service`
- **Asynchronous Message Broker**:
  - **RabbitMQ Topic Exchange**: `thinkaloud_events`
  - Routing Keys: `interview.completed`, `user.registered`, `code.execution`

---

# 1. Scalable User Service (Port 8000)

The **Scalable User Service** manages user authentication, account verification via email OTP, password resets, token blacklisting via Redis, user profiles, preferences, and achievements.

## 1.1 Authentication & Account Lifecycle

### `POST /api/v1/users/signup`
- **Summary**: Register a new candidate account.
- **Auth**: Public
- **Rate Limit**: 5 req / min
- **Behavior**:
  - Validates username uniqueness, password complexity (at least 8 chars, 1 uppercase, 1 digit), and email format.
  - If email is registered and verified $\to$ returns `409 Conflict`.
  - If email is registered but unverified $\to$ regenerates OTP and updates credentials.
  - Stores 6-digit numeric OTP in Redis (`email_verification:<email>`, 15m TTL).
  - Publishes `user.created:<id>` to Redis Pub/Sub channel `user_events`.
  - Dispatches background email task.
- **Request Body (`SignupRequest`)**:
```json
{
  "username": "johndoe123",
  "email": "john@example.com",
  "full_name": "John Doe",
  "password": "StrongPassword123!"
}
```
- **Success Response (`201 Created`)**:
```json
{
  "message": "User registered successfully. Please verify your email using the OTP."
}
```
- **Errors**: `409 Conflict` (Email/username exists), `422 Unprocessable Entity`, `429 Too Many Requests`.

---

### `POST /api/v1/users/login`
- **Summary**: Authenticate candidate and issue access/refresh token pair.
- **Auth**: Public
- **Rate Limit**: 10 req / min
- **Behavior**:
  - Checks Redis failed counter (`login_attempts:<email>`). Lockout after 5 attempts for 15 mins.
  - Verifies bcrypt password hash (executes dummy hash on non-existent user to avoid timing attacks).
  - Enforces `is_verified == True`.
  - Resets login attempt counter, records `last_login_at`, and returns tokens with unique `jti`.
- **Request Body (`LoginRequest`)**:
```json
{
  "email": "john@example.com",
  "password": "StrongPassword123!"
}
```
- **Success Response (`200 OK`)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```
- **Errors**: `401 Unauthorized` (Invalid credentials), `403 Forbidden` (Email unverified), `429 Too Many Requests`.

---

### `POST /api/v1/users/refresh`
- **Summary**: Rotate refresh token and issue a fresh access token.
- **Auth**: Public
- **Behavior**:
  - Checks if refresh token `jti` is blacklisted in Redis (`blacklist:token:<jti>`).
  - Blacklists old refresh token in Redis and issues a new pair.
- **Request Body (`RefreshTokenRequest`)**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```
- **Success Response (`200 OK`)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```
- **Errors**: `401 Unauthorized`.

---

### `POST /api/v1/users/logout`
- **Summary**: Blacklist current access and refresh tokens.
- **Auth**: JWT Bearer (`Authorization: Bearer <access_token>`)
- **Request Body (`LogoutRequest`)**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```
- **Success Response (`200 OK`)**:
```json
{
  "message": "Logged out successfully"
}
```

---

### `POST /api/v1/users/verify-email`
- **Summary**: Verify account using 6-digit email OTP.
- **Auth**: Public
- **Behavior**:
  - Performs constant-time comparison on Redis key `email_verification:<email>`.
  - Sets `is_verified = True`, invalidates cached user profile, publishes `user.verified:<id>` event.
- **Request Body (`VerifyEmailRequest`)**:
```json
{
  "email": "john@example.com",
  "token": "123456"
}
```
- **Success Response (`200 OK`)**:
```json
{
  "message": "Email verified successfully"
}
```
- **Errors**: `400 Bad Request` (Invalid or expired token).

---

### `POST /api/v1/users/resend-verification`
- **Summary**: Resend email verification OTP.
- **Auth**: Public
- **Request Body (`ResendVerificationRequest`)**:
```json
{
  "email": "john@example.com"
}
```
- **Success Response (`200 OK`)**:
```json
{
  "message": "If the email exists, verification instructions are ready."
}
```

---

### `POST /api/v1/users/forgot-password`
- **Summary**: Request password reset OTP.
- **Auth**: Public
- **Request Body (`ForgotPasswordRequest`)**:
```json
{
  "email": "john@example.com"
}
```
- **Success Response (`200 OK`)**:
```json
{
  "message": "If the email exists, password reset instructions are ready."
}
```

---

### `POST /api/v1/users/reset-password`
- **Summary**: Reset password using 6-digit OTP.
- **Auth**: Public
- **Behavior**: Verifies OTP from `password_reset:<email>`, hashes new password, invalidates cached profile in Redis.
- **Request Body (`ResetPasswordRequest`)**:
```json
{
  "email": "john@example.com",
  "otp": "123456",
  "new_password": "NewStrongPassword123!"
}
```
- **Success Response (`200 OK`)**:
```json
{
  "message": "Password reset successful"
}
```

---

## 1.2 Profiles & Preferences

### `GET /api/v1/users/me`
- **Summary**: Retrieve current authenticated user account info.
- **Auth**: JWT Bearer
- **Behavior**: Checks Redis cache `user:profile:<id>` (300s TTL) before falling back to PostgreSQL.
- **Success Response (`200 OK`)**:
```json
{
  "id": 1,
  "username": "johndoe123",
  "email": "john@example.com",
  "full_name": "John Doe",
  "is_verified": true,
  "created_at": "2026-06-25T10:00:00Z",
  "updated_at": "2026-06-25T10:00:00Z",
  "last_login_at": "2026-06-25T10:05:00Z"
}
```

---

### `PATCH /api/v1/users/me`
- **Summary**: Update username or full name.
- **Auth**: JWT Bearer
- **Request Body (`UpdateUserRequest`)**:
```json
{
  "username": "newjohndoe123",
  "full_name": "Johnathan Doe"
}
```
- **Success Response (`200 OK`)**: Returns updated `UserResponse`.
- **Errors**: `409 Conflict` (Username already taken).

---

### `GET /api/v1/users/me/profile`
- **Summary**: Get complete user profile with achievements.
- **Auth**: JWT Bearer
- **Behavior**: Cached in Redis `user:full_profile:<id>` (60s TTL).
- **Success Response (`200 OK`)**:
```json
{
  "username": "johndoe123",
  "email": "john@example.com",
  "full_name": "John Doe",
  "is_verified": true,
  "created_at": "2026-06-25T10:00:00Z",
  "bio": "Software engineer passionate about distributed systems.",
  "avatar_url": "https://example.com/avatar.jpg",
  "github_url": "https://github.com/johndoe",
  "linkedin_url": "https://linkedin.com/in/johndoe",
  "headline": "Senior Full-Stack Engineer",
  "location": "San Francisco, CA",
  "institution": "Stanford University",
  "preferred_language": "python",
  "resume_url": "https://example.com/resume.pdf",
  "achievements": [
    {
      "title": "First Problem Solved",
      "description": "Solved your first coding problem on ThinkAloudAI",
      "icon_url": "https://example.com/icons/first_problem.png",
      "earned_at": "2026-06-25T12:00:00Z"
    }
  ]
}
```

---

### `GET /api/v1/users/profile/{username}`
- **Summary**: Get public profile by username.
- **Auth**: Public
- **Success Response (`200 OK`)**: Returns `PublicUserProfileResponse` (omits private `email` and `resume_url`).

---

### `PATCH /api/v1/users/me/profile/details`
- **Summary**: Update user profile biography, links, and resume.
- **Auth**: JWT Bearer
- **Request Body (`UpdateProfileDetailsRequest`)**:
```json
{
  "bio": "Updated bio description",
  "avatar_url": "https://example.com/avatar_new.jpg",
  "github_url": "https://github.com/newjohn",
  "linkedin_url": "https://linkedin.com/in/newjohn",
  "headline": "Staff Engineer",
  "location": "New York, NY",
  "institution": "MIT",
  "preferred_language": "cpp",
  "resume_url": "https://example.com/new_resume.pdf"
}
```
- **Success Response (`200 OK`)**:
```json
{
  "message": "Profile details updated"
}
```

---

### `GET /api/v1/users/me/preferences` & `PUT /api/v1/users/me/preferences`
- **Summary**: Retrieve or update UI theme (`dark`, `light`, `system`) and notification settings.
- **Auth**: JWT Bearer
- **Request Body (`UpdateUserPreferenceRequest`)**:
```json
{
  "theme": "dark",
  "email_notifications": true,
  "push_notifications": false
}
```
- **Success Response (`200 OK`)**:
```json
{
  "theme": "dark",
  "email_notifications": true,
  "push_notifications": false
}
```

---

### `GET /api/v1/users/achievements`
- **Summary**: List all available global achievements.
- **Auth**: Public
- **Success Response (`200 OK`)**:
```json
[
  {
    "id": 1,
    "title": "First Problem Solved",
    "description": "Solved your first coding problem on ThinkAloudAI",
    "icon_url": "https://example.com/icons/first_problem.png"
  }
]
```

---

## 1.3 Admin & Health

### `GET /api/v1/users/admin/users/stats`
- **Summary**: Get administrative analytics and 30-day signup growth.
- **Auth**: JWT Bearer + Admin email check (`ADMIN_EMAILS`)
- **Success Response (`200 OK`)**:
```json
{
  "total_users": 150,
  "verified_users": 130,
  "unverified_users": 20,
  "growth": [
    { "date": "2026-07-18", "users": 8 }
  ]
}
```

---

### `GET /health/live` & `GET /health/ready`
- **Summary**: Liveness (`200 OK {"status": "alive"}`) and Readiness probe checking PostgreSQL and Redis connectivity.

---

# 2. Main Service (Port 8001)

The **Main Service** orchestrates AI Chat assistants, Monaco Code Execution (DSA), System Design evaluations, Learning Roadmaps, Question Banks, and the Candidate Performance Dashboard.

## 2.1 AI Chat & Real-Time Assistant

### `POST /chat/stream`
- **Summary**: Server-Sent Events (SSE) stream for AI tutoring, roadmap generation, and conversational interview assistance.
- **Auth**: JWT Bearer
- **Behavior**:
  - Emits incremental LangGraph agent deltas, thinking blocks, tool calls, and roadmap generation events.
  - Pushes user and assistant messages to Redis buffer (`chat:buffer`).
  - An atomic Lua script batch writer flushes buffer entries into PostgreSQL every 5 seconds.
- **Request Body (`ChatStreamRequest`)**:
```json
{
  "session_id": "session-uuid-12345",
  "message": "Can you create a 4-week roadmap for mastering dynamic programming?",
  "images": ["https://storage.example.com/diagram.png"]
}
```
- **SSE Stream Output**:
```text
data: {"type": "execution_start", "executionId": "exec_101", "time": 1723829000.1}
data: {"type": "rename_chat", "title": "Dynamic Programming Plan"}
data: {"type": "thinking_start", "time": 1723829000.4}
data: {"type": "thinking_delta", "content": "Structuring weekly modules..."}
data: {"type": "thinking_end", "time": 1723829001.0}
data: {"type": "tool_start", "id": "t1", "tool": {"title": "Generate Roadmap"}, "input": {"title": "DP Mastery"}}
data: {"type": "roadmap", "id": "42"}
data: {"type": "tool_end", "id": "t1", "tool": "create_user_roadmap", "output": "Created", "status": "completed"}
data: {"type": "writing_start"}
data: {"type": "text_delta", "content": "I have created your Dynamic Programming roadmap!"}
data: {"type": "writing_end"}
data: {"type": "execution_end"}
```

---

### `GET /sessions` & `GET /sessions/{session_id}/messages`
- **Summary**: List user chat sessions or retrieve historical message transcripts (merges PostgreSQL history with unflushed Redis buffer entries).
- **Auth**: JWT Bearer
- **Success Response (`200 OK`)**:
```json
[
  {
    "id": 101,
    "session_id": "session-uuid-12345",
    "role": "user",
    "content": "Can you create a 4-week roadmap?",
    "created_at": "2026-08-16T15:30:00Z"
  }
]
```

---

### `DELETE /sessions/{session_id}`
- **Summary**: Delete a chat session and cascade delete all messages.
- **Auth**: JWT Bearer

---

### `WEBSOCKET /chat/voice-stream`
- **Summary**: Low-latency WebSocket bridge to Speechmatics Real-Time Speech-to-Text.
- **Auth**: Public WebSocket
- **Protocol**: Client sends binary 16kHz PCM audio (`pcm_s16le`, 1-channel); server returns partial and final transcription JSON packets:
```json
{"type": "partial", "text": "let us solve the two"}
{"type": "final", "text": "Let us solve the Two Sum problem."}
```

---

## 2.2 Data Structures & Algorithms (DSA)

### `GET /dsa/questions`
- **Summary**: Paginated list of DSA problems.
- **Auth**: Public
- **Caching**: Cached in Redis (`dsa:questions:all:skip={skip}:limit={limit}`) for 1 hour.
- **Query Parameters**: `skip` (int, default: 0), `limit` (int, default: 50).
- **Success Response (`200 OK`)**:
```json
[
  {
    "id": 1,
    "title": "Two Sum",
    "description": "Given an array of integers...",
    "difficulty": "Easy",
    "test_cases": "{\"cases\": [{\"args\": {\"nums\": [2, 7, 11, 15], \"target\": 9}, \"expected\": [0, 1]}]}",
    "python_starter_code": "class Solution:\n    def twoSum(self, nums: List[int], target: int) -> List[int]:\n        pass",
    "cpp_starter_code": "#include <vector>\nusing namespace std;\nclass Solution {\npublic:\n    vector<int> twoSum(vector<int>& nums, int target) {\n    }\n};",
    "function_name": "twoSum",
    "optimal_time_complexity": "O(n)",
    "optimal_space_complexity": "O(n)"
  }
]
```

---

### `GET /dsa/questions/{question_id}`
- **Summary**: Retrieve a single DSA problem by ID.
- **Auth**: Public

---

### `POST /dsa/questions/{question_id}/run`
- **Summary**: Queue test run against sample test cases (`is_submission=False`).
- **Auth**: JWT Bearer
- **Behavior**: Persists pending `CodeSubmission` in PostgreSQL and publishes task to RabbitMQ `code_execution_queue`.
- **Request Body (`CodeSubmitRequest`)**:
```json
{
  "session_id": "interview_59182",
  "code": "class Solution:\n    def twoSum(self, nums: List[int], target: int) -> List[int]:\n        return [0, 1]",
  "language": "python"
}
```
- **Success Response (`200 OK`)**:
```json
{
  "status": "Pending",
  "submission_id": 883,
  "passed_tests": 0,
  "total_tests": 0,
  "execution_time_ms": 0.0,
  "output": "Execution queued with ID: 883"
}
```

---

### `POST /dsa/questions/{question_id}/submit`
- **Summary**: Submit code for graded evaluation (`is_submission=True`).
- **Auth**: JWT Bearer
- **Request Body (`CodeSubmitRequest`)**: Same as `/run`.
- **Success Response (`200 OK`)**: Same as `/run`.

---

### `GET /dsa/submissions/{submission_id}/stream`
- **Summary**: Server-Sent Events (SSE) stream for real-time code evaluation status.
- **Auth**: Public
- **Behavior**:
  - Checks if submission is already finished in DB (prevents race condition).
  - Subscribes to Redis Pub/Sub channel `submission_updates_{submission_id}`.
  - Performs 2-second DB polling fallback with a 45-second timeout safety.
- **SSE Stream Output**:
```text
event: connected
data: connected

event: result
data: {"status": "Accepted", "passed_tests": 5, "total_tests": 5, "error_message": null, "execution_time_ms": 14.8}
```

---

### `GET /dsa/status` & `GET /dsa/recommendations`
- **Summary**: Retrieve solved/attempted statuses and personalized practice recommendations.
- **Auth**: JWT Bearer

---

## 2.3 System Design Interviews

### `GET /system-design/questions` & `GET /system-design/questions/{question_id}`
- **Summary**: Query architecture problems filtered by `domain` and `role`. Cached in Redis for 1 hour.
- **Auth**: Public

---

### `POST /system-design/questions/{question_id}/submit`
- **Summary**: Evaluates architectural text answer and optional architecture diagram image using Vision LLM (`llama-v3p2-11b-vision-instruct`).
- **Auth**: JWT Bearer
- **Request Body (`SystemDesignSubmitRequest`)**:
```json
{
  "answer_text": "I would use Redis with a Sliding Window Log algorithm...",
  "image_data": "data:image/png;base64,iVBORw0KGgo..."
}
```
- **Success Response (`200 OK`)**:
```json
{
  "score": 85,
  "feedback": "Strong architectural foundation with good Redis partitioning strategy.",
  "strengths": ["Clear separation of data layers", "Proper latency tradeoff discussion"],
  "improvements": ["Address failover semantics if Redis Master becomes unreachable"]
}
```

---

## 2.4 Learning Roadmaps

### `GET /roadmaps` & `GET /roadmaps/{roadmap_id}`
- **Summary**: List user roadmaps or retrieve full hierarchical roadmap with nested topics, checklist items, and estimated timelines.
- **Auth**: JWT Bearer

---

### `POST /roadmaps/`
- **Summary**: Create a custom learning roadmap with topics and items.
- **Auth**: JWT Bearer
- **Request Body (`RoadmapCreate`)**:
```json
{
  "title": "System Design & Distributed Systems",
  "description": "Preparation for Senior Staff Engineer interviews",
  "topics": [
    {
      "title": "Data Consistency & Consensus",
      "order_index": 0,
      "items": [
        {
          "title": "Raft Algorithm vs Paxos",
          "content_type": "system_design",
          "content_id": "3",
          "timeline_days": 4,
          "is_completed": false
        }
      ]
    }
  ]
}
```

---

### `PATCH /roadmaps/items/{item_id}/toggle`
- **Summary**: Toggle the completion checkbox status of a specific roadmap item.
- **Auth**: JWT Bearer
- **Query Parameters**: `is_completed` (bool)

---

### `DELETE /roadmaps/{roadmap_id}`
- **Summary**: Permanently delete a roadmap and all nested items.
- **Auth**: JWT Bearer

---

## 2.5 Dashboard & Domain Pools

### `GET /dashboard/overview`
- **Summary**: Returns denormalized user overview: problems solved count, acceptance rate, average interview scores, current & longest daily streaks, 365-day heatmap, and skill scores.
- **Auth**: JWT Bearer
- **Success Response (`200 OK`)**:
```json
{
  "user_id": "user-uuid-12345",
  "stats": {
    "problems_solved_total": 45,
    "acceptance_rate": 78.5,
    "interviews_completed": 8,
    "avg_interview_score": 84.2,
    "current_streak": 5,
    "rating": 1350
  },
  "heatmap": [
    { "date": "2026-08-16", "count": 6 }
  ],
  "skills": [
    { "domain": "Algorithms", "score": 1420.5, "problems_solved": 30, "interviews_done": 4 }
  ]
}
```

---

### `GET /behavioral/questions`, `GET /pm/questions`, `GET /aiml/questions`
- **Summary**: Question banks for Behavioral (STAR method), Product Management, and AI/ML Engineering rounds.
- **Auth**: JWT Bearer OR `X-Internal-Service` Header.

---

### `GET /admin/coding/stats` & `GET /admin/roadmaps/stats`
- **Summary**: Platform admin metrics for DSA code execution runs vs submissions, popular problems, and roadmap creation trends.
- **Auth**: Admin JWT Bearer (`require_admin`).

---

# 3. AI Interviewer Service (Port 8002)

The **AI Interviewer Service** manages real-time WebRTC voice interview orchestration with LiveKit, state machine transitions, code snapshot synchronization, automated LLM post-interview evaluations, and global leaderboards.

## 3.1 WebRTC Room & Token Generation

### `GET /api/interview-types`
- **Summary**: List all available mock interview configurations (`dsa`, `system_design`, `hr`, `presentation`, `ai_ml`, `pm`).
- **Auth**: Public

---

### `POST /api/token`
- **Summary**: Mint LiveKit WebRTC access token and initialize the interview session.
- **Auth**: JWT Bearer
- **Behavior**:
  - Authenticates candidate via JWT.
  - Queries Main Service for active interview questions or dynamically selects pool questions.
  - Generates LiveKit access token with `can_publish=True`, `can_subscribe=True`, and participant metadata.
  - Upserts `InterviewSession` with initial stage `intro_audio_check`.
- **Request Body (`TokenRequest`)**:
```json
{
  "room_name": "interview_59182",
  "interview_type": "dsa",
  "question_ids": ["1", "12"],
  "domain": "backend",
  "role": "Senior Software Engineer"
}
```
- **Success Response (`200 OK`)**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "url": "ws://localhost:7880",
  "roomName": "interview_59182",
  "candidate": "johndoe",
  "ai_selected_questions": [
    {
      "id": "1",
      "title": "Two Sum",
      "difficulty": "Easy"
    }
  ]
}
```

---

## 3.2 Interview Session Lifecycle & Evaluation

### `GET /api/interview/{room_name}`
- **Summary**: Retrieve full interview transcript and post-interview evaluation report.
- **Auth**: JWT Bearer (strictly checks session ownership)
- **Success Response (`200 OK`)**:
```json
{
  "room_name": "interview_59182",
  "stage": "completed",
  "candidate_name": "johndoe",
  "transcript": [
    { "role": "assistant", "content": "Hello John! Welcome to your interview. Can you hear me clearly?" },
    { "role": "user", "content": "Yes, I can hear you loud and clear." }
  ],
  "evaluation": {
    "technical_score": 88,
    "communication_score": 92,
    "english_score": 90,
    "strengths": ["Identified optimal hash map solution immediately"],
    "weaknesses": ["Initial edge case testing was slightly rushed"],
    "improvement_plan": ["Dry run complex boundary conditions before submitting code"],
    "recommended_topics": ["Hash Tables", "Two-Pointer Technique"],
    "detailed_metrics": {
      "hiring_decision": "Strong Hire",
      "executive_summary": "Candidate demonstrated solid algorithmic problem-solving skills...",
      "technical_breakdown": { "algorithms": 90, "code_quality": 92 },
      "speaking_analytics": { "candidate_percentage": 68, "ai_percentage": 32 }
    }
  },
  "created_at": "2026-08-16T10:00:00",
  "updated_at": "2026-08-16T10:45:00"
}
```

---

### `GET /api/interview/{room_name}/stream`
- **Summary**: Server-Sent Events (SSE) stream subscribing to Redis channel `interview_events`.
- **Auth**: JWT Bearer (supports `?token=<JWT_TOKEN>` query parameter for EventSource).
- **Behavior**: Broadcasts `InterviewCompleted` event as soon as the background analysis worker finishes LLM evaluation.

---

### `POST /api/interview/{room_name}/end`
- **Summary**: Force complete an interview session and trigger background analysis.
- **Auth**: JWT Bearer
- **Behavior**:
  - Updates `InterviewSession.stage` to `"completed"` in PostgreSQL.
  - Publishes task payload to RabbitMQ `interview_analysis_queue`.
  - `analysis_worker.py` consumes task, fetches candidate code submissions from Main Service, evaluates transcript with LLM, computes speech analytics, updates Redis `global_leaderboard`, and publishes to `thinkaloud_events` topic exchange (`interview.completed`).
- **Success Response (`200 OK`)**:
```json
{
  "status": "success",
  "message": "Interview marked as completed and analysis triggered"
}
```

---

### `GET /api/interviews/me`
- **Summary**: List all past completed and in-progress interviews for current candidate.
- **Auth**: JWT Bearer

---

### `GET /api/interviews/me/analytics`
- **Summary**: Aggregated radar chart scores, weekly activity counts, and score trend analytics.
- **Auth**: JWT Bearer

---

### `GET /api/leaderboard`
- **Summary**: Real-time global leaderboard from Redis Sorted Set (`global_leaderboard`).
- **Auth**: JWT Bearer
- **Success Response (`200 OK`)**:
```json
{
  "leaderboard": [
    { "rank": 1, "candidate_name": "alex_coder", "score": 1420 },
    { "rank": 2, "candidate_name": "johndoe", "score": 890 }
  ],
  "me": {
    "rank": 2,
    "candidate_name": "johndoe",
    "score": 890
  }
}
```

---

## 3.3 Admin Interview Metrics

### `GET /api/admin/stats`, `GET /api/admin/users`, `GET /api/admin/interviews`
- **Summary**: Admin-only platform metrics: total interview minutes, session breakdown by type, user session counts, and paginated master session logs.
- **Auth**: JWT Bearer + Admin Email Whitelist (`require_admin`).

---

# 4. Standard Error Responses & Status Codes

All microservices adhere to standard RFC 7807 error structures:

| HTTP Status | Meaning | Typical Trigger | Response Body Schema |
|---|---|---|---|
| `400 Bad Request` | Malformed input | Missing claims in JWT token | `{"detail": "Invalid token payload: 'sub' missing"}` |
| `401 Unauthorized` | Missing / Invalid Auth | Expired or absent Bearer token | `{"detail": "Missing authentication credentials"}` |
| `403 Forbidden` | Access Denied | Admin endpoint called by standard user | `{"detail": "Not authorized. Admin access required."}` |
| `404 Not Found` | Resource Not Found | Question ID or Session ID not in DB | `{"detail": "Question not found"}` |
| `409 Conflict` | Duplicate Resource | Email or username already registered | `{"detail": "Email is already registered"}` |
| `422 Unprocessable Entity` | Schema Validation | Missing required JSON body field | `{"detail": [{"loc": ["body", "code"], "msg": "Field required"}]}` |
| `429 Too Many Requests` | Rate Limit Exceeded | Exceeded signup/login rate limits | `{"detail": "Too many failed login attempts."}` |
| `500 Internal Error` | Server Exception | Uncaught runtime error | `{"detail": "Internal server error"}` |
