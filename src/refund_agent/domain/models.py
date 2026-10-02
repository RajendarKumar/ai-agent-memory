from datetime import date
from typing import Literal, TypedDict

from pydantic import BaseModel


class EmailDetails(BaseModel):
    category: Literal["refund", "shipping", "complaint", "other"]
    order_number: str | None = None
    amount: float | None = None
    order_date: date | None = None


class RefundPolicyResult(BaseModel):
    refund_possible: Literal["YES", "NO", "NOT SURE"]
    reason: str


class RefundState(TypedDict, total=False):
    email_body: str
    refund_policy: str
    evaluation_date: date
    extracted: dict
    order: dict | None
    policy_result: dict
    related_memories: list[str]
    status: str
    reason: str