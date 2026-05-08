import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

DANGEROUS_TRACKED_PATTERNS = (
    ".env",
    "config.py",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".log",
)

REQUIRED_FILES = (
    ".gitignore",
    ".env.example",
    "requirements.txt",
    "bot.py",
    "config.example.py",
)

RUNTIME_FILES = (
    "data/baza_users.db",
    "bot_stdout.log",
    "bot_stderr.log",
    "logs/bot_errors.log",
)

CONTENT_FILES = (
    "data/movies.json",
    "data/series.json",
    "data/books.json",
    "data/games.json",
    "data/anime.json",
    "data/public_vibes.json",
)

SECRET_PATTERNS = (
    ("Telegram bot token", re.compile(r"\b\d{8,12}:AA[\w-]{25,}\b")),
    ("Google API key", re.compile(r"\bAIza[\w-]{25,}\b")),
)

LOCAL_PATH_PATTERNS = (
    "c:/users/",
    "c:\\users\\",
    "/users/",
    "/home/",
    "desktop/",
)


def run_git(args: list[str]) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode not in (0, 1):
        print(result.stderr.strip())
        raise SystemExit(result.returncode)

    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def is_dangerous_tracked(path: str) -> bool:
    lower = path.lower().replace("\\", "/")
    name = Path(lower).name
    return (
        name in DANGEROUS_TRACKED_PATTERNS
        or lower.startswith("runtime/")
        or lower.startswith("logs/")
        or lower.startswith("backups/")
        or any(lower.endswith(pattern) for pattern in DANGEROUS_TRACKED_PATTERNS)
    )


def read_text(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8-sig")


def check_required_files(errors: list[str]):
    for rel_path in REQUIRED_FILES:
        if not (ROOT / rel_path).exists():
            errors.append(f"Required release file is missing: {rel_path}")


def check_private_files(errors: list[str]):
    tracked_files = run_git(["ls-files"])
    dangerous = [path for path in tracked_files if is_dangerous_tracked(path)]
    if dangerous:
        errors.append(
            "Dangerous runtime/private files are tracked by git:\n"
            + "\n".join(f"  - {path}" for path in dangerous)
        )

    ignored_missing = []
    for rel_path in RUNTIME_FILES:
        path = ROOT / rel_path
        if path.exists():
            ignored = run_git(["check-ignore", rel_path])
            if not ignored:
                ignored_missing.append(rel_path)

    if ignored_missing:
        errors.append(
            "Runtime files exist but are not ignored:\n"
            + "\n".join(f"  - {path}" for path in ignored_missing)
        )


def check_secrets(errors: list[str]):
    scan_paths = [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and "__pycache__" not in path.parts
        and path.suffix.lower() in {".py", ".json", ".md", ".txt", ".example"}
    ]

    findings = []
    for path in scan_paths:
        rel_path = path.relative_to(ROOT).as_posix()
        if rel_path == ".env.example":
            continue

        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            continue

        for label, pattern in SECRET_PATTERNS:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                findings.append(f"  - {rel_path}:{line} contains {label}")

    if findings:
        errors.append(
            "Possible real secrets found in release files:\n"
            + "\n".join(findings)
            + "\nRotate leaked keys before publishing."
        )


def check_content_json(errors: list[str]):
    missing_files = []
    invalid_json = []
    local_media_paths = []
    empty_media_sources = []

    for rel_path in CONTENT_FILES:
        path = ROOT / rel_path
        if not path.exists():
            missing_files.append(rel_path)
            continue

        try:
            payload = json.loads(read_text(rel_path))
        except json.JSONDecodeError as error:
            invalid_json.append(f"  - {rel_path}: {error}")
            continue

        if not isinstance(payload, list):
            continue

        for index, item in enumerate(payload):
            if not isinstance(item, dict):
                continue

            title = item.get("title") or f"item #{index}"
            media = item.get("media")
            if not isinstance(media, dict):
                continue

            file_id = media.get("file_id")
            file_path = media.get("file_path")
            if not file_id and not file_path:
                empty_media_sources.append(f"  - {rel_path}: {title}")
                continue

            if file_path:
                normalized_path = str(file_path).lower().replace("\\", "/")
                if any(pattern.replace("\\", "/") in normalized_path for pattern in LOCAL_PATH_PATTERNS):
                    local_media_paths.append(f"  - {rel_path}: {title} -> {file_path}")

    if missing_files:
        errors.append(
            "Required content JSON files are missing:\n"
            + "\n".join(f"  - {path}" for path in missing_files)
        )
    if invalid_json:
        errors.append("Invalid JSON content files:\n" + "\n".join(invalid_json))
    if local_media_paths:
        errors.append(
            "Local media paths found. Replace them with Telegram file_id before VPS deploy:\n"
            + "\n".join(local_media_paths)
        )
    if empty_media_sources:
        errors.append(
            "Media blocks without file_id/file_path found:\n"
            + "\n".join(empty_media_sources)
        )


def main() -> int:
    errors: list[str] = []

    check_required_files(errors)
    check_private_files(errors)
    check_secrets(errors)
    check_content_json(errors)

    if errors:
        print("Release check failed:\n")
        print("\n\n".join(errors))
        return 1

    print("Release check passed. No private files, secrets, or local media paths found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
