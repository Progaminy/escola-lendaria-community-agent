# Escola Lendária Community Agent

**A proactive Good Neighbor AI for schools: detect silent learner risk, prioritize scarce staff attention, use Strands + Amazon Bedrock for bounded reasoning, and keep consequential decisions human-controlled.**

Built for the **Agents for Humans Hackathon 2026** with **Strands Agents SDK + Amazon Bedrock**, an **Amazon Bedrock AgentCore runtime adapter**, FastAPI, persistent operational state, and a privacy-minimized read-only connection to real Escola Lendária learner progress.

> **One agent, many learners, one prioritized human queue.**

## The specific problem

Small schools cannot continuously watch every learner. The learner most likely to be missed is often the one who never opens a support chat: they quietly stop returning, repeat the same failure, or accumulate warning signals while limited staff attention is elsewhere.

A request-only chatbot sees the learner who speaks. **Community Agent is designed to notice the learner who goes quiet.**

## One end-to-end workflow

The judge-focused dashboard makes the product loop explicit:

1. **Observe** — synchronize only the learner activity/progress fields needed for monitoring.
2. **Detect** — autonomously scan the whole community for silent inactivity, unresolved repeated failures, and accumulating support signals.
3. **Persist and deduplicate** — keep each risk episode across scans instead of creating a new alert every time; clear it when evidence disappears.
4. **Prioritize human attention** — deterministically rank open work using urgency, active monitoring risk, and waiting time.
5. **Reason with Strands + Bedrock** — explain community state and ranked work through a deliberately constrained tool surface.
6. **Keep judgment human** — payments, access, discipline, enrollment, deletion, medical/legal, and safeguarding decisions are never model-executable actions.
7. **Resolve and audit** — a person closes the task and the complete chain remains auditable.
8. **Measure operations** — report scans, duplicate suppression, cleared conditions, decision modes, and human resolutions without pretending those metrics prove learning outcomes.

## Why this is agentic

This is not a request/response chatbot.

- **Autonomous:** a scheduled monitor runs without a learner prompt.
- **Stateful:** risk conditions survive across runs and later clear.
- **Tool-using:** Strands reads bounded case/community context, fixed triage evidence, impact evidence, and can write only validated advisory support notes.
- **Goal-directed:** it converts limited staff attention into a prioritized shared resource.
- **Human-aware:** consequential decisions are escalated rather than executed.
- **Resilient:** if Bedrock is unavailable, deterministic monitoring, safety, triage, and evidence remain available.

## Deterministic attention planning

`GET /attention-plan` ranks open human follow-ups using an explainable formula:

```text
priority = urgency base + active-risk bonus + waiting-time bonus
```

The score is computed in `src/community_agent/triage.py`, not by the language model. Strands may explain the ordering but cannot alter scores or resolve cases.

This matters because the real bottleneck in a small school is not simply detecting risk — it is deciding **what the limited human team should look at first**.

## Strands tools

The model-facing surface is intentionally smaller than the application surface:

- `get_community_overview` — aggregate-only community context, no learner identities;
- `get_attention_plan` — fixed deterministic human-work ordering;
- `get_impact_metrics` — observed operational evidence, explicitly non-causal;
- `get_learner_context` — factual context for a specific case;
- `list_open_followups` — visibility into open human work;
- `record_support_note` — bounded advisory note with independent deterministic validation.

There is **no Strands tool** for payment confirmation, course-access changes, punishment, expulsion, enrollment decisions, account deletion, medical/legal decisions, or safeguarding decisions.

## Safety is code, not just prompting

1. **Policy before model:** hard escalation rules execute before Strands and cannot be downgraded by it.
2. **Tool minimization:** consequential write tools do not exist in the model tool surface.
3. **Support-note validator:** even advisory model text is rejected if it is empty, oversized, targets an unknown learner, or tries to encode a consequential action.
4. **Fail-safe cloud behavior:** a Bedrock failure preserves the deterministic decision instead of erasing it.
5. **Secret scanning:** CI scans for high-confidence committed credential patterns before lint/tests.

See [`SECURITY.md`](SECURITY.md), [`src/community_agent/safety.py`](src/community_agent/safety.py), and [`scripts/security_scan.py`](scripts/security_scan.py).

