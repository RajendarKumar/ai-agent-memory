import json

import pytest

from refund_agent.domain.policy import parse_refund_rules
from refund_agent.infrastructure.orders import find_order_by_id, load_orders


def test_load_csv_and_find_order(tmp_path):
    order_file = tmp_path / "orders.csv"
    order_file.write_text("order_id,amount\nORD-1,30\n", encoding="utf-8")

    orders = load_orders(order_file)

    assert find_order_by_id(orders, "ORD-1") == {"order_id": "ORD-1", "amount": "30"}


def test_load_json(tmp_path):
    order_file = tmp_path / "orders.json"
    order_file.write_text(json.dumps([{"order_id": "ORD-2"}]), encoding="utf-8")

    assert load_orders(order_file) == [{"order_id": "ORD-2"}]


def test_rejects_unsupported_file_type(tmp_path):
    order_file = tmp_path / "orders.txt"
    order_file.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="CSV or JSON"):
        load_orders(order_file)


def test_parse_numbered_refund_rules():
    rules = parse_refund_rules("1. Requests are within 3 days. 2. Amount is below 2500.")

    assert rules == [
        {"rule": "Rule 1", "value": "Requests are within 3 days."},
        {"rule": "Rule 2", "value": "Amount is below 2500."},
    ]