# Profile Page API Documentation

This document contains the exact API specifications for the two endpoints required to build the comprehensive LeetCode-style profile page. 

**Note for Frontend Agent:** You will need to make parallel requests to both endpoints to render the full profile. Both endpoints require a valid JWT token.

---

## 1. User Identity & Gamification Stats
This endpoint provides the user's basic information, streaks, domain skills, unlocked achievements, and a log of recent learning events.

**Service:** Scalable User Service
**URL:** `GET http://localhost:8000/api/v1/users/me/profile`
**Auth Required:** Yes (`Authorization: Bearer <token>`)

### JSON Response Schema
```json
{
  "username": "string",
  "email": "string",
  "full_name": "string",
  "is_verified": true,
  "created_at": "2026-06-25T10:00:00Z",
  "bio": "string | null",
  "avatar_url": "string | null",
  "github_url": "string | null",
  "linkedin_url": "string | null",
  "streak": {
    "current_streak": "integer",
    "longest_streak": "integer",
    "last_activity_date": "datetime | null"
  },
  "skills": [
    {
      "domain": "string (e.g., Python, System Design)",
      "score": "integer"
    }
  ],
  "achievements": [
    {
      "title": "string",
      "description": "string",
      "icon_url": "string | null",
      "earned_at": "datetime"
    }
  ],
  "recent_activity": [
    {
      "event_type": "string (e.g., ProblemSolved)",
      "reference_id": "string | null",
      "score_change": "integer",
      "created_at": "datetime"
    }
  ]
}
```

---

## 2. DSA Submissions & Activity Heatmap
This endpoint provides the user's coding statistics, including total problems solved, overall accuracy, and the daily submission heatmap for rendering a GitHub/LeetCode style contribution graph.

**Service:** Main Service (DSA)
**URL:** `GET http://localhost:8001/users/profile`
**Auth Required:** Yes (`Authorization: Bearer <token>`)

### JSON Response Schema
```json
{
  "session_id": "string",
  "total_submissions": "integer",
  "total_solved": "integer",
  "accuracy_percentage": "float",
  "heatmap": [
    {
      "date": "string (YYYY-MM-DD)",
      "count": "integer"
    }
  ],
  "recent_submissions": [
    {
      "id": "integer",
      "question_id": "integer",
      "question_title": "string",
      "language": "string",
      "status": "string (e.g., Accepted, Wrong Answer)",
      "created_at": "datetime"
    }
  ]
}
```
