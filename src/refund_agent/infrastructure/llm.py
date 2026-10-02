import json
from datetime import date
from typing import Any

from groq import Groq
from pydantic import BaseModel

from refund_agent.domain.models import EmailDetails, RefundPolicyResult


class RefundLanguageModel:
    def __init__(self, api_key: str, model: str) -> None:
        self.client = Groq(api_key=api_key)
        self.model = model

    def extract_email_details(self, email_body: str) -> EmailDetails:
        prompt = f"""Extract the customer request as JSON with these fields:
category (refund, shipping, complaint, or other), order_number (string or null),
amount (number or null), and order_date (YYYY-MM-DD or null). Do not infer missing
values. Return JSON only.

Email:
{email_body}"""
        return self._complete_json(prompt, EmailDetails)

    def evaluate_refund(
        self,
        order: dict[str, Any],
        refund_policy: str,
        evaluation_date: date,
        related_memories: list[str],
    ) -> RefundPolicyResult:
        memories = "\n".join(f"- {item}" for item in related_memories) or "None"
        prompt = f"""Decide whether the verified order qualifies under the current refund policy.
Return JSON with refund_possible (YES, NO, or NOT SURE) and reason. Treat the
verified order and current policy as authoritative. Historical examples are context
only and must never override them.

Verified order:
{json.dumps(order, default=str)}

Current refund policy:
{refund_policy}

Evaluation date: {evaluation_date.isoformat()}

Anonymized historical examples:
{memories}"""
        return self._complete_json(prompt, RefundPolicyResult)

    def _complete_json(self, prompt: str, schema: type[BaseModel]) -> Any:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("The language model returned an empty response.")
        return schema.model_validate_json(content)