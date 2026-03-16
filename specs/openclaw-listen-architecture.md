# openclaw-listen Architecture v1

## Status

Proposed architecture spec for a new `openclaw-listen` component inside `linux-agents`.

- **Document type:** architecture / product-technical spec
- **Version:** v1
- **Implementation status:** not implemented
- **Goal:** define a listener that is complementary to `listen`, but native to the OpenClaw runtime and tool model

---

## 1. Overview

`openclaw-listen` is an OpenClaw-native async job listener for `linux-agents`.

Its purpose is to accept automation requests from multiple entrypoints, normalize them into a common job envelope, execute them through OpenClaw session primitives, and return user-friendly results suitable for chat surfaces such as Telegram and Discord.

Conceptually:

- `listen` is a **Codex-centric HTTP job server** that launches a tmux worker and drives `codex exec`
- `openclaw-listen` should be an **OpenClaw-centric orchestration layer** that launches work through OpenClaw-native runtime mechanisms

It should sit at the boundary between:

- external callers or internal platform events
- runtime orchestration (`sessions_spawn`, subagents, ACP where useful)
- output shaping for human-facing messaging channels

The component is not a generic shell job server like `rpi-job`, and it should not be a thin wrapper around `codex exec`. Its main value is understanding OpenClaw’s execution model and chat-native delivery semantics.

---

## 2. Motivation

The current repository already has two job patterns:

1. **`rpi-job`** — generic subprocess execution over HTTP
2. **`listen`** — agent-oriented job execution, but tightly coupled to Codex CLI + tmux

That leaves a gap:

- no listener that is native to **OpenClaw sessions and subagents**
- no first-class path for accepting work from **OpenClaw gateway messaging surfaces**
- no standard result model optimized for **Telegram/Discord delivery**
- no architecture that can choose between **direct inline work**, **subagent delegation**, or **ACP-backed tool execution** based on task shape

`openclaw-listen` exists to close that gap.

### Why not just keep using `listen`?

Because `listen` assumes the worker is a Codex CLI process inside tmux. That is effective for Codex-driven jobs, but it is the wrong abstraction for an OpenClaw deployment where:

- the runtime already knows how to spawn sessions and subagents
- tools are first-class and policy-aware
- messaging channels are first-class destinations, not an afterthought
- the execution strategy may vary by job type

In short: `listen` launches an LLM process. `openclaw-listen` should orchestrate OpenClaw work.

---

## 3. Positioning and Comparison with `listen`

### Shared intent

Both components:

- accept asynchronous jobs
- persist job state
- provide a queryable record of progress and outcome
- decouple submission from execution

### Key differences

| Topic | `listen` | `openclaw-listen` |
|---|---|---|
| Primary runtime | Codex CLI in tmux | OpenClaw sessions / subagents / ACP-aware execution |
| Coupling | Strongly coupled to Codex | Coupled to OpenClaw runtime contracts |
| Main input | HTTP prompt submission | HTTP + direct internal calls + gateway/messaging events |
| Result shape | Raw text summary from worker output | Structured result envelope + chat-friendly rendering |
| Delivery target | Poll/read later via HTTP | Pull via API and optionally push to Telegram/Discord |
| Execution model | One worker process per job | Strategy-based orchestration per job type |
| Tooling assumption | Shell + tmux + codex exec | OpenClaw tools, policies, channels, and subagents |
| Best for | Codex job execution | OpenClaw-native assistants and multi-channel workflows |

### Relationship between the two

`openclaw-listen` should be treated as **complementary**, not as an immediate replacement.

Recommended positioning:

- keep `listen` for Codex-specific remote job workflows
- use `openclaw-listen` for OpenClaw-native automation, agent delegation, and messaging-first operations

This avoids unnecessary migration pressure and preserves a clean separation of concerns.

---

## 4. Design Goals

### Primary goals

1. **OpenClaw-native runtime integration**
   - execute work using session/subagent patterns instead of embedding a specific CLI model runner

2. **Multi-ingress support**
   - receive jobs from HTTP, internal/direct calls, and gateway-backed messaging events

3. **Friendly, structured output**
   - produce machine-readable state plus concise, readable summaries for chat delivery

4. **Operational clarity**
   - persist enough job metadata for monitoring, retries, debugging, and auditing

5. **Pragmatic v1 scope**
   - prefer a small reliable core over a too-clever orchestration engine

### Non-goals for v1

