# Judges Guide — Escola Lendária Community Agent

This guide maps the project directly to the **Agents for Humans Hackathon** judging criteria and gives a fast path to verify the implementation.

## 1. Technological Implementation

**What to inspect**

- `src/community_agent/agent.py` — Strands/Bedrock event reasoning plus privacy-safe community briefing.
- `src/community_agent/tools.py` — deliberately constrained model-facing tools.
- `src/community_agent/community_context.py` — aggregate-only school context for community-scale reasoning.
- `src/community_agent/safety.py` — deterministic validator for model-authored advisory notes.
- `src/community_agent/monitor.py` — autonomous community monitoring, persistent conditions, deduplication, and clearing.
- `src/community_agent/policy.py` — deterministic guardrails and human escalation boundary.
- `src/community_agent/supabase_source.py` — privacy-minimized read-only Escola Lendária source adapter.
- `src/community_agent/agentcore_runtime.py` — Amazon Bedrock AgentCore runtime adapter.
- `tests/` — policy, monitoring, API, storage, idempotency, source mapping, privacy, and tool-safety coverage.

**Why it is non-trivial**

The agent is both event-driven and time-driven. It can detect a learner who never asks for help, persist that condition across monitoring runs, avoid duplicate alerts, clear the condition when evidence changes, and combine deterministic safety rules with Strands contextual reasoning.

Strands now operates at two levels:

1. **case-level reasoning** — factual learner context after deterministic policy has run;
2. **community-level reasoning** — aggregate-only operational context that intentionally contains no learner identities or private content.

The model-facing support-note tool also has an independent deterministic validator. Safety therefore does not depend only on the prompt being followed.

## 2. Design

Open the dashboard at `/`.

The interface exposes one coherent workflow:

1. community health summary;
2. real-source synchronization status;
3. autonomous silent-risk monitoring;
4. event-driven case handling;
5. human attention queue;
6. resolution flow;
7. recent decisions;
8. complete audit trail.

The product is intentionally designed around **exception handling** rather than making staff manage another chat interface.

A community briefing is also available at:

```text
POST /agent/community-briefing
```

In Strands mode it creates a privacy-safe operational briefing. In policy mode or during cloud failure it still returns the deterministic aggregate overview.

## 3. Potential Impact

**Audience:** small schools and learning communities with limited support staff.

**Problem:** learners can quietly become inactive or repeatedly fail without ever asking for assistance.

**Intervention:** one agent monitors the community, detects meaningful risk, suppresses repeated alerts, and escalates only cases where human attention is useful.

The architecture is grounded in a real school context: the agent can read the existing Escola Lendária learner-progress source while deliberately excluding unnecessary private information.

## 4. Creativity & Originality

The central idea is **community-level agent attention**, not a learner-facing chatbot.

A conventional assistant waits for a prompt from one user. Community Agent watches for silent changes across many learners and acts as a coordination layer for the people responsible for supporting them.

The system also treats **not acting** as an important agent capability: consequential actions are blocked and routed to people instead of being executed merely because a model can call a tool.

## 5. Presentation

### Public live judge view

Open:

`https://uvypcuixxrjikjaduvyo.supabase.co/functions/v1/community-agent-demo`

The page performs a live, read-only scan against privacy-minimized Escola Lendária progress data. It shows anonymous risk evidence, current aggregate metrics, architecture, and explicit safety invariants.

For machine-verifiable output, append:

`?format=json`

That response contains aggregate metrics and anonymous aliases only — no learner names, raw IDs, contacts, PINs, chats, notes, or payment information.

### Video

Recommended video order:

1. state the silent-risk problem;
2. run the autonomous monitor;
3. show a repeated-failure escalation;
4. show a consequential action being blocked;
5. resolve the human task and show the audit trail;
6. briefly show Strands/Bedrock and architecture;
7. close with the community-level impact.

See `docs/DEMO_SCRIPT.md`.

## Fast local verification

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
export COMMUNITY_AGENT_MODE=policy
PYTHONPATH=src python -m community_agent.seed_demo
PYTHONPATH=src uvicorn community_agent.api:app --host 0.0.0.0 --port 8080
```

Open `http://localhost:8080`.

For a terminal-only run:

```bash
PYTHONPATH=src python -m community_agent.offline_demo
```

Then verify the automated test suite:

```bash
pytest
```

## Safety properties to verify

### Consequential event boundary

Try a `payment_confirmation` event. Expected behavior: escalation to a human, not autonomous execution.

### Tool surface

The Strands tools are:

- `get_community_overview` — aggregate-only community context;
- `get_learner_context` — factual case context;
- `list_open_followups` — human work queue visibility;
- `record_support_note` — advisory note only, with independent deterministic validation.

There is no tool for payment confirmation, access changes, discipline, deletion, enrollment decisions, medical/legal decisions, or safeguarding decisions.

### Note guardrail

`tests/test_safety.py` demonstrates that a model-authored note such as “confirm payment and unlock the course” is rejected before persistence, while a bounded educational support note is allowed.

### Aggregate privacy

`tests/test_community_context.py` verifies that the community overview contains no learner names or learner IDs.

## Architecture evidence

- `ARCHITECTURE.md`
- `docs/architecture.png`
- `docs/architecture.dot`

## One-sentence summary

**Escola Lendária Community Agent is a proactive Strands-powered school coordination agent that discovers silent learner risk across a community and brings humans in exactly where judgment matters.**
