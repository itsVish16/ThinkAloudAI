# ThinkAloudAI — Target Architecture Proposal

> Status: proposal. Nothing here is implemented yet.
> Based on the July 2026 audit of `main_service`, `Scalable_User_Service`, and `AI_Interviewer`.

---

## 1. What's wrong with the current shape

The three-service split itself is fine. The problems are in **how boundaries were drawn inside and between the services**:

1. **`main_service` is a monolith wearing a microservice costume.** It owns the question catalog (DSA, system design, behavioral, PM, AI/ML), user activity (submissions, problem status), roadmaps, *and* the chat assistant — five unrelated domains in one DB and one deployable.
2. **Identity is fragmented.** `user_id` is `int` in user-service, `String` in main_service, a UUID-ish string in AI_Interviewer. `submissions.session_id` is secretly a user ID. There are two `UserProfileReplica` tables maintained by hand. The main_service `/auth/token` endpoint mints JWTs for anyone — it exists *because* real auth propagation was never built.
3. **Events exist but don't work.** RabbitMQ is declared FANOUT but published with topic routing keys (silently ignored — every consumer gets every event). A whole Redis `user_events` pipeline has zero consumers. Events are published fire-and-forget with no outbox, so DB commits and event publishes can diverge.
4. **Sync coupling where async belongs, async where nothing listens.** Progress/stats (streaks, skill scores, achievements) should be computed from events, but they're entangled with the request path. Meanwhile the "replica" pattern (the right idea for decoupling) is implemented ad-hoc.
5. **Cross-cutting concerns are per-service snowflakes.** Three different SQLAlchemy styles, three auth mechanisms, inconsistent error shapes, no shared event contracts, no DLQs anywhere.

---

## 2. Design principles for the target

1. **One service, one reason to change.** Boundaries follow business domains, not technical layers.
2. **Database-per-service is non-negotiable.** No cross-service FKs, no cross-service joins, ever. Foreign data is either replicated via events (read models) or fetched via a versioned API call.
3. **Synchronous calls only for queries that must be fresh.** Everything that can be eventual is an event.
4. **Events are contracts.** Every event has a versioned schema, an owner, and a topic. Producers never know their consumers.
5. **Identity is established once, at the edge.** One JWT issuer (identity-service), verified at the gateway. Downstream services trust a propagated `X-User-Id` header on the internal network — no service ever re-authenticates end users or mints its own tokens.
6. **Every side effect that must not be lost goes through the outbox.** DB commit and event publish are one transaction.
7. **Boring where possible, clever only where it pays.** Pragmatic service count over microservice maximalism.

---

## 3. Target service map

### Recommended: 4 services + edge (pragmatic)

| Service | Owns | Does NOT own |
|---|---|---|
| **edge-gateway** (Caddy → Kong/Traefik later) | TLS, routing, JWT verification, rate limiting, request-ID injection | Any business logic |
| **identity-service** (evolved user-service) | Users, credentials, profiles, preferences, sessions/JWT issuing | Stats, achievements, anything derived |
| **learning-service** (evolved main_service) | Question catalog (all types), practice/submissions, code execution, roadmaps, chat assistant | User credentials, interview state |
| **interview-service** (evolved AI_Interviewer) | LiveKit sessions, interview state machine, transcripts, feedback/analysis | Question catalog (fetches via event-replicated read model) |

Plus existing serverless: **notification pipeline** (SQS → Lambda → Resend), unchanged.

Why not 7 microservices? The domains that would split out of learning-service (catalog vs practice vs progress) share the same data and the same team. Splitting them buys deploy independence you don't need and costs distributed transactions you can't afford. Split later along the module seams below if a real scaling or team-boundary reason appears.

### Internal module seams inside learning-service

These are separate Python packages with their own routers, services, repositories, and tables — ready to extract into services later:

```
learning-service/app/
  modules/
    catalog/      # dsa_questions, sd_questions, behavioral, pm, aiml (read-heavy, cacheable)
    practice/     # submissions, user_problem_status, code execution via E2B
    progress/     # user stats, streaks, skill scores (projections from events)
    roadmaps/     # roadmaps, topics, items
    assistant/    # chat sessions, messages, RAG agent
```

