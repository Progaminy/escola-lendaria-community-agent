# Judges Guide — Escola Lendária Community Agent

This guide maps the project directly to the **Agents for Humans Hackathon** judging criteria and gives a fast path to verify the implementation.

## 1. Technological Implementation

**What to inspect**

- `src/community_agent/agent.py` — Strands/Bedrock event reasoning path.
- `src/community_agent/tools.py` — deliberately constrained model-facing tools.
- `src/community_agent/monitor.py` — autonomous community monitoring, persistent conditions, deduplication, and clearing.
- `src/community_agent/policy.py` — deterministic guardrails and human escalation boundary.
- `src/community_agent/supabase_source.py` — privacy-minimized read-only Escola Lendária source adapter.
- `src/community_agent/agentcore_runtime.py` — Amazon Bedrock AgentCore runtime adapter.
- `tests/` — policy, monitoring, API, storage, idempotency, and source-mapping coverage.

**Why it is non-trivial**

The agent is both event-driven and time-driven. It can detect a learner who never asks for help, persist that condition across monitoring runs, avoid duplicate alerts, clear the condition when evidence changes, and combine deterministic safety rules with Strands contextual reasoning.

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

Try a `payment_confirmation` event. The expected behavior is escalation to a human, not autonomous execution.

The Strands tool surface is limited to learner context retrieval, open-follow-up listing, and support-note recording. This separation ensures that model reasoning cannot directly perform payments, access changes, discipline, deletion, or other consequential actions.

## Architecture evidence

- `ARCHITECTURE.md`
- `docs/architecture.png`
- `docs/architecture.dot`

## One-sentence summary

**Escola Lendária Community Agent is a proactive Strands-powered school coordination agent that discovers silent learner risk across a community and brings humans in exactly where judgment matters.**
