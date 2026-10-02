import csv
import json
from pathlib import Path
from typing import Any


def load_orders(file_path: Path) -> list[dict[str, Any]]:
    """Load order records from a CSV or JSON file."""
    if not file_path.is_file():
        raise FileNotFoundError(f"Orders file not found: {file_path}")

    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        with file_path.open(newline="", encoding="utf-8") as orders_file:
            return list(csv.DictReader(orders_file))
    if suffix == ".json":
        with file_path.open(encoding="utf-8") as orders_file:
            records = json.load(orders_file)
        if not isinstance(records, list):
            raise ValueError("The JSON orders file must contain a list of order objects.")
        return records
    raise ValueError("Unsupported orders file format. Use CSV or JSON.")


def find_order_by_id(orders: list[dict[str, Any]], order_id: str | None) -> dict[str, Any] | None:
    if not order_id:
        return None
    return next((order for order in orders if str(order.get("order_id")) == order_id), None)