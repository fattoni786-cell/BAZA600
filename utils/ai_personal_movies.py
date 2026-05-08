import json
import re
from html import escape

from data.add_movies import load_movies
from utils.content_history import get_recently_seen_titles
from utils.ai_profile import flatten_ai_profile
from utils.ai_intent import (
    compact_intent_for_prompt,
    extract_intent,
    score_item_against_intent,
    score_item_against_taste,
    weighted_user_taste,
)
from utils.db import get_user_favorites, get_user_rated_content
from utils.llm_client import LLMClientError, ask_gemini
from utils.public_vibes import get_public_vibes

AI_MOVIE_CANDIDATE_LIMIT = 120
AI_MOVIE_EXTENDED_CANDIDATE_LIMIT = 200
AI_MOVIE_RESULT_LIMIT = 2

AI_REASON_STYLE = """
Стиль объяснения:
- обращайся к человеку только на «ты», никогда не используй «вы»;
- голос БАЗЫ №600: живой, слегка ироничный, уверенный, но без токсичности и без клоунады;
- 2-3 коротких предложения, без канцелярита и без пересказа всей карточки;
- не пиши «я как нейросеть», «алгоритм решил», «уважаемый пользователь»;
- для фильма учитывай атмосферу, темп, послевкусие, визуальный нерв и состояние вечера.
""".strip()

TOKEN_ALIASES = {
    "мрач": {"темн", "dark", "noir", "тревож", "давящ"},
    "темн": {"мрач", "dark", "noir", "тревож", "давящ"},
    "одинок": {"одиноч", "lonely", "меланхол", "тих"},
    "одиноч": {"одинок", "lonely", "меланхол", "тих"},
    "романт": {"love", "любов", "отношен", "нежн"},
    "любов": {"romance", "романт", "отношен", "нежн"},
    "жесть": {"жестк", "насил", "blood", "тяжел"},
    "жестк": {"жесть", "насил", "blood", "тяжел"},
    "психолог": {"mind", "давлен", "тревож", "параной"},
    "космос": {"space", "sci", "фантаст", "звезд"},
    "детектив": {"тайн", "расслед", "crime", "преступ"},
}

STOP_TOKENS = {
    "про", "для", "или", "что", "это", "где", "как", "мне", "могу", "можно",
    "хочу", "надо", "нужн", "какой", "какая", "какое", "какие", "что-то",
    "фильм", "фильмы", "кино", "мульт", "мультик", "мультики",
}

RUSSIAN_ENDINGS = (
    "иями", "ями", "ами", "ого", "ему", "ыми", "ими", "ить", "ать", "ять",
    "ешь", "ает", "уют", "ого", "его", "ому", "ему", "ой", "ый", "ий",
    "ая", "ое", "ые", "ых", "им", "ам", "ям", "ах", "ях", "ом", "ем",
    "ов", "ев", "ей", "ую", "юю", "а", "я", "ы", "и", "е", "у",
)


