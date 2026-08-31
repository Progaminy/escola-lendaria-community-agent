# Security and Privacy

Escola Lendária Community Agent is designed so that model reasoning is not the final authority for consequential actions.

## Secrets

- Runtime credentials must be supplied through environment variables or a secret manager.
- `.env` is ignored by Git.
- Supabase secret/service-role credentials are server-side only.
- AWS credentials are never embedded in source code.
- CI runs `python scripts/security_scan.py` to reject high-confidence committed secret patterns.

## Data minimization

The Escola Lendária source adapter requests only the learner/activity fields required for monitoring and projects only `state.progress` from the JSON state. It intentionally excludes contacts, PINs, chats, private notes, drafts, payment information, and support-message bodies.

The public live demo is read-only and returns anonymous aliases plus aggregate risk evidence. It does not return learner names or raw learner IDs.

## Human-control boundary

Payments, enrollment/expulsion, punishment, account deletion, course-access changes, medical/legal decisions, and safeguarding decisions are not model-executable tools. Deterministic policy routes those cases to humans before Strands reasoning.

Model-authored support notes are also independently validated by `src/community_agent/safety.py` before persistence.

## Tool minimization

The Strands tool surface is intentionally smaller than the application surface. The agent can read bounded context, inspect/prioritize human work, and record advisory educational notes; it cannot execute consequential school actions.

## Reporting

If you discover a security issue, avoid posting private learner information or credentials in a public issue. Contact the repository owner privately and rotate any credential that may have been exposed.
