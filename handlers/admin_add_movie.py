from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from config_baze.admins import ADMINS
from handlers.admin_state import admin_sessions
from utils.movies_storage import save_movie
from keyboards.admin.tags import tags_keyboard

router = Router()


@router.message(F.text == "/add_movie")
async def add_movie_start(message: Message):
    if message.from_user.id not in ADMINS:
        return

    admin_sessions[message.from_user.id] = {"step": "media"}
    await message.answer("🎬 Пришли фото или гифку для фильма")


@router.message(F.photo | F.animation)
async def receive_media(message: Message):
    session = admin_sessions.get(message.from_user.id)
    if not session or session.get("step") != "media":
        return

    if message.photo:
        session["media_type"] = "photo"
        session["media_id"] = message.photo[-1].file_id
    else:
        session["media_type"] = "animation"
        session["media_id"] = message.animation.file_id

    session["step"] = "title"
    await message.answer("✍️ Введи название фильма")


@router.message()
async def receive_text(message: Message):
    session = admin_sessions.get(message.from_user.id)
    if not session:
        return

    # ШАГ: название
    if session.get("step") == "title":
        session["title"] = message.text
        session["step"] = "desc"
        await message.answer("📝 Введи описание")
        return

    # ШАГ: описание
    if session.get("step") == "desc":
        session["desc"] = message.text
        session["step"] = "tags"
        await message.answer(
            "🏷 Выбери теги",
            reply_markup=tags_keyboard()
        )
        return

# =========================
# ДОБАВЛЕНИЕ ТЕГОВ
# =========================
@router.callback_query(F.data.startswith("tag:"))
async def add_tag(callback: CallbackQuery):
    session = admin_sessions.get(callback.from_user.id)
    if not session:
        await callback.answer("❌ Сессия не найдена", show_alert=True)
        return

    tag = callback.data.split(":")[1]
    tags = session.setdefault("tags", set())
    tags.add(tag)

    await callback.answer(f"➕ Добавлен тег: {tag}")


# =========================
# СОХРАНЕНИЕ ФИЛЬМА
# =========================
@router.callback_query(F.data == "save_movie")
async def save_movie_handler(callback: CallbackQuery):
    session = admin_sessions.pop(callback.from_user.id, None)
    if not session:
        await callback.answer("❌ Сессия не найдена", show_alert=True)
        return

    session["tags"] = list(session.get("tags", []))
    save_movie(session)

    await callback.message.edit_text("✅ Фильм сохранён в базе")
