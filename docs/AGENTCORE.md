# Amazon Bedrock AgentCore Runtime Path

The repository includes `src/community_agent/agentcore_runtime.py`, an AgentCore runtime adapter that reuses the same Strands + Amazon Bedrock agent and the same deterministic safety boundary as the local API.

This file is a deployment path, not a claim that the public Supabase judge page is running AgentCore. The public page is deliberately a read-only monitoring verifier; AgentCore is the AWS runtime target for the full agent.

## Supported actions

### Event handling

```json
{
  "action": "event",
  "event_id": "example-001",
  "learner_id": "L-001",
  "event_type": "repeated_failure",
  "details": "Learner failed the same exercise three times.",
  "severity_hint": "medium"
}
```

The deterministic policy executes before Strands reasoning. Consequential cases remain human-controlled.

### Community briefing

```json
{
  "action": "community_briefing"
}
```

Returns deterministic community evidence, the fixed human-attention plan, operational impact metrics, and a Strands briefing when Bedrock is available.

### Attention plan

```json
{
  "action": "attention_plan",
  "limit": 12
}
```

Returns the deterministic priority ordering without model modification.

### Operational evidence

```json
{
  "action": "impact"
}
```

Returns auditable coordination metrics such as scans, duplicate suppression, cleared conditions and human resolutions.

## Authority model

AgentCore changes the runtime location, not the authority boundary. The model still has no tool for payment confirmation, course-access changes, discipline, enrollment decisions, account deletion, medical/legal decisions, or safeguarding decisions.

The runtime adapter deliberately routes all event handling through `process_event`, so the local API and AgentCore path do not implement separate safety logic.