- full workflow DSL
- arbitrary distributed scheduling across multiple hosts
- durable queue semantics comparable to Kafka/RabbitMQ
- advanced retry orchestration with exponential backoff matrices
- graphical dashboard
- replacing OpenClaw gateway itself

---

## 5. Supported Inputs

`openclaw-listen` v1 should support three ingress classes.

## 5.1 REST API

Primary external integration surface for automation systems.

Example uses:

- submit a long-running job from CI
- request a remote agent action from another service
- query job state and retrieve structured result

Suggested endpoints:

- `POST /jobs` — submit job
- `GET /jobs/{id}` — full job state
- `GET /jobs` — list/filter jobs
- `POST /jobs/{id}/cancel` — request cancellation
- `POST /jobs/{id}/retry` — resubmit from previous spec if eligible

REST should accept the normalized job envelope directly.

## 5.2 Direct/Internal Invocation

For code running on the same host or within the same repository/runtime.

Example uses:

- `linux-agents` utilities that want to submit work without HTTP overhead
- internal orchestration modules
- tests and fixtures

This path should call the same normalization and scheduling pipeline as REST, just without network transport.

Design principle: **one core service, multiple adapters**.

## 5.3 Gateway / Messaging Ingress

For jobs initiated from chat platforms through the OpenClaw gateway.

Example uses:

- Telegram message invokes a long-running task
- Discord mention starts an automation workflow
- a bot command results in an async delegated job

This ingress is important because it is where OpenClaw has a natural advantage over `listen`: the system already understands channels, message IDs, reply threading, and message delivery.

For v1, the gateway ingress can be command-driven rather than fully generic. Example patterns:

- explicit slash/command syntax
- explicit “run async” or “delegate” flows
- selected automations wired to `openclaw-listen`

---

## 6. Proposed Job Model

Each inbound request should be normalized into a single job record.

### Core fields

- `id`
- `kind`
- `source`
- `status`
- `created_at`
- `updated_at`
- `submitted_by`
- `instruction`
- `input`
- `execution`
- `delivery`
- `artifacts`
- `updates`
- `result`
- `error`

### Suggested status lifecycle

- `queued`
- `planning`
- `running`
- `waiting`
- `succeeded`
- `failed`
- `cancelled`

`waiting` is useful when the runtime is blocked on external confirmation, browser attach, human approval, or a subagent/tool completion boundary.

---

## 7. Suggested YAML Schema

The YAML below is intentionally opinionated but small enough for v1.

```yaml
id: 7d2f3d9a
kind: task
status: queued
priority: normal

source:
  type: telegram            # rest | direct | telegram | discord | gateway
  channel: telegram
  chat_id: "1129943309"
  message_id: "88421"
  user_id: "1129943309"
  request_id: null

submitted_by:
  actor_type: user          # user | system | service
  actor_id: "telegram:1129943309"
  display_name: Alysson

instruction: >-
  Abra o Chromium, valide a página de status e me devolva um resumo curto.

input:
  mode: natural_language    # natural_language | structured
  args: {}
  attachments: []
  context_refs:
    - linux-agents/specs/terminal-and-browser.md

execution:
  strategy: auto            # auto | inline | subagent | acp
  timeout_seconds: 900
  max_turns: 40
  working_dir: /home/alyssonpi/.openclaw/workspace
  tools_allow:
    - browser
    - exec
    - read
    - write
  requires_approval: inherit
  concurrency_key: null

delivery:
  mode: reply               # reply | silent | poll_only | push
  audience: human           # human | machine | both
  channels:
    - type: telegram
      target: "1129943309"
      thread_id: null
      reply_to_message_id: "88421"
  format:
    style: friendly_short   # raw | structured | friendly_short | friendly_detailed
    include_artifacts: true
    max_chars: 2500

artifacts: []
updates: []

result:
  summary: ""
  details: ""
  structured: {}

error: null

created_at: 2026-03-16T20:00:00Z
updated_at: 2026-03-16T20:00:00Z
started_at: null
completed_at: null
```

### Schema notes

- `source` preserves enough transport metadata to reply in the right place
- `execution.strategy=auto` lets the scheduler choose the runtime path
- `delivery.format.style` decouples execution from presentation
- `result.structured` allows API consumers to parse outcomes without scraping human text
- `updates` remains append-only and human-readable for debugging and streaming

---

## 8. Internal Architecture

## 8.1 Main Components

### 1. Ingress Adapters

Transport-specific adapters that translate inbound requests into the normalized job envelope.

Examples:

- REST adapter
- direct Python adapter
- gateway message adapter

Responsibility ends after validation + normalization.

### 2. Job Store

