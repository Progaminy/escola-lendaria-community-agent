# Grand-prize demo script

## 0:00–0:25 — The problem
A small school can serve many learners but cannot afford a support team watching every learner. A learner can quietly stop progressing without ever opening a chatbot.

## 0:25–0:55 — Real community source
Open the dashboard and show **Escola Lendária data source**. Explain that the agent can read the school's real learner-progress state while deliberately excluding contacts, PINs, chats, private notes and payment data. Trigger **Sync real learner state** when production credentials are configured.

## 0:55–1:40 — Proactive monitoring
Click **Run autonomous scan now**. Show the monitor discovering inactivity or unresolved repeated failures without the learner asking for help. Show the persistent silent-risk table and human attention queue.

## 1:40–2:25 — Event-driven handling
Send a `repeated_failure` event. Show deterministic risk scoring, an evidence-backed signal and the follow-up. With AWS active, show the Strands/Bedrock contextual support note after the safety decision.

## 2:25–3:00 — Human boundary
Send a `payment_confirmation` or safety-sensitive event. Show that the agent does not execute the consequential action and instead routes it to a person. Resolve the follow-up and show the audit record.

## 3:00–3:30 — No alert fatigue
Send a normal `lesson_completed` event. Show that ordinary progress does not create a human task. The value is fewer, better interventions rather than more notifications.

## 3:30–4:15 — Architecture
Show `docs/architecture.png`: real Supabase learner source → privacy-minimized adapter → community memory → autonomous monitor → deterministic guardrails → Strands + Amazon Bedrock → constrained tools → human queue, with AgentCore as the deployment target.

## 4:15–4:45 — Community impact
Explain the Good Neighbor idea: one small school can proactively coordinate support across many learners with limited staff. The agent notices silent risk that a request-only chatbot cannot see.

## 4:45–5:00 — Closing
“One agent, many learners, proactive support, human judgment where it matters.”
