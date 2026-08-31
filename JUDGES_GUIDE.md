# Judges Guide — Escola Lendária Community Agent

This guide maps the project directly to the **Agents for Humans Hackathon** judging criteria and gives reviewers a fast, reproducible verification path.

## 1. Technological Implementation

### What to inspect

- `src/community_agent/agent.py` — Strands + Amazon Bedrock case reasoning and privacy-minimized community briefing.
- `src/community_agent/tools.py` — deliberately constrained five-tool model-facing surface.
- `src/community_agent/monitor.py` — autonomous whole-community monitoring, persistent conditions, deduplication and clearing.
- `src/community_agent/triage.py` — deterministic human-attention ranking plus an identifier-free model projection.
- `src/community_agent/impact.py` — auditable operational metrics without causal-outcome inflation.
- `src/community_agent/policy.py` — deterministic consequential-action/safety boundary before model reasoning.
- `src/community_agent/safety.py` — independent validator for model-authored advisory notes.
- `src/community_agent/community_context.py` — aggregate-only community context.
- `src/community_agent/supabase_source.py` — privacy-minimized read-only Escola Lendária source mapping.
- `src/community_agent/agentcore_runtime.py` — Amazon Bedrock AgentCore runtime adapter for event, briefing, model-safe attention-plan and impact actions.
- `.github/workflows/ci.yml` + `scripts/security_scan.py` — secret scan, compile, lint and tests on every push/PR.

### Why it is non-trivial

The system is both **event-driven and time-driven**. It can detect a learner who never asks for help, persist the risk episode across scans, avoid duplicate human tasks, clear the condition when evidence changes, rank scarce staff attention deterministically, and then use Strands for bounded contextual explanation.

Strands operates over evidence rather than replacing the policy layer. Its current tool surface contains only five tools:

1. `get_community_overview` — privacy-safe aggregate group context;
2. `get_attention_plan` — fixed deterministic ranking with temporary aliases such as `priority-case-01`, not stable learner/follow-up/event IDs;
3. `get_impact_metrics` — observed coordination evidence, explicitly not causal learning claims;
4. `get_learner_context` — factual context only when processing a specific learner case;
5. `record_support_note` — advisory text with independent deterministic validation.

The raw human follow-up queue remains available to the application and authorized staff, but it is **not a Strands community tool**. A Bedrock/model failure does not disable monitoring, triage, hard safety rules or auditability.

## 2. Design

Open `/`. The main dashboard is deliberately structured as **one workflow**, not a collection of unrelated features:

**Observe → Detect → Prioritize → Explain/Decide → Resolve → Measure**

1. privacy-minimized learner activity is synchronized;
2. the autonomous monitor detects silent risk;
3. the human attention plan ranks actual open work with `why_now` evidence;
4. a Strands community briefing explains the state and workload using identifier-minimized community evidence;
5. staff resolve consequential/high-risk work;
6. the audit trail and operational metrics update.

This design treats staff attention as the scarce resource. It is an exception-handling product rather than another chat interface.

Useful endpoints:

```text
GET  /attention-plan
GET  /impact
POST /agent/community-briefing
```

## 3. Potential Impact

**Audience:** small schools and learning communities with limited support staff.

**Specific pain:** silent learners can become inactive or repeatedly fail without ever initiating a support conversation, while staff have too many learners to inspect manually.

**Specific intervention:** one background agent detects qualifying evidence, maintains one persistent risk episode instead of repeated alerts, and converts open cases into an explainable prioritized human queue.

### Evidence available now

`GET /impact` reports what the product can directly prove from its own operational store:

- completed scans and learner scans;
- new alerts;
- continuing risk observations that did not create duplicate alerts;
- duplicate-suppression rate;
- conditions cleared;
- human resolutions;
- decision modes and open human work.

The project intentionally does **not** claim that these metrics prove improved grades or retention. A future longitudinal evaluation plan is documented in `docs/IMPACT_MEASUREMENT.md`.

## 4. Creativity & Originality

The core idea is **community-level attention allocation**, not learner-facing conversation.

A normal assistant waits for whoever speaks. Community Agent watches for people who go quiet and asks a different question: **given limited human capacity, which case deserves attention first and why?**

Three non-obvious design choices:

- **Not acting is an agent capability.** Consequential actions are absent from the model tool surface.
- **The model does not own priority.** Human-work ordering is deterministic and explainable; Strands can reason over it but cannot silently change it.
- **Community reasoning does not require community identities.** The model sees temporary ranked case aliases while staff retain the internal identifiers needed to resolve work.

## 5. Presentation

### Public live judge view

`https://uvypcuixxrjikjaduvyo.supabase.co/functions/v1/community-agent-demo`

Machine-verifiable form:

`https://uvypcuixxrjikjaduvyo.supabase.co/functions/v1/community-agent-demo?format=json`

The public endpoint performs a fresh, read-only monitoring preview and renders anonymous aliases only.

### Fast local judge flow

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
2. inspect the ranked internal attention plan and `why_now` evidence;
3. generate the community briefing and verify its plan contains temporary aliases rather than stable IDs;
4. send a `payment_confirmation` event and verify human escalation rather than execution;
5. resolve a follow-up;
6. confirm that `/impact` and the audit trail reflect the work.

### Automated verification

```bash
python scripts/security_scan.py
ruff check src tests scripts
pytest -q
```

`docs/EVALUATION.md` provides the full reproducible matrix.

## Safety properties to verify

- **Consequential boundary:** payment, access, discipline, enrollment, deletion, legal/medical and safeguarding cases remain human work.
- **Note guardrail:** `tests/test_safety.py` proves consequential instructions cannot be smuggled through advisory notes.
- **Aggregate privacy:** `tests/test_community_context.py` proves the community overview excludes learner names and IDs.
- **Priority integrity:** `tests/test_triage.py` proves priority comes from deterministic urgency/risk/waiting evidence.
- **Identifier minimization:** `tests/test_triage.py` and `tests/test_v03_api.py` prove the model-facing community plan preserves the same scores while removing stable learner/event identifiers.
- **Evidence integrity:** `tests/test_impact.py` proves suppression, clearing and human-resolution metrics are derived from operational records.

## Architecture evidence

- `ARCHITECTURE.md`
- `docs/architecture.png`
- `docs/architecture.dot`
- `docs/AGENTCORE.md`
- `SECURITY.md`

## One-sentence summary

**Escola Lendária Community Agent is a Strands-powered school coordination agent that discovers silent learner risk, deterministically prioritizes scarce human attention, and brings people in exactly where judgment matters.**
