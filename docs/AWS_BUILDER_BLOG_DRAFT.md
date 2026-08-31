# Agents for Humans: Building a Good Neighbor Agent for Silent Learner Risk

Small schools do not usually fail because nobody cares. They fail because a small number of people are expected to notice too many things at once.

A learner can stop opening lessons, repeat the same exercise unsuccessfully, or quietly disappear from the learning flow without ever sending a message asking for help. A normal chatbot cannot see that learner, because a chatbot waits for a prompt.

For the Agents for Humans Hackathon, I built **Escola Lendária Community Agent**, a Strands-powered Good Neighbor Agent designed to notice those silent changes across a school community and route only the meaningful cases to people.

## The design goal

The goal was not to create another chat interface. It was to create a quiet coordination layer that can run in the background.

The agent:

- reads privacy-minimized learner activity;
- runs scheduled community scans;
- detects prolonged inactivity and unresolved repeated failures;
- persists active conditions across scans;
- avoids duplicate alerts;
- clears a condition when the evidence disappears;
- uses Strands Agents SDK with Amazon Bedrock for bounded contextual reasoning;
- routes consequential decisions to humans;
- records an audit trail.

The beneficiary is not one user. It is the whole learning community.

## Why deterministic guardrails come before the model

I did not want the model to be the authority on whether it is allowed to perform a consequential action.

The application therefore has a deterministic policy layer before Strands reasoning. Payments, course-access changes, enrollment or punishment decisions, account deletion, medical/legal decisions, and safeguarding decisions are human-controlled.

The model-facing tool surface is deliberately small:

- `get_community_overview`
- `get_learner_context`
- `list_open_followups`
- `record_support_note`

There is no model tool that can confirm a payment, unlock a course, delete an account, or punish a learner.

I also added a second deterministic validator to `record_support_note`. Even though the note is advisory text, the tool rejects attempts to encode a consequential instruction such as confirming payment or unlocking access. This means the safety property does not depend only on the system prompt being followed.

## Community-level reasoning without exposing identities

A Good Neighbor Agent should reason about the community, but that does not mean the model needs every learner identity.

The `get_community_overview` Strands tool returns aggregate operational context: counts, risk categories, monitoring rules, event mix, and follow-up workload. It intentionally excludes learner names, learner IDs, contacts, PINs, chats, private notes, and payment information.

That allows the agent to produce a community briefing for staff without unnecessarily exposing individual identities to the model.

## Real-world source, privacy-minimized adapter

The project can synchronize read-only with the existing Escola Lendária Supabase learner-progress source.

Only the progress/activity information needed for monitoring is mapped into the agent. Contacts, PINs, chats, drafts, support-message bodies, and payment information are excluded.

A public live judge view demonstrates the read-only risk scan with temporary learner aliases only. The same endpoint also offers structured JSON so the output can be verified without exposing private data.

## AWS and Strands

The agent uses:

- **Strands Agents SDK** for tool-using contextual reasoning;
- **Amazon Bedrock** as the model layer;
- an **Amazon Bedrock AgentCore runtime adapter** as a deployment path;
- FastAPI for the application API;
- SQLite for local operational state and auditability;
- Supabase as an optional read-only real learner-progress source.

The cloud model is not a single point of failure. If Bedrock is unavailable, deterministic monitoring and guardrails remain usable in policy-fallback mode.

## The most important agent action can be “do not act”

One of the most useful lessons from this project is that autonomy is not the same as unrestricted action.

A trustworthy agent should know where its authority stops. In Escola Lendária Community Agent, detecting risk can be autonomous. Contextual support reasoning can be autonomous. Creating an advisory note can be autonomous. But a consequential decision is routed to a person.

That separation makes the agent more useful, not less agentic, because staff can trust it to run quietly without giving it powers it does not need.

## What I would build next

The next steps are to improve intervention-outcome measurement, add configurable school-level policies, and deploy the full Strands runtime to managed AWS infrastructure so the same community-monitoring pattern can support more schools and local organizations.

The core principle will remain the same:

**One agent, many learners, proactive support, human judgment where it matters.**

## Project links

- Public repository: https://github.com/Progaminy/escola-lendaria-community-agent
- Live demo: https://uvypcuixxrjikjaduvyo.supabase.co/functions/v1/community-agent-demo
- Demo video: https://youtu.be/RcocWXhlpHc?si=gKgfsBtqiRPv8GEp

#AgentsForHumans #AWS #StrandsAgents #AmazonBedrock #GoodNeighborAgents
