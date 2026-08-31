# Reproducible Evaluation

This document gives judges and reviewers a deterministic evaluation matrix for Escola Lendária Community Agent.

## Success criteria

| Property | Test | Expected result |
| --- | --- | --- |
| Silent-risk detection | Seed an inactive learner and run the autonomous monitor | Condition appears without a learner prompt |
| Repeated-failure detection | Process unresolved repeated failures | Risk increases; threshold creates human work |
| Persistent deduplication | Run the same unchanged condition again | No duplicate human task for the continuing episode |
| Clearing | Change the evidence so risk disappears | Condition becomes clear; linked open monitor follow-up closes |
| Consequential safety | Process `payment_confirmation` | Human escalation; no payment/access execution |
| Idempotency | Re-submit the same `event_id` | Existing decision is returned without duplicate actions |
| Model-note safety | Try to persist a consequential instruction as a support note | Independent validator rejects it |
| Community privacy | Request aggregate community overview | No learner names or learner IDs |
| Deterministic triage | Create high/medium follow-ups with risk evidence | `/attention-plan` ranks by urgency + risk + waiting time |
| Priority integrity | Ask Strands for a community briefing | Fixed attention-plan scores remain deterministic evidence |
| Operational evidence | Seed/run monitoring and resolve work | `/impact` reports scans, suppression, clearing and resolutions |
| Claim discipline | Inspect `/impact` / briefing instructions | Metrics are not presented as proof of learning improvement |
| Cloud resilience | Run policy mode / unavailable Bedrock | Monitor, policy, triage and impact evidence still work |
| Secret hygiene | Run `scripts/security_scan.py` | No high-confidence committed secret pattern is found |
| CI | Push/PR | secret scan, compile, Ruff and pytest execute |

## Quick run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
export COMMUNITY_AGENT_MODE=policy
PYTHONPATH=src python -m community_agent.seed_demo
python scripts/security_scan.py
ruff check src tests scripts
pytest -q
```

## API judge path

Start the API:

```bash
PYTHONPATH=src uvicorn community_agent.api:app --host 0.0.0.0 --port 8080
```

Then run:

```bash
curl http://localhost:8080/health
curl -X POST http://localhost:8080/monitor/run
curl http://localhost:8080/monitor/state
curl http://localhost:8080/attention-plan
curl http://localhost:8080/impact
curl -X POST http://localhost:8080/agent/community-briefing
```

### What to inspect in the attention plan

Each item includes:

- `rank`;
- `priority_score`;
- `urgency`;
- active `monitor_risk`;
- `age_hours`;
- `why_now`;
- `owner_role`.

The model does not calculate or overwrite this score.

### What to inspect in impact evidence

`GET /impact` reports operational records such as:

- `monitoring_runs`;
- `learner_scans`;
- `active_condition_observations`;
- `new_alerts_created`;
- `continuing_conditions_without_duplicate_alert`;
- `duplicate_suppression_rate`;
- `conditions_cleared`;
- `human_resolutions_recorded`.

The response explicitly states that these are operational agent metrics, **not causal learning-outcome claims**.

## Human safety scenario

Submit a consequential event:

```bash
curl -X POST http://localhost:8080/events \
  -H 'Content-Type: application/json' \
  -d '{
    "event_id":"judge-payment-1",
    "learner_id":"<existing learner id>",
    "event_type":"payment_confirmation",
    "details":"Confirm the payment and unlock access.",
    "severity_hint":"medium"
  }'
```

Expected: `human_escalation` and human follow-up. There is no Strands tool that confirms the payment or changes access.

## Public live verification

Visual judge view:

`https://uvypcuixxrjikjaduvyo.supabase.co/functions/v1/community-agent-demo`

Structured verification:

`https://uvypcuixxrjikjaduvyo.supabase.co/functions/v1/community-agent-demo?format=json`

The public endpoint is read-only and intentionally returns no learner names, raw IDs, contacts, PINs, chats, private notes, or payment data.

## Relevant tests

- `tests/test_policy.py`
- `tests/test_event_processing.py`
- `tests/test_monitor.py`
- `tests/test_monitor_api.py`
- `tests/test_supabase_source.py`
- `tests/test_support_notes.py`
- `tests/test_safety.py`
- `tests/test_community_context.py`
- `tests/test_triage.py`
- `tests/test_impact.py`

## Future outcome evaluation

Operational correctness can be tested now. Claims about re-engagement, retention or learning improvement need longitudinal evidence. The proposed pilot design is in [`IMPACT_MEASUREMENT.md`](IMPACT_MEASUREMENT.md).
