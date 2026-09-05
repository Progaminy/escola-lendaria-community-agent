# Agents for Humans: Building a Good Neighbor Agent for Silent Learner Risk

Small schools do not usually fail because nobody cares. They fail because a small number of people are expected to notice too many things at once.

A learner can stop opening lessons, repeat the same exercise unsuccessfully, or quietly disappear from the learning flow without ever sending a message asking for help. A normal chatbot cannot see that learner because a chatbot waits for a prompt.

For the **Agents for Humans Hackathon**, I built **Escola Lendária Community Agent**, a proactive Good Neighbor Agent powered by **Strands Agents SDK + Amazon Bedrock**. Its job is simple to describe but hard to implement well: notice the learner who goes quiet, suppress alert noise, rank scarce staff attention, and stop exactly where human judgment should begin.

> **One agent, many learners, one prioritized human queue.**

## The design goal

I did not want another chat interface. I wanted a quiet coordination layer that could run in the background.

The agent:

- reads privacy-minimized learner progress/activity;
- runs autonomous community scans;
- detects silent inactivity and repeated unresolved failures;
- persists active risk episodes across scans;
- suppresses duplicate alerts;
- clears conditions when the evidence disappears;
- ranks open human work deterministically;
- uses Strands + Bedrock to explain bounded evidence;
- escalates consequential decisions to people;
- records an auditable operational trail.

The beneficiary is not one chat user. It is the whole learning community.

## Why prioritization matters as much as detection

Detecting risk is only half of the real school problem. Staff still need to know what deserves attention first.

The attention plan is computed outside the language model:

```text
priority = urgency base + active-risk bonus + waiting-time bonus
```

That means the LLM does not silently decide who is more important. The application computes an explainable ordering from operational evidence. Strands may explain that ordering, but it cannot change the score or resolve the task.

Before community-level model reasoning, the same ranked plan is projected to temporary aliases such as `priority-case-01`. Stable learner, follow-up, and event identifiers are removed from the model-facing form while authorized staff retain the identifiers they need to resolve work.

## Five Strands tools, deliberately constrained

The current model-facing tool surface contains only five tools:

- `get_community_overview` — aggregate community state without learner identities;
- `get_attention_plan` — deterministic ranked human work projected to temporary aliases;
- `get_impact_metrics` — auditable operational evidence, explicitly non-causal;
- `get_learner_context` — factual context only when processing a specific learner case;
- `record_support_note` — bounded advisory text with an independent deterministic validator.

The raw human follow-up queue remains available to authorized staff in the application, but it is deliberately **not** exposed as a Strands community tool.

There is no model tool that can confirm a payment, change course access, punish a learner, decide enrollment, delete an account, resolve a safeguarding case, or make a medical/legal decision.

## Safety is code, not only prompting

I did not want the model to be the authority on whether a consequential action is allowed.

The application therefore evaluates consequential events with a deterministic policy layer before Strands reasoning. Mandatory human escalation cannot be downgraded by the model.

I also added an independent deterministic validator to `record_support_note`. Even though the note is advisory text, the tool rejects attempts to encode a consequential instruction such as confirming payment, unlocking access, deleting an account, or punishing a learner.

This makes the safety boundary a property of the software architecture rather than a promise written only in a system prompt.

## Community-level reasoning without community identities

A Good Neighbor Agent should reason about the community, but the model does not need every learner identity to do that.

`get_community_overview` returns aggregate operational context. `get_attention_plan` returns the exact ranked workload but replaces stable identifiers with temporary aliases.

That lets Strands produce a useful community briefing while minimizing unnecessary identity exposure.

## Real-world source, privacy-minimized adapter

The project can synchronize read-only with the existing **Escola Lendária** Supabase learner-progress source.

The adapter requests only the activity/progress data needed for monitoring. It excludes contacts, progress PINs, chats, drafts, private notes, support-message bodies, and payment information.

The public judge endpoint is also read-only and renders anonymous aliases plus aggregate risk evidence.

## Operational evidence without inflated impact claims

The application exposes `GET /impact` to report what the agent can directly prove from its own operational store:

- monitoring runs and learner scans;
- active risk observations;
- new alerts created;
- continuing conditions that did not create duplicate alerts;
- duplicate-suppression rate;
- conditions cleared;
- human resolutions;
- open human work and decision modes.

I deliberately do **not** claim that these metrics prove better grades, retention, or completion. They prove coordination behavior. A separate longitudinal measurement plan documents how real learning outcomes should be evaluated in a future school pilot.

## AWS and Strands architecture

The agent uses:

- **Strands Agents SDK** for bounded tool-using reasoning;
- **Amazon Bedrock** as the model layer;
- an **Amazon Bedrock AgentCore runtime adapter** that routes event handling, community briefing, safe attention-plan retrieval, and impact retrieval through the same safety path;
- FastAPI for the application API;
- SQLite for operational state and auditability;
- Supabase as an optional privacy-minimized read-only learner-progress source.

The cloud model is not a single point of failure. If Bedrock is temporarily unavailable, deterministic monitoring, safety policy, triage, metrics, and auditability remain usable in policy-fallback mode.

## Why this is more than a chatbot

The system is both time-driven and event-driven.

It can discover a learner who never asks for help, remember the risk episode across scans, avoid creating duplicate work, clear the condition when evidence changes, rank scarce human attention, and then use Strands to explain that evidence through a small tool surface.

That is the agent loop I wanted: **observe, detect, persist, prioritize, explain, escalate, resolve, measure**.

## The most important agent action can be “do not act”

One of the strongest lessons from this project is that autonomy is not the same as unrestricted action.

A trustworthy agent should know where its authority stops. In Escola Lendária Community Agent, detecting risk can be autonomous. Contextual explanation can be autonomous. Writing a validated advisory note can be autonomous. But a consequential decision is routed to a person.

That separation makes the agent more useful, not less agentic, because staff can trust it to run quietly without giving it powers it does not need.

## What I would build next

The next steps are to run a longitudinal school pilot, improve intervention-outcome measurement, add configurable school-level policies, and deploy the full Strands runtime on managed AWS infrastructure for broader community use.

The core principle will remain the same:

**A normal assistant waits for whoever speaks. Community Agent is built to notice who goes quiet.**

## Project links

- Devpost: https://devpost.com/software/escola-lendaria-community-agent
- Public repository: https://github.com/Progaminy/escola-lendaria-community-agent
- Judge Fast Path: https://github.com/Progaminy/escola-lendaria-community-agent/blob/main/docs/JUDGE_FAST_PATH.md
- Live demo: https://uvypcuixxrjikjaduvyo.supabase.co/functions/v1/community-agent-demo
- Structured live verification: https://uvypcuixxrjikjaduvyo.supabase.co/functions/v1/community-agent-demo?format=json
- Demo video: https://youtu.be/RcocWXhlpHc?si=gKgfsBtqiRPv8GEp

#AgentsForHumans #AWS #StrandsAgents #AmazonBedrock #GoodNeighborAgents
