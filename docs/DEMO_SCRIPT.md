# Final Demo Script — Escola Lendária Community Agent

Target length: **3:45–4:15 minutes**. The hackathon allows up to 5 minutes. Show the working product before architecture. Every segment below maps to a judging criterion.

## 0:00–0:18 — Hook: the learner who never asks

Open the **live judge demo** first.

Say:

> “A chatbot sees the learner who speaks. Escola Lendária Community Agent is built to notice the learner who goes quiet.”

Then:

> “Small schools cannot manually inspect every learner every day. This agent watches the community in the background, finds silent risk, and turns limited staff attention into a prioritized human queue.”

On screen: show that the public endpoint is live, read-only, privacy-minimized, and using temporary learner aliases.

## 0:18–0:48 — Live community evidence

Click **Run fresh scan** on the public demo.

Point to:

- learners scanned;
- watchlist;
- human-attention count;
- inactivity signals;
- repeated-failure signals;
- anonymous top-risk evidence.

Say:

> “This public page reads real Escola Lendária progress data without returning names, raw learner IDs, contacts, PINs, chats, private notes, or payment data.”

Briefly open **Verify JSON** to prove the same privacy and safety properties in machine-readable form.

## 0:48–1:25 — Autonomous monitoring + persistent risk

Switch to the full local agent dashboard and click **Run fresh community scan**.

Show a detected inactivity or repeated-failure condition.

Say:

> “The learner did not need to open a chatbot. Monitoring is time-driven and autonomous. A risk episode persists across scans, duplicate alerts are suppressed, and the condition clears when the evidence disappears.”

Point to the monitor state or audit evidence rather than describing it abstractly.

## 1:25–1:58 — The scarce-resource problem: what should staff look at first?

Show the **ranked human attention plan**.

Point to `priority_score` and `why_now`.

Say:

> “Detection is only half the problem. A small team still needs to know what deserves attention first. Priority is calculated outside the language model from urgency, active-risk evidence, and waiting time.”

Display the formula:

```text
priority = urgency base + active-risk bonus + waiting-time bonus
```

Then say:

> “Strands can explain this ordering, but it cannot silently change the score.”

## 1:58–2:27 — Strands + Bedrock, with identity minimization

Click **Generate community briefing**.

Show the Strands/Bedrock response and its attention plan.

Point out temporary aliases such as `priority-case-01`.

Say:

> “At community level, the model receives the same deterministic ranking but stable learner, follow-up, and event identifiers are removed. Staff retain the real identifiers needed to resolve work; the model does not need them.”

Mention the five model-facing tools:

- `get_community_overview`
- `get_attention_plan`
- `get_impact_metrics`
- `get_learner_context`
- `record_support_note`

Do not spend time reading every tool description.

## 2:27–2:58 — Human safety boundary

Send a `payment_confirmation` event.

Show that the system creates human work instead of confirming the payment or changing course access.

Say:

> “Agentic does not mean unrestricted. Consequential decisions are evaluated by deterministic policy before model reasoning. Payment, access, discipline, enrollment, deletion, safeguarding, and medical or legal decisions stay human-controlled.”

If visible, point to the administrator owner role and the audit record.

## 2:58–3:20 — Resolve and prove the loop closes

Resolve the follow-up as a human.

Show the audit trail and then open `GET /impact` or the impact panel.

Say:

> “The human resolution is recorded, and the system measures what it can actually prove: scans, alerts, duplicate suppression, cleared conditions, open work, decision modes, and human resolutions.”

Then explicitly state:

> “These are operational coordination metrics, not a claim that the agent has already caused better grades or retention.”

## 3:20–3:43 — Architecture and resilience

Show `docs/architecture.png`.

Trace only the main path:

```text
Escola Lendária progress
→ privacy-minimized adapter
→ autonomous monitor + persistent state
→ deterministic policy + attention ranking
→ Strands Agents SDK + Amazon Bedrock
→ five constrained tools
→ human queue
→ resolution + audit + operational evidence
```

Mention:

> “The repository also includes an Amazon Bedrock AgentCore runtime adapter. If Bedrock is temporarily unavailable, monitoring, deterministic safety, priority, and auditability remain usable in policy-fallback mode.”

## 3:43–4:05 — Reproducibility: do not ask the judge to trust the pitch

Open the repository and briefly show the **Judge Fast Path** and **Verification Report**.

Say:

> “The core claims are reproducible. CI runs secret scanning, compile checks, Ruff, pytest, and an end-to-end live-HTTP judge smoke test.”

Mention that the smoke verifier checks:

- autonomous monitoring;
- deterministic priority evidence;
- payment escalation rather than AI execution;
- removal of stable IDs from model-facing community triage;
- persisted decisions and audit records.

## 4:05–4:15 — Close

Return to the live demo or attention queue.

Say:

> “One agent, many learners, one prioritized human queue. Escola Lendária Community Agent notices who goes quiet and brings people in exactly where judgment matters.”

---

## Recording checklist

Before recording:

- use the improved public live demo and click **Run fresh scan**;
- ensure at least one silent-risk condition is visible;
- make the deterministic attention plan and `why_now` visible;
- generate a community briefing and show `priority-case-*` aliases;
- show a `payment_confirmation` event becoming human escalation;
- resolve a follow-up and show impact/audit evidence changing;
- show the architecture for no more than 20–25 seconds;
- show the Judge Fast Path / Verification Report briefly;
- if AWS credentials are available, record the Strands + Bedrock path directly;
- if Bedrock is unavailable, clearly identify policy-fallback instead of pretending a cloud model call occurred;
- never show secret keys, phone numbers, PINs, private learner information, or payment details;
- keep the final video below **5 minutes**.

## Presentation rule

Do not spend the opening minute explaining infrastructure. The judge should see, in this order:

**real problem → working agent → deterministic priority → Strands reasoning → human safety boundary → measurable evidence → architecture.**
