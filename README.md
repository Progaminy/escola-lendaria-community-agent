# Escola Lendária Community Agent

A **new Good Neighbor AI agent** created for the **Agents for Humans Hackathon 2026**.

The agent is a quiet coordination layer for small schools and learning communities. It does
not wait for every learner to ask for help. It consumes learning activity, keeps a small
privacy-minimized community memory, detects silent risk, and routes consequential cases to
people.

## What makes it agentic

The product combines three layers:

1. **Deterministic guardrails** decide what the system may never do autonomously.
2. **Autonomous community monitoring** scans the whole learner population for time-based and
   cumulative support signals.
3. **Strands Agents SDK + Amazon Bedrock** adds contextual reasoning and constrained tool use
   after the safety boundary has already been enforced.

If Bedrock is unavailable, the deterministic path remains usable (`policy-fallback`) instead
of taking the product offline.

## Good Neighbor impact

The beneficiary is a **group**: a school community with many learners and limited support
staff. The agent can surface a learner who has become inactive or is repeatedly struggling
even when that learner never opens a chatbot.

It currently detects:

- 7+ and 14+ days of inactivity;
- 3+ and 5+ unresolved failed attempts;
- accumulating support signals;
- high-risk or consequential events requiring human judgment.

The monitor deduplicates active conditions so one continuing problem does not create a new
alert on every scan. When the evidence disappears, the condition is marked clear.

## Real Escola Lendária data source

The same hackathon agent can synchronize with the existing Escola Lendária Supabase backend.
The integration is intentionally **read-only and privacy-minimized**.

Source table used:

- `public.learning_user_state`

Fields used by the agent:

- learner `user_id`;
- display `name`;
- `school_level`;
- `last_access_at`;
- `updated_at`;
- only `state.progress` from the JSON state.

The integration **does not request or copy** contact numbers, progress PINs, chats, notes,
drafts, scratch data, payment information, or support-message bodies.

For every progress entry, the adapter uses lesson/course context, completion state,
`wrongAttempts`, and activity timestamps. Resolved failures on completed lessons are not
counted as current repeated-failure risk.

### Configure the real source

Copy `.env.example` to `.env`, then inject a server-side Supabase service-role key using your
secret manager or local environment. Never commit that key.

```bash
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_SECRET_KEY=<sb_secret_... backend key>
SUPABASE_SYNC_ENABLED=true
```

Manual source synchronization:

```bash
curl -X POST http://localhost:8080/source/supabase/sync
```

Source status:

```bash
curl http://localhost:8080/source/status
```

When `SUPABASE_SYNC_ENABLED=true`, every autonomous monitor run attempts a source sync first.
A temporary Supabase outage does **not** disable the local deterministic monitor.

## Human safety boundary

The agent is intentionally not allowed to autonomously confirm or execute:

- payments;
- enrollment, expulsion, or punishment;
- account deletion;
- course-access changes;
- medical or legal decisions;
- safeguarding decisions requiring a person.

These cases are routed to the human attention queue with an owner role and urgency.

## Core persistent records

Local SQLite keeps the hackathon agent's own operational state:

- privacy-minimized learners;
- incoming learner events;
- deterministic decisions;
- support signals;
- human follow-ups;
- Strands support notes;
- monitoring state and run history;
- source-sync history;
- complete agent audit actions.

## API

Main endpoints:

```text
GET  /health
GET  /stats
GET  /digest
POST /events
GET  /events
GET  /decisions
GET  /learners/{learner_id}
GET  /followups
POST /followups/{id}/resolve
GET  /audit
POST /monitor/run
GET  /monitor/state
GET  /monitor/runs
POST /source/supabase/sync
GET  /source/status
```

The root URL (`/`) serves the live dashboard with the human queue, silent-risk monitor,
source status, recent decisions and audit trail.

## Strands tools

The model-facing tool surface is deliberately smaller than the application surface:

- `get_learner_context`
- `list_open_followups`
- `record_support_note`

The model can add a support note. It cannot execute payment, access, discipline, deletion,
or other consequential actions.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

## Run without AWS

```bash
export COMMUNITY_AGENT_MODE=policy
PYTHONPATH=src python -m community_agent.seed_demo
PYTHONPATH=src uvicorn community_agent.api:app --host 0.0.0.0 --port 8080
```

Then open `http://localhost:8080`.

## Run with Strands + Bedrock

After AWS credentials and Bedrock access are configured:

```bash
export COMMUNITY_AGENT_MODE=strands
PYTHONPATH=src uvicorn community_agent.api:app --host 0.0.0.0 --port 8080
```

The repository also contains an `agentcore_runtime.py` adapter for Amazon Bedrock AgentCore
Runtime deployment.

## Tests

```bash
pytest
```

The test suite covers policy decisions, idempotency, storage, API behavior, autonomous
monitoring, silent-risk clearing, support notes, and privacy-minimized Supabase mapping.

## Architecture

See `ARCHITECTURE.md` and `docs/architecture.png`.

## Hackathon provenance

This repository is the new hackathon agent implementation. The existing Escola Lendária
platform is used as the real-world community context and, when configured, as a read-only
source of learner progress. Pre-existing platform code is not represented as newly created
hackathon work.

## License

MIT