Persists job state and supports listing/querying.

For v1, YAML storage is acceptable and consistent with the current repo patterns.

Suggested filesystem layout:

```text
openclaw-listen/
  jobs/
    queued/
    running/
    completed/
    failed/
    cancelled/
    archived/
```

Alternative v1 simplification:

```text
openclaw-listen/jobs/
  <job-id>.yaml
  archived/<job-id>.yaml
```

The simpler single-directory layout is probably enough for v1 unless queue scanning becomes noisy.

### 3. Scheduler / Strategy Selector

Chooses how to execute a job.

Input signals:

- source type
- declared execution strategy
- timeout
- estimated complexity
- whether chat push delivery is required
- whether ACP/tool access is needed

### 4. Runtime Executor

Executes the job according to the chosen strategy.

This is the core difference versus `listen`.

### 5. Result Renderer

Transforms raw execution outputs into:

- API-friendly structured result
- Telegram-friendly summary
- Discord-friendly summary

### 6. Delivery Dispatcher

Pushes completion/updates to messaging channels when configured.

---

## 8.2 Execution Strategies

v1 should support a small set of strategies.

### Strategy A — Inline session work

Best for:

- short jobs
- deterministic tool sequences
- low-overhead internal operations

Characteristics:

- minimal orchestration overhead
- easier debugging
- less isolation than subagents

### Strategy B — Subagent execution

Best for:

- non-trivial tasks
- long-running work
- work that benefits from isolated context
- jobs that should complete asynchronously and report back later

Characteristics:

- maps naturally to OpenClaw’s push-based completion model
- cleaner separation between listener control plane and task execution plane
- easier to scale conceptually without binding to a shell worker

This should likely be the **default strategy for natural-language async jobs**.

### Strategy C — ACP-backed execution

Best for:

- environments where capability packaging matters
- delegated tool execution that should be expressed through ACP-compatible control boundaries
- future interoperability with broader OpenClaw ecosystems

For v1, ACP should be **optional and explicit**, not the default for every job.

Reason: ACP is valuable, but forcing it into the first iteration risks architecture inflation before the ingestion and result pipeline are stable.

---

## 8.3 Recommended v1 Runtime Policy

A pragmatic policy for `execution.strategy=auto`:

1. **Structured internal job with known small scope** → `inline`
2. **Natural-language async job from REST/direct** → `subagent`
3. **Gateway/chat-originated job needing reply delivery** → `subagent`
4. **Specialized toolpack / ACP integration requested** → `acp`

This keeps the default behavior predictable:

- trivial jobs avoid unnecessary spawning
- chat jobs get isolation and better completion semantics
- ACP remains available without becoming mandatory ceremony

---

## 9. Internal Flows

## 9.1 REST Submission Flow

```text
POST /jobs
  -> validate request
  -> normalize to job YAML
  -> persist status=queued
  -> scheduler selects strategy
  -> mark status=planning/running
  -> execute via inline/subagent/ACP
  -> append updates during progress
  -> write structured result
  -> optionally push human-friendly completion message
  -> mark succeeded/failed/cancelled
```

## 9.2 Direct/Internal Flow

```text
internal caller
  -> submit_job(job_spec)
  -> same validation + normalization
  -> same scheduler
  -> same persistence + result path
```

No parallel codepath should bypass the core state machine.

## 9.3 Gateway/Messaging Flow

```text
incoming Telegram/Discord event
  -> message adapter parses intent
  -> create job with source metadata
  -> optional immediate acknowledgement message
  -> subagent executes task
  -> result renderer creates channel-specific summary
  -> delivery dispatcher replies in original thread/channel
  -> job state finalized
```

### Immediate acknowledgement behavior

For chat channels, v1 should generally send a lightweight acknowledgement when the job is clearly asynchronous.

Examples:

- Telegram: "Recebi. Vou executar isso em background e te mando o resultado aqui."
- Discord: "Running this asynchronously — I’ll post the result in this thread."

This matters because silent async behavior feels broken in chat.

---

## 10. Result Delivery for Telegram and Discord

This is a first-class requirement, not a formatting footnote.

## 10.1 Output Principles

Results delivered to chat should be:

- concise first
- structured when helpful
- explicit about success/failure
- safe for mobile reading
- artifact-aware

The listener should not dump raw logs unless explicitly requested.

## 10.2 Suggested Result Envelope

Internally:

