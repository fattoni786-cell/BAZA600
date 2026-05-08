import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_PATH = Path("data/series.json")


def load_series(include_premium_collection_only: bool = True) -> List[Dict[str, Any]]:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        series = json.load(f)

    if include_premium_collection_only:
        return series

    return [
        item for item in series
        if not item.get("premium_collection_only", False)
    ]


def get_random_series(
    vibe: Optional[str] = None,
    excluded_titles: set[str] | None = None,
) -> Dict[str, Any]:
    series = load_series(include_premium_collection_only=False)
    excluded_titles = excluded_titles or set()

    if not series:
        raise ValueError("Series database is empty")

    if vibe:
        matching = [item for item in series if vibe in item.get("tags", [])]
        if not matching:
            return None

        available_matching = [
            item for item in matching
            if item["title"] not in excluded_titles
        ]
        return random.choice(available_matching) if available_matching else None

    available_series = [item for item in series if item["title"] not in excluded_titles]
    source = available_series or series

    return random.choice(source)
