import os
import json
from typing import Dict, Any

_RAW = os.getenv("TARIFFS", "[]")


def load_tariffs() -> Dict[int, Dict[str, Any]]:
    try:
        arr = json.loads(_RAW)
    except Exception:
        arr = []
    out: Dict[int, Dict[str, Any]] = {}
    for item in arr:
        try:
            price = int(item["price"])
            out[price] = {
                "price": price,
                "type": item.get("type"),
                "period": item.get("period"),
            }
        except Exception:
            continue
    return out


TARIFFS = load_tariffs()


def period_to_months(period: str) -> int:
    if not period:
        return 0
    if period.endswith("m"):
        return int(period[:-1])
    return 0
