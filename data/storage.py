import json
from pathlib import Path

from scripts.generate_ai_tags import build_ai_tags, with_ai_tags_after_public_tags
from utils.ai_profile import build_ai_profile

FILES_BY_TYPE = {
    "anime": Path("data/anime.json"),
    "movie": Path("data/movies.json"),
    "series": Path("data/series.json"),
    "game": Path("data/games.json"),
    "book": Path("data/books.json"),
}


def save_content(content_type: str, item: dict):
    path = FILES_BY_TYPE.get(content_type)

    if not path:
        raise ValueError(f"Unknown content type: {content_type}")

    if not path.exists():
        path.write_text("[]", encoding="utf-8")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    new_item = {
        "title": item["title"],
        "desc": item["desc"],
        "media": item.get("media"),
        "tags": item.get("tags", []),
        "premium_collections": item.get("premium_collections", []),
        "premium_collection_only": item.get("premium_collection_only", False),
    }

    if content_type == "book":
        new_item["audio"] = item.get("audio")
    elif content_type == "game":
        new_item["platforms"] = item.get("platforms", [])

    new_item["ai_tags"] = build_ai_tags(content_type, new_item)
    new_item["ai_profile"] = build_ai_profile(content_type, new_item)
    new_item = with_ai_tags_after_public_tags(new_item)

    data.append(new_item)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
