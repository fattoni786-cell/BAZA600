MIN_AI_PROMPT_LENGTH = 8
MAX_AI_PROMPT_LENGTH = 700

MAX_SUGGESTION_TITLE_LENGTH = 120
MAX_SUGGESTION_DESCRIPTION_LENGTH = 1200
MAX_SUGGESTION_VIBE_LENGTH = 400

MAX_ADMIN_TITLE_LENGTH = 160
MAX_ADMIN_DESCRIPTION_LENGTH = 1800
MAX_ADMIN_COLLECTIONS_LENGTH = 700
MAX_ADMIN_PUBLIC_VIBES_LENGTH = 700


def clean_user_text(value: str | None) -> str:
    if not value:
        return ""

    allowed = []
    for char in value.strip():
        if ord(char) < 32 and char not in "\n\t":
            continue
        if char in "\n\t" or not char.isspace() or char == " ":
            allowed.append(char)

    return "".join(allowed).strip()


def is_too_long(value: str, max_length: int) -> bool:
    return len(value) > max_length


def length_error_text(max_length: int) -> str:
    return f"Слишком длинно. Давай уложимся до {max_length} символов."
