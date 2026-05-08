import hashlib
import json
import re
from pathlib import Path

from data.anime_vibes import ANIME_VIBES
from data.book_vibes import BOOK_VIBES
from data.game_vibes import GAME_VIBES
from data.movie_vibes import MOVIE_FAST_VIBES
from data.series_vibes import SERIES_VIBES

PUBLIC_VIBES_PATH = Path("data/public_vibes.json")
DATA_FILES_BY_TYPE = {
    "anime": Path("data/anime.json"),
    "movie": Path("data/movies.json"),
    "game": Path("data/games.json"),
    "book": Path("data/books.json"),
    "series": Path("data/series.json"),
}

BASE_PUBLIC_VIBES_BY_TYPE = {
    "anime": ANIME_VIBES,
    "movie": MOVIE_FAST_VIBES,
    "game": GAME_VIBES,
    "book": BOOK_VIBES,
    "series": SERIES_VIBES,
}


def load_public_vibes_store() -> dict[str, dict[str, str]]:
    if not PUBLIC_VIBES_PATH.exists():
        return {}

    with open(PUBLIC_VIBES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        return {}

    normalized_store: dict[str, dict[str, str]] = {}
    migrations: dict[str, dict[str, str]] = {}
    changed = False

    for content_type, vibes in data.items():
        if not isinstance(vibes, dict):
            continue

        content_store: dict[str, str] = {}
        content_migrations: dict[str, str] = {}
        for raw_key, label in vibes.items():
            safe_key = build_safe_vibe_key(str(raw_key), str(label))
            if safe_key in content_store and content_store[safe_key] == label:
                continue
            if safe_key != raw_key:
                changed = True
                content_migrations[str(raw_key)] = safe_key
            content_store[safe_key] = str(label)

        normalized_store[content_type] = content_store
        if content_migrations:
            migrations[content_type] = content_migrations

    if changed:
        save_public_vibes_store(normalized_store)
        migrate_content_tag_keys(migrations)

    return normalized_store


def save_public_vibes_store(data: dict[str, dict[str, str]]):
    with open(PUBLIC_VIBES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_custom_public_vibes(content_type: str) -> dict[str, str]:
    return load_public_vibes_store().get(content_type, {})


def get_public_vibes(content_type: str) -> dict[str, str]:
    catalog = dict(BASE_PUBLIC_VIBES_BY_TYPE.get(content_type, {}))
    catalog.update(get_custom_public_vibes(content_type))
    return catalog


def normalize_vibe_key(raw_key: str) -> str:
    key = raw_key.strip().lower().replace(" ", "_")
    key = re.sub(r"[^a-z0-9_]+", "_", key, flags=re.IGNORECASE)
    key = re.sub(r"_+", "_", key).strip("_")
    return key


def build_safe_vibe_key(raw_key: str, label: str) -> str:
    key = normalize_vibe_key(raw_key) or normalize_vibe_key(label)

    if key and len(key) <= 32:
        return key

    digest = hashlib.sha1(f"{raw_key}|{label}".encode("utf-8")).hexdigest()[:12]
    return f"vibe_{digest}"


def parse_new_public_vibes(raw_text: str) -> list[tuple[str, str]]:
    chunks = raw_text.replace("\n", ";").split(";")
    result: list[tuple[str, str]] = []
    seen = set()

    for chunk in chunks:
        part = chunk.strip()
        if not part:
            continue

        if "=" in part:
            raw_key, label = part.split("=", 1)
        elif ":" in part:
            raw_key, label = part.split(":", 1)
        else:
            raw_key, label = part, part

        label = label.strip()
        key = build_safe_vibe_key(raw_key, label)

        if not key or not label or key in seen:
            continue

        seen.add(key)
        result.append((key, label))

    return result


def add_public_vibes(content_type: str, vibes: list[tuple[str, str]]):
    if not vibes:
        return

    store = load_public_vibes_store()
    content_store = dict(store.get(content_type, {}))

    for key, label in vibes:
        content_store[key] = label

    store[content_type] = content_store
    save_public_vibes_store(store)


def migrate_content_tag_keys(migrations: dict[str, dict[str, str]]):
    for content_type, tag_map in migrations.items():
        path = DATA_FILES_BY_TYPE.get(content_type)
        if not path or not path.exists():
            continue

        with open(path, "r", encoding="utf-8") as f:
            items = json.load(f)

        changed = False
        for item in items:
            tags = item.get("tags", [])
            if not isinstance(tags, list):
                continue

            new_tags = []
            for tag in tags:
                new_tag = tag_map.get(tag, tag)
                if new_tag != tag:
                    changed = True
                if new_tag not in new_tags:
                    new_tags.append(new_tag)
            item["tags"] = new_tags

        if changed:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
