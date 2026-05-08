from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message

from config_baze.admins import ADMINS
from data.games import get_game_platform_label
from data.storage import save_content as save_to_json
from handlers.admin_state import admin_sessions
from keyboards.admin.content_type import content_type_keyboard
from keyboards.admin.game_platforms import game_platforms_keyboard
from keyboards.admin.premium_collections import premium_collections_keyboard
from keyboards.admin.tags import tags_keyboard
from utils.analytics import track_event
from utils.backup import create_snapshot_backup
from utils.db import get_admin_content_draft, mark_admin_content_draft_used
from utils.premium_collections import get_all_collection_names, normalize_collection_names
from utils.public_vibes import add_public_vibes, get_public_vibes, parse_new_public_vibes
from utils.tag_catalog import get_tag_catalog
from utils.text_limits import (
    MAX_ADMIN_COLLECTIONS_LENGTH,
    MAX_ADMIN_DESCRIPTION_LENGTH,
    MAX_ADMIN_PUBLIC_VIBES_LENGTH,
    MAX_ADMIN_TITLE_LENGTH,
    clean_user_text,
    is_too_long,
    length_error_text,
)

router = Router()


def is_admin_id(user_id: int | None) -> bool:
    return bool(user_id and user_id in ADMINS)


def build_draft_session(draft: tuple) -> dict:
    return {
        "draft_id": draft[0],
        "type": draft[3],
        "title": draft[4],
        "desc": draft[5],
        "audio": None,
        "tags": set(),
        "platforms": [],
        "premium_collections": [],
        "new_public_vibes": [],
        "premium_collection_only": False,
        "step": "media",
    }


def draft_loaded_text(draft: tuple) -> str:
    vibe_hint = draft[6] or "-"
    return (
        f"Черновик #{draft[0]} загружен.\n\n"
        f"Тип: {draft[3]}\n"
        f"Название: {draft[4]}\n"
        f"Описание: {draft[5]}\n"
        f"Вайб от пользователя: {vibe_hint}\n\n"
        "Теперь пришли обложку / гифку / mp4."
    )


def premium_collections_text(session: dict) -> str:
    selected = session.get("premium_collections", [])
    existing_count = len(session.get("premium_collection_options", []))
    selected_text = "\n".join(f"• {name}" for name in selected) if selected else "Пока ничего не выбрано."
    premium_only = session.get("premium_collection_only", False)
    distribution_text = (
        "🔒 Только внутри premium-подборок"
        if premium_only
        else "🌍 Доступно и в общей выдаче"
    )

    return (
        "💎 Подборки для Premium\n\n"
        "Можно сделать две вещи:\n"
        "1. Нажать на существующие подборки ниже\n"
        "2. Или прислать новые названия текстом через `;` или `,`\n\n"
        "Например: `Самое то чтобы смотреть с девушкой вечером; Ночной comfort`\n\n"
        f"Уже существует подборок: *{existing_count}*\n\n"
        f"*Режим выдачи:* {distribution_text}\n\n"
        f"*Выбрано сейчас:*\n{selected_text}"
    )


def game_platforms_text(session: dict) -> str:
    selected_platforms = session.get("platforms", [])
    selected_text = (
        "\n".join(f"• {get_game_platform_label(platform)}" for platform in selected_platforms)
        if selected_platforms
        else "Пока ничего не выбрано."
    )

    return (
        "🎮 Платформы для игры\n\n"
        "Отметь, где эта игра доступна. Можно выбрать несколько платформ.\n\n"
        f"*Выбрано сейчас:*\n{selected_text}"
    )


async def ask_premium_collections(message: Message, session: dict):
    options = get_all_collection_names(session["type"])
    session["premium_collection_options"] = options
    session["step"] = "premium_collections"

    await message.answer(
        premium_collections_text(session),
        reply_markup=premium_collections_keyboard(
            options=options,
            selected=session.get("premium_collections", []),
            premium_only=session.get("premium_collection_only", False),
        ),
        parse_mode="Markdown",
    )


async def ask_game_platforms(message: Message, session: dict):
    session["step"] = "game_platforms"
    await message.answer(
        game_platforms_text(session),
        reply_markup=game_platforms_keyboard(session.get("platforms", [])),
        parse_mode="Markdown",
    )


