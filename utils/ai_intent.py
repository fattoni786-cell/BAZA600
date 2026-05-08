import re
from collections import Counter
from collections.abc import Iterable

from utils.ai_profile import flatten_ai_profile


def normalize_text(text: str) -> str:
    text = (text or "").lower().replace("ё", "е")
    text = re.sub(r"[^a-zа-я0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def token_set(text: str) -> set[str]:
    return {
        token
        for token in normalize_text(text).split()
        if len(token) >= 3
    }


def _has_any(text: str, patterns: Iterable[str]) -> bool:
    return any(pattern in text for pattern in patterns)


def _add(target: dict[str, list[str]], field: str, values: Iterable[str]):
    bucket = target.setdefault(field, [])
    seen = set(bucket)
    for value in values:
        value = normalize_text(value)
        if len(value) >= 3 and value not in seen:
            bucket.append(value)
            seen.add(value)


INTENT_RULES = [
    ("mechanics", ["паркур", "крыши", "крышам", "прыгать", "прыжки"], ["паркур", "прыжки", "движение по крышам"]),
    ("mechanics", ["стелс", "скрытно", "незаметно", "тихо пройти"], ["стелс", "тихий подход", "незаметность"]),
    ("mechanics", ["кооп", "вдвоем", "с другом", "с друзьями"], ["кооп", "для двоих", "с друзьями"]),
    ("mechanics", ["строить", "строительство", "база", "город", "ресурсы"], ["строительство", "менеджмент ресурсов", "база"]),
    ("mechanics", ["стратегия", "тактика", "планировать"], ["стратегия", "тактика", "планирование"]),
    ("mechanics", ["стрельба", "шутер", "оружие", "перестрелки"], ["стрельба", "шутер", "оружие"]),
    ("mood", ["мрачно", "мрачный", "темно", "нуар"], ["мрачно", "темный вайб", "нуар"]),
    ("mood", ["уют", "уютно", "тепло", "выдохнуть", "спокойно"], ["уютно", "тепло", "спокойно"]),
    ("mood", ["одинок", "одиночество", "меланхол", "тоска"], ["одиночество", "меланхолия", "тихая грусть"]),
    ("mood", ["романтика", "любовь", "свидание", "вдвоем"], ["романтика", "нежность", "отношения"]),
    ("mood", ["смешно", "юмор", "комедия", "абсурд"], ["юмор", "абсурд", "ирония"]),
    ("pace", ["короткий", "коротко", "быстро", "на вечер", "один вечер"], ["короткий заход", "на один вечер"]),
    ("pace", ["долго", "надолго", "залипнуть", "много часов"], ["долгое погружение", "залипательно"]),
    ("pace", ["динамично", "драйв", "экшен", "быстро", "без провисаний"], ["быстрый темп", "драйв", "без провисаний"]),
    ("pace", ["медленно", "созерцательно", "медитативно"], ["медленный темп", "созерцательно", "без спешки"]),
    ("themes", ["психология", "психологическое", "разум", "паранойя"], ["психология", "давление на голову", "внутренний конфликт"]),
    ("themes", ["детектив", "расследование", "тайна", "маньяк"], ["тайна", "расследование", "преступление"]),
    ("themes", ["антиутопия", "система", "контроль", "слежка"], ["антиутопия", "контроль системы", "общество давит"]),
    ("themes", ["космос", "звезды", "планеты"], ["космос", "большие вопросы", "научная фантастика"]),
    ("themes", ["философия", "смысл", "экзистенциально"], ["философия", "смысл жизни", "экзистенциальность"]),
    ("themes", ["выживание", "ресурсы", "апокалипсис", "зомби"], ["выживание", "опасный мир", "ресурсы"]),
    ("intensity", ["жесть", "жестко", "кровь", "насилие", "без цензуры"], ["высокая интенсивность", "тяжело"]),
    ("intensity", ["легко", "мягко", "не душно", "без напряга"], ["низкая интенсивность", "мягко"]),
]

NEGATIVE_RULES = [
    (["не хоррор", "без хоррора", "не ужасы", "без ужасов", "не страшно"], ["хоррор", "страшно", "жутко"]),
    (["не душно", "без духоты", "не затянуто", "без затянутости"], ["медленный темп", "тяжело", "давит атмосферой"]),
    (["без романтики", "не романтика", "не про любовь"], ["романтика", "любовь", "отношения"]),
    (["без жести", "не жестко", "без крови", "без насилия"], ["жестко", "кровь", "насилие", "высокая интенсивность"]),
    (["не долго", "без долгого", "мало времени"], ["долгое погружение", "залипательно"]),
    (["без коопа", "не кооп", "одному", "соло"], ["кооп", "для двоих", "с друзьями"]),
]


def extract_intent(user_prompt: str) -> dict[str, list[str]]:
    normalized = normalize_text(user_prompt)
    intent: dict[str, list[str]] = {}

    for field, patterns, values in INTENT_RULES:
        if _has_any(normalized, patterns):
            _add(intent, field, values)

    for patterns, values in NEGATIVE_RULES:
        if _has_any(normalized, patterns):
            _add(intent, "avoid", values)

    # Preserve rare but meaningful user words so niche requests can still surface.
    generic = {
        "хочу", "надо", "нужно", "что", "чтобы", "можно", "про", "для",
        "игра", "игры", "фильм", "кино", "книга", "сериал", "аниме",
    }
    keywords = [
        token for token in token_set(user_prompt)
        if token not in generic and len(token) >= 5
    ]
    avoid_tokens = set()
    for value in intent.get("avoid", []):
        avoid_tokens.update(token_set(value))
    keywords = [
        keyword for keyword in keywords
        if keyword not in avoid_tokens
    ]
    _add(intent, "keywords", keywords[:10])
    return intent


def _value_matches_prompt(value: str, prompt_tokens: set[str], prompt_normalized: str) -> bool:
    normalized = normalize_text(value)
    if len(normalized) >= 4 and normalized in prompt_normalized:
        return True
    return bool(token_set(value) & prompt_tokens)


def score_item_against_intent(item: dict, intent: dict[str, list[str]], prompt_tokens: set[str], prompt_normalized: str) -> float:
    profile_values = flatten_ai_profile(item.get("ai_profile"))
    searchable_values = (
        profile_values
        + list(item.get("ai_tags", []) or [])
        + list(item.get("tags", []) or [])
        + list(item.get("premium_collections", []) or [])
        + [item.get("title", ""), item.get("desc", "")]
    )
    item_text = normalize_text(" ".join(str(value) for value in searchable_values))
    item_tokens = token_set(item_text)

    weights = {
        "mechanics": 5.0,
        "themes": 3.4,
        "mood": 3.0,
        "pace": 2.8,
        "intensity": 2.6,
        "keywords": 1.4,
    }
    score = 0.0

    for field, weight in weights.items():
        for value in intent.get(field, []):
            value_tokens = token_set(value)
            if normalize_text(value) in item_text:
                score += weight
            elif value_tokens & item_tokens:
                score += weight * 0.55

    for value in intent.get("avoid", []):
        value_tokens = token_set(value)
        if normalize_text(value) in item_text:
            score -= 6.0
        elif value_tokens & item_tokens:
            score -= 3.5

    for value in profile_values:
        if _value_matches_prompt(value, prompt_tokens, prompt_normalized):
            score += 1.6

    return score


def weighted_user_taste(
    positive_items: Iterable[dict],
    liked_items: Iterable[dict],
    disliked_items: Iterable[dict],
) -> tuple[Counter[str], Counter[str]]:
    positive: Counter[str] = Counter()
    negative: Counter[str] = Counter()

    def add_item(counter: Counter[str], item: dict, weight: float):
        values = (
            list(item.get("tags", []) or [])
            + list(item.get("ai_tags", []) or [])
            + flatten_ai_profile(item.get("ai_profile"))
        )
        for value in values:
            normalized = normalize_text(str(value))
            if normalized:
                counter[normalized] += weight

    for item in positive_items:
        add_item(positive, item, 1.4)
    for item in liked_items:
        add_item(positive, item, 1.0)
    for item in disliked_items:
        add_item(negative, item, 1.6)

    return positive, negative


def score_item_against_taste(item: dict, positive_taste: Counter[str], negative_taste: Counter[str]) -> float:
    if not positive_taste and not negative_taste:
        return 0.0

    values = (
        list(item.get("tags", []) or [])
        + list(item.get("ai_tags", []) or [])
        + flatten_ai_profile(item.get("ai_profile"))
    )
    normalized_values = {normalize_text(str(value)) for value in values if value}

    score = 0.0
    for value in normalized_values:
        score += min(positive_taste.get(value, 0), 4.0) * 0.38
        score -= min(negative_taste.get(value, 0), 4.0) * 0.72

    return score


def compact_intent_for_prompt(intent: dict[str, list[str]]) -> dict[str, list[str]]:
    return {
        field: values
        for field, values in intent.items()
        if values
    }
