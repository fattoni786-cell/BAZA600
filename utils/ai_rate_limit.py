from time import monotonic

AI_REQUEST_COOLDOWN_SECONDS = 25

_last_ai_request_at: dict[int, float] = {}


def check_ai_request_limit(user_id: int) -> tuple[bool, int]:
    now = monotonic()
    last_at = _last_ai_request_at.get(user_id)

    if last_at is None:
        _last_ai_request_at[user_id] = now
        return True, 0

    elapsed = now - last_at
    if elapsed < AI_REQUEST_COOLDOWN_SECONDS:
        retry_after = int(AI_REQUEST_COOLDOWN_SECONDS - elapsed) + 1
        return False, retry_after

    _last_ai_request_at[user_id] = now
    return True, 0


def ai_rate_limit_text(retry_after: int) -> str:
    return (
        "Нейро-подбору нужна маленькая пауза, чтобы не жечь лимиты впустую.\n\n"
        f"Попробуй ещё раз через {retry_after} сек."
    )