```yaml
result:
  outcome: succeeded
  summary: Chromium opened and the status page reports all checks healthy.
  details: >-
    Verified page load, located the health summary, and confirmed there were no visible error indicators.
  structured:
    checks_passed: 3
    checks_failed: 0
    url: https://example.local/status
  artifacts:
    - type: screenshot
      path: artifacts/status-page.png
      caption: Status page after validation
```

## 10.3 Telegram Rendering Guidance

Telegram works best with:

- short paragraphs
- bullets
- selective emoji/status markers
- compact artifact captions

Suggested rendering shape:

```text
✅ Job concluído

Resumo:
- Chromium abriu corretamente
- Página de status carregou
- 3 verificações OK, 0 falhas

Se quiser, eu também posso te mandar os detalhes técnicos ou os logs.
```

If there are artifacts:

- send the summary first or as caption
- attach screenshot/file when useful
- avoid overly long captions that get truncated or become annoying to read

## 10.4 Discord Rendering Guidance

Discord supports longer formatting, but v1 should still prefer compactness.

Suggested rendering shape:

```text
✅ Completed
- Opened Chromium successfully
- Validated status page
- Result: 3 checks passed, 0 failed
- Artifact: screenshot attached
```

For Discord specifically:

- avoid markdown tables for routine results
- prefer bullets
- use thread replies when the source message came from a thread

## 10.5 Failure Rendering

Failures should separate:

- what failed
- whether anything partial succeeded
- what the operator can do next

Example:

```text
⚠️ Job falhou
- Consegui abrir o navegador
- A página não carregou dentro de 30s
- Não houve validação final

Próximo passo sugerido: tentar novamente ou verificar conectividade da aplicação.
```

That is much more useful than pasting a stack trace into a chat like a crime scene report.

---

## 11. Persistence and State Handling

v1 can stay with YAML-backed job storage, matching the rest of the repository.

### Why YAML is acceptable in v1

- easy to inspect manually
- consistent with `listen`
- low implementation overhead
- useful for debugging on a Raspberry Pi / single-node deployment

### Required fields for operability

At minimum, each record should preserve:

- source metadata
- execution strategy used
- status transitions
- timestamps
- human-readable updates
- final structured result
- error object
- delivery attempts

### Suggested error shape

```yaml
error:
  code: timeout
  message: Timed out waiting for browser attach
  retryable: true
  stage: execution
```

---

## 12. API Contract Suggestions

## 12.1 Submit Job

`POST /jobs`

Suggested request body:

```json
{
  "instruction": "Open the browser and validate the status page",
  "source": {
    "type": "rest"
  },
  "execution": {
    "strategy": "auto",
    "timeout_seconds": 900
  },
  "delivery": {
    "mode": "poll_only",
    "audience": "machine"
  }
}
```

Suggested response:

```json
{
  "id": "7d2f3d9a",
  "status": "queued",
  "status_url": "/jobs/7d2f3d9a"
}
```

## 12.2 Get Job

`GET /jobs/{id}`

Returns the normalized job document, preferably as JSON by default and optionally YAML for debugging compatibility.

## 12.3 Cancel Job

`POST /jobs/{id}/cancel`

Should request cooperative cancellation. If the underlying runtime is a subagent/session, cancellation semantics should be best-effort in v1.

## 12.4 List Jobs

`GET /jobs?status=running&source=telegram`

Useful filters:

- status
- source type
- created_after
- created_before
- submitted_by

---

## 13. Observability

v1 does not need a full telemetry stack, but it does need enough observability to avoid black-box pain.

### Minimum observability requirements

- append-only job updates
- timestamps for submit/start/finish
- runtime strategy used
- delivery attempts and outcome
- final error code/message

### Nice-to-have v1.1+

- event stream / SSE for live updates
- structured logs with job ID correlation
- metrics: queued jobs, running jobs, success rate, mean duration

---

## 14. Security and Policy Considerations

Because this component may accept work from external or chat-originated inputs, guardrails matter.

### v1 expectations

- inherit OpenClaw approval and tool policies
- preserve source identity metadata
- distinguish human-facing delivery from machine-facing retrieval
- avoid implicit broad tool access unless requested or configured
- make runtime strategy visible in job metadata for auditability

### Important constraint

`openclaw-listen` should not silently become an unrestricted remote execution endpoint.

Even when receiving jobs over REST, execution should still respect:

- configured tool availability
- approval requirements
- channel and policy boundaries

---

## 15. v1 Scope

## In scope

