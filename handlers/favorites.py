from pathlib import Path

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from data.anime import load_anime
from data.books import load_books
from data.games import load_games
from data.movies import load_movies
from data.series import load_series
from utils.access import (
    consume_free_favorites_export_use,
    free_favorites_export_locked_text,
    free_favorites_export_status,
    has_premium_access,
)
from utils.db import get_user_favorites, remove_from_favorites
from utils.favorites_export import build_favorites_text, render_favorites_image
from utils.media_sender import send_media
from utils.ui import replace_screen

router = Router()

CONTENT_LOADERS = {
    "anime": load_anime,
    "book": load_books,
    "game": load_games,
    "movie": load_movies,
    "series": load_series,
}

CONTENT_TITLES = {
    "anime": "🎌 Аниме",
    "book": "📚 Книги",
    "game": "🎮 Игры",
    "movie": "🎬 Фильмы",
    "series": "📺 Сериалы",
}


CONTENT_ORDER = ["anime", "book", "game", "movie", "series"]


def get_available_favorite_types(user_id: int) -> list[str]:
    rows = get_user_favorites(user_id)
    available_types = {content_type for content_type, _content_id in rows}
    return [content_type for content_type in CONTENT_ORDER if content_type in available_types]


def get_favorites_count_map(user_id: int) -> dict[str, int]:
    rows = get_user_favorites(user_id)
    counts: dict[str, int] = {}

    for content_type, _content_id in rows:
        counts[content_type] = counts.get(content_type, 0) + 1

    return counts


def favorites_root_keyboard(user_id: int):
    counts = get_favorites_count_map(user_id)
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text=f"{CONTENT_TITLES[content_type]} ({counts.get(content_type, 0)})",
                callback_data=f"favorites:{content_type}",
            )
        ]
        for content_type in get_available_favorite_types(user_id)
    ]
    if counts:
        inline_keyboard.append(
            [InlineKeyboardButton(text="📝 Список текстом", callback_data="favorites_export:text")]
        )
        inline_keyboard.append(
            [InlineKeyboardButton(text="🖼 Список картинкой", callback_data="favorites_export:image")]
        )
    if not inline_keyboard:
        return None
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def favorites_root_text(user_id: int) -> str:
    available_types = get_available_favorite_types(user_id)
    if not available_types:
        return "⭐ Моё избранное\n\nПока пусто 😶"
    return "⭐ Моё избранное\n\nВыбери раздел:"


def _export_type_picker_text(export_type: str, selected_types: list[str], user: dict) -> str:
    export_label = "текстом" if export_type == "text" else "картинкой"
    premium_note = (
        "💎 Premium: безлимитный экспорт"
        if has_premium_access(user)
        else "🤗 Free: экспорт 1 раз в 7 дней"
    )
    selected_count = len(selected_types)
    return (
        f"⭐ <b>Экспорт избранного {export_label}</b>\n\n"
        "Выбери, какие разделы включить в список.\n"
        f"Сейчас выбрано: <b>{selected_count}</b>\n\n"
        f"{premium_note}"
    )


def _image_style_picker_text(selected_types: list[str], image_style: str, user: dict) -> str:
    premium_note = (
        "💎 Premium: безлимитный экспорт"
        if has_premium_access(user)
        else "🤗 Free: экспорт 1 раз в 7 дней"
    )
    style_titles = {
        "minimal": "Минималистичный",
        "colorful": "Красочный и яркий",
        "warm": "Тёплый и милый",
    }
    return (
        "🖼 <b>Экспорт избранного картинкой</b>\n\n"
        "Шаг 2 из 2: выбери стиль оформления.\n"
        f"Разделов в экспорте: <b>{len(selected_types)}</b>\n"
        f"Текущий стиль: <b>{style_titles.get(image_style, 'Минималистичный')}</b>\n\n"
        f"{premium_note}"
    )