async def ask_tags(message: Message, session: dict):
    session["step"] = "tags"
    await message.answer(
        (
            "Выбери теги.\n\n"
            "Важно: если тайтл должен попадать в обычный быстрый подбор, "
            "у него должен быть хотя бы один публичный вайб-тег.\n"
            "Если сохранить обычный тайтл без такого тега, быстрый подбор его не увидит."
        ),
        reply_markup=tags_keyboard(get_tag_catalog(session["type"])),
    )


async def ask_public_vibes(message: Message, session: dict):
    session["step"] = "public_vibes"
    existing_vibes = get_public_vibes(session["type"])
    vibe_labels = list(existing_vibes.values())

    if vibe_labels:
        preview = "\n".join(f"• {label}" for label in vibe_labels[:25])
        if len(vibe_labels) > 25:
            preview += f"\n• ... и ещё {len(vibe_labels) - 25}"
    else:
        preview = "Пока нет ни одного публичного вайба."

    await message.answer(
        (
            "✨ Если хочешь, добавь новые публичные вайбы именно под этот тайтл.\n\n"
            "Они будут показываться пользователям в обычном быстром подборе, "
            "даже если в них всего 1-2 объекта.\n\n"
            "Форматы:\n"
            "`Ночная тоска; Сломанная романтика`\n"
            "`night_ache = Ночная тоска; broken_love = Сломанная романтика`\n\n"
            f"*Уже существующие публичные вайбы для этого типа:*\n{preview}\n\n"
            "Отправь `-`, если новые вайбы не нужны."
        ),
        parse_mode="Markdown",
    )


@router.message(F.text == "/add")
async def add_content_start(message: Message):
    if not is_admin_id(message.from_user.id):
        return

    admin_sessions[message.from_user.id] = {}
    await message.answer(
        "Что будем добавлять?",
        reply_markup=content_type_keyboard(),
    )


@router.message(Command("use_draft"))
async def use_draft(message: Message, command: CommandObject):
    if not is_admin_id(message.from_user.id):
        return

    if not command.args or not command.args.isdigit():
        await message.answer("Используй: /use_draft <id>")
        return

    draft_id = int(command.args)
    draft = get_admin_content_draft(draft_id)

    if not draft:
        await message.answer("Черновик не найден")
        return

    if draft[7] != "pending":
        await message.answer("Этот черновик уже использован")
        return

    admin_sessions[message.from_user.id] = build_draft_session(draft)
    await message.answer(draft_loaded_text(draft))


@router.callback_query(F.data.startswith("use_draft_cb:"))
async def use_draft_callback(callback: CallbackQuery):
    if not is_admin_id(callback.from_user.id):
        await callback.answer("Раздел только для админа", show_alert=True)
        return

    draft_id = int(callback.data.split(":", 1)[1])
    draft = get_admin_content_draft(draft_id)

    if not draft:
        await callback.answer("Черновик не найден", show_alert=True)
        return

    if draft[7] != "pending":
        await callback.answer("Этот черновик уже использован", show_alert=True)
        return

    admin_sessions[callback.from_user.id] = build_draft_session(draft)
    await callback.answer("Черновик загружен")
    await callback.message.answer(draft_loaded_text(draft))


@router.callback_query(F.data.startswith("admin_type:"))
async def choose_content_type(callback: CallbackQuery):
    if not is_admin_id(callback.from_user.id):
        await callback.answer("Раздел только для админа", show_alert=True)
        return

    session = admin_sessions.setdefault(callback.from_user.id, {})
    session["type"] = callback.data.split(":")[1]
    session["premium_collections"] = []
    session["premium_collection_only"] = False
    session["platforms"] = []
    session["step"] = "media"

    await callback.answer()
    await callback.message.answer("Пришли обложку / гифку / mp4")