Modules communicate through the service's internal event bus (same topic exchange, same contracts) — **not** by importing each other's repositories. This is what keeps the seams real.

---

## 4. Identity & auth — the single most important fix

**Current:** three identity schemes, one open mint, session_id-as-user.

**Target:**

```
signup/login ──► identity-service ──► JWT (RS256, iss=identity, sub=user_uuid, exp=15min + refresh)
     │
     ▼
All API calls ──► edge-gateway verifies JWT signature + iss + exp
     │              (public key fetched from identity-service JWKS endpoint, cached)
     ▼
Gateway injects:  X-User-Id: <uuid>   X-Request-Id: <uuid>
     ▼
Downstream services trust X-User-Id (internal network only, Caddy strips client-supplied ones)
```

Rules:

- **One user ID type everywhere: UUID.** `users.id` becomes UUID; every `user_id` / `session_id`-as-user column across all services migrates to it.
- **Delete `/auth/token` from main_service.** It exists only because token propagation was never done.
- **Service-to-service calls** (the few that remain) use short-lived signed tokens from a shared `SERVICE_JWT_SECRET`, or better: mTLS on the internal network.
- **RS256 over HS256** so downstream services and the gateway verify with a public key — no shared secret sprawl.

---

## 5. Event architecture (the loose-coupling backbone)

### Exchange & topics

One RabbitMQ **topic** exchange: `thinkaloud.events`. Routing keys are `<domain>.<entity>.<verb>`:

| Event | Producer | Consumers | Payload (versioned) |
|---|---|---|---|
| `identity.user.registered` | identity | learning, interview (build read replicas), engagement projection | `{user_id, username, display_name, avatar_url}` |
| `identity.user.profile_updated` | identity | learning, interview | same shape |
| `practice.submission.judged` | learning/practice | learning/progress (stats, streaks, skill scores) | `{user_id, question_id, status, difficulty, runtime_ms, judged_at}` |
| `practice.problem.solved` | learning/practice | learning/progress, roadmaps (item completion) | `{user_id, question_id, first_solve}` |
| `interview.session.completed` | interview | learning/progress (interview stats), notification | `{user_id, session_id, type, score, duration_s}` |
| `interview.feedback.ready` | interview | notification (email report) | `{user_id, session_id, feedback_id}` |
| `roadmap.item.completed` | learning/roadmaps | learning/progress | `{user_id, roadmap_id, item_id}` |

### Reliability rules

1. **Outbox pattern**: every service has an `outbox` table. Business write + outbox row commit in one transaction; a relay process publishes to RabbitMQ and marks sent. Kills the "DB committed but event lost" class of bug (and the reverse).
2. **Dead-letter exchange everywhere**: each queue gets `x-dead-letter-exchange=thinkaloud.dlx`, max 3 retries via `x-death` count, then park in DLQ with an alert. Fixes today's infinite-requeue poison loops.
3. **Idempotent consumers**: every event carries `event_id` (UUID); consumers record processed IDs (or use natural idempotency keys like `unique(user_id, question_id)` on `user_problem_status`).
4. **Consumers own projections**: progress/stats are *derived* tables rebuilt from events. `learning_events` becomes the append-only event log this projection is built from.
5. **Delete the Redis `user_events` pipeline** — one event backbone (RabbitMQ), not two.

### Data replication via events (formalized replica pattern)

Today there are two hand-maintained `UserProfileReplica` tables. Keep the pattern, make it principled:

- `learning-service.user_read_model` and `interview-service.user_read_model`: minimal projection (`user_id, username, display_name, avatar_url`), updated only by `identity.user.*` events.
- Never synced by request-path HTTP calls. Staleness of seconds is acceptable for display names.
- Interview-service gets a `question_read_model` (id, title, difficulty, function_name, starter code) fed by a `catalog.question.published` event — removing its sync dependency on the catalog at interview start.

---

## 6. Target DB schemas (per service)

Conventions everywhere: UUID primary keys (`gen_random_uuid()`), `created_at`/`updated_at` timestamptz, JSONB (not `Text`-holding-JSON), SQLAlchemy 2.0 `Mapped[]` style only, Alembic migrations per service, soft deletes only where audit requires.

### 6.1 identity_db (identity-service)