def _favorites_export_picker_keyboard(
    user_id: int,
    export_type: str,
    selected_types: list[str],
):
    counts = get_favorites_count_map(user_id)
    selected_set = set(selected_types)
    keyboard = []

    for content_type in get_available_favorite_types(user_id):
        mark = "✅" if content_type in selected_set else "⬜"
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{mark} {CONTENT_TITLES[content_type]} ({counts.get(content_type, 0)})",
                    callback_data=f"favorites_export_toggle:{content_type}",
                )
            ]
        )

    if export_type == "text":
        keyboard.append([InlineKeyboardButton(text="📝 Собрать список текстом", callback_data="favorites_export_build")])
    else:
        keyboard.append([InlineKeyboardButton(text="➡️ Дальше к стилю", callback_data="favorites_export_step:image_style")])
    keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="my_favorites")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def _favorites_export_style_keyboard(image_style: str):
    style_labels = {
        "minimal": "Минималистичный",
        "colorful": "Красочный и яркий",
        "warm": "Тёплый и милый",
    }
    keyboard = []
    for style_key in ["minimal", "colorful", "warm"]:
        mark = "✅" if image_style == style_key else "⬜"
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{mark} {style_labels[style_key]}",
                    callback_data=f"favorites_export_style:{style_key}",
                )
            ]
        )

    keyboard.append([InlineKeyboardButton(text="🖼 Собрать картинкой", callback_data="favorites_export_build")])
    keyboard.append([InlineKeyboardButton(text="⬅️ К разделам", callback_data="favorites_export_step:types")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.message(F.text == "⭐ Избранное")
async def my_favorites_button(message: Message, user: dict):
    await message.answer(
        favorites_root_text(user["telegram_id"]),
        reply_markup=favorites_root_keyboard(user["telegram_id"]),
    )


@router.callback_query(F.data == "my_favorites")
async def my_favorites(callback: CallbackQuery, user: dict):
    await replace_screen(
        callback,
        text=favorites_root_text(user["telegram_id"]),
        reply_markup=favorites_root_keyboard(user["telegram_id"]),
    )


@router.callback_query(F.data.startswith("favorites_export:"))
async def favorites_export(callback: CallbackQuery, state: FSMContext, user: dict):
    export_type = callback.data.split(":", 1)[1]
    rows = get_user_favorites(user["telegram_id"])

    if not rows:
        await callback.answer("В избранном пока пусто", show_alert=True)
        return

    can_use, next_available_at = free_favorites_export_status(user)
    if not can_use and next_available_at:
        await callback.answer(
            f"Для Free экспорт доступен раз в 7 дней. Следующий после {next_available_at.strftime('%d.%m %H:%M')}",
            show_alert=True,
        )
        return

    if export_type not in {"text", "image"}:
        await callback.answer("Формат не найден", show_alert=True)
        return

    selected_types = get_available_favorite_types(user["telegram_id"])
    await state.update_data(
        favorites_export_mode=export_type,
        favorites_export_selected_types=selected_types,
        favorites_export_image_style="minimal",
    )
    await replace_screen(
        callback,
        text=_export_type_picker_text(export_type, selected_types, user),
        reply_markup=_favorites_export_picker_keyboard(
            user_id=user["telegram_id"],
            export_type=export_type,
            selected_types=selected_types,
        ),
    )


@router.callback_query(F.data.startswith("favorites_export_toggle:"))
async def favorites_export_toggle(callback: CallbackQuery, state: FSMContext, user: dict):
    content_type = callback.data.split(":", 1)[1]
    available_types = get_available_favorite_types(user["telegram_id"])

    if content_type not in available_types:
        await callback.answer("Раздел недоступен", show_alert=True)
        return

    data = await state.get_data()
    export_type = data.get("favorites_export_mode")
    selected_types = data.get("favorites_export_selected_types", available_types)
    image_style = data.get("favorites_export_image_style", "minimal")

    if export_type not in {"text", "image"}:
        await callback.answer("Сначала выбери формат", show_alert=True)
        return

    selected_set = set(selected_types)
    if content_type in selected_set:
        selected_set.remove(content_type)
    else:
        selected_set.add(content_type)

    updated_types = [item for item in CONTENT_ORDER if item in selected_set and item in available_types]
    await state.update_data(favorites_export_selected_types=updated_types)

    await replace_screen(
        callback,
        text=_export_type_picker_text(export_type, updated_types, user),
        reply_markup=_favorites_export_picker_keyboard(
            user_id=user["telegram_id"],
            export_type=export_type,
            selected_types=updated_types,
        ),
    )


@router.callback_query(F.data == "favorites_export_step:image_style")
async def favorites_export_step_image_style(callback: CallbackQuery, state: FSMContext, user: dict):
    data = await state.get_data()
    export_type = data.get("favorites_export_mode")
    selected_types = data.get("favorites_export_selected_types", [])
    image_style = data.get("favorites_export_image_style", "minimal")

    if export_type != "image":
        await callback.answer("Этот шаг только для картинки", show_alert=True)
        return

    if not selected_types:
        await callback.answer("Выбери хотя бы один раздел", show_alert=True)
        return

    await replace_screen(
        callback,
        text=_image_style_picker_text(selected_types, image_style, user),
        reply_markup=_favorites_export_style_keyboard(image_style),
    )


@router.callback_query(F.data == "favorites_export_step:types")
async def favorites_export_step_types(callback: CallbackQuery, state: FSMContext, user: dict):
    data = await state.get_data()
    export_type = data.get("favorites_export_mode")
    selected_types = data.get(
        "favorites_export_selected_types",
        get_available_favorite_types(user["telegram_id"]),
    )

    if export_type not in {"text", "image"}:
        await callback.answer("Сначала выбери формат", show_alert=True)
        return

    await replace_screen(
        callback,
        text=_export_type_picker_text(export_type, selected_types, user),
        reply_markup=_favorites_export_picker_keyboard(
            user_id=user["telegram_id"],
            export_type=export_type,
            selected_types=selected_types,
        ),
    )


@router.callback_query(F.data.startswith("favorites_export_style:"))
async def favorites_export_style(callback: CallbackQuery, state: FSMContext, user: dict):
    style = callback.data.split(":", 1)[1]
    if style not in {"minimal", "colorful", "warm"}:
        await callback.answer("Стиль не найден", show_alert=True)
        return

    data = await state.get_data()
    export_type = data.get("favorites_export_mode")
    selected_types = data.get("favorites_export_selected_types", get_available_favorite_types(user["telegram_id"]))

    if export_type != "image":
        await callback.answer("Стиль доступен только для картинки", show_alert=True)
        return

    await state.update_data(favorites_export_image_style=style)
    await replace_screen(
        callback,
        text=_image_style_picker_text(selected_types, style, user),
        reply_markup=_favorites_export_style_keyboard(style),
    )


@router.callback_query(F.data == "favorites_export_build")
async def favorites_export_build(callback: CallbackQuery, state: FSMContext, user: dict):
    rows = get_user_favorites(user["telegram_id"])
    if not rows:
        await callback.answer("В избранном пока пусто", show_alert=True)
        return

    data = await state.get_data()
    export_type = data.get("favorites_export_mode")
    selected_types = data.get("favorites_export_selected_types", [])
    image_style = data.get("favorites_export_image_style", "minimal")

    if export_type not in {"text", "image"}:
        await callback.answer("Сначала выбери формат", show_alert=True)
        return

    if not selected_types:
        await callback.answer("Выбери хотя бы один раздел", show_alert=True)
        return

    can_use, next_available_at = free_favorites_export_status(user)
    if not can_use and next_available_at:
        await callback.answer(
            f"Для Free экспорт доступен раз в 7 дней. Следующий после {next_available_at.strftime('%d.%m %H:%M')}",
            show_alert=True,
        )
        return

    if not has_premium_access(user):
        consume_free_favorites_export_use(user["telegram_id"])

    if export_type == "text":
        await callback.message.answer(
            build_favorites_text(rows, selected_types=selected_types),
            parse_mode="HTML",
        )
        await callback.answer("Список отправлен")
        return

    image_path = render_favorites_image(
        rows,
        selected_types=selected_types,
        style=image_style,
    )
    try:
        image_file = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=image_file,
            caption="🖼 Избранное в Базе №600",
        )
    except Exception:
        await callback.answer("Не получилось отправить картинку", show_alert=True)
        return
    finally:
        try:
            Path(image_path).unlink(missing_ok=True)
        except Exception:
            pass

    await callback.answer("Картинка готова")


@router.callback_query(F.data.startswith("favorites:"))
async def favorites_by_type(callback: CallbackQuery, user: dict):
    content_type = callback.data.split(":", 1)[1]
    rows = get_user_favorites(user["telegram_id"], content_type)

    if not rows:
        await replace_screen(
            callback,
            text=f"{CONTENT_TITLES[content_type]}\n\nПока пусто 😶",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="my_favorites")]
                ]
            ),
        )
        return

    items = CONTENT_LOADERS[content_type]()
    favorites = {title for (title,) in rows}
    keyboard = []

    for idx, item in enumerate(items):
        if item["title"] in favorites:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=item["title"],
                        callback_data=f"favorite_open:{content_type}:{idx}",
                    )
                ]
            )

    keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="my_favorites")])

    await replace_screen(
        callback,
        text=f"{CONTENT_TITLES[content_type]} — избранное:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
    )


