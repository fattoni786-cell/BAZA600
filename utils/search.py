import difflib
import re
from dataclasses import dataclass

from data.add_movies import load_movies
from data.anime import load_anime
from data.books import load_books
from data.games import load_games
from data.series import load_series
from utils.ai_profile import flatten_ai_profile


CONTENT_LABELS = {
    "anime": "🎌 Аниме",
    "book": "📚 Книга",
    "game": "🎮 Игра",
    "movie": "🎬 Фильм",
    "series": "📺 Сериал",
}

CONTENT_LOADERS = {
    "anime": load_anime,
    "book": load_books,
    "game": load_games,
    "movie": load_movies,
    "series": load_series,
}

QUERY_ALIASES = {
    "gta": ("gta", "grand theft auto"),
    "gta5": ("gta 5", "gta v", "grand theft auto v", "grand theft auto 5"),
    "gta 5": ("gta 5", "gta v", "grand theft auto v", "grand theft auto 5"),
    "gta v": ("gta v", "gta 5", "grand theft auto v", "grand theft auto 5"),
    "grand theft auto 5": ("grand theft auto v", "gta 5", "gta v"),
    "гта": ("gta", "grand theft auto"),
    "гта5": ("gta 5", "gta v", "grand theft auto v", "grand theft auto 5"),
    "гта 5": ("gta 5", "gta v", "grand theft auto v", "grand theft auto 5"),
    "джта": ("gta", "grand theft auto"),
    "джитиа": ("gta", "grand theft auto"),
    "миррорс эйдж": ("mirrors edge", "mirror edge", "mirror's edge"),
    "мирорс эйдж": ("mirrors edge", "mirror edge", "mirror's edge"),
    "миррор эйдж": ("mirrors edge", "mirror edge", "mirror's edge"),
    "мирор эйдж": ("mirrors edge", "mirror edge", "mirror's edge"),
    "миррорс": ("mirrors", "mirror"),
    "эйдж": ("edge",),
    "ведьмак": ("witcher", "ведьмак"),
    "мафия": ("mafia", "мафия"),
    "дум": ("doom", "дум"),
    "сталкер": ("stalker", "s t a l k e r", "сталкер"),
    "дарк соулс": ("dark souls",),
    "дарксоулс": ("dark souls",),
    "киберпанк": ("cyberpunk", "киберпанк"),
    "ред дед": ("red dead redemption", "rdr"),
    "рдр": ("rdr", "red dead redemption"),
    "халф лайф": ("half life",),
    "халфлайф": ("half life",),
    "сайлент хилл": ("silent hill",),
    "сайлентхилл": ("silent hill",),
    "резидент": ("resident evil",),
    "резидент ивел": ("resident evil",),
    "паркур": ("паркур", "бег по крышам", "движение по крышам"),
    "прыгать по крышам": ("паркур", "бег по крышам", "движение по крышам"),
    "бег по крышам": ("паркур", "бег по крышам", "движение по крышам"),
}

CYRILLIC_TO_LATIN = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "e",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "h",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "sch",
    "ы": "y",
    "э": "e",
    "ю": "yu",
    "я": "ya",
    "ь": "",
    "ъ": "",
}

VERSION_MARKERS = {
    "1": "1",
    "i": "1",
    "2": "2",
    "ii": "2",
    "3": "3",
    "iii": "3",
    "4": "4",
    "iv": "4",
    "5": "5",
    "v": "5",
    "6": "6",
    "vi": "6",
    "7": "7",
    "vii": "7",
    "8": "8",
    "viii": "8",
    "9": "9",
    "ix": "9",
}


@dataclass
class SearchResult:
    content_type: str
    index: int
    item: dict
    score: float


def normalize_query(value: str) -> str:
    value = value.lower().replace("ё", "е")
    return re.sub(r"[^a-zа-я0-9]+", "", value)


def normalize_words(value: str) -> str:
    value = value.lower().replace("ё", "е")
    return re.sub(r"\s+", " ", re.sub(r"[^a-zа-я0-9]+", " ", value)).strip()


def transliterate_ru_to_latin(value: str) -> str:
    return "".join(CYRILLIC_TO_LATIN.get(char, char) for char in value.lower())


def version_markers(value: str) -> set[str]:
    markers = set()
    for token in normalize_words(value).split():
        if token.isdigit() and len(token) >= 4:
            continue
        marker = VERSION_MARKERS.get(token)
        if marker:
            markers.add(marker)
    return markers


def _add_variant(variants: set[str], value: str):
    normalized = normalize_words(value)
    if not normalized:
        return

    variants.add(normalized)
    variants.add(normalize_query(normalized))
    transliterated = transliterate_ru_to_latin(normalized)
    if transliterated != normalized:
        variants.add(transliterated)
        variants.add(normalize_query(transliterated))


def query_variants(query: str) -> set[str]:
    normalized_words = normalize_words(query)
    variants = set()
    _add_variant(variants, query)
    _add_variant(variants, normalized_words)

    compact = normalize_query(query)
    if compact:
        variants.add(compact)

    for alias, replacement in QUERY_ALIASES.items():
        alias_normalized = alias.replace("ё", "е")
        alias_compact = normalize_query(alias_normalized)
        if len(alias_compact) <= 3 and compact != alias_compact:
            continue
        if alias_normalized in normalized_words or alias_compact and alias_compact in compact:
            for replacement_value in replacement:
                _add_variant(variants, replacement_value)

    return {variant for variant in variants if variant}


