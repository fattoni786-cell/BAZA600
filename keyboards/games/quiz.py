from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def game_q1_tempo_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ Быстрый", callback_data="tempo_fast")],
        [InlineKeyboardButton(text="😌 Спокойный", callback_data="tempo_chill")]
    ])


def game_q2_story_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Очень важен", callback_data="story_yes")],
        [InlineKeyboardButton(text="❌ Не важен", callback_data="story_no")]
    ])


def game_q3_difficulty_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💀 Люблю хардкор", callback_data="hardcore_yes")],
        [InlineKeyboardButton(text="🙂 Хочу расслабиться", callback_data="hardcore_no")]
    ])


def game_q4_mood_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌑 Мрачное", callback_data="mood_dark")],
        [InlineKeyboardButton(text="🌈 Светлое", callback_data="mood_light")]
    ])


def game_q5_mode_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧍 Один", callback_data="mode_single")],
        [InlineKeyboardButton(text="🤝 С друзьями", callback_data="mode_multi")]
    ])
