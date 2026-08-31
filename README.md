# Escola Lendária Community Agent

**Good Neighbor AI for schools: detect silent learner risk early, coordinate support, and keep consequential decisions human-controlled.**

Built for the **Agents for Humans Hackathon 2026** with **Strands Agents SDK + Amazon Bedrock**, with an **Amazon Bedrock AgentCore runtime adapter** and a privacy-minimized read-only connection to the real Escola Lendária learner-progress source.

> **One agent, many learners, proactive support, human judgment where it matters.**

## The problem

Small schools and learning communities often have many learners and very limited support staff. The hardest learner to help is often the one who never asks: they stop opening lessons, repeat the same failures, or quietly fall behind.

A normal chatbot waits for a message. **Community Agent watches the community as a whole.** It detects meaningful risk signals, avoids duplicate alerts, and routes only the cases that deserve human attention.

## What the agent does end to end

1. **Observes privacy-minimized learner activity** from local events or the read-only Escola Lendária Supabase source.
2. **Runs autonomous community scans** to detect silent inactivity and unresolved repeated failures.
3. **Applies deterministic safety guardrails** before any model reasoning.
4. **Uses Strands + Amazon Bedrock** for contextual reasoning and constrained tool use.
5. **Creates and prioritizes human follow-ups** when judgment is required.
6. **Deduplicates continuing conditions** so staff are not flooded with repeated alerts.
7. **Clears resolved conditions** when the underlying evidence disappears.
8. **Records an audit trail** of monitoring, decisions, notes, escalation, and human resolution.

## Why this is agentic

This is not a request/response chatbot. The core loop runs even when no learner talks to it.

- **Autonomous:** the monitor scans the learner population on a schedule.
- **Stateful:** conditions persist across runs and clear when evidence changes.
- **Tool-using:** Strands can retrieve learner context, inspect open follow-ups, and write bounded support notes.
- **Goal-directed:** the objective is to reduce silent learner risk while minimizing unnecessary staff interruptions.
- **Human-aware:** consequential actions are escalated instead of executed autonomously.
- **Resilient:** if Bedrock is temporarily unavailable, deterministic monitoring continues in policy-fallback mode.

## 90-second judge path

After starting the app, open `http://localhost:8080` and:

1. Click **Run autonomous scan now** — see silent learner conditions appear without a learner request.
2. Send a **repeated_failure** event — see a risk decision and human follow-up.
3. Send a **payment_confirmation** event — see the agent refuse autonomous execution and route it to a person.
4. Resolve the follow-up — see the resolution enter the audit trail.
5. Open **Recent agent decisions** and **Audit trail** — inspect the full chain of evidence and action.

For the full judging map, see [`JUDGES_GUIDE.md`](JUDGES_GUIDE.md). For the video flow, see [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md).

## Good Neighbor impact

The beneficiary is a **group**, not a single user: a school community whose staff cannot continuously watch every learner.

The monitor currently detects:

- 7+ and 14+ days of inactivity;
- 3+ and 5+ unresolved failed attempts;
- accumulating support signals;
- high-risk or consequential events requiring human judgment.

The value is not “more alerts.” The value is **fewer, better interventions**: identify silent risk, suppress duplicates, clear stale conditions, and send only meaningful cases to people.

## Real Escola Lendária data source

The hackathon agent can synchronize with the existing Escola Lendária Supabase backend. The integration is intentionally **read-only and privacy-minimized**.

Source table:

- `public.learning_user_state`

Fields used:

- learner `user_id`;
- display `name`;
- `school_level`;
- `last_access_at`;
- `updated_at`;
- only `state.progress` from the JSON state.

The integration **does not request or copy** contact numbers, progress PINs, chats, notes, drafts, scratch data, payment information, or support-message bodies.

For every progress entry, the adapter uses lesson/course context, completion state, `wrongAttempts`, and activity timestamps. Resolved failures on completed lessons are not counted as current repeated-failure risk.

### Configure the real source

Copy `.env.example` to `.env`, then inject a server-side Supabase service-role key with a secret manager or local environment. Never commit that key.

```bash
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_SECRET_KEY=<sb_secret_... backend key>
SUPABASE_SYNC_ENABLED=true
```

Manual synchronization:

```bash
curl -X POST http://localhost:8080/source/supabase/sync
```

Source status:

```bash
curl http://localhost:8080/source/status
```

When `SUPABASE_SYNC_ENABLED=true`, every autonomous monitor run attempts a source sync first. A temporary source outage does **not** disable the local deterministic monitor.

## Human safety boundary

Community Agent intentionally cannot autonomously confirm or execute:

- payments;
- enrollment, expulsion, or punishment;
- account deletion;
- course-access changes;
- medical or legal decisions;
- safeguarding decisions requiring a person.

These cases are routed to a human attention queue with an owner role and urgency. The model-facing tool surface is deliberately smaller than the application surface.

## Strands tools

The Strands agent can use only:

- `get_learner_context`
- `list_open_followups`
- `record_support_note`

It can reason about a case and record a support note. It cannot change access, confirm payment, discipline a learner, delete an account, or execute another consequential action.

## Architecture

```text
Escola Lendária / local events
            |
            v
 privacy-minimized adapter
            |
            v
   community state + audit
            |
     +------+------+
     |             |
     v             v
 autonomous     event-driven
 monitor        processing
     |             |
     +------+------+
            v
 deterministic guardrails
            |
            v
 Strands Agents + Bedrock
    constrained tools
            |
            v
 human attention queue
            |
            v
 human resolution + audit
```

See [`ARCHITECTURE.md`](ARCHITECTURE.md) and [`docs/architecture.png`](docs/architecture.png). The repository also includes an **Amazon Bedrock AgentCore runtime adapter** for deployment.

## API

```text
GET  /health
GET  /stats
GET  /digest
POST /events
GET  /events
GET  /decisions
GET  /learners/{learner_id}
GET  /support-notes
GET  /followups
POST /followups/{id}/resolve
GET  /audit
POST /monitor/run
GET  /monitor/state
GET  /monitor/runs
POST /source/supabase/sync
GET  /source/status
```

The root URL serves the dashboard with the human queue, silent-risk monitor, source status, recent decisions, and audit trail.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

## Run without AWS

This mode is ideal for reviewing the safety and monitoring path locally.

```bash
export COMMUNITY_AGENT_MODE=policy
PYTHONPATH=src python -m community_agent.seed_demo
PYTHONPATH=src uvicorn community_agent.api:app --host 0.0.0.0 --port 8080
```

Then open `http://localhost:8080`.

You can also run the complete offline scenario from the terminal:

```bash
PYTHONPATH=src python -m community_agent.offline_demo
```

## Run with Strands + Amazon Bedrock

After AWS credentials and Bedrock model access are configured:

```bash
export COMMUNITY_AGENT_MODE=strands
PYTHONPATH=src uvicorn community_agent.api:app --host 0.0.0.0 --port 8080
```

## Tests

```bash
pytest
```

The suite covers policy decisions, idempotency, storage, API behavior, autonomous monitoring, silent-risk clearing, support notes, and privacy-minimized Supabase mapping.

## Hackathon provenance

This repository is the new hackathon agent implementation. The existing Escola Lendária platform provides real-world community context and, when configured, a read-only source of learner progress. Pre-existing platform code is not represented as newly created hackathon work.

## License

MIT
