# Judge Fast Path — Escola Lendária Community Agent

This page is the shortest path to understanding and verifying the project against the **Agents for Humans Hackathon** criteria.

## 30-second pitch

Small schools cannot continuously inspect every learner. The learner most likely to be missed is often the one who never asks for help: they quietly stop returning, repeat the same failure, or accumulate warning signals while limited staff attention is elsewhere.

**Escola Lendária Community Agent is a proactive Good Neighbor AI that notices the learner who goes quiet, keeps one persistent risk episode instead of creating alert noise, ranks scarce human attention deterministically, and uses Strands + Amazon Bedrock to explain evidence without taking consequential decisions away from people.**

> One agent, many learners, one prioritized human queue.

## Live verification

- Visual judge demo: https://uvypcuixxrjikjaduvyo.supabase.co/functions/v1/community-agent-demo
- Structured JSON: https://uvypcuixxrjikjaduvyo.supabase.co/functions/v1/community-agent-demo?format=json

The public endpoint is read-only and privacy-minimized. It exposes anonymous aliases and aggregate risk evidence rather than stable learner identities.

## What happens end to end

1. **Observe** — read only the progress/activity fields needed for monitoring.
2. **Detect** — scan the community without waiting for a learner prompt.
3. **Persist + deduplicate** — keep one continuing risk episode; do not create a new alert every scan.
4. **Prioritize** — compute human-work order outside the LLM from urgency, active-risk evidence, and waiting time.
5. **Explain with Strands + Bedrock** — reason over bounded evidence through five purpose-built tools.
6. **Escalate consequential decisions** — payment, access, discipline, enrollment, deletion, safeguarding, medical, and legal decisions remain human-controlled.
7. **Resolve + audit** — humans close the task and the evidence/action trail remains inspectable.
8. **Measure operations** — report scans, suppression, clearing, open work, and human resolutions without claiming causal learning outcomes.

## Why this is genuinely agentic

- **Autonomous:** time-driven monitoring runs without a learner request.
- **Stateful:** risk episodes survive across scans and later clear when evidence changes.
- **Tool-using:** Strands operates through a deliberately constrained five-tool surface.
- **Goal-directed:** the system turns limited staff attention into a prioritized shared resource.
- **Human-aware:** the model can explain and advise, but consequential actions are not model-executable.
- **Resilient:** if Bedrock is unavailable, deterministic monitoring, triage, policy, and audit remain available.

## Five Strands tools

1. `get_community_overview` — aggregate community state without learner identities.
2. `get_attention_plan` — deterministic ranked human work projected to temporary aliases.
3. `get_impact_metrics` — operational evidence, explicitly non-causal.
4. `get_learner_context` — factual case context only when processing a specific learner case.
5. `record_support_note` — bounded advisory text with an independent deterministic validator.

The raw human follow-up queue is deliberately **not** exposed as a Strands community tool.

## Judging scorecard

### 1. Technological Implementation

Evidence:
- Strands Agents SDK + Amazon Bedrock integration.
- Amazon Bedrock AgentCore runtime adapter.
- Autonomous monitoring with persistence, deduplication, and clearing.
- Deterministic attention ranking separate from the LLM.
- Independent validator for model-authored support notes.
- CI with secret scanning, compile check, Ruff, pytest, and a live HTTP end-to-end smoke test.

Key files:
- `src/community_agent/agent.py`
- `src/community_agent/tools.py`
- `src/community_agent/monitor.py`
- `src/community_agent/triage.py`
- `src/community_agent/policy.py`
- `src/community_agent/safety.py`
- `src/community_agent/agentcore_runtime.py`
- `scripts/judge_smoke_test.py`

### 2. Design

The product is one coherent exception-handling workflow:

**Observe → Detect → Prioritize → Explain → Human decision → Resolve → Measure**

It is intentionally not another chat interface. Staff see only the cases that deserve attention, in a ranked queue with evidence explaining *why now*.

### 3. Potential Impact

Target audience: small schools and learning communities with limited support staff.

Specific problem: silent inactivity and repeated unresolved failure can go unnoticed when staff must manually inspect too many learners.

Specific intervention: one background agent converts weak signals into a deduplicated, prioritized human attention queue.

Operational proof available now:
- monitoring runs;
- learner scans;
- new alerts;
- continuing conditions without duplicate alerts;
- duplicate-suppression rate;
- cleared conditions;
- human resolutions;
- open human work and decision modes.

### 4. Creativity & Originality

Three deliberately non-obvious choices:
- **Not acting is an agent capability:** consequential tools do not exist in the model surface.
- **The LLM does not own priority:** ranking is deterministic and explainable.
- **Community reasoning does not require community identities:** model-facing triage uses temporary case aliases while authorized staff retain internal identifiers.

### 5. Presentation

Fast judge path:
1. Open the live demo.
2. Inspect detected community risk and anonymous aliases.
3. Review the deterministic attention plan and `why_now` evidence.
4. Run locally and generate a Strands community briefing.
5. Send a consequential event such as `payment_confirmation` and verify human escalation rather than execution.
6. Resolve a follow-up and verify `/impact` plus the audit trail update.

## Local 90-second verification

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
export COMMUNITY_AGENT_MODE=policy
PYTHONPATH=src python -m community_agent.seed_demo
PYTHONPATH=src uvicorn community_agent.api:app --host 0.0.0.0 --port 8080
```

Then open `http://localhost:8080`.

For Strands + Bedrock:

```bash
export COMMUNITY_AGENT_MODE=strands
PYTHONPATH=src uvicorn community_agent.api:app --host 0.0.0.0 --port 8080
```

## Automated end-to-end judge proof

With the app running locally, execute:

```bash
python scripts/judge_smoke_test.py
```

The verifier checks the live HTTP product path for:

- health + Strands identification;
- autonomous monitoring;
- deterministic priority and `why_now` evidence;
- payment confirmation being escalated instead of executed;
- temporary aliases and removal of stable IDs from model-facing community triage;
- policy / Strands / policy-fallback continuity;
- correct operational-impact scope;
- audit-trail evidence.

GitHub Actions now runs the same smoke test after the normal security, compile, lint, and pytest stages. See [`docs/VERIFICATION_REPORT.md`](VERIFICATION_REPORT.md) for the evidence map.

Automated checks:

```bash
python scripts/security_scan.py
ruff check src tests scripts
pytest -q
python scripts/judge_smoke_test.py
```

## Safety boundary in one sentence

**The agent may detect, prioritize, explain, and write validated advisory notes; it may not confirm payments, change course access, punish learners, decide enrollment, delete accounts, resolve safeguarding cases, or make medical/legal decisions.**

## Final one-line summary

**A Strands-powered school coordination agent that finds silent learner risk, prioritizes scarce human attention, and brings people in exactly where judgment matters.**