def _normalize(text: str) -> str:
    text = text.lower().replace("ё", "е")
    text = re.sub(r"[^a-zа-я0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _stem_token(token: str) -> str:
    if len(token) < 5:
        return token

    for ending in RUSSIAN_ENDINGS:
        if token.endswith(ending) and len(token) - len(ending) >= 3:
            return token[: -len(ending)]

    return token


def _expand_token(token: str) -> set[str]:
    stem = _stem_token(token)
    expanded = {token, stem}

    for key, aliases in TOKEN_ALIASES.items():
        if token.startswith(key) or stem.startswith(key) or key.startswith(stem):
            expanded.update(aliases)

    return {value for value in expanded if len(value) >= 3}


def _tokens(text: str) -> set[str]:
    tokens: set[str] = set()
    for token in _normalize(text).split():
        if len(token) >= 3 and token not in STOP_TOKENS:
            tokens.update(_expand_token(token))
    return tokens


def _candidate_limit_for_prompt(user_prompt: str) -> int:
    normalized = _normalize(user_prompt)
    word_count = len(normalized.split())

    if "\n" in user_prompt or len(normalized) >= 180 or word_count >= 28:
        return AI_MOVIE_EXTENDED_CANDIDATE_LIMIT

    return AI_MOVIE_CANDIDATE_LIMIT


def _movie_search_text(movie: dict, public_vibes: dict[str, str]) -> str:
    tags = movie.get("tags", [])
    ai_tags = movie.get("ai_tags", [])
    ai_profile = flatten_ai_profile(movie.get("ai_profile"))
    tag_labels = [public_vibes.get(tag, "") for tag in tags]
    return " ".join(
        [
            movie.get("title", ""),
            movie.get("desc", ""),
            " ".join(tags),
            " ".join(ai_tags),
            " ".join(ai_profile),
            " ".join(tag_labels),
        ]
    )


def _profile_titles(user_id: int) -> tuple[set[str], set[str], set[str]]:
    favorites = {title for (title,) in get_user_favorites(user_id, "movie")}
    liked = set(get_user_rated_content(user_id, "movie", value=1))
    disliked = set(get_user_rated_content(user_id, "movie", value=-1))
    return favorites, liked, disliked


def _candidate_score(
    movie: dict,
    prompt_tokens: set[str],
    prompt_normalized: str,
    public_vibes: dict[str, str],
    favorite_tags: set[str],
    liked_tags: set[str],
    disliked_tags: set[str],
    intent: dict[str, list[str]],
    positive_taste,
    negative_taste,
) -> float:
    search_text = _movie_search_text(movie, public_vibes)
    search_tokens = _tokens(search_text)
    profile_values = flatten_ai_profile(movie.get("ai_profile"))
    tags = set(movie.get("tags", [])) | set(movie.get("ai_tags", [])) | set(profile_values)
    score = 0.0

    score += len(prompt_tokens & search_tokens) * 2.2
    exact_matches = prompt_tokens & search_tokens
    if exact_matches:
        score += min(len(exact_matches), 4) * 1.1

    if _normalize(movie.get("title", "")) in prompt_normalized:
        score += 8

    for ai_tag in movie.get("ai_tags", []):
        tag_normalized = _normalize(ai_tag)
        if not tag_normalized:
            continue
        tag_matches = prompt_tokens & _tokens(ai_tag)
        if tag_matches:
            score += min(len(tag_matches), 3) * 0.8
        if len(tag_normalized) >= 4 and tag_normalized in prompt_normalized:
            score += 3.5

    for profile_value in profile_values:
        profile_tokens = _tokens(profile_value)
        profile_matches = prompt_tokens & profile_tokens
        if profile_matches:
            score += min(len(profile_matches), 4) * 1.6
        normalized_profile = _normalize(profile_value)
        if len(normalized_profile) >= 4 and normalized_profile in prompt_normalized:
            score += 4.2

    for tag in tags:
        label = public_vibes.get(tag)
        if label and (_tokens(label) & prompt_tokens):
            score += 2.5

    score += len(tags & favorite_tags) * 0.45
    score += len(tags & liked_tags) * 0.35
    score -= len(tags & disliked_tags) * 0.8
    score += score_item_against_intent(
        item=movie,
        intent=intent,
        prompt_tokens=prompt_tokens,
        prompt_normalized=prompt_normalized,
    )
    score += score_item_against_taste(
        item=movie,
        positive_taste=positive_taste,
        negative_taste=negative_taste,
    )

    if "mr600_choice" in tags:
        score += 0.3
    if movie.get("premium_collections"):
        score += 0.15

    return score


def _profile_tag_sets(user_id: int, movies_by_title: dict[str, dict]) -> tuple[set[str], set[str], set[str]]:
    favorites, liked, disliked = _profile_titles(user_id)

    def collect(titles: set[str]) -> set[str]:
        tags: set[str] = set()
        for title in titles:
            movie = movies_by_title.get(title)
            if movie:
                tags.update(movie.get("tags", []))
                tags.update(movie.get("ai_tags", []))
                tags.update(flatten_ai_profile(movie.get("ai_profile")))
        return tags

    return collect(favorites), collect(liked), collect(disliked)


def _profile_taste_sets(user_id: int, movies_by_title: dict[str, dict]):
    favorites, liked, disliked = _profile_titles(user_id)

    def items_for(titles: set[str]) -> list[dict]:
        return [
            movies_by_title[title]
            for title in titles
            if title in movies_by_title
        ]

    return weighted_user_taste(
        positive_items=items_for(favorites),
        liked_items=items_for(liked),
        disliked_items=items_for(disliked),
    )


def select_movie_candidates(user_id: int, user_prompt: str) -> list[dict]:
    movies = load_movies(include_premium_collection_only=False)
    recently_seen = get_recently_seen_titles(user_id, "movie")
    available = [movie for movie in movies if movie["title"] not in recently_seen]
    source = available or movies

    public_vibes = get_public_vibes("movie")
    movies_by_title = {movie["title"]: movie for movie in movies}
    favorite_tags, liked_tags, disliked_tags = _profile_tag_sets(user_id, movies_by_title)
    positive_taste, negative_taste = _profile_taste_sets(user_id, movies_by_title)
    candidate_limit = _candidate_limit_for_prompt(user_prompt)
    prompt_tokens = _tokens(user_prompt)
    prompt_normalized = _normalize(user_prompt)
    intent = extract_intent(user_prompt)

    scored = [
        (
            _candidate_score(
                movie=movie,
                prompt_tokens=prompt_tokens,
                prompt_normalized=prompt_normalized,
                public_vibes=public_vibes,
                favorite_tags=favorite_tags,
                liked_tags=liked_tags,
                disliked_tags=disliked_tags,
                intent=intent,
                positive_taste=positive_taste,
                negative_taste=negative_taste,
            ),
            movie,
        )
        for movie in source
    ]
    scored.sort(key=lambda item: item[0], reverse=True)

    strong = [movie for score, movie in scored if score > 0.4]
    if len(strong) >= 15:
        return strong[:candidate_limit]

    fallback = [movie for _score, movie in scored[:candidate_limit]]
    return fallback


def _compact_movie(movie: dict, index: int) -> dict:
    desc = movie.get("desc", "")
    if len(desc) > 420:
        desc = desc[:420].rsplit(" ", 1)[0] + "..."

    return {
        "id": index,
        "title": movie.get("title", ""),
        "desc": desc,
        "tags": movie.get("tags", []),
        "ai_tags": movie.get("ai_tags", []),
        "ai_profile": movie.get("ai_profile", {}),
        "collections": movie.get("premium_collections", []),
    }


def _build_prompt(user_prompt: str, candidates: list[dict], intent: dict[str, list[str]]) -> str:
    compact_candidates = [
        _compact_movie(movie, index)
        for index, movie in enumerate(candidates, start=1)
    ]
    candidates_json = json.dumps(compact_candidates, ensure_ascii=False)
    intent_json = json.dumps(compact_intent_for_prompt(intent), ensure_ascii=False)

    return f"""
Ты внутри Telegram-бота «БАЗА №600». Пользователь описал настроение и пожелания к фильму свободным текстом.

Твоя задача: выбрать ТОЛЬКО фильмы из списка candidates. Нельзя выдумывать названия. Нельзя выбирать фильм, которого нет в candidates.

Учитывай:
- настроение, эмоции и скрытый вайб пользователя;
- чего пользователь явно хочет или не хочет;
- описание фильма, теги и подборки;
- лучше выбрать точное попадание, чем просто популярный фильм.
- если пользователь назвал конкретную тему, атмосферу или ощущение, это важнее общей популярности.

{AI_REASON_STYLE}

Запрос пользователя:
{user_prompt}

Parsed intent JSON:
{intent_json}

Candidates JSON:
{candidates_json}

Верни строго JSON без markdown:
{{
  "choices": [
    {{
      "title": "точное название из candidates",
      "reason": "2-3 предложения по-русски в стиле БАЗЫ №600: почему этот фильм попал в запрос пользователя. Только на ты.",
      "confidence": 0.0
    }}
  ]
}}

Верни 2 разных choices, если есть достойный запасной вариант. Первый choice — основной.
""".strip()


def _extract_json(raw_text: str) -> dict:
    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.S)
        if not match:
            raise
        return json.loads(match.group(0))


