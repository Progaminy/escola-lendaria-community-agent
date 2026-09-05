# Verification Report — Escola Lendária Community Agent

This document turns the main hackathon claims into concrete, reproducible checks.

## Why this exists

The project makes several architectural claims that matter to the **Agents for Humans Hackathon** judging criteria: autonomous monitoring, deterministic prioritization, privacy-minimized model context, human escalation for consequential decisions, fail-safe operation without the cloud model, and auditable operational evidence.

Those claims should be easy for a judge to verify rather than accepted from prose alone.

## One-command end-to-end verifier

With the local application running on `http://127.0.0.1:8080`:

```bash
python scripts/judge_smoke_test.py
```

Set a different endpoint when needed:

```bash
JUDGE_BASE_URL=http://127.0.0.1:8080 python scripts/judge_smoke_test.py
```

The script uses only the Python standard library.

## What the verifier proves

### 1. The running product identifies its agent framework and human boundary

It checks `GET /health` and verifies that:

- the service is ready;
- the framework is reported as **Strands Agents SDK**;
- human-in-the-loop operation is enabled.

### 2. Autonomous monitoring actually runs

It calls:

```text
POST /monitor/run
```

Then it checks the deterministic attention plan and requires real human work to be present after the seeded demonstration scenario.

### 3. Priority is evidence-backed, not an LLM opinion

For every returned attention-plan item, the verifier requires:

- `priority_score`;
- `why_now` evidence.

The ranking itself is calculated in `src/community_agent/triage.py` from urgency, active monitoring risk, and waiting time.

### 4. Consequential payment action is not executed by the AI

The verifier submits a fresh `payment_confirmation` event and checks that:

- the event is accepted by the system;
- the deterministic decision is `human_escalation`;
- `escalate` is true;
- the owner role is `administrator`.

This tests the actual HTTP event path, not only the policy function in isolation.

### 5. Model-facing community triage removes stable identifiers

The verifier requests:

```text
POST /agent/community-briefing
```

It then checks the model-facing attention plan and rejects it if stable internal fields such as learner IDs, event IDs, or raw internal IDs appear. Cases must use temporary aliases beginning with:

```text
priority-case-
```

The human-facing application still retains the internal identifiers required to resolve work.

### 6. The product remains usable across model modes

The community briefing is accepted when its reported mode is any designed operating state:

- `policy`;
- `strands`;
- `policy-fallback`.

That proves the product architecture does not make deterministic monitoring and safety depend on a successful model call.

### 7. Impact evidence is correctly scoped

The verifier checks `GET /impact` and requires the endpoint to identify its metrics as operational evidence rather than causal proof of learning outcomes.

It also verifies that a completed monitoring run has actually been recorded.

### 8. The consequential test path is auditable

Finally, it checks `GET /audit` and confirms that the unique smoke-test event appears in the audit trail.

## CI enforcement

The GitHub Actions workflow runs four layers of verification on every push and pull request:

```text
secret scan → compile → lint → pytest → full HTTP judge smoke test
```

For the end-to-end stage, CI:

1. seeds the demonstration learner state;
2. starts FastAPI/Uvicorn in deterministic policy mode;
3. runs `scripts/judge_smoke_test.py` against the live HTTP service;
4. fails the workflow if any key judge-facing invariant is broken.

This complements the unit/integration tests by verifying the product through the same HTTP surface a reviewer can use.

## Manual 90-second judge path

For a visual verification, run:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
export COMMUNITY_AGENT_MODE=policy
PYTHONPATH=src python -m community_agent.seed_demo
PYTHONPATH=src uvicorn community_agent.api:app --host 0.0.0.0 --port 8080
```

Open `http://localhost:8080` and:

1. run a fresh community scan;
2. inspect the ranked human attention queue and `why_now` evidence;
3. generate the community briefing;
4. verify temporary case aliases in model-facing community triage;
5. send a `payment_confirmation` scenario;
6. verify human escalation instead of autonomous execution;
7. resolve the follow-up as a human;
8. inspect `/impact` and the audit trail.

## Evidence map

| Claim | Primary evidence |
| --- | --- |
| Autonomous monitoring | `src/community_agent/monitor.py` + `/monitor/run` |
| Deterministic priority | `src/community_agent/triage.py` + `/attention-plan` |
| Strands tool reasoning | `src/community_agent/agent.py`, `src/community_agent/tools.py` |
| Human consequential boundary | `src/community_agent/policy.py` |
| Advisory-note guardrail | `src/community_agent/safety.py` |
| Identifier minimization | `attention_plan_for_agent_data()` + briefing path |
| Operational impact evidence | `src/community_agent/impact.py` + `/impact` |
| Auditability | persisted actions + `/audit` |
| End-to-end verification | `scripts/judge_smoke_test.py` |
| Continuous verification | `.github/workflows/ci.yml` |

## Bottom line

**The project does not ask a judge to trust a pitch. Its core Good Neighbor Agent claims are testable through code, deterministic policy, a live application surface, an audit trail, and an automated end-to-end verifier.**