@router.message(F.photo | F.animation | F.video)
async def receive_media(message: Message):
    if not is_admin_id(message.from_user.id):
        return

    session = admin_sessions.get(message.from_user.id)
    if not session or session.get("step") != "media":
        return

    if message.photo:
        session["media"] = {
            "type": "photo",
            "file_id": message.photo[-1].file_id,
        }
    elif message.animation:
        session["media"] = {
            "type": "animation",
            "file_id": message.animation.file_id,
        }
    elif message.video:
        session["media"] = {
            "type": "video",
            "file_id": message.video.file_id,
        }

    if session.get("title") and session.get("desc"):
        if session.get("type") == "book":
            session["step"] = "audio"
            await message.answer(
                "Черновик уже заполнен. Пришли аудио-отрывок или отправь `-`, чтобы пропустить.",
                parse_mode="Markdown",
            )
        elif session.get("type") == "game":
            await ask_game_platforms(message, session)
        else:
            await ask_premium_collections(message, session)
        return

    session["step"] = "title"
    await message.answer("Введи название")


@router.message(F.voice | F.audio)
async def receive_book_audio(message: Message):
    if not is_admin_id(message.from_user.id):
        return

    session = admin_sessions.get(message.from_user.id)
    if not session:
        return

    if session.get("type") != "book":
        await message.answer("Аудио только для книг")
        return

    if session.get("step") != "audio":
        return

    if message.voice:
        session["audio"] = {
            "type": "voice",
            "file_id": message.voice.file_id,
        }
    else:
        session["audio"] = {
            "type": "audio",
            "file_id": message.audio.file_id,
        }

    await ask_premium_collections(message, session)


@router.message(F.text)
async def receive_text(message: Message):
    if not is_admin_id(message.from_user.id):
        return

    session = admin_sessions.get(message.from_user.id)
    if not session:
        return

    if session.get("step") == "title":
        title = clean_user_text(message.text)
        if not title:
            await message.answer("Название не должно быть пустым.")
            return
        if is_too_long(title, MAX_ADMIN_TITLE_LENGTH):
            await message.answer(length_error_text(MAX_ADMIN_TITLE_LENGTH))
            return

        session["title"] = title
        session["step"] = "desc"
        await message.answer("Введи описание")
        return

    if session.get("step") == "desc":
        description = clean_user_text(message.text)
        if not description:
            await message.answer("Описание не должно быть пустым.")
            return
        if is_too_long(description, MAX_ADMIN_DESCRIPTION_LENGTH):
            await message.answer(length_error_text(MAX_ADMIN_DESCRIPTION_LENGTH))
            return

        session["desc"] = description

        if session.get("type") == "book":
            session["step"] = "audio"
            await message.answer(
                "Пришли аудио-отрывок (voice или audio)\n\nИли отправь `-`, чтобы пропустить",
                parse_mode="Markdown",
            )
        elif session.get("type") == "game":
            await ask_game_platforms(message, session)
        else:
            await ask_premium_collections(message, session)
        return

    if session.get("step") == "audio" and message.text == "-":
        session["audio"] = None
        await ask_premium_collections(message, session)
        return

    if session.get("step") == "premium_collections":
        collection_text = clean_user_text(message.text)
        if collection_text == "-":
            session["premium_collections"] = []
            await ask_public_vibes(message, session)
            return
        if is_too_long(collection_text, MAX_ADMIN_COLLECTIONS_LENGTH):
            await message.answer(length_error_text(MAX_ADMIN_COLLECTIONS_LENGTH))
            return

        selected = session.setdefault("premium_collections", [])
        for name in normalize_collection_names(collection_text):
            if name not in selected:
                selected.append(name)

        await ask_premium_collections(message, session)
        return

    if session.get("step") == "public_vibes":
        public_vibes_text = clean_user_text(message.text)
        if public_vibes_text == "-":
            session["new_public_vibes"] = []
            await ask_tags(message, session)
            return
        if is_too_long(public_vibes_text, MAX_ADMIN_PUBLIC_VIBES_LENGTH):
            await message.answer(length_error_text(MAX_ADMIN_PUBLIC_VIBES_LENGTH))
            return

        parsed_public_vibes = parse_new_public_vibes(public_vibes_text)
        if not parsed_public_vibes:
            await message.answer(
                "Не удалось разобрать новые вайбы. Попробуй форматы `Ночная тоска` или `night_ache = Ночная тоска`."
            )
            return

        existing_public_vibes = get_public_vibes(session["type"])
        pending_new_public_vibes = {
            key: label for key, label in session.get("new_public_vibes", [])
        }
        tags = session.setdefault("tags", set())
        actually_new_public_vibes: list[tuple[str, str]] = []
        linked_existing_labels: list[str] = []

        for vibe_key, label in parsed_public_vibes:
            tags.add(vibe_key)
            if vibe_key in existing_public_vibes or vibe_key in pending_new_public_vibes:
                linked_existing_labels.append(
                    existing_public_vibes.get(
                        vibe_key,
                        pending_new_public_vibes.get(vibe_key, label),
                    )
                )
                continue
            actually_new_public_vibes.append((vibe_key, label))
            pending_new_public_vibes[vibe_key] = label

        session["new_public_vibes"] = list(pending_new_public_vibes.items())

        response_parts = []
        if actually_new_public_vibes:
            added_labels = "\n".join(f"• {label}" for _key, label in actually_new_public_vibes)
            response_parts.append(f"Новые публичные вайбы добавлены:\n{added_labels}")
        if linked_existing_labels:
            reused_labels = "\n".join(f"• {label}" for label in linked_existing_labels)
            response_parts.append(f"Уже существующие вайбы просто привязаны к тайтлу:\n{reused_labels}")

        await message.answer("\n\n".join(response_parts))
        await ask_tags(message, session)
        return


