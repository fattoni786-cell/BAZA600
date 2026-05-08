import asyncio
import json
import shutil
from datetime import datetime
from pathlib import Path

from aiogram import Bot
from aiogram.types import FSInputFile

from config import BOT_TOKEN
from config_baze.admins import ADMINS


ROOT = Path(__file__).resolve().parents[1]
CONTENT_FILES = (
    "data/movies.json",
    "data/series.json",
    "data/books.json",
    "data/games.json",
    "data/anime.json",
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload):
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def iter_local_media():
    for rel_path in CONTENT_FILES:
        path = ROOT / rel_path
        if not path.exists():
            continue

        payload = load_json(path)
        if not isinstance(payload, list):
            continue

        for index, item in enumerate(payload):
            if not isinstance(item, dict):
                continue

            media = item.get("media")
            if not isinstance(media, dict):
                continue

            file_path = media.get("file_path")
            if file_path and not media.get("file_id"):
                yield path, payload, index, item, media, Path(file_path)


async def upload_media(bot: Bot, chat_id: int, title: str, media_type: str, file_path: Path) -> str:
    file = FSInputFile(file_path)
    caption = f"file_id для базы: {title}"

    if media_type == "photo":
        message = await bot.send_photo(chat_id, file, caption=caption)
        return message.photo[-1].file_id
    if media_type == "animation":
        message = await bot.send_animation(chat_id, file, caption=caption)
        return message.animation.file_id
    if media_type == "video":
        message = await bot.send_video(chat_id, file, caption=caption)
        return message.video.file_id

    message = await bot.send_document(chat_id, file, caption=caption)
    return message.document.file_id


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not configured. Put the new token into .env first.")
    if not ADMINS:
        raise RuntimeError("ADMINS is empty. Add your Telegram ID to config_baze/admins.py.")

    admin_id = next(iter(ADMINS))
    backup_dir = ROOT / "backups" / datetime.now().strftime("%Y-%m-%d_%H-%M-%S_before_file_id_upload")
    changed_files: set[Path] = set()

    async with Bot(BOT_TOKEN) as bot:
        for path, payload, index, item, media, file_path in iter_local_media():
            if not file_path.exists():
                print(f"SKIP missing file: {item.get('title')} -> {file_path}")
                continue

            if path not in changed_files:
                backup_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, backup_dir / path.name)
                changed_files.add(path)

            title = item.get("title", f"item #{index}")
            media_type = media.get("type", "document")
            print(f"Uploading {title} -> {file_path}")
            file_id = await upload_media(bot, admin_id, title, media_type, file_path)

            payload[index]["media"] = {
                "type": media_type,
                "file_id": file_id,
            }
            save_json(path, payload)
            print(f"Saved file_id for {title}")

    if changed_files:
        print(f"Done. Backups saved to {backup_dir}")
    else:
        print("No local media without file_id found.")


if __name__ == "__main__":
    asyncio.run(main())