def score_title(query: str, title: str) -> float:
    normalized_title = normalize_query(title)
    title_words = normalize_words(title)
    variants = query_variants(query)
    all_query_versions = set()
    for variant in variants:
        all_query_versions.update(version_markers(variant))

    if not normalized_title:
        return 0.0

    best_score = 0.0
    for variant in variants:
        normalized_query = normalize_query(variant)
        query_words = normalize_words(variant)
        if not normalized_query:
            continue

        if normalized_query == normalized_title or query_words == title_words:
            score = 1.0
        elif normalized_query in normalized_title:
            score = 0.92
        elif normalized_title in normalized_query:
            score = 0.82
        elif normalized_query.isdigit() or len(normalized_query) <= 3:
            score = 0.0
        else:
            score = difflib.SequenceMatcher(None, normalized_query, normalized_title).ratio()

        query_versions = version_markers(query_words) or all_query_versions
        title_versions = version_markers(title_words)
        if query_versions and not (query_versions & title_versions):
            score = min(score, 0.61)

        best_score = max(best_score, score)

    return best_score


def _as_text_values(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [str(item) for item in flatten_ai_profile(value)]
    if isinstance(value, (list, tuple, set)):
        values = []
        for item in value:
            values.extend(_as_text_values(item))
        return values
    return [str(value)]


def item_title_values(item: dict) -> list[str]:
    values = []
    for key in ("title", "aliases", "alt_titles", "alternative_titles", "original_title", "english_title", "ru_title"):
        values.extend(_as_text_values(item.get(key)))
    return [value for value in values if value]


def item_semantic_values(item: dict) -> list[str]:
    values = []
    for key in ("tags", "ai_tags", "premium_collections", "desc", "description", "vibe", "vibe_text", "ai_profile"):
        values.extend(_as_text_values(item.get(key)))
    return [value for value in values if value]


def _score_semantic_values(
    query: str,
    query_tokens: set[str],
    values: list[str],
    exact_score: float,
    overlap_base: float,
    overlap_bonus: float,
) -> float:
    semantic_text = normalize_words(" ".join(values))
    if not semantic_text:
        return 0.0

    semantic_compact = normalize_query(semantic_text)
    best_score = 0.0
    for variant in query_variants(query):
        variant_words = normalize_words(variant)
        variant_compact = normalize_query(variant_words)
        if len(variant_compact) >= 4 and variant_compact in semantic_compact:
            best_score = max(best_score, exact_score)

    semantic_tokens = set(semantic_text.split())
    overlap = query_tokens & semantic_tokens
    if overlap:
        coverage = len(overlap) / max(len(query_tokens), 1)
        best_score = max(best_score, overlap_base + coverage * overlap_bonus)

    return best_score


def score_semantic(query: str, item: dict) -> float:
    query_tokens = {
        token
        for variant in query_variants(query)
        for token in normalize_words(variant).split()
        if len(token) >= 4 or token.isdigit()
    }
    if not query_tokens:
        return 0.0

    primary_values = []
    for key in ("tags", "premium_collections", "desc", "description", "vibe", "vibe_text"):
        primary_values.extend(_as_text_values(item.get(key)))
    weak_values = []
    for key in ("ai_tags", "ai_profile"):
        weak_values.extend(_as_text_values(item.get(key)))

    return max(
        _score_semantic_values(query, query_tokens, primary_values, 0.78, 0.48, 0.26),
        _score_semantic_values(query, query_tokens, weak_values, 0.60, 0.38, 0.20),
    )


def score_item(query: str, item: dict) -> float:
    title_score = max((score_title(query, value) for value in item_title_values(item)), default=0.0)
    semantic_score = score_semantic(query, item)

    if title_score >= 1.0:
        return 1.2
    if title_score >= 0.92:
        return 1.05
    return max(title_score, semantic_score)


def search_content(query: str, is_premium: bool, limit: int = 8) -> list[SearchResult]:
    results: list[SearchResult] = []

    for content_type, loader in CONTENT_LOADERS.items():
        items = loader(include_premium_collection_only=True)
        for index, item in enumerate(items):
            score = score_item(query, item)
            if score < 0.62:
                continue
            if item.get("premium_collection_only", False) and not is_premium:
                continue

            results.append(
                SearchResult(
                    content_type=content_type,
                    index=index,
                    item=item,
                    score=score,
                )
            )

    results.sort(key=lambda result: (-result.score, len(result.item.get("title", ""))))
    return results[:limit]


def get_content_item(content_type: str, index: int) -> dict | None:
    loader = CONTENT_LOADERS.get(content_type)
    if not loader:
        return None

    items = loader(include_premium_collection_only=True)
    if index < 0 or index >= len(items):
        return None

    return items[index]


def search_result_label(result: SearchResult) -> str:
    content_label = CONTENT_LABELS.get(result.content_type, result.content_type)
    return f"{content_label} • {result.item.get('title', 'Без названия')}"