@router.callback_query(F.data.startswith("admin_game_platform_toggle:"))
async def toggle_game_platform(callback: CallbackQuery):
    if not is_admin_id(callback.from_user.id):
        await callback.answer("Раздел только для админа", show_alert=True)
        return

    session = admin_sessions.get(callback.from_user.id)
    if not session or session.get("step") != "game_platforms":
        await callback.answer("Сессия выбора платформ не активна", show_alert=True)
        return

    platform = callback.data.split(":", 1)[1]
    selected = session.setdefault("platforms", [])

    if platform in selected:
        selected.remove(platform)
        await callback.answer("Платформа снята")
    else:
        selected.append(platform)
        await callback.answer("Платформа добавлена")

    await callback.message.edit_text(
        game_platforms_text(session),
        reply_markup=game_platforms_keyboard(selected),
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "admin_game_platforms_done")
async def finish_game_platforms(callback: CallbackQuery):
    if not is_admin_id(callback.from_user.id):
        await callback.answer("Раздел только для админа", show_alert=True)
        return

    session = admin_sessions.get(callback.from_user.id)
    if not session or session.get("step") != "game_platforms":
        await callback.answer("Сессия выбора платформ не активна", show_alert=True)
        return

    if not session.get("platforms"):
        await callback.answer("Выбери хотя бы одну платформу", show_alert=True)
        return

    await callback.answer()
    await ask_premium_collections(callback.message, session)


@router.callback_query(F.data.startswith("admin_collection_toggle:"))
async def toggle_premium_collection(callback: CallbackQuery):
    if not is_admin_id(callback.from_user.id):
        await callback.answer("Раздел только для админа", show_alert=True)
        return

    session = admin_sessions.get(callback.from_user.id)
    if not session or session.get("step") != "premium_collections":
        await callback.answer("Сессия premium-подборок не активна", show_alert=True)
        return

    index = int(callback.data.split(":", 1)[1])
    options = session.get("premium_collection_options", [])

    if index < 0 or index >= len(options):
        await callback.answer("Подборка не найдена", show_alert=True)
        return

    name = options[index]
    selected = session.setdefault("premium_collections", [])

    if name in selected:
        selected.remove(name)
        await callback.answer("Подборка снята")
    else:
        selected.append(name)
        await callback.answer("Подборка добавлена")

    await callback.message.edit_text(
        premium_collections_text(session),
        reply_markup=premium_collections_keyboard(
            options=options,
            selected=selected,
            premium_only=session.get("premium_collection_only", False),
        ),
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "admin_collection_only_toggle")
async def toggle_collection_only(callback: CallbackQuery):
    if not is_admin_id(callback.from_user.id):
        await callback.answer("Раздел только для админа", show_alert=True)
        return

    session = admin_sessions.get(callback.from_user.id)
    if not session or session.get("step") != "premium_collections":
        await callback.answer("Сессия premium-подборок не активна", show_alert=True)
        return

    session["premium_collection_only"] = not session.get("premium_collection_only", False)
    await callback.answer(
        "Контент будет только в premium-подборках"
        if session["premium_collection_only"]
        else "Контент снова доступен и для общей выдачи"
    )

    await callback.message.edit_text(
        premium_collections_text(session),
        reply_markup=premium_collections_keyboard(
            options=session.get("premium_collection_options", []),
            selected=session.get("premium_collections", []),
            premium_only=session.get("premium_collection_only", False),
        ),
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "admin_collections_done")
async def finish_premium_collections(callback: CallbackQuery):
    if not is_admin_id(callback.from_user.id):
        await callback.answer("Раздел только для админа", show_alert=True)
        return

    session = admin_sessions.get(callback.from_user.id)
    if not session or session.get("step") != "premium_collections":
        await callback.answer("Сессия premium-подборок не активна", show_alert=True)
        return

    await callback.answer()
    await ask_public_vibes(callback.message, session)


