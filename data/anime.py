import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_PATH = Path("data/anime.json")


def load_anime(include_premium_collection_only: bool = True) -> List[Dict[str, Any]]:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        items = json.load(f)

    if include_premium_collection_only:
        return items

    return [
        item for item in items
        if not item.get("premium_collection_only", False)
    ]


def get_random_anime(
    vibe: Optional[str] = None,
    excluded_titles: set[str] | None = None,
) -> Dict[str, Any] | None:
    anime_list = load_anime(include_premium_collection_only=False)
    excluded_titles = excluded_titles or set()

    if vibe:
        matching = [item for item in anime_list if vibe in item.get("tags", [])]
        if not matching:
            return None

        available_matching = [
            item for item in matching
            if item["title"] not in excluded_titles
        ]
        return random.choice(available_matching) if available_matching else None

    available_items = [item for item in anime_list if item["title"] not in excluded_titles]
    source = available_items or anime_list

    return random.choice(source) if source else None
