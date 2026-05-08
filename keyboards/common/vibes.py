from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def build_vibe_keyboard(vibe_keys, vibe_dict, callback_prefix):
    keyboard = []

    for key in vibe_keys:
        vibe = vibe_dict[key]
        keyboard.append([
            InlineKeyboardButton(
                text=vibe["label"],
                callback_data=f"{callback_prefix}_{key}"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