@router.callback_query(F.data.startswith("tag:"))
async def add_tag(callback: CallbackQuery):
    if not is_admin_id(callback.from_user.id):
        await callback.answer("Раздел только для админа", show_alert=True)
        return

    session = admin_sessions.get(callback.from_user.id)
    if not session:
        return

    tags = session.setdefault("tags", set())
    tag = callback.data.split(":")[1]
    tags.add(tag)

    await callback.answer(f"Добавлен: {tag}")


@router.callback_query(F.data == "save_content")
async def save_content_handler(callback: CallbackQuery):
    if not is_admin_id(callback.from_user.id):
        await callback.answer("Раздел только для админа", show_alert=True)
        return

    session = admin_sessions.pop(callback.from_user.id, None)

    if not session:
        await callback.answer("Сессия потеряна", show_alert=True)
        return

    content_type = session.get("type")
    if not content_type:
        await callback.answer("Тип не определён", show_alert=True)
        return

    tags = set(session.get("tags", set()))
    public_vibe_keys = set(get_public_vibes(content_type).keys())
    pending_public_vibe_keys = {
        key for key, _label in session.get("new_public_vibes", [])
    }
    public_vibe_keys |= pending_public_vibe_keys
    premium_collection_only = session.get("premium_collection_only", False)

    if content_type == "game" and not session.get("platforms"):
        admin_sessions[callback.from_user.id] = session
        await callback.answer("Для игры нужна хотя бы одна платформа", show_alert=True)
        await callback.message.answer(
            "У игры пока не выбрана ни одна платформа. Отметь хотя бы одну платформу и потом сохраняй."
        )
        return

    if not premium_collection_only and not tags:
        admin_sessions[callback.from_user.id] = session
        await callback.answer("Нужно выбрать хотя бы один тег", show_alert=True)
        await callback.message.answer(
            "Этот тайтл сейчас сохраняется без тегов, поэтому быстрый подбор его не увидит.\n\n"
            "Добавь хотя бы один публичный вайб-тег и потом сохраняй."
        )
        return

    if not premium_collection_only and not (tags & public_vibe_keys):
        admin_sessions[callback.from_user.id] = session
        await callback.answer("Нет fast-вайба для общей выдачи", show_alert=True)
        await callback.message.answer(
            "У тайтла сейчас есть только персональные или внутренние теги.\n\n"
            "Чтобы он появлялся в быстром подборе, добавь хотя бы один публичный вайб из списка тегов."
        )
        return

    data = {
        "title": session.get("title"),
        "desc": session.get("desc"),
        "media": session.get("media"),
        "tags": list(tags),
        "platforms": session.get("platforms", []) if content_type == "game" else [],
        "premium_collections": session.get("premium_collections", []),
        "premium_collection_only": premium_collection_only,
        "audio": session.get("audio") if content_type == "book" else None,
    }

    try:
        create_snapshot_backup(f"before_add_{content_type}")
        add_public_vibes(content_type, session.get("new_public_vibes", []))
        save_to_json(content_type, data)
    except Exception as error:
        await callback.message.answer(f"Ошибка сохранения:\n{error}")
        return

    draft_id = session.get("draft_id")
    if draft_id:
        mark_admin_content_draft_used(draft_id)

    track_event(
        callback.from_user.id,
        "content_added",
        content_type=content_type,
        content_id=data["title"],
        source="admin_add_content",
        metadata={
            "tags_count": len(data["tags"]),
            "premium_collection_only": premium_collection_only,
            "premium_collections_count": len(data["premium_collections"]),
        },
    )

    await callback.message.answer("Контент сохранён в базе")
    await callback.answer()
