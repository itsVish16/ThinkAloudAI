# Building a ChatGPT-like Chatbot UI in ReactJS — Production-Grade Plan

This document is a complete blueprint for turning the existing chat stack in this repo
([`src/components/chat/`](src/components/chat), [`src/services/chatService.ts`](src/services/chatService.ts))
into a **production-grade, ChatGPT-class** conversational UI with first-class support for
**streaming answers**, **reasoning/thinking display**, and **tool calling**.

---

## 1. What "ChatGPT-class" actually requires

A real ChatGPT UI is not just a message list. It is a **streaming, event-driven, stateful**
application. The hard parts are:

1. **Token streaming** — answers appear word-by-word, not after the full response.
2. **Reasoning / "thinking"** — the model's chain-of-thought is shown in a collapsible block
   *while* it thinks, then auto-collapses when the final answer arrives.
3. **Tool calling** — the model can invoke tools (search, code-exec, db query, roadmaps…).
   Each invocation must render as a live card with `pending → running → completed/failed`
   states and a result summary.
4. **Mixed-order events** — reasoning, tool calls, and final tokens can interleave in any
   order within a single assistant turn. The UI must place each event in the correct slot
   of the current assistant message, not create a new message per event.
5. **Interruptibility** — the user can stop generation mid-stream.
6. **Persistence + replay** — past sessions reload from the backend and must render the
   same way they were produced (including tool calls and reasoning), even though the live
   stream is gone.
7. **Resilience** — network drops, partial chunks, malformed SSE lines, auth expiry.

Your repo already has the bones for 1, 2, 3, 6. The plan below upgrades each to
production quality and fills the gaps.

---

## 2. Architecture overview

```
┌──────────────────────────────────────────────────────────────┐
│  React UI (single source of truth: messages[] in ChatScreen) │
│                                                              │
│  ChatScreen                                                  │
│   ├─ MessageList (virtualized)                               │
│   │    └─ MessageBubble                                      │
│   │         ├─ ReasoningBlock   (thinking)                   │
│   │         ├─ ToolCallBlock[]   (tool calls)                │
│   │         └─ MarkdownAnswer    (streamed content)          │
│   ├─ Composer / ChatInput       (send, stop, attach)         │
│   └─ Sidebar (sessions, new chat, rename, delete)            │
│                                                              │
│  services/                                                   │
│   ├─ chatService.ts   (REST: sessions, messages)             │
│   └─ chatStream.ts    (SSE event pump → typed events)        │
└──────────────────────────────────────────────────────────────┘
                          │ fetch / SSE (Server-Sent Events)
                          ▼
                  LangGraph / LLM backend
```

**Key principle:** the backend emits a single normalized SSE event stream.
The frontend has **one reducer** that turns those events into updates on the
current assistant `Message`. Everything visual is a pure function of `messages[]`.

---

## 3. The streaming event contract (the most important part)

A ChatGPT-like UI lives or dies on the **event schema**. Define it once and make the
backend obey it. Upgrading [`chatService.ts`](src/services/chatService.ts:99) (which already
switches on `event.type`) to this richer contract:

```ts
type StreamEvent =
  | { type: "session.ready"; session_id: string }
  | { type: "message.start"; message_id: string }
  | { type: "reasoning.delta"; text: string }          // chain-of-thought token
  | { type: "reasoning.done" }
  | { type: "tool.call"; tool_id: string; name: string; args: unknown }
  | { type: "tool.result"; tool_id: string; output: unknown; duration_ms: number; status: "ok" | "error" }
  | { type: "token"; text: string }                     // final-answer token
  | { type: "message.done"; message_id: string }
  | { type: "error"; message: string };
```

