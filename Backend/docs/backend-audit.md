# Backend Audit — 3 Services

## Critical Security (fix first)

1. **Secrets sprawled across .env files on disk**
   Good news: none git-tracked (verified git ls-files + history). Bad news: live keys in plaintext on disk, shared across services — JWT secret, Fireworks, E2B, Speechmatics, Tavily, Opik (main_service);
   LiveKit, Cartesia (AI_Interviewer); AWS access key + secret + Resend key (Scalable_User_Service). Rotate AWS + Resend keys at minimum — AWS creds give SQS access to account 230477418848. Move to secrets manager.

2. **Auth backdoor** — `main_service/app/routes/auth.py:12`
   POST `/auth/token` mints valid JWT for ANY session_id, zero verification. All protected routes bypassable. Delete endpoint or add real auth.

3. **11 unauthenticated routes** — `main_service`: DSA run/submit (anonymous billable E2B execution), system-design submit (anonymous LLM calls), behavioral/pm/aiml question routes. Add `Depends(verify_jwt)`.

4. **"test_user_id" authz bypass** — `main_service/app/routes/roadmap.py:36,68,83,134,158`. Every roadmap query ORs in `user_id == "test_user_id"` — all users see/edit that user's roadmaps.

5. **Rate limiting disabled** — `Scalable_User_Service/.env:16` `ENABLE_RATE_LIMITING=false`. Brute-force login/signup/reset wide open. Also AI_Interviewer POST `/api/token` has no rate limit at all — cost-amplification vector.

6. **AUTH_BYPASS toggle** — `AI_Interviewer/app/services/auth.py:14`. One env var mistake = full auth disable. Gate behind explicit dev check or remove.

7. **Weak JWT posture** — fallback secrets "replace_me_in_env" / "default-fallback-only-for-dev" in config; no audience/issuer validation; algorithm from env not whitelisted; token-in-query-param fallback (`AI_Interviewer/app/services/auth.py:24`) leaks tokens into logs.

## Bugs

| # | Bug | Location |
|---|---|---|
| 1 | SyntaxError, app cannot boot — malformed dict | `Scalable_User_Service/app/api/user.py:761` (verified) |
| 2 | db.query() on AsyncSession — crashes at runtime | `main_service/app/routes/behavioral.py:9`, `pm.py:9` |
| 3 | settings.REDIS_URL never exists — always falls back localhost Redis | `main_service` code_worker.py:47,55, dsa.py:212 (verified) |
| 4 | login() reuses closed DB session + redundant query | `Scalable_User_Service/app/api/user.py:308,333` |
| 5 | achievements silently stripped from profile responses (missing in schema) | `Scalable_User_Service/app/schemas/profile.py:66-101` |
| 6 | Infinite requeue of poison messages, no DLQ | `AI_Interviewer/app/analysis_worker.py:20` |
| 7 | Race: silence monitor + turn handler both mutate state, both call session.say | `AI_Interviewer/app/worker.py:182,481` |
| 8 | conftest imports dead app.tasks.celery_app — entire test suite fails | `Scalable_User_Service/tests/conftest.py:70` |
| 9 | 7 fire-and-forget create_task — lost transcripts/evals on crash | `AI_Interviewer/app/worker.py` |
| 10 | Tests assert Redis pub/sub events code never publishes | `Scalable_User_Service/tests/test_auth.py:288` |

## Architecture / Quality

- **Layering violated everywhere**. CLAUDE.md says API→Service→Repository→DB. Reality: business logic in routes across all 3 services. chat.py ~335 lines logic in routes; signup()/login() ~100-line orchestration in route handlers; evaluate_system_design() LLM call lives in routes file. services/ holds only infra workers.
- **Giant functions**: event_generator ~270 lines, run_code_in_docker ~280, voice_stream ~100, get_user_profile ~120.
- **Dead code**: whole legacy `AI_Interviewer/app/agent/graph.py` (~275 lines) unused; factory.py build_graph(interview_type) ignores its argument; commented-out ORM relationship models/profile.py:38; unused background_tasks param dsa.py:155.
- **Inline imports** scattered in all 3 services (chat.py, user.py, main.py) — PEP8 violation, runtime fragility.
- **Bare except: pass** ~12 sites — cache invalidation, parsing, Opik failures all swallowed silently.
- **Raw SQL in lifespan seeding** (`main.py:43-74`) — belongs in Alembic.
- **~90% duplicated full-profile vs public-profile handlers** (~100 lines).
- **Admin via hardcoded email list** with personal emails as fallback default — use role column.

## Performance / Scalability

1. **Unbounded queries** — DSA questions, chat sessions, submissions: no pagination anywhere.
2. **Whole Redis chat buffer pulled into memory per request** — chat.py:87 `lrange("chat:buffer", 0, -1)`, filtered in Python. O(n) per request.
3. **No DB pool config** — main_service/database.py: no pool_size/max_overflow; 4 uvicorn workers + 3 background workers starve default pool.
4. **New Redis connection per execution / per SSE client** — no pooling; pubsub cleanup unreliable on disconnect (connection leak).
5. **asyncio.to_thread for 30s code runs** — exhausts default thread pool under load; give it dedicated executor.
6. **New httpx.AsyncClient per request** (AI_Interviewer main.py:169) — TLS handshake each call. Singleton client.
7. **Missing composite indexes** — (question_id, session_id) on submissions; (user_id, achievement_id) on UserAchievement.
8. **Admin stats loads ALL completed sessions into memory** — AI_Interviewer/app/routers/admin.py:62. Use SQL aggregation.
9. **Voice latency**: silence-monitor path calls session.say(full_text) — no streaming TTS; sequential DB checks in signup; CSV write to disk per turn on event loop (worker.py:256).
10. **Cost burn**: VLM frame analysis every 3s regardless of silence (~2000 calls/50min interview); analysis retries resend full transcript 3x; no LLM response caching; LLM call every 40s of silence.

## Suggested Fix Order

**Phase 0 (today)**: Rotate AWS/Resend/LiveKit keys. Fix SyntaxError user.py:761 (service is down). ENABLE_RATE_LIMITING=true. Kill /auth/token backdoor. Remove "test_user_id".

**Phase 1 (this week)**: Auth guards on 11 routes. Fix behavioral/pm async crash. Fix REDIS_URL config (rename to actual setting). Login session bug. DLQ + max-retry on analysis worker. Silence-monitor lock. Fix test suite (conftest + pub/sub test).

**Phase 2 (refactor)**: Extract service layer per domain (chat, dsa, users) from routes. Delete dead graph.py. Singleton httpx/Redis/LLM clients. DB pool config + composite indexes. Pagination on list endpoints.

**Phase 3 (scale)**: Aggregate admin stats in SQL. Cache hot LLM evals. VLM frame sampling adaptive (skip during silence). Alembic-managed seed data.