@router.callback_query(F.data.startswith("favorite_open:"))
async def open_favorite(callback: CallbackQuery, state: FSMContext):
    _, content_type, idx = callback.data.split(":", 2)
    idx = int(idx)

    items = CONTENT_LOADERS[content_type]()

    if idx < 0 or idx >= len(items):
        await callback.answer("Элемент не найден", show_alert=True)
        return

    item = items[idx]

    await state.update_data(
        current_item=item,
        current_type=content_type,
        current_vibe=None,
    )

    try:
        await callback.message.delete()
    except Exception:
        pass

    await send_media(
        callback,
        item,
        content_type=content_type,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌ Убрать из избранного",
                        callback_data="favorite_remove",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⬅️ К списку",
                        callback_data=f"favorites:{content_type}",
                    )
                ],
            ]
        ),
    )


@router.callback_query(F.data == "favorite_remove")
async def remove_favorite(callback: CallbackQuery, state: FSMContext, user: dict):
    data = await state.get_data()
    item = data.get("current_item")
    content_type = data.get("current_type")

    if not item:
        await callback.answer("Ошибка состояния", show_alert=True)
        return

    remove_from_favorites(
        user_id=user["telegram_id"],
        content_type=content_type,
        content_id=item["title"],
    )

    await replace_screen(
        callback,
        text=f"❌ «{item['title']}» удалено из избранного",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⬅️ К списку",
                        callback_data=f"favorites:{content_type}",
                    )
                ],
            ]
        ),
    )
