# Impact Measurement Plan

Escola Lendária Community Agent is built around a specific operational problem: a small school cannot continuously watch every learner, and the learner who needs help may never ask for it.

The project separates **what the agent can already measure** from **outcomes that require a real longitudinal pilot**. This avoids turning promising operational signals into unsupported causal claims.

## What is measured now

`GET /impact` reports auditable behavior from the agent's own operational store:

- completed monitoring runs;
- learner scans performed;
- active risk-condition observations;
- new alerts created;
- continuing conditions that did not create another alert;
- duplicate-alert suppression rate;
- conditions automatically cleared when evidence disappeared;
- human resolutions recorded;
- open human follow-ups;
- decision modes (`policy`, `strands`, or `policy-fallback`).

These metrics answer: **Is the agent actually doing the coordination work it claims to do?**

## Primary hypotheses for a school pilot

### H1 — Earlier visibility of silent risk

If the background monitor is useful, staff should discover inactivity and repeated-failure cases earlier than with request-only support.

Future comparison metric:

- median time from risk threshold crossing to first staff review;
- percent of qualifying silent-risk cases reviewed within 24/48 hours.

### H2 — Less alert fatigue

If persistent-condition deduplication works, repeated scans should not create repeated human tasks for the same unchanged problem.

Measured now:

- `continuing_conditions_without_duplicate_alert`;
- `duplicate_suppression_rate`.

Future operational metric:

- alerts per distinct risk episode;
- staff-reported irrelevant-alert rate.

### H3 — Better use of scarce staff attention

If deterministic triage is useful, the highest-urgency/highest-risk/longest-waiting open cases should reliably appear first.

Measured now:

- `GET /attention-plan` ranking;
- owner-role workload counts;
- deterministic `why_now` explanation.

Future operational metric:

- time-to-review by priority band;
- number of high-priority cases waiting beyond the school's target service level.

## Learner outcomes that require a longer pilot

The project does **not** currently claim that the agent causes better grades, retention, or completion. Those outcomes need a study over time.

Useful future outcome measures include:

- re-engagement within 7 days after a human intervention;
- successful next attempt after repeated-failure support;
- lesson completion after an inactivity intervention;
- course retention/completion over a defined comparison period.

A credible evaluation should compare like-for-like cohorts or periods and account for changes in curriculum, staffing, enrollment and seasonality.

## Safety and fairness evaluation

The prioritization formula uses operational evidence only:

- urgency assigned by deterministic policy;
- active monitoring risk;
- waiting time.

It does not use protected demographic characteristics. A future pilot should still audit whether data completeness or access patterns create uneven monitoring coverage across groups.

Recommended checks:

- missing-activity-data rate by course/level;
- false-positive and false-negative review by staff;
- intervention rate by monitoring rule;
- manual override reasons;
- cases where staff judged the priority order inappropriate.

## Success definition

The project succeeds operationally if it can demonstrate a repeatable chain:

**silent evidence → one persistent risk episode → one appropriately prioritized human task → human resolution → auditable clearing**, without unnecessary exposure of learner data or autonomous consequential decisions.
