import random

MOVIES_BY_VIBE = {
    "sad_motivation": [
        {
            "title": "В погоне за счастьем",
            "desc": "История о том, как не сдаться, когда всё против тебя."
        },
        {
            "title": "Форрест Гамп",
            "desc": "Доброе кино о жизни и людях."
        }
    ],
    "action": [
        {
            "title": "Джон Уик",
            "desc": "Чистый экшен без лишних слов."
        }
    ]
}


def get_random_movie(vibe):
    return random.choice(MOVIES_BY_VIBE[vibe])
