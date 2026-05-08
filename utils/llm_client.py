import asyncio
import json
import os
import urllib.error
import urllib.request


DEFAULT_GEMINI_MODEL = "gemini-2.5-flash-lite"


class LLMClientError(Exception):
    pass


class LLMNotConfiguredError(LLMClientError):
    pass


def _config_value(name: str) -> str | None:
    value = os.getenv(name)
    if value:
        return value

    try:
        import config
    except Exception:
        return None

    value = getattr(config, name, None)
    return value or None


def _extract_gemini_text(response: dict) -> str:
    candidates = response.get("candidates") or []
    if not candidates:
        raise LLMClientError("Gemini returned no candidates")

    parts = candidates[0].get("content", {}).get("parts") or []
    text_parts = [part.get("text", "") for part in parts if part.get("text")]
    text = "\n".join(text_parts).strip()
    if not text:
        raise LLMClientError("Gemini returned empty text")

    return text


def _call_gemini_sync(prompt: str, timeout: int) -> str:
    api_key = _config_value("GEMINI_API_KEY")
    if not api_key:
        raise LLMNotConfiguredError("GEMINI_API_KEY is not configured")

    model = _config_value("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "temperature": 0.35,
            "response_mime_type": "application/json",
        },
    }
    request = urllib.request.Request(
        url=url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise LLMClientError(f"Gemini HTTP {error.code}: {details}") from error
    except urllib.error.URLError as error:
        raise LLMClientError(f"Gemini request failed: {error}") from error

    return _extract_gemini_text(json.loads(body))


async def ask_gemini(prompt: str, timeout: int = 25) -> str:
    return await asyncio.to_thread(_call_gemini_sync, prompt, timeout)
