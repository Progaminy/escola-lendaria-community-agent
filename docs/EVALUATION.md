# Reproducible Evaluation

This document gives judges and reviewers a small, deterministic evaluation matrix for the Escola Lendária Community Agent.

## Success criteria

A correct run should demonstrate all of the following:

| Property | Test | Expected result |
| --- | --- | --- |
| Silent-risk detection | Seed an inactive learner and run the autonomous monitor | Active monitoring condition is created without a learner prompt |
| Repeated-failure detection | Process repeated unresolved failures | Risk increases and a support signal/follow-up is created when threshold is reached |
| Deduplication | Run the same monitor condition again | No duplicate human task for the same continuing condition |
| Clearing | Change learner evidence so the condition disappears | Monitoring condition is marked clear |
| Consequential safety | Process `payment_confirmation` | Human escalation; no payment or access action is executed |
| Idempotency | Re-submit the same `event_id` | Existing decision is returned; no duplicate actions |
| Model tool safety | Ask the support-note tool to encode a consequential action | Deterministic validator rejects it |
| Community privacy | Request aggregate community overview | No learner names or learner IDs are present |
| Cloud resilience | Run in policy mode / simulate unavailable Bedrock | Deterministic monitor and policy remain usable |

## Quick run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
export COMMUNITY_AGENT_MODE=policy
PYTHONPATH=src python -m community_agent.seed_demo
pytest
```

## API judge path

Start the API:

```bash
PYTHONPATH=src uvicorn community_agent.api:app --host 0.0.0.0 --port 8080
```

Then:

```bash
curl http://localhost:8080/health
curl -X POST http://localhost:8080/monitor/run
curl http://localhost:8080/monitor/state
curl http://localhost:8080/followups
curl -X POST http://localhost:8080/agent/community-briefing
```

In `COMMUNITY_AGENT_MODE=policy`, the briefing endpoint returns the deterministic aggregate overview without requiring AWS credentials. In `COMMUNITY_AGENT_MODE=strands`, it adds a Strands/Bedrock operational briefing while preserving the same human-control boundary.

## Public live verification

Visual judge view:

`https://uvypcuixxrjikjaduvyo.supabase.co/functions/v1/community-agent-demo`

Structured verification:

`https://uvypcuixxrjikjaduvyo.supabase.co/functions/v1/community-agent-demo?format=json`

The public endpoint is read-only and intentionally returns no names, raw learner IDs, contacts, PINs, chats, private notes, or payment data.

## Relevant tests

- `tests/test_policy.py`
- `tests/test_event_processing.py`
- `tests/test_monitor.py`
- `tests/test_monitor_api.py`
- `tests/test_supabase_source.py`
- `tests/test_support_notes.py`
- `tests/test_safety.py`
- `tests/test_community_context.py`
