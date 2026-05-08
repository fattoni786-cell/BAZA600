import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_PATH = Path("data/games.json")
LEGACY_COMBINED_PLATFORM = "xbox_nintendo"
GAME_PLATFORMS = ("android", "pc", "playstation", "xbox", "nintendo")
GAME_PLATFORM_LABELS = {
    "android": "Android",
    "pc": "ПК",
    "playstation": "PlayStation",
    "xbox": "Xbox",
    "nintendo": "Nintendo",
    LEGACY_COMBINED_PLATFORM: "Xbox / Nintendo",
}
GAME_PLATFORM_ICONS = {
    "android": "📱",
    "pc": "🖥️",
    "playstation": "🎮",
    "xbox": "🟩",
    "nintendo": "🔴",
    LEGACY_COMBINED_PLATFORM: "🕹",
}


def normalize_game_platforms(platforms: list[str] | None) -> list[str]:
    if not platforms:
        return list(GAME_PLATFORMS)

    normalized: list[str] = []
    for platform in platforms:
        if platform == LEGACY_COMBINED_PLATFORM:
            for mapped_platform in ("xbox", "nintendo"):
                if mapped_platform not in normalized:
                    normalized.append(mapped_platform)
            continue

        if platform not in GAME_PLATFORMS:
            continue
        if platform not in normalized:
            normalized.append(platform)

    return normalized or list(GAME_PLATFORMS)


def normalize_platform_filter(platforms: str | list[str] | tuple[str, ...] | set[str] | None) -> list[str] | None:
    if not platforms:
        return None

    if isinstance(platforms, str):
        values = [platforms]
    else:
        values = list(platforms)

    normalized = normalize_game_platforms(values)
    return normalized or None


def game_matches_platforms(
    game: Dict[str, Any],
    platforms: str | list[str] | tuple[str, ...] | set[str] | None,
) -> bool:
    normalized_filter = normalize_platform_filter(platforms)
    if not normalized_filter:
        return True

    game_platforms = set(normalize_game_platforms(game.get("platforms")))
    return any(platform in game_platforms for platform in normalized_filter)


def get_game_platform_label(platform: str | None) -> str:
    return GAME_PLATFORM_LABELS.get(platform, "🎮 Все платформы")


def get_game_platforms_text(platforms: str | list[str] | tuple[str, ...] | set[str] | None) -> str:
    normalized = normalize_platform_filter(platforms)
    if not normalized:
        return "🎮 Все платформы"
    return ", ".join(get_game_platform_label(platform) for platform in normalized)


def get_game_platforms_icons_text(platforms: str | list[str] | tuple[str, ...] | set[str] | None) -> str:
    normalized = normalize_platform_filter(platforms)
    if not normalized:
        return "🎮"
    return " • ".join(GAME_PLATFORM_ICONS.get(platform, "🎮") for platform in normalized)


def load_games(
    include_premium_collection_only: bool = True,
    platform: str | list[str] | tuple[str, ...] | set[str] | None = None,
) -> List[Dict[str, Any]]:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        games = json.load(f)

    if include_premium_collection_only:
        source = games
    else:
        source = [
            game for game in games
            if not game.get("premium_collection_only", False)
        ]

    if not platform:
        return source

    return [game for game in source if game_matches_platforms(game, platform)]


def get_random_game(
    vibe: Optional[str] = None,
    excluded_titles: set[str] | None = None,
    platform: str | list[str] | tuple[str, ...] | set[str] | None = None,
) -> Dict[str, Any] | None:
    games = load_games(include_premium_collection_only=False, platform=platform)
    excluded_titles = excluded_titles or set()

    if vibe:
        matching = [game for game in games if vibe in game.get("tags", [])]
        if not matching:
            return None

        available_matching = [
            game for game in matching
            if game["title"] not in excluded_titles
        ]
        return random.choice(available_matching) if available_matching else None

    available_games = [game for game in games if game["title"] not in excluded_titles]
    source = available_games or games

    return random.choice(source) if source else None
