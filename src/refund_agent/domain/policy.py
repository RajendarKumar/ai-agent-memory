import re


def parse_refund_rules(refund_policy: str) -> list[dict[str, str]]:
    """Split a numbered policy into named rule records for display or indexing."""
    rules = re.split(r"(?:^|\s)\d+\.\s+", refund_policy.strip())
    return [
        {"rule": f"Rule {index}", "value": text.strip()}
        for index, text in enumerate((item for item in rules if item.strip()), start=1)
    ]