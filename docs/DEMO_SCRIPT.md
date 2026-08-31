# Demo Script — Escola Lendária Community Agent

Target length: **3:30–4:00 minutes**. Show the working product first; explain architecture only after the judge has seen the agent act.

## 0:00–0:20 — The problem

“Small schools cannot watch every learner all the time. The learner most at risk may never ask for help. Escola Lendária Community Agent watches the community in the background and surfaces only the cases that need human attention.”

Show the dashboard immediately.

## 0:20–0:55 — Autonomous silent-risk detection

Click **Run autonomous scan now**.

Point out that the scan runs across the learner population without waiting for a chat message. Show an inactivity or unresolved repeated-failure condition appearing in the monitor.

Say:

“This is the key difference from a chatbot: the learner did not have to ask first.”

## 0:55–1:35 — Event-driven support

Send a `repeated_failure` event.

Show:

- the evidence-backed risk decision;
- the human attention queue;
- the owner role and urgency;
- the decision/audit record.

With AWS configured, show the Strands + Amazon Bedrock contextual support note after the deterministic safety decision.

## 1:35–2:10 — Human safety boundary

Send a `payment_confirmation` event.

Show that the system **does not execute** the payment confirmation or course-access change. It routes the case to a person.

Say:

“Agentic does not mean unrestricted. The model can reason, but consequential actions remain human-controlled.”

Resolve the follow-up and show the audit trail update.

## 2:10–2:35 — No alert fatigue

Show that continuing conditions are deduplicated instead of creating a new alert on every scan. Mention that conditions clear when the evidence disappears.

If useful, send a normal `lesson_completed` event and show that ordinary progress does not create unnecessary human work.

## 2:35–3:00 — Real Escola Lendária context

Show **Escola Lendária data source**.

Explain that the integration is read-only and privacy-minimized: learner activity/progress is used, while contacts, PINs, chats, private notes, drafts, and payment information are deliberately excluded.

If production credentials are configured, click **Sync real learner state**.

## 3:00–3:25 — Architecture and Strands

Show `docs/architecture.png` and briefly trace:

`Escola Lendária / events → privacy-minimized adapter → community state → autonomous monitor → deterministic guardrails → Strands + Amazon Bedrock → constrained tools → human queue → audit`

Mention the included Amazon Bedrock AgentCore runtime adapter.

## 3:25–3:45 — Close on impact

“Escola Lendária Community Agent turns limited staff attention into a shared resource. One agent can watch many learners, detect silent risk early, and bring a person in exactly where judgment matters.”

End with:

**“One agent, many learners, proactive support, human judgment where it matters.”**

## Recording checklist

Before recording, verify:

- the dashboard loads cleanly;
- at least one silent-risk condition is available for the autonomous scan;
- the repeated-failure scenario creates a visible follow-up;
- the consequential-action scenario is visibly blocked/escalated;
- the human resolution appears in the audit trail;
- the Strands/Bedrock path is enabled if AWS credentials are available;
- no secret keys, phone numbers, PINs, or private learner data are visible on screen;
- the final video is under the hackathon's 5-minute limit.
