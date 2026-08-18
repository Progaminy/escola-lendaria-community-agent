from __future__ import annotations

from .agent import process_event
from .seed_demo import seed


def main() -> None:
    seed()
    scenarios = [
        {
            "learner_id": "L-002",
            "event_type": "repeated_failure",
            "details": "Learner failed the same practical circuit exercise three times and asked for help.",
            "severity_hint": "medium",
        },
        {
            "learner_id": "L-003",
            "event_type": "lesson_completed",
            "details": "Learner completed the typing lesson successfully with no help request.",
            "severity_hint": "low",
        },
    ]
    for event in scenarios:
        print("=" * 72)
        print(process_event(**event))


if __name__ == "__main__":
    main()
