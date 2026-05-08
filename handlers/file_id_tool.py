import json

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config_baze.admins import ADMINS
from states.file_id import FileIdTool

router = Router()


def _is_admin(message: Message) -> bool:
    return bool(message.from_user and message.from_user.id in ADMINS)


def _media_payload(message: Message) -> dict | None:
    if message.photo:
        return {
            "type": "photo",
            "file_id": message.photo[-1].file_id,
        }
    if message.animation:
        return {
            "type": "animation",
            "file_id": message.animation.file_id,
        }
    if message.video:
        return {
            "type": "video",
            "file_id": message.video.file_id,
        }
    if message.voice:
        return {
            "type": "voice",
            "file_id": message.voice.file_id,
        }
    if message.audio:
        return {
            "type": "audio",
            "file_id": message.audio.file_id,
        }
    if message.document:
        mime_type = message.document.mime_type or ""
        media_type = "video" if mime_type.startswith("video/") else "document"
        return {
            "type": media_type,
            "file_id": message.document.file_id,
        }
    return None


@router.message(Command("fileid"))
async def file_id_start(message: Message, state: FSMContext):
    if not _is_admin(message):
        return

    await state.set_state(FileIdTool.waiting_media)
    await message.answer(
        "Пришли фото, видео, gif, voice или audio. Я верну готовый JSON-блок с file_id.\n\n"
        "Отмена: /cancel_fileid"
    )


@router.message(Command("cancel_fileid"))
async def file_id_cancel(message: Message, state: FSMContext):
    if not _is_admin(message):
        return

    await state.clear()
    await message.answer("Режим получения file_id закрыт.")


@router.message(FileIdTool.waiting_media, F.photo | F.animation | F.video | F.voice | F.audio | F.document)
async def file_id_receive_media(message: Message, state: FSMContext):
    if not _is_admin(message):
        return

    payload = _media_payload(message)
    if not payload:
        await message.answer("Не смог прочитать медиа. Пришли файл ещё раз.")
        return

    await state.clear()
    await message.answer(
        "Готово. Вставляй в базу так:\n\n"
        f"<pre>{json.dumps(payload, ensure_ascii=False, indent=2)}</pre>",
        parse_mode="HTML",
    )


@router.message(FileIdTool.waiting_media)
async def file_id_waiting_wrong_message(message: Message):
    if not _is_admin(message):
        return

    await message.answer("Нужно прислать именно медиа. Отмена: /cancel_fileid")
