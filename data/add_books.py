import json
import random
from pathlib import Path
from typing import Optional, Dict, Any, List

DATA_PATH = Path("data/books.json")


def load_books() -> List[Dict[str, Any]]:
    if not DATA_PATH.exists():
        return []

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_random_book(tag: Optional[str] = None) -> Optional[Dict[str, Any]]:
    books = load_books()
    if not books:
        return None

    if tag:
        filtered = [b for b in books if tag in b.get("tags", [])]
        if filtered:
            return random.choice(filtered)

    return random.choice(books)
