import random

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from data.books import load_books
from utils.public_vibes import get_public_vibes
from utils.rating_ui import build_card_back_row, build_card_nav_row, build_copy_title_row, build_rating_rows


def book_vibe_keyboard(excluded_titles: set[str] | None = None):
    keyboard = []
    excluded_titles = excluded_titles or set()

    books = load_books(include_premium_collection_only=False)
    all_vibes = [
        (tag, label)
        for tag, label in get_public_vibes("book").items()
        if any(
            tag in book.get("tags", []) and book["title"] not in excluded_titles
            for book in books
        )
    ]
    count = min(3, len(all_vibes))
    random_vibes = random.sample(all_vibes, k=count) if count else []

    for tag, label in random_vibes:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"fast_book_vibe:{tag}",
                )
            ]
        )

    keyboard.append(
        [InlineKeyboardButton(text="🔄 Обновить вайбы", callback_data="refresh_book_vibes")]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def another_book_keyboard(
    vibe: str | None,
    title: str | None = None,
    show_another: bool = True,
    collection_name: str | None = None,
    show_next_collection: bool = False,
    show_change_vibe: bool = False,
    has_audio: bool = False,
    is_favorite: bool = False,
    user_rating: int | None = None,
    is_premium: bool = False,
    view: str = "main",
):
    keyboard = []

    if view == "reactions":
        keyboard.extend(build_rating_rows(user_rating=user_rating, is_premium=is_premium))
        keyboard.append(build_card_back_row())
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    if view == "more":
        if has_audio and is_premium:
            keyboard.append(
                [InlineKeyboardButton(text="🎧 Послушать отрывок", callback_data="listen_book_excerpt")]
            )
        keyboard.append(build_card_back_row())
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    copy_row = build_copy_title_row(title)
    if copy_row:
        keyboard.append(copy_row)

    if collection_name and show_next_collection:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="➡️ Дальше по подборке",
                    callback_data="next_book_collection",
                )
            ]
        )
    elif vibe and show_another:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="🎲 Другая книга",
                    callback_data=f"another_book:{vibe}",
                )
            ]
        )

    if vibe and (show_change_vibe or not show_another):
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="🔄 Выбрать другой вайб",
                    callback_data="books_fast",
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                text="❌ Убрать из избранного" if is_favorite else "⭐ В избранное",
                callback_data="toggle_favorite",
            )
        ]
    )
    keyboard.append(build_card_nav_row(show_more=has_audio and is_premium))

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
