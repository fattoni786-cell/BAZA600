from utils.ai_intent import extract_intent, normalize_text, token_set


STRONG_FIELDS = ("mechanics", "themes", "mood", "pace", "intensity", "avoid")

BROAD_PATTERNS = (
    "что нибудь",
    "что-нибудь",
    "не знаю",
    "любой",
    "любое",
    "любая",
    "нормальное",
    "интересное",
    "что посмотреть",
    "что почитать",
    "во что поиграть",
    "посоветуй",
    "на вечер",
)

CLARIFICATION_QUESTIONS = {
    "movie": (
        "БАЗА чуть сомневается. Уточни одним сообщением: "
        "что важнее сейчас — атмосфера, эмоция, сюжет или чего точно не надо?"
    ),
    "series": (
        "БАЗА чуть сомневается. Уточни одним сообщением: "
        "какой сериал нужен — залипательный, короткий, мрачный, смешной или без чего точно?"
    ),
    "book": (
        "БАЗА чуть сомневается. Уточни одним сообщением: "
        "что важнее — состояние, польза, стиль, сложность или чего точно избегаем?"
    ),
    "game": (
        "БАЗА чуть сомневается. Уточни одним сообщением: "
        "что важнее — геймплей, атмосфера, темп, сложность или чего точно не надо?"
    ),
    "anime": (
        "БАЗА чуть сомневается. Уточни одним сообщением: "
        "какой вайб важнее — тепло, экшен, психология, странность или без чего точно?"
    ),
}


def _has_broad_pattern(user_prompt: str) -> bool:
    normalized = normalize_text(user_prompt)
    return any(pattern in normalized for pattern in BROAD_PATTERNS)


def personal_clarification_question(content_type: str, user_prompt: str) -> str | None:
    intent = extract_intent(user_prompt)
    strong_field_count = sum(1 for field in STRONG_FIELDS if intent.get(field))
    keyword_count = len(intent.get("keywords", []))
    token_count = len(token_set(user_prompt))

    if intent.get("mechanics") and token_count >= 3:
        return None
    if intent.get("themes") and (strong_field_count >= 2 or token_count >= 5):
        return None
    if strong_field_count >= 2:
        return None
    if strong_field_count == 1 and keyword_count >= 4 and not _has_broad_pattern(user_prompt):
        return None
    if token_count >= 9 and keyword_count >= 5 and not _has_broad_pattern(user_prompt):
        return None

    return CLARIFICATION_QUESTIONS.get(
        content_type,
        "БАЗА чуть сомневается. Уточни одним сообщением: что важнее и чего точно не надо?",
    )


def combine_prompt_with_clarification(original_prompt: str, clarification: str) -> str:
    original_prompt = (original_prompt or "").strip()
    clarification = (clarification or "").strip()
    if not original_prompt:
        return clarification
    if not clarification:
        return original_prompt
    return f"{original_prompt}\n\nУточнение: {clarification}"
