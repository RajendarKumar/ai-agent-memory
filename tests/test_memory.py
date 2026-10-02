from datetime import date

from refund_agent.memory.short_term import ShortTermMemory


def test_short_term_memory_contains_only_current_request():
    memory = ShortTermMemory("email", "policy", date(2026, 9, 23))

    assert memory.as_state() == {
        "email_body": "email",
        "refund_policy": "policy",
        "evaluation_date": date(2026, 9, 23),
    }