from aiogram import Router, F
from aiogram.types import CallbackQuery

from keyboards.movies import movie_vibe_keyboard, another_movie_keyboard

from data.movies import get_random_movie

router = Router()   # ← ОБЯЗАТЕЛЬНО


@router.callback_query(F.data == "choose_movie")
async def choose_movie(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎬 Какой сейчас вайб?",
        reply_markup=movie_vibe_keyboard()
    )


@router.callback_query(F.data.startswith("movie_vibe_"))
async def movie_selected(callback: CallbackQuery):
    vibe = callback.data.replace("movie_vibe_", "")
    movie = get_random_movie(vibe)

    await callback.message.edit_text(
        f"🎥 <b>{movie['title']}</b>\n\n{movie['desc']}",
        reply_markup=another_movie_keyboard(vibe),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("another_movie:"))
async def another_movie(callback: CallbackQuery):
    vibe = callback.data.split(":")[1]
    movie = get_random_movie(vibe)

    await callback.message.edit_text(
        f"🎥 <b>{movie['title']}</b>\n\n{movie['desc']}",
        reply_markup=another_movie_keyboard(vibe),
        parse_mode="HTML"
    )