```
users                id uuid PK, email citext UNIQUE, username citext UNIQUE,
                     password_hash text, is_verified bool, created_at, updated_at, last_login_at
user_profiles        user_id uuid PK/FK, bio, avatar_url, github_url, linkedin_url,
                     headline, location, institution, preferred_language, resume_url
user_preferences     user_id uuid PK/FK, theme, email_notifications, push_notifications
refresh_tokens       id uuid PK, user_id FK, token_hash text UNIQUE, expires_at, revoked_at
                     -- replaces stateless-only refresh; enables logout/revocation
outbox               id uuid PK, topic, payload jsonb, occurred_at, published_at NULL
```

Dropped: `UserStats`, `DailyActivity`, `UserSkillScore`, `Achievement`, `UserAchievement`, `LearningEvent` — all move to learning-service progress module (they're derived data, not identity). Admin via env-var email list → `users.role` column (`user|admin`).

### 6.2 learning_db (learning-service)

**catalog module** (content, read-heavy, aggressively cached):

```
questions            id uuid PK, kind enum('dsa','system_design','behavioral','pm','aiml'),
                     title, description text, difficulty enum('easy','medium','hard'),
                     function_name, starter_code jsonb  -- {python: "...", cpp: "..."}
                     test_harness text, hints jsonb,
                     optimal_time_complexity, optimal_space_complexity,
                     status enum('draft','published'), created_at, updated_at
tags                 id, name UNIQUE                      -- 'array', 'dp', 'graphs'...
question_tags        question_id FK, tag_id FK, PK(question_id, tag_id)
question_test_cases  id uuid PK, question_id FK, input jsonb, expected jsonb,
                     is_public bool, order_index int
                     -- replaces test_cases Text blob; queryable, orderable
```

One `questions` table with `kind` replaces five parallel question tables (dsa/system_design/behavioral/pm/aiml) that share 80% of their columns and force five parallel routers/schemas today.

**practice module** (user activity):

```
submissions          id uuid PK, user_id uuid (indexed, no FK — cross-module),
                     question_id FK, code text, language, status,
                     error_message, is_submission bool,
                     execution_time_ms, memory_used_kb, passed_tests, total_tests,
                     created_at
                     INDEX (user_id, created_at DESC), INDEX (question_id, status)
user_problem_status  user_id uuid, question_id FK, status, best_runtime_ms,
                     best_memory_kb, last_attempted_at,
                     PK(user_id, question_id)      -- natural idempotency key
```

`session_id` → `user_id` (uuid). Fixes today's identity confusion and enables the missing pagination indexes.

**progress module** (projections — rebuildable from events):

```
user_stats           user_id PK, problems_solved_total/easy/medium/hard,
                     total_submissions, interviews_completed, avg/best_interview_score,
                     current_streak, longest_streak, last_activity_date, rating
daily_activity       (user_id, activity_date) UNIQUE, counters...
user_skill_scores    (user_id, domain) UNIQUE, score, problems_solved, interviews_done
achievements         id, title, description, icon_url, rule jsonb   -- rule drives auto-award
user_achievements    (user_id, achievement_id) UNIQUE, earned_at
processed_events     event_id uuid PK, processed_at   -- consumer idempotency
```

**roadmaps module**: as today, plus `roadmap_items.question_id uuid FK → questions` (replaces the loose `content_type`+`content_id` string pair), remove `or_(user_id=='test_user_id')`, add `is_template` flag instead of nullable user_id for general roadmaps.

**assistant module**: `chat_sessions(id uuid, user_id uuid, title, created_at)`, `chat_messages(id, session_id FK, role, content, created_at, INDEX(session_id, created_at))`.

### 6.3 interview_db (interview-service)

```
interview_sessions   id uuid PK, user_id uuid (indexed), interview_type, difficulty,
                     stage, status enum('active','completed','abandoned'),
                     started_at, ended_at
                     -- state_data JSONB: keep ONLY as recovery snapshot, not source of truth
transcript_entries   id uuid PK, session_id FK, seq int, role, content, created_at,
                     UNIQUE(session_id, seq)
                     -- transcript becomes rows, not a JSON blob in state_data
interview_feedback   session_id UNIQUE FK, technical_score, communication_score,
                     english_score, strengths, weaknesses, improvement_plan,
                     recommended_topics jsonb, detailed_metrics jsonb
user_read_model      user_id PK, username, display_name, avatar_url, synced_at
question_read_model  question_id PK, title, difficulty, starter_code jsonb, synced_at
outbox               ...
```

Dropped: `interview_questions`, `interview_responses` (dead tables — nothing reads or writes them).

---

## 7. How components connect (target flow)

```
                 ┌──────────────────────────────────────────────┐
Browser ──HTTPS──►  edge-gateway (Caddy)                         │
                 │  TLS · JWT verify (JWKS) · rate limit ·       │
                 │  X-User-Id / X-Request-Id injection           │
                 └───┬───────────┬───────────────┬──────────────┘
                     │           │               │
              identity:8000  learning:8001   interview-api:8002
                     │           │               │        │
                     │           │               │   interview-worker ◄──► LiveKit (WebRTC)
                     │           │               │        │
                     └─────┬─────┴───────┬───────┘        │
                           │   Postgres (3 DBs)           │
                           │   Redis (cache/rate-limit)   │
                           └──────────► RabbitMQ topic exchange ◄──┐
                                        thinkaloud.events         │
                                              │                   │
                              progress projection consumers       │
                              question/user read-model consumers ─┘
                                              │
                              DLX: thinkaloud.dlx (retry x3 → park + alert)

  identity ──► SQS ──► Lambda ──► Resend   (notifications, unchanged)
  learning/practice ──► E2B sandboxes      (code execution, unchanged)
  Datadog agent ◄── all containers (ddtrace-run, unchanged)
```

Sync HTTP between services is allowed for exactly two things: (a) reads that must be fresh (rare), (b) interview-api fetching a question snapshot at session start — which the `question_read_model` eventually removes.

---

## 8. Cross-cutting standards

- **Cache-aside with stampede protection** (Redis `SET NX` mutex) for catalog reads and profile reads. Catalog questions cache for 1h+ (they're near-immutable); invalidate on `catalog.question.published`.
- **Pagination contract**: every list endpoint takes `cursor` + `limit` (keyset pagination on `created_at, id`), never offset, never unbounded.
- **Error contract**: one shape — `{error: {code, message, request_id}}`; no stack traces outward, full trace in Datadog via request-id correlation.
- **Retries**: outbound HTTP (LLM, E2B, Resend) with exponential backoff + jitter + circuit breaker (e.g. `tenacity`); message consumers with retry-count → DLQ.
- **Rate limiting at the edge** (per-IP on auth endpoints, per-user on execution/LLM endpoints) — this is where the login-lockout logic moves, fixing the pre-signup DoS as a side effect.
- **Secrets**: nothing in code, no weak defaults — app refuses to boot if `JWT_SECRET`/`DB_PASSWORD` are unset or equal known defaults.
- **CI per service** (lint → typecheck → test → build); contract tests for event schemas (producer publishes, consumer validates against shared pydantic contract package `thinkaloud-contracts`, versioned).

---

## 9. Migration path (phased, each phase ships value)

**Phase 0 — Stop the bleeding (1–2 days, no schema changes)**
Silence-monitor fix, auth sweep on open endpoints, delete `/auth/token`, kill `test_user_id` fallbacks, fix `AsyncSession.query()` crashes, fix test-suite import, add DLQs, delete dead code/tables/deps.

**Phase 1 — Identity unification (1 week)**
UUID user IDs, JWT RS256 + JWKS, gateway-side verification + `X-User-Id` propagation, `submissions.session_id → user_id` migration, refresh-token table, role column replacing admin email env-var.

**Phase 2 — Event backbone (1 week)**
Topic exchange, event contracts package, outbox tables + relays in all three services, progress module becomes a projection consumer, delete Redis `user_events`, formalize read models.

**Phase 3 — Schema normalization (1–2 weeks)**
Unify question tables into `questions` + `question_test_cases` + tags, transcript rows in interview-service, drop dead tables, keyset pagination everywhere.

**Phase 4 — Module seams (ongoing)**
Reorganize learning-service into the five internal modules with event-only cross-module communication. Extract to a real service only when a scaling/team reason forces it.

Each phase is independently deployable and reversible; phases 1–3 are where 90% of the coupling and correctness wins live.
