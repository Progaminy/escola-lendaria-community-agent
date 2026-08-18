from community_agent.policy import assess_event

LEARNER = {
    "learner_id": "L-1",
    "failed_attempts": 3,
    "last_active_at": "2026-08-01T00:00:00Z",
}


def test_repeated_failure_requires_teacher():
    decision = assess_event(
        event_type="repeated_failure",
        details="Learner failed 3 times.",
        severity_hint="medium",
        learner=LEARNER,
    )
    assert decision.escalate is True
    assert decision.owner_role == "teacher"
    assert decision.risk_score >= 50


def test_payment_is_never_autonomous():
    decision = assess_event(
        event_type="payment_confirmation",
        details="Please confirm payment.",
        severity_hint="low",
        learner=LEARNER,
    )
    assert decision.escalate is True
    assert decision.owner_role == "administrator"
    assert decision.status == "human_escalation"


def test_completed_lesson_does_not_escalate():
    decision = assess_event(
        event_type="lesson_completed",
        details="Completed successfully.",
        severity_hint="low",
        learner=LEARNER,
    )
    assert decision.escalate is False
    assert decision.status == "normal_progress"
