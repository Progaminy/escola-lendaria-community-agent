from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

from .seed_demo import seed
from .monitor import monitoring_state_data, run_community_monitor
from .service import community_digest_data, list_open_followups_data, process_event_locally


def run() -> dict:
    if "COMMUNITY_AGENT_DB" not in os.environ:
        demo_dir = Path(tempfile.mkdtemp(prefix="community-agent-demo-"))
        os.environ["COMMUNITY_AGENT_DB"] = str(demo_dir / "community_agent.db")
    seed()

    scenarios = [
        {
            "event_id": "demo-001",
            "learner_id": "L-002",
            "event_type": "repeated_failure",
            "details": "Learner failed the same practical circuit exercise 3 times and requested help.",
            "severity_hint": "medium",
        },
        {
            "event_id": "demo-002",
            "learner_id": "L-003",
            "event_type": "lesson_completed",
            "details": "Learner completed the typing lesson successfully.",
            "severity_hint": "low",
        },
        {
            "event_id": "demo-003",
            "learner_id": "L-001",
            "event_type": "payment_confirmation",
            "details": "Learner asks the system to confirm a payment and unlock the next course.",
            "severity_hint": "medium",
        },
    ]

    monitor = run_community_monitor()
    results = [process_event_locally(**scenario) for scenario in scenarios]
    return {
        "autonomous_monitor": monitor,
        "monitoring_state": monitoring_state_data(),
        "scenarios": results,
        "open_followups": list_open_followups_data(),
        "digest": community_digest_data(),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