## Real-world, privacy-minimized source

The agent can synchronize read-only with Escola Lendária's existing Supabase learner state. The source projection deliberately requests only the minimum fields needed for monitoring and only `state.progress` from the JSON state.

The integration does **not request or copy** contacts, progress PINs, chats, private notes, drafts, scratch data, payment information, or support-message bodies.

The public live judge page also renders only temporary aliases and aggregate risk evidence.

## Public live judge demo

Visual live view:

`https://uvypcuixxrjikjaduvyo.supabase.co/functions/v1/community-agent-demo`

Structured verification:

`https://uvypcuixxrjikjaduvyo.supabase.co/functions/v1/community-agent-demo?format=json`

The public endpoint is a read-only verifier against privacy-minimized real learner progress. The full operational agent and human queue live in this repository.

## Operational evidence, not inflated claims

`GET /impact` reports what the agent can actually prove from its own audit store:

- monitoring runs and learner scans;
- active condition observations;
- new alerts created;
- continuing conditions that did not create duplicate alerts;
- duplicate-suppression rate;
- conditions cleared;
- human resolutions;
- open follow-ups and decision modes.

It deliberately labels those as **operational agent behavior, not causal proof of better learning outcomes**. See [`docs/IMPACT_MEASUREMENT.md`](docs/IMPACT_MEASUREMENT.md) for the future pilot design.

## 90-second judge path

Run the app and open `http://localhost:8080`:

1. Click **Run fresh community scan**.
2. Inspect the **ranked human attention plan** and its `why_now` evidence.
3. Click **Generate briefing** to see the Strands/community path (or deterministic fallback in policy mode).
4. Send a `payment_confirmation` event and verify that it becomes human work rather than an executed action.
5. Resolve a follow-up and watch the **operational evidence + audit trail** change.

For a deeper verification path see [`JUDGES_GUIDE.md`](JUDGES_GUIDE.md) and [`docs/EVALUATION.md`](docs/EVALUATION.md).

## Architecture

```text
Escola Lendária learner progress / school events
                    |
                    v
         privacy-minimized adapter
                    |
                    v
        community state + audit store
                    |
             autonomous monitor
                    |
      persistent risk episodes / clearing
                    |
                    v
       deterministic guardrail policy
                    |
        +-----------+-----------+
        |                       |
        v                       v
 deterministic attention   safe contextual cases
       planning                  |
        |                        v
        |               Strands + Amazon Bedrock
        |                 constrained tools
        +-----------+-----------+
                    v
            human attention queue
                    |
                    v
          human resolution + audit
                    |
                    v
          operational impact metrics

Amazon Bedrock AgentCore runtime adapter -> same agent/safety path
```

See [`ARCHITECTURE.md`](ARCHITECTURE.md), [`docs/architecture.png`](docs/architecture.png), and [`docs/AGENTCORE.md`](docs/AGENTCORE.md).

## API

```text
GET  /health
GET  /stats
GET  /digest
GET  /attention-plan
GET  /impact
POST /agent/community-briefing
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

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
export COMMUNITY_AGENT_MODE=policy
PYTHONPATH=src python -m community_agent.seed_demo
PYTHONPATH=src uvicorn community_agent.api:app --host 0.0.0.0 --port 8080
```

For Strands + Bedrock:

```bash
export COMMUNITY_AGENT_MODE=strands
PYTHONPATH=src uvicorn community_agent.api:app --host 0.0.0.0 --port 8080
```

## Verification

```bash
python scripts/security_scan.py
ruff check src tests scripts
pytest -q
```

The suite covers policy, idempotency, monitor detection/deduplication/clearing, API behavior, source minimization, model-note safety, aggregate privacy, deterministic attention ranking, and operational impact metrics.

## Bonus and provenance

- AWS Builder Center bonus-post draft: [`docs/AWS_BUILDER_BLOG_DRAFT.md`](docs/AWS_BUILDER_BLOG_DRAFT.md)
- Reproducible evaluation: [`docs/EVALUATION.md`](docs/EVALUATION.md)
- Demo script: [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md)

This repository is the new hackathon agent implementation. The existing Escola Lendária platform supplies real community context and an optional read-only progress source; pre-existing platform code is not represented as newly built hackathon work.

## License

MIT