Why this shape:
- `reasoning.delta` is separate from `token` so thinking and the final answer can render
  in different regions of the same bubble (exactly like ChatGPT's "Thought for Xs" block).
- `tool.call` / `tool.result` are keyed by `tool_id` so multiple parallel tools can be
  tracked and updated independently (your current `ToolExecution` already has `id` — good).
- `message.start` / `message.done` give deterministic boundaries for stop, retry, and
  persistence replay.

---

## 4. State model & the reducer

Move the streaming mutation logic out of imperative `setState` callbacks into a single
pure reducer. This is the single biggest production upgrade over the current
[`ChatScreen.tsx`](src/components/chat/ChatScreen.tsx:40) which patches state with several
`setMessages` calls inside `startChatStream` callbacks.

```ts
interface ChatState {
  messages: Message[];
  status: "idle" | "streaming" | "error";
  activeAssistantId: string | null;
}

type ChatAction =
  | { type: "USER_SEND"; message: Message }
  | { type: "ASSISTANT_START"; id: string }
  | { type: "REASONING_DELTA"; id: string; text: string }
  | { type: "REASONING_DONE"; id: string }
  | { type: "TOOL_CALL"; id: string; tool: ToolExecution }
  | { type: "TOOL_RESULT"; id: string; tool_id: string; patch: Partial<ToolExecution> }
  | { type: "TOKEN"; id: string; text: string }
  | { type: "ASSISTANT_DONE"; id: string }
  | { type: "ERROR"; id: string; message: string }
  | { type: "STOP"; id: string }
  | { type: "LOAD_HISTORY"; messages: Message[] };
```

The reducer **always** updates by `id` (the active assistant message), never appends a new
message mid-stream. This is what prevents the classic bug of "each token creates a new
bubble".

---

## 5. Showing "thinking" in the UI

You already have [`ReasoningBlock.tsx`](src/components/chat/ReasoningBlock.tsx:11).
Production-grade behaviors to add:

1. **Live typing while reasoning** — append `reasoning.delta` text with a blinking cursor
   (`▍`) while `isThinking` is true.
2. **Auto-collapse on `reasoning.done`** — already done via the `useEffect` in
   [`ReasoningBlock.tsx`](src/components/chat/ReasoningBlock.tsx:16). Keep it.
3. **Duration label after collapse** — "Thought for 3.2s" (track start/end timestamps).
4. **Streaming markdown** — render reasoning with [`ReactMarkdown`](src/components/chat/ReasoningBlock.tsx:4)
   *incrementally*; it already does, but wrap in a `memo` so token appends don't reparse
   the whole tree each tick.
5. **Privacy toggle** — some deployments hide reasoning for end users; gate via a prop.
6. **Reduced-motion support** — disable `animate-pulse` when `prefers-reduced-motion`.

---

## 6. Showing tool calling in the UI

You already have [`ToolCallBlock.tsx`](src/components/chat/ToolCallBlock.tsx:16) with a
status state machine and an icon map. Production upgrades:

1. **Lifecycle from events** — `tool.call` → status `running` (with spinner),
   `tool.result` → `completed` (green check) or `failed` (red).
2. **Expandable result** — clicking the card expands to show the raw `args` and `output`
   in a syntax-highlighted viewer (reuse
   [`SyntaxHighlighter.tsx`](src/components/SyntaxHighlighter.tsx)).
3. **Per-tool icon mapping** — extend the `iconMap` in
   [`ToolCallBlock.tsx`](src/components/chat/ToolCallBlock.tsx:8) to cover all backend
   tools; fall back to a generic `Wrench` icon.
4. **Summary, not dump** — show `outputSummary` (one line) collapsed; full output expanded.
   The backend should send a `summary` field so the UI doesn't render megabytes.
5. **Parallel tools** — render multiple cards stacked; each keyed by `tool_id`.
6. **Tool errors are non-fatal** — a failed tool shows red but the assistant continues with
   a follow-up token stream explaining the failure.
7. **Re-run / approve** (optional, for agentic UIs) — add an "Approve" button on
   human-in-the-loop tools; emit a `tool.approve` event back to the backend.

---

## 7. The message bubble layout (ChatGPT parity)

Inside one assistant [`MessageBubble`](src/components/chat/MessageBubble.tsx:27), the
vertical order must be:

```
┌─────────────────────────────┐
│ ▶ Thought for 3.2s          │  ReasoningBlock (collapsible)
│   "Let me consider…"        │
├─────────────────────────────┤
│ 🔍 Searched the web · 1.1s  │  ToolCallBlock(s)
│ 📦 Retrieved 5 docs         │
├─────────────────────────────┤
│ The answer is… (streaming)  │  MarkdownAnswer
│ ```code```                  │
│ [Copy] [Retry] [Regenerate] │  action row
└─────────────────────────────┘
```

This is exactly how ChatGPT orders reasoning → tools → answer, and your component tree
already supports it — just confirm the render order in
[`MessageBubble.tsx`](src/components/chat/MessageBubble.tsx:50).

---

## 8. Streaming, interruption & resilience

1. **AbortController** — you already keep `abortControllerRef` in
   [`ChatScreen.tsx`](src/components/chat/ChatScreen.tsx:47). Wire a **Stop** button that
   calls `abort()` and dispatches `STOP`, freezing the partial assistant message in place
   (ChatGPT keeps the partial text — do the same).
2. **SSE reassembly** — your line-splitting buffer in
   [`chatService.ts`](src/services/chatService.ts:84) is correct; keep it. Add a guard for
   `data: [DONE]` sentinel.
3. **Reconnect / resume** — on network drop mid-stream, do not silently fail; show a
   "Connection lost — Retry" banner and resume by replaying the user message or by a
   backend `resume` endpoint keyed on `message_id`.
4. **Backpressure** — batch multiple `token` events into one `setState` per animation frame
   (use `requestAnimationFrame`) to avoid 60+ renders/sec on fast token streams.
5. **Token coalescing** — accumulate tokens in a ref and flush on a 16ms timer; this is
   the single biggest performance win for streaming UIs.

---

## 9. Performance = production grade

| Concern | Solution |
|---|---|
| Long sessions (1000s of messages) | Virtualize [`MessageList`](src/components/chat/ChatScreen.tsx) with `react-virtuoso` or `@tanstack/react-virtual`. Keep unmounting from destroying streaming state by lifting active message out of the virtual window. |
| Re-renders on every token | `React.memo` on `MessageBubble`; only the active assistant bubble should re-render. Use a selector/store so inactive bubbles never subscribe to token updates. |
| Markdown re-parse cost | `memo` + stable `components` map; consider `markdown-it` streaming or `marked` + manual `dangerouslySetInnerHTML` for very long answers. |
| Image / code highlight cost | Lazy-mount [`SyntaxHighlighter`](src/components/SyntaxHighlighter.tsx) only when a code block scrolls into view (`IntersectionObserver`). |
| Memory | Cap retained messages; paginate history via cursor from `getSessionMessages` ([`chatService.ts`](src/services/chatService.ts:26)). |

Consider introducing a small store (Zustand) to replace prop-drilling and to make
"only-active-bubble re-renders" trivial.

---

## 10. Composer / input

[`ChatInput.tsx`](src/components/chat/ChatInput.tsx) should support:

- `Enter` to send, `Shift+Enter` newline, `Cmd/Ctrl+Enter` force-send.
- **Stop** button visible only while `status === "streaming"`.
- **Auto-grow textarea** up to a max height, then scroll.
- **Attachments** (images) — you already pass `images` to
  [`startChatStream`](src/services/chatService.ts:43); show thumbnails + paste-from-clipboard.
- **Disabled state** while streaming (or allow queued sends — product decision).
- **Edit & resend** a previous user message (ChatGPT feature) — dispatch `LOAD_HISTORY`
  with a truncated tail then re-send.

---

## 11. Sidebar / session management

Production chat UIs need:
- New chat, rename (you have `onRenameChat` in [`ChatScreen.tsx`](src/components/chat/ChatScreen.tsx:14)),
  delete ([`deleteSession`](src/services/chatService.ts:34)).
- **Title auto-generation** from the first user message (backend or client heuristic).
- **Search sessions** and **group by date** (Today / Yesterday / Previous 7 days).
- **Active session highlight** and optimistic UI for delete/rename.

---

## 12. Persistence & replay fidelity

The tricky part: a streamed message is rebuilt from events live, but history is loaded
from DB rows ([`getSessionMessages`](src/services/chatService.ts:26)). To make replay
identical to live:

1. **Persist structured message parts**, not just a flat `content` string. Store:
   `content`, `reasoning`, `tool_calls[]` as columns/JSON on the message row.
2. On load, hydrate a `Message` with `thinkingContent`, `toolInvocations`, and `content`
   already separated — no regex parsing of `<MeshThink>` tags (the legacy fallback in
   [`MessageBubble.tsx`](src/components/chat/MessageBubble.tsx:38) is a smell to retire).
3. Mark replayed messages `isThinking=false` and tool calls `completed`.

---

## 13. Accessibility & polish

- All collapsibles are real `<button>`s with `aria-expanded` (you use buttons in
  [`ReasoningBlock.tsx`](src/components/chat/ReasoningBlock.tsx:28) — good; add the aria).
- Focus management: after send, keep focus in composer; after stop, return focus to composer.
- Screen-reader live region announcing "Assistant is typing…", "Tool completed".
- Keyboard nav across messages.
- `prefers-reduced-motion` to disable framer-motion animations
  ([`ReasoningBlock.tsx`](src/components/chat/ReasoningBlock.tsx:3) uses framer-motion).
- Copy-to-clipboard with toast confirmation (you have `Copy`/`Check` in
  [`MessageBubble.tsx`](src/components/chat/MessageBubble.tsx:8)).

---

## 14. Error handling & edge cases

| Case | Behavior |
|---|---|
| Auth expired (401) | [`apiClient`](src/services/apiClient.ts) should refresh token or redirect to [`LoginPage`](src/pages/LoginPage.tsx); never dump raw 401 into chat. |
| Stream error mid-way | Keep partial answer, append a red inline error chip, offer Retry. |
| Tool throws | `tool.result` with `status:"error"`; card red; assistant explains. |
| Empty response | Show "No response" placeholder, not a blank bubble. |
| Rate limited (429) | Toast + retry-after countdown. |
| Malformed SSE line | Already logged in [`chatService.ts`](src/services/chatService.ts:113); also surface a non-fatal warning. |

---

## 15. Suggested file / module layout

```
src/
  components/chat/
    ChatScreen.tsx          (orchestrator + reducer hookup)
    MessageList.tsx         (NEW: virtualized list)
    MessageBubble.tsx       (layout: reasoning → tools → answer)
    ReasoningBlock.tsx      (thinking UI)
    ToolCallBlock.tsx       (tool lifecycle card)
    MarkdownAnswer.tsx      (NEW: extracted streamed markdown + actions)
    ChatInput.tsx           (composer)
    ChatSidebar.tsx         (NEW: sessions)
  state/
    chatReducer.ts          (NEW: pure reducer + actions)
    chatStream.ts           (NEW: SSE pump → actions, extracted from chatService)
  services/
    chatService.ts          (REST only: sessions, messages)
  hooks/
    useChatSession.ts       (NEW: wires reducer + stream + persistence)
    useAutoScroll.ts        (NEW: smart scroll that doesn't fight the user)
```

---

## 16. Phased implementation roadmap

**Phase 0 — Contract (1 day)**
Agree the `StreamEvent` schema (§3) with the backend; update
[`chatService.ts`](src/services/chatService.ts:99) switch cases.

**Phase 1 — Reducer & stream pump (1–2 days)**
Extract `chatReducer.ts` and `chatStream.ts`; replace imperative `setMessages` in
[`ChatScreen.tsx`](src/components/chat/ChatScreen.tsx). Behavior unchanged, but
state mutations are now pure and testable.

**Phase 2 — Reasoning + tool polish (1 day)**
Add duration labels, expandable tool results, streaming cursor, aria attributes
(§5, §6, §13). Retire the `<MeshThink>` regex fallback (§12).

**Phase 3 — Performance (1–2 days)**
Token coalescing via rAF, `React.memo` boundaries, virtualized `MessageList`,
lazy syntax highlighting (§9).

**Phase 4 — Composer & sidebar (1–2 days)**
Stop button, edit-resend, attachments UX, session search/grouping (§10, §11).

**Phase 5 — Resilience & a11y (1 day)**
Reconnect banner, retry, reduced-motion, live regions, keyboard nav (§8, §13, §14).

**Phase 6 — Persistence fidelity (1 day)**
Backend stores structured parts; client hydrates without regex (§12).

---

## 17. Why this approach

- **One event contract, one reducer** → every UI state is predictable and testable;
  this is the architectural difference between a "demo chat" and "ChatGPT-class chat".
- **Reasoning and tools are first-class event types**, not string-encoded inside content,
  so the UI can place them in dedicated regions and replay them faithfully.
- **Performance is designed in** (coalescing, memo, virtualization) rather than bolted on,
  which is what makes it feel "production grade" at 100k-token sessions.
- **The plan reuses your existing components** — [`ReasoningBlock`](src/components/chat/ReasoningBlock.tsx),
  [`ToolCallBlock`](src/components/chat/ToolCallBlock.tsx), [`MessageBubble`](src/components/chat/MessageBubble.tsx),
  [`chatService`](src/services/chatService.ts) — so it is incremental, not a rewrite.

Start with Phase 0 + Phase 1; everything else is additive on top of the reducer.