def _fallback_reason(user_prompt: str, movie: dict) -> str:
    safe_prompt = escape(user_prompt.strip())
    title = escape(movie.get("title", "этот фильм"))
    return (
        f"<b><i>БАЗА зацепилась за твой запрос: «{safe_prompt}». "
        f"{title} лёг ближе остальных: тут совпал нерв, а не просто красивая вывеска. "
        "Берём, пока вечер не передумал.</i></b>"
    )


def _format_ai_reason(reason: str) -> str:
    reason = reason.strip()
    if not reason:
        return ""
    return f"<b><i>{escape(reason)}</i></b>"


def _fallback_recommendations(user_prompt: str, candidates: list[dict]) -> list[dict]:
    return [
        {
            "movie": movie,
            "explanation": _fallback_reason(user_prompt, movie),
        }
        for movie in candidates[:AI_MOVIE_RESULT_LIMIT]
    ]


async def recommend_movies_from_prompt(user_id: int, user_prompt: str) -> list[dict]:
    candidates = select_movie_candidates(user_id, user_prompt)
    if not candidates:
        return []

    intent = extract_intent(user_prompt)
    prompt = _build_prompt(user_prompt, candidates, intent)
    by_title = {movie["title"]: movie for movie in candidates}

    try:
        raw_response = await ask_gemini(prompt)
        parsed = _extract_json(raw_response)
    except LLMClientError:
        raise
    except Exception as error:
        raise LLMClientError(f"Could not parse movie AI response: {error}") from error

    recommendations = []
    used_titles: set[str] = set()
    for choice in parsed.get("choices", []):
        title = choice.get("title")
        movie = by_title.get(title)
        if not movie or title in used_titles:
            continue

        reason = _format_ai_reason(choice.get("reason", ""))
        if not reason:
            reason = _fallback_reason(user_prompt, movie)

        recommendations.append(
            {
                "movie": movie,
                "explanation": reason,
            }
        )
        used_titles.add(title)

        if len(recommendations) >= AI_MOVIE_RESULT_LIMIT:
            break

    if recommendations:
        return recommendations

    return _fallback_recommendations(user_prompt, candidates)