- OpenClaw-native job listener component design
- REST ingress
- direct/internal ingress
- gateway/messaging ingress for selected async flows
- YAML job persistence
- strategy selection: `inline`, `subagent`, `acp`, `auto`
- structured result envelope
- Telegram/Discord-friendly completion messages
- basic cancellation
- basic job listing/querying

## Out of scope

- multi-node distributed scheduler
- priority queues with advanced fairness guarantees
- pluggable database backends
- fully generic conversational intent parser for all chats
- rich web UI
- guaranteed exactly-once delivery
- elaborate retry policy engine

This is enough to prove the product shape without disappearing into architecture astronautics.

---

## 16. Risks

### 1. Runtime ambiguity

OpenClaw offers multiple execution primitives, which is powerful but easy to overcomplicate.

**Risk:** too many strategy branches too early.

**Mitigation:** keep `auto` policy simple and explicit in v1.

### 2. Chat-originated job quality

Natural-language requests from Telegram/Discord can be underspecified.

**Risk:** async jobs fail because the request was ambiguous.

**Mitigation:** require clear acknowledgement + optionally reject with a clarification-needed result before spawning expensive work.

### 3. Delivery coupling

Pushing results back to messaging platforms introduces formatting, size, and artifact-handling concerns.

**Risk:** completion succeeds technically but the user receives an ugly or truncated message.

**Mitigation:** make rendering a dedicated layer, not an afterthought inside the executor.

### 4. YAML scaling limits

YAML is fine at small scale, but not forever.

**Risk:** file contention, awkward filtering, and brittle concurrent updates.

**Mitigation:** accept YAML for v1, design interfaces so storage can be swapped later.

### 5. Cancellation semantics

Subagent or ACP-backed work may not stop instantly.

**Risk:** API says “cancelled” while underlying work is still winding down.

**Mitigation:** model cancellation as requested/cooperative in v1 and document best-effort behavior.

### 6. Role confusion with existing components

If naming and docs are sloppy, users will not know when to use `rpi-job`, `listen`, or `openclaw-listen`.

**Mitigation:** document the three-way split clearly:

- `rpi-job` = generic shell jobs
- `listen` = Codex-native agent jobs
- `openclaw-listen` = OpenClaw-native orchestration jobs

---

## 17. Recommended Repository Placement

Suggested component layout:

```text
linux-agents/
  openclaw-listen/
    README.md
    pyproject.toml
    main.py
    adapters/
      rest.py
      direct.py
      gateway.py
    runtime/
      scheduler.py
      executor.py
      render.py
      delivery.py
    jobs/
      .gitkeep
```

Notes:

- keep the layout parallel to `listen/` where it helps discoverability
- separate adapters from runtime logic early; that boundary will matter
- avoid baking channel formatting directly into API handlers

---

## 18. Recommended Implementation Order

### Phase 1 — Core listener skeleton

- create component directory
- define job schema
- implement YAML store
- expose REST submit/get/list/cancel

### Phase 2 — Runtime strategy layer

- implement `inline`
- implement `subagent`
- persist updates/results consistently

### Phase 3 — Messaging delivery

- add Telegram/Discord result renderer
- add push delivery dispatcher
- support source reply metadata

### Phase 4 — Gateway ingress

- bind selected async chat flows to listener submission
- add immediate acknowledgement message behavior

### Phase 5 — ACP integration

- add explicit ACP-backed execution mode
- validate which job classes truly benefit from ACP

This sequence gets a usable system early and saves the more opinionated integration work for after the job model is proven.

---

## 19. Open Questions

These do not block the architecture, but they should be decided before implementation.

1. Should v1 store jobs as YAML only, or JSON for API + YAML mirror for debugging?
2. What is the exact internal API for spawning OpenClaw sessions/subagents from this component?
3. Should gateway ingress be generic, or limited to explicit command patterns at first?
4. What are the artifact retention rules for screenshots/logs/files?
5. Does `cancel` mean “user no longer wants delivery” or “actively stop execution” or both?
6. Which result fields are guaranteed stable for machine consumers?

---

## 20. Final Recommendation

Build `openclaw-listen` as a **small OpenClaw-native orchestration listener**, not as another generic job server and not as a clone of `listen`.

The correct v1 shape is:

- **multi-ingress** at the edge
- **single normalized job model** in the middle
- **strategy-based OpenClaw runtime execution** underneath
- **chat-friendly result rendering and delivery** on the way out

If implemented this way, `openclaw-listen` becomes the right place for async OpenClaw jobs that start from REST, internal code, or chat — while `listen` remains the right tool for Codex-specific tmux workers.

That split is clean, pragmatic, and unlikely to regret itself later.
