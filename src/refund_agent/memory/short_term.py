from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ShortTermMemory:
    """Per-invocation context. It is discarded when the request finishes."""

    email_body: str
    refund_policy: str
    evaluation_date: date

    def as_state(self) -> dict:
        return {
            "email_body": self.email_body,
            "refund_policy": self.refund_policy,
            "evaluation_date": self.evaluation_date,
        }