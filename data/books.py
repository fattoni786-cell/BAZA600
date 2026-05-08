import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_PATH = Path("data/books.json")


def load_books(include_premium_collection_only: bool = True) -> List[Dict[str, Any]]:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        books = json.load(f)

    if include_premium_collection_only:
        return books

    return [
        book for book in books
        if not book.get("premium_collection_only", False)
    ]


def get_random_book(
    vibe: Optional[str] = None,
    excluded_titles: set[str] | None = None,
) -> Dict[str, Any]:
    books = load_books(include_premium_collection_only=False)
    excluded_titles = excluded_titles or set()

    if not books:
        raise ValueError("Books database is empty")

    if vibe:
        matching = [book for book in books if vibe in book.get("tags", [])]
        if not matching:
            return None

        available_matching = [
            book for book in matching
            if book["title"] not in excluded_titles
        ]
        return random.choice(available_matching) if available_matching else None

    available_books = [book for book in books if book["title"] not in excluded_titles]
    source = available_books or books

    return random.choice(source)


def has_audio(book: Dict[str, Any]) -> bool:
    audio = book.get("audio")
    return bool(audio and audio.get("file_id"))


def get_audio_file_id(book: Dict[str, Any]) -> Optional[str]:
    if has_audio(book):
        return book["audio"]["file_id"]
    return None


def get_media(book: Dict[str, Any]) -> Optional[Dict[str, str]]:
    media = book.get("media")

    if not media:
        return None

    return {
        "type": media.get("type"),
        "file_id": media.get("file_id")
    }
