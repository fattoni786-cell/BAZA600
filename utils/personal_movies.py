import random
from collections import Counter, defaultdict

from data.add_movies import load_movies
from utils.content_history import get_recently_seen_titles
from utils.db import get_user_favorites, get_user_rated_content
from utils.public_vibes import get_public_vibes

QUESTION_COUNT = 4
ANSWER_LABELS = ["0%", "50%", "75%", "600%"]
MOVIE_PUBLIC_VIBES = get_public_vibes("movie")
MOVIE_TAG_FREQUENCY = Counter(
    tag
    for movie in load_movies(include_premium_collection_only=False)
    for tag in movie.get("tags", [])
)


def _answers(weight_sets: list[dict[str, float]]) -> list[dict]:
    return [
        {"text": ANSWER_LABELS[index], "weights": weights}
        for index, weights in enumerate(weight_sets)
    ]


MOVIE_PERSONAL_QUESTIONS = [
    {
        "id": "q01",
        "text": "Насколько тебе сейчас близок более личный и одинокий тон?",
        "answers": _answers([
            {"comedy": 2, "action": 2, "hopeful": 1},
            {"atmospheric": 2, "philosophical": 1},
            {"lonely": 3, "melancholic": 2},
            {"lonely": 4, "melancholic": 3, "heartbreaking": 1},
        ]),
    },
    {
        "id": "q02",
        "text": "Насколько тебе сегодня комфортно с темнотой и тяжестью?",
        "answers": _answers([
            {"hopeful": 2, "chill": 2},
            {"dark_drama": 1, "realistic_thriller": 1},
            {"dark_drama": 3, "realistic_thriller": 2},
            {"dark_drama": 4, "uncomfortable": 2, "vibe_569903b64556": 1},
        ]),
    },
    {
        "id": "q03",
        "text": "Нужен ли тебе сегодня драйв важнее атмосферы?",
        "answers": _answers([
            {"atmospheric": 3, "chill": 2},
            {"thriller": 2, "realistic_thriller": 1},
            {"action": 3, "thriller": 2},
            {"action": 4, "thriller": 2, "vibe_d2ab183d1db7": 2},
        ]),
    },
    {
        "id": "q04",
        "text": "Хочется ли чего-то мягкого и согревающего, а не колючего?",
        "answers": _answers([
            {"uncomfortable": 2, "dark_drama": 1},
            {"chill": 2, "hopeful": 1},
            {"chill": 3, "hopeful": 2, "romantic": 1},
            {"chill": 4, "hopeful": 3, "comedy": 1},
        ]),
    },
    {
        "id": "q05",
        "text": "Насколько тебе хочется, чтобы фильм немного сломал голову?",
        "answers": _answers([
            {"classic": 1, "romantic": 1},
            {"philosophical": 2, "thriller": 1},
            {"mind_bending": 3, "philosophical": 2},
            {"mind_bending": 4, "weird": 2, "vibe_30583a1ac107": 2},
        ]),
    },
    {
        "id": "q06",
        "text": "Жизненность и приземлённость тебе сейчас важнее эскапизма?",
        "answers": _answers([
            {"weird": 2, "mind_bending": 1},
            {"atmospheric": 2, "documentary": 1},
            {"realistic_thriller": 3, "documentary": 2},
            {"realistic_thriller": 4, "documentary": 2, "ru_voice": 1},
        ]),
    },
    {
        "id": "q07",
        "text": "Нужен ли юмор, чтобы чуть легче дышалось?",
        "answers": _answers([
            {"dark_drama": 2, "thriller": 1},
            {"comedy": 2},
            {"black_comedy": 3, "comedy": 2},
            {"black_comedy": 4, "comedy": 2, "weird": 1},
        ]),
    },
    {
        "id": "q08",
        "text": "Хочется ли морально неприятных и неудобных вещей?",
        "answers": _answers([
            {"hopeful": 2, "chill": 2},
            {"moral_dilemma": 2},
            {"moral_dilemma": 3, "uncomfortable": 2},
            {"moral_dilemma": 4, "uncomfortable": 3, "dark_drama": 1},
        ]),
    },
    {
        "id": "q09",
        "text": "Сердце сейчас просит света и надежды?",
        "answers": _answers([
            {"dark_drama": 3, "melancholic": 2},
            {"inspiring": 2, "hopeful": 1},
            {"hopeful": 3, "inspiring": 2},
            {"hopeful": 4, "inspiring": 3, "romantic": 1},
        ]),
    },
    {
        "id": "q10",
        "text": "Нужна ли романтическая нота, а не только концепт?",
        "answers": _answers([
            {"action": 2, "thriller": 2},
            {"atmospheric": 2, "melancholic": 1},
            {"romantic": 3, "melancholic": 1},
            {"romantic": 4, "heartbreaking": 2, "hopeful": 1},
        ]),
    },
    {
        "id": "q11",
        "text": "Насколько тебя тянет к странному и не очень удобному кино?",
        "answers": _answers([
            {"classic": 2, "hopeful": 1},
            {"weird": 2, "atmospheric": 1},
            {"weird": 3, "uncomfortable": 2},
            {"weird": 4, "uncomfortable": 2, "vibe_30583a1ac107": 1},
        ]),
    },
    {
        "id": "q12",
        "text": "Насколько тебе нужен фильм, после которого захочется подумать?",
        "answers": _answers([
            {"comedy": 2, "action": 1},
            {"philosophical": 2},
            {"philosophical": 3, "moral_dilemma": 2},
            {"philosophical": 4, "moral_dilemma": 2, "mind_bending": 1},
        ]),
    },
    {
        "id": "q13",
        "text": "Нужен ли нерв и напряжение без пауз на раскачку?",
        "answers": _answers([
            {"chill": 3, "romantic": 1},
            {"thriller": 2},
            {"thriller": 3, "realistic_thriller": 2},
            {"thriller": 4, "realistic_thriller": 3, "action": 1},
        ]),
    },
    {
        "id": "q14",
        "text": "Хочется ли узнаваемого и проверенного, а не эксперимента?",
        "answers": _answers([
            {"weird": 2, "mind_bending": 1},
            {"classic": 2},
            {"classic": 3, "nostalgic": 2},
            {"classic": 4, "nostalgic": 2, "mr600_choice": 1},
        ]),
    },
    {
        "id": "q15",
        "text": "Нужен ли сейчас импульс роста, преодоления и подъёма?",
        "answers": _answers([
            {"dark_drama": 2, "melancholic": 1},
            {"inspiring": 2},
            {"inspiring": 3, "sad_motivation": 2},
            {"inspiring": 4, "sad_motivation": 3, "hopeful": 1},
        ]),
    },
    {
        "id": "q16",
        "text": "Насколько тебе ок, если фильм будет больным и печальным?",
        "answers": _answers([
            {"comedy": 2, "hopeful": 1},
            {"melancholic": 2},
            {"melancholic": 3, "heartbreaking": 2},
            {"heartbreaking": 4, "melancholic": 3, "vibe_9374ea3ab146": 1},
        ]),
    },
    {
        "id": "q17",
        "text": "Документальная шероховатость и реальность сейчас скорее плюс?",
        "answers": _answers([
            {"mind_bending": 2, "weird": 1},
            {"documentary": 2},
            {"documentary": 3, "realistic_thriller": 2},
            {"documentary": 4, "realistic_thriller": 2, "ru_voice": 1},
        ]),
    },
    {
        "id": "q18",
        "text": "Насколько тебе сейчас заходит цинизм и чёрный юмор?",
        "answers": _answers([
            {"hopeful": 2, "romantic": 1},
            {"black_comedy": 2},
            {"black_comedy": 3, "moral_dilemma": 1},
            {"black_comedy": 4, "moral_dilemma": 2, "weird": 1},
        ]),
    },
    {
        "id": "q19",
        "text": "Хочется ли фильма-зеркала, а не фильма-побега?",
        "answers": _answers([
            {"action": 2, "comedy": 1},
            {"atmospheric": 2, "lonely": 1},
            {"lonely": 3, "philosophical": 2},
            {"lonely": 4, "philosophical": 2, "melancholic": 2},
        ]),
    },
    {
        "id": "q20",
        "text": "Насколько ты сегодня готов быть на нервах?",
        "answers": _answers([
            {"chill": 3, "comedy": 2},
            {"atmospheric": 2, "thriller": 1},
            {"thriller": 3, "realistic_thriller": 2},
            {"thriller": 4, "realistic_thriller": 3, "uncomfortable": 1},
        ]),
    },
    {
        "id": "q21",
        "text": "Ностальгия сейчас может сработать лучше нового и острого?",
        "answers": _answers([
            {"weird": 2, "action": 1},
            {"nostalgic": 2},
            {"nostalgic": 3, "classic": 2},
            {"nostalgic": 4, "classic": 2, "hopeful": 1},
        ]),
    },
    {
        "id": "q22",
        "text": "Моральная дилемма для тебя сейчас вкуснее простого сюжета?",
        "answers": _answers([
            {"comedy": 2, "chill": 1},
            {"moral_dilemma": 2},
            {"moral_dilemma": 3, "philosophical": 2},
            {"moral_dilemma": 4, "philosophical": 2, "realistic_thriller": 1},
        ]),
    },
    {
        "id": "q23",
        "text": "Насколько тебе важна густая атмосфера и послевкусие кадра?",
        "answers": _answers([
            {"action": 2, "thriller": 1},
            {"atmospheric": 2},
            {"atmospheric": 3, "melancholic": 1},
            {"atmospheric": 4, "melancholic": 2, "vibe_d6bb72e0c67b": 1},
        ]),
    },
    {
        "id": "q24",
        "text": "Тянет ли тебя к истории, где из боли рождается движение вперёд?",
        "answers": _answers([
            {"comedy": 2, "action": 1},
            {"sad_motivation": 2},
            {"sad_motivation": 3, "inspiring": 2},
            {"sad_motivation": 4, "inspiring": 2, "hopeful": 1},
        ]),
    },
    {
        "id": "q25",
        "text": "Ощущение «что-то не так» сейчас скорее манит, чем раздражает?",
        "answers": _answers([
            {"hopeful": 2, "classic": 1},
            {"uncomfortable": 2, "thriller": 1},
            {"uncomfortable": 3, "mind_bending": 2},
            {"uncomfortable": 4, "mind_bending": 2, "vibe_d7577e6e46be": 1},
        ]),
    },
    {
        "id": "q26",
        "text": "Искренность и тепло сейчас важнее цинизма и панциря?",
        "answers": _answers([
            {"black_comedy": 3, "dark_drama": 1},
            {"philosophical": 1, "melancholic": 1},
            {"hopeful": 2, "romantic": 1},
            {"hopeful": 4, "romantic": 2, "inspiring": 1},
        ]),
    },
    {
        "id": "q27",
        "text": "Нужен ли фильм, который можно потом долго обсасывать в голове?",
        "answers": _answers([
            {"action": 1, "comedy": 1, "chill": 1},
            {"philosophical": 2, "atmospheric": 1},
            {"philosophical": 3, "mind_bending": 1},
            {"philosophical": 4, "mind_bending": 3, "mr600_choice": 1},
        ]),
    },
    {
        "id": "q28",
        "text": "Хочется ли фильма, который встряхнёт, а не убаюкает?",
        "answers": _answers([
            {"chill": 3, "romantic": 1},
            {"heartbreaking": 2, "melancholic": 1},
            {"thriller": 3, "action": 2},
            {"thriller": 4, "action": 2, "uncomfortable": 1},
        ]),
    },
    {
        "id": "q29",
        "text": "Нужен ли сейчас фильм с чётким авторским «я», а не нейтральная история?",
        "answers": _answers([
            {"action": 1, "classic": 1},
            {"mr600_choice": 2, "atmospheric": 1},
            {"mr600_choice": 3, "philosophical": 1},
            {"mr600_choice": 4, "philosophical": 2, "weird": 1},
        ]),
    },
    {
        "id": "q30",
        "text": "Насколько тебе заходит точечный микро-вайб вместо общего жанра?",
        "answers": _answers([
            {"classic": 2, "hopeful": 1},
            {"vibe_b56620b6437b": 1, "vibe_40c54e51e2ba": 1, "vibe_d2ab183d1db7": 1},
            {"vibe_30583a1ac107": 2, "vibe_b0e6144db061": 2, "vibe_58e157639b9f": 2},
            {"vibe_d6bb72e0c67b": 2, "vibe_0029a3aef271": 2, "vibe_9374ea3ab146": 2},
        ]),
    },
    {
        "id": "q31",
        "text": "Насколько тебе сейчас нужна русская интонация и земля под ногами?",
        "answers": _answers([
            {"weird": 1, "mind_bending": 1},
            {"ru_voice": 2, "realistic_thriller": 1},
            {"ru_voice": 3, "realistic_thriller": 2, "dark_drama": 1},
            {"ru_voice": 4, "realistic_thriller": 2, "moral_dilemma": 1},
        ]),
    },
    {
        "id": "q32",
        "text": "Тема свободы против системы сейчас тебе близка?",
        "answers": _answers([
            {"romantic": 1, "chill": 1},
            {"moral_dilemma": 2, "philosophical": 1},
            {"vibe_58e157639b9f": 3, "action": 2, "moral_dilemma": 1},
            {"vibe_0029a3aef271": 3, "vibe_58e157639b9f": 3, "moral_dilemma": 2},
        ]),
    },
    {
        "id": "q33",
        "text": "Хочется ли семейного нерва и тяжёлой темы родителей / детей?",
        "answers": _answers([
            {"action": 1, "thriller": 1},
            {"heartbreaking": 2, "melancholic": 1},
            {"vibe_b56620b6437b": 3, "heartbreaking": 2},
            {"vibe_b56620b6437b": 4, "heartbreaking": 2, "hopeful": 1},
        ]),
    },
    {
        "id": "q34",
        "text": "Нужно ли тебе что-то праздничное, детское или очень светлое по теплу?",
        "answers": _answers([
            {"dark_drama": 2, "uncomfortable": 1},
            {"nostalgic": 2, "hopeful": 1},
            {"vibe_40c54e51e2ba": 3, "nostalgic": 2, "classic": 1},
            {"vibe_40c54e51e2ba": 4, "hopeful": 3, "nostalgic": 2},
        ]),
    },
    {
        "id": "q35",
        "text": "Манит ли тебя сейчас мрачная сказка, миф или тревожная притча?",
        "answers": _answers([
            {"comedy": 1, "classic": 1},
            {"atmospheric": 2, "weird": 1},
            {"vibe_d6bb72e0c67b": 3, "uncomfortable": 2, "atmospheric": 1},
            {"vibe_d6bb72e0c67b": 4, "uncomfortable": 2, "philosophical": 1},
        ]),
    },
    {
        "id": "q36",
        "text": "Хочется ли жёсткого русского реализма без смягчения углов?",
        "answers": _answers([
            {"hopeful": 2, "romantic": 1},
            {"ru_voice": 2, "documentary": 1},
            {"ru_voice": 3, "realistic_thriller": 2, "documentary": 1},
            {"ru_voice": 4, "realistic_thriller": 3, "dark_drama": 2},
        ]),
    },
]

MOVIE_BASE_QUESTIONS = MOVIE_PERSONAL_QUESTIONS.copy()

MOVIE_PRECISION_QUESTIONS = [
    {
        "id": "q37",
        "text": "Тебе сейчас ближе большой путь героя и чувство, что мир всё ещё можно спасти?",
        "answers": _answers([
            {"realistic_thriller": 2, "dark_drama": 1},
            {"hopeful": 2, "classic": 1},
            {"hopeful": 3, "inspiring": 2, "action": 1},
            {"hopeful": 4, "inspiring": 3, "classic": 2, "mr600_choice": 1},
        ]),
    },
    {
        "id": "q38",
        "text": "Нужна история про человека, который идёт против правил, системы или клетки вокруг себя?",
        "answers": _answers([
            {"chill": 2, "romantic": 1},
            {"moral_dilemma": 2, "philosophical": 1},
            {"moral_dilemma": 3, "action": 2, "vibe_58e157639b9f": 1},
            {"vibe_58e157639b9f": 4, "vibe_0029a3aef271": 2, "moral_dilemma": 2},
        ]),
    },
    {
        "id": "q39",
        "text": "Хочется кино про одиночество, где человек вроде среди людей, но всё равно отдельно?",
        "answers": _answers([
            {"comedy": 2, "action": 1},
            {"lonely": 2, "melancholic": 1},
            {"lonely": 3, "romantic": 1, "philosophical": 1},
            {"lonely": 4, "melancholic": 3, "heartbreaking": 2},
        ]),
    },
    {
        "id": "q40",
        "text": "Тянет к фильму, где любовь странная, невозможная или вообще не совсем человеческая?",
        "answers": _answers([
            {"action": 2, "thriller": 1},
            {"romantic": 2, "weird": 1},
            {"romantic": 3, "lonely": 2, "melancholic": 1},
            {"romantic": 4, "lonely": 2, "vibe_659c99e503c2": 2, "mind_bending": 1},
        ]),
    },
    {
        "id": "q41",
        "text": "Нужен холодный, почти детективный нерв, где правда собирается по кускам?",
        "answers": _answers([
            {"chill": 2, "hopeful": 1},
            {"thriller": 2, "realistic_thriller": 1},
            {"realistic_thriller": 3, "mind_bending": 2},
            {"realistic_thriller": 4, "thriller": 3, "documentary": 1},
        ]),
    },
    {
        "id": "q42",
        "text": "Хочется, чтобы фильм был красивым, но красота в нём немного пугала?",
        "answers": _answers([
            {"comedy": 2, "hopeful": 1},
            {"atmospheric": 2, "weird": 1},
            {"atmospheric": 3, "uncomfortable": 2},
            {"atmospheric": 4, "uncomfortable": 3, "vibe_d6bb72e0c67b": 1},
        ]),
    },
    {
        "id": "q43",
        "text": "Тебе сейчас подходит история про отцов, детей, семью и тяжёлое наследство?",
        "answers": _answers([
            {"action": 2, "black_comedy": 1},
            {"melancholic": 2, "nostalgic": 1},
            {"vibe_b56620b6437b": 3, "heartbreaking": 2},
            {"vibe_b56620b6437b": 4, "heartbreaking": 3, "moral_dilemma": 1},
        ]),
    },
    {
        "id": "q44",
        "text": "Нужна история про талант, одержимость, успех и цену, которую за это платят?",
        "answers": _answers([
            {"chill": 2, "hopeful": 1},
            {"inspiring": 2, "moral_dilemma": 1},
            {"inspiring": 3, "thriller": 2, "philosophical": 1},
            {"inspiring": 4, "thriller": 3, "moral_dilemma": 2},
        ]),
    },
    {
        "id": "q45",
        "text": "Хочется криминального драйва: грязные сделки, опасные люди, нерв и стиль?",
        "answers": _answers([
            {"romantic": 2, "hopeful": 1},
            {"action": 2, "black_comedy": 1},
            {"action": 3, "thriller": 2, "classic": 1},
            {"action": 4, "black_comedy": 3, "moral_dilemma": 1},
        ]),
    },
    {
        "id": "q46",
        "text": "Тянет к фильму, где юмор грубый, неудобный и немного переходит границы?",
        "answers": _answers([
            {"hopeful": 2, "romantic": 1},
            {"comedy": 2, "weird": 1},
            {"black_comedy": 3, "uncomfortable": 1},
            {"black_comedy": 4, "comedy": 2, "weird": 2, "uncomfortable": 1},
        ]),
    },
    {
        "id": "q47",
        "text": "Нужен фильм, где мир рушится, но внутри всё ещё есть маленький шанс на надежду?",
        "answers": _answers([
            {"comedy": 2, "chill": 1},
            {"dark_drama": 2, "hopeful": 1},
            {"hopeful": 3, "thriller": 2, "moral_dilemma": 1},
            {"hopeful": 4, "dark_drama": 3, "action": 2, "heartbreaking": 1},
        ]),
    },
    {
        "id": "q48",
        "text": "Тебе хочется фильма, где герой морально неприятен, но оторваться невозможно?",
        "answers": _answers([
            {"chill": 2, "hopeful": 1},
            {"moral_dilemma": 2, "black_comedy": 1},
            {"moral_dilemma": 3, "uncomfortable": 2},
            {"moral_dilemma": 4, "uncomfortable": 3, "dark_drama": 2},
        ]),
    },
    {
        "id": "q49",
        "text": "Хочется магии, приключения или сказочного масштаба, но без ощущения пустой аттракционности?",
        "answers": _answers([
            {"realistic_thriller": 2, "documentary": 1},
            {"nostalgic": 2, "classic": 1},
            {"nostalgic": 3, "hopeful": 2, "action": 1},
            {"vibe_324b9e887369": 3, "vibe_40c54e51e2ba": 3, "classic": 2},
        ]),
    },
    {
        "id": "q50",
        "text": "Хочется, чтобы фильм не объяснял всё напрямую, а оставлял странный след?",
        "answers": _answers([
            {"comedy": 2, "action": 1},
            {"weird": 2, "atmospheric": 1},
            {"mind_bending": 3, "weird": 2},
            {"mind_bending": 4, "weird": 3, "vibe_30583a1ac107": 2},
        ]),
    },
    {
        "id": "q51",
        "text": "Нужна тёплая человеческая история, где боль не отменяет свет?",
        "answers": _answers([
            {"thriller": 2, "uncomfortable": 1},
            {"hopeful": 2, "melancholic": 1},
            {"hopeful": 3, "heartbreaking": 1, "romantic": 1},
            {"hopeful": 4, "heartbreaking": 2, "inspiring": 2, "sad_motivation": 1},
        ]),
    },
    {
        "id": "q52",
        "text": "Тебе сейчас ближе русская безысходность, где правда звучит без украшений?",
        "answers": _answers([
            {"comedy": 2, "hopeful": 1},
            {"ru_voice": 2, "melancholic": 1},
            {"ru_voice": 3, "realistic_thriller": 2, "moral_dilemma": 1},
            {"ru_voice": 4, "realistic_thriller": 3, "dark_drama": 2, "vibe_d7577e6e46be": 1},
        ]),
    },
]

MOVIE_PERSONAL_QUESTIONS.extend(MOVIE_PRECISION_QUESTIONS)

QUESTION_BY_ID = {question["id"]: question for question in MOVIE_PERSONAL_QUESTIONS}

TAG_EXPLANATIONS = {
    "action": [
        "тебе нужен драйв, а не медленное раскачивание",
        "сейчас хочется энергии и движения",
    ],
    "atmospheric": [
        "тебе важна густая атмосфера",
        "сейчас цепляет именно дыхание кадра и настроение",
    ],
    "black_comedy": [
        "тебе заходит юмор с ядом",
        "сейчас нужен смех, но не слишком безопасный",
    ],
    "chill": [
        "тебе нужен мягкий режим",
        "сейчас лучше сработает более спокойное и дышащее кино",
    ],
    "classic": [
        "тебя тянет к проверенным историям",
        "сейчас хочется чего-то надёжного и вечного",
    ],
    "comedy": [
        "хочется разрядиться и выдохнуть",
        "сегодня юмор тебе явно не помешает",
    ],
    "dark_drama": [
        "тянет в более тёмную и серьёзную сторону",
        "сейчас ты нормально выдерживаешь тяжесть",
    ],
    "heartbreaking": [
        "ты не против, если фильм заденет по-настоящему",
        "сейчас тебя не пугает эмоциональный удар",
    ],
    "hopeful": [
        "внутри есть запрос на свет",
        "тебе явно не хочется уходить в полную тьму",
    ],
    "inspiring": [
        "хочется почувствовать внутренний импульс",
        "сейчас нужна история, которая поднимает",
    ],
    "lonely": [
        "в ответах чувствуется немного одиночества",
        "сегодня тебе ближе более личная интонация",
    ],
    "melancholic": [
        "тебе подходит тихая меланхолия",
        "в этом состоянии лучше работает лёгкая грусть",
    ],
    "mind_bending": [
        "хочется, чтобы фильм остался в голове и чуть повёл почву",
        "тебе сейчас интереснее история с ментальным сдвигом",
    ],
    "moral_dilemma": [
        "тебе интересны сложные выборы без простых ответов",
        "тебя сейчас цепляют истории, где мораль начинает шататься",
    ],
    "nostalgic": [
        "похоже, хочется знакомого тепла",
        "сейчас ностальгия ляжет особенно хорошо",
    ],
    "philosophical": [
        "тебе нужен не только сюжет, но и внутренний отклик",
        "сейчас хочется не просто смотреть, а думать",
    ],
    "realistic_thriller": [
        "подходит напряжение без сильного отрыва от реальности",
        "сейчас лучше работает приземлённая тревога",
    ],
    "romantic": [
        "в подборе явно просится сердечная нота",
        "сейчас тебе заходит более чувственный вайб",
    ],
    "ru_voice": [
        "тебе может особенно точно лечь русская интонация и местная шероховатость",
        "сейчас язык, среда и культурный нерв для тебя не фон, а часть попадания",
    ],
    "sad_motivation": [
        "тебе может откликнуться история, где боль двигает вперёд",
        "сейчас особенно хорошо ложится грустная мотивация вместо бодрой плакатности",
    ],
    "thriller": [
        "тебе нужен нерв",
        "сегодня без напряжения будет слишком пресно",
    ],
    "uncomfortable": [
        "ты не против, если фильм будет немного неудобным",
        "тебя не отпугивает тревожная вязкость и острые углы",
    ],
    "weird": [
        "тебе можно предложить что-то со странностью",
        "сейчас хочется не самого очевидного выбора",
    ],
    "mr600_choice": [
        "сейчас тебе подходит не случайный тайтл, а вещь с авторским вкусом и весом",
        "в ответах чувствуется запрос на более точечный и выверенный выбор",
    ],
    "documentary": [
        "тебе может зайти документальная шероховатость и ощущение правды",
        "сейчас реальность важнее глянцевого эскапизма",
    ],
    "vibe_30583a1ac107": [
        "в ответах чувствуется тяга к состоянию «что чёрт подери происходит...»",
    ],
    "vibe_b0e6144db061": [
        "тебе может откликнуться история про близость и внезапный уход без объяснений",
    ],
    "vibe_569903b64556": [
        "сейчас хорошо ложится жестокая тишина без лишнего шума",
    ],
    "vibe_b56620b6437b": [
        "тебя может зацепить тема отцов и детей с тяжёлым послевкусием",
    ],
    "vibe_659c99e503c2": [
        "внутри чувствуется поиск себя и своего имени",
    ],
    "vibe_40c54e51e2ba": [
        "сейчас может неожиданно точно лечь праздничное и детское тепло",
    ],
    "vibe_58e157639b9f": [
        "тебя может зарядить история про свободу, которую берут сами",
    ],
    "vibe_d2ab183d1db7": [
        "есть явный запрос на скорость и резкий моторный импульс",
    ],
    "vibe_d6bb72e0c67b": [
        "тебя может зацепить сказка с обратной стороны, где красота тревожит",
    ],
    "vibe_0029a3aef271": [
        "в ответах чувствуется тема системы, которая сильнее человека",
    ],
    "vibe_48afe724ecb5": [
        "тебе сейчас подходит более холодный и распадающийся тон",
    ],
    "vibe_d7577e6e46be": [
        "тебя может зацепить жёсткая правда, которую врубают без смягчения",
    ],
    "vibe_324b9e887369": [
        "внутри есть запрос на приключение и дух абордажа",
    ],
    "vibe_72d26688b1bf": [
        "тебе может понравиться история про фокус, иллюзию и контроль внимания",
    ],
    "vibe_9374ea3ab146": [
        "сейчас тебе может лечь история, где боль становится топливом",
    ],
}

EXPLANATION_OPENERS = [
    "Я собрал твой вайб как довольно точную смесь.",
    "По ответам вырисовалось не случайное, а очень читаемое состояние.",
    "Твой набор ответов сложился в довольно конкретный кинематографический запрос.",
    "Здесь чувствуется не настроение наобум, а вполне считываемая внутренняя настройка.",
]

EXPLANATION_CLOSERS = [
    "Поэтому этот фильм должен лечь особенно метко.",
    "Так что именно он сейчас выглядит самым естественным попаданием.",
    "Из доступных вариантов именно он лучше всего держит этот баланс.",
    "Поэтому выбор получился не общий, а именно твой.",
]


def pick_random_questions(count: int = QUESTION_COUNT) -> list[dict]:
    if count <= 0:
        return []

    if count == 1:
        return random.sample(MOVIE_PERSONAL_QUESTIONS, k=1)

    precision_count = min(len(MOVIE_PRECISION_QUESTIONS), max(1, count // 2))
    base_count = min(len(MOVIE_BASE_QUESTIONS), count - precision_count)

    questions = []
    questions.extend(random.sample(MOVIE_BASE_QUESTIONS, k=base_count))
    questions.extend(random.sample(MOVIE_PRECISION_QUESTIONS, k=precision_count))

    if len(questions) < count:
        used_ids = {question["id"] for question in questions}
        remaining = [
            question
            for question in MOVIE_PERSONAL_QUESTIONS
            if question["id"] not in used_ids
        ]
        questions.extend(random.sample(remaining, k=min(count - len(questions), len(remaining))))

    random.shuffle(questions)
    return questions


def get_question(question_id: str) -> dict:
    return QUESTION_BY_ID[question_id]


def accumulate_answer_weights(answer_history: list[dict]) -> dict[str, float]:
    weights: dict[str, float] = defaultdict(float)

    for answer in answer_history:
        answer_data = get_question(answer["question_id"])["answers"][answer["answer_index"]]
        for tag, value in answer_data["weights"].items():
            if value:
                weights[tag] += value

    return dict(weights)


def build_preference_profile(user_id: int) -> tuple[dict[str, float], dict[str, float], set[str]]:
    movies = load_movies(include_premium_collection_only=False)
    by_title = {movie["title"]: movie for movie in movies}

    favorite_titles = {title for (title,) in get_user_favorites(user_id, "movie")}
    liked_titles = set(get_user_rated_content(user_id, "movie", value=1))
    disliked_titles = set(get_user_rated_content(user_id, "movie", value=-1))

    positive_weights: dict[str, float] = defaultdict(float)
    negative_weights: dict[str, float] = defaultdict(float)

    for title in favorite_titles:
        movie = by_title.get(title)
        if movie:
            for tag in movie.get("tags", []):
                positive_weights[tag] += 1.8

    for title in liked_titles:
        movie = by_title.get(title)
        if movie:
            for tag in movie.get("tags", []):
                positive_weights[tag] += 1.2

    for title in disliked_titles:
        movie = by_title.get(title)
        if movie:
            for tag in movie.get("tags", []):
                negative_weights[tag] += 1.3

    return (
        dict(positive_weights),
        dict(negative_weights),
        disliked_titles | favorite_titles | liked_titles,
    )


def tag_priority_bonus(tag: str) -> float:
    count = MOVIE_TAG_FREQUENCY.get(tag, 0)

    if count <= 1:
        return 0.55
    if count <= 2:
        return 0.42
    if count <= 4:
        return 0.28
    if count <= 7:
        return 0.14
    return 0.0


def score_movie(
    movie: dict,
    answer_weights: dict[str, float],
    positive_profile: dict[str, float],
    negative_profile: dict[str, float],
) -> tuple[float, list[tuple[str, float]]]:
    tag_scores: list[tuple[str, float]] = []
    score = 0.0

    for tag in movie.get("tags", []):
        answer_signal = answer_weights.get(tag, 0.0)
        profile_signal = positive_profile.get(tag, 0.0) * 0.8
        negative_signal = negative_profile.get(tag, 0.0) * 0.9

        tag_score = answer_signal + profile_signal - negative_signal

        if answer_signal > 0:
            tag_score += tag_priority_bonus(tag) * min(1.0, answer_signal / 3)

        if tag == "mr600_choice":
            tag_score += 0.22
        if tag == "ru_voice":
            tag_score += 0.16
        if tag.startswith("vibe_") and answer_signal > 0:
            tag_score += 0.12

        if tag_score:
            tag_scores.append((tag, tag_score))
            score += tag_score

    score += random.uniform(0, 0.25)
    tag_scores.sort(key=lambda item: item[1], reverse=True)
    return score, tag_scores


def fallback_tag_explanation(tag: str) -> str | None:
    label = MOVIE_PUBLIC_VIBES.get(tag)
    if not label:
        return None
    return f"тебя явно тянет в вайб «{label}»"


def build_explanation(movie: dict, tag_scores: list[tuple[str, float]]) -> str:
    top_tags = [tag for tag, score in tag_scores if score > 0][:3]
    fragments = []

    for tag in top_tags:
        options = TAG_EXPLANATIONS.get(tag)
        if options:
            fragments.append(random.choice(options))
            continue

        fallback = fallback_tag_explanation(tag)
        if fallback:
            fragments.append(fallback)

    if not fragments:
        fragments.append(
            "в твоих ответах чувствуется запрос на точное настроение, а не просто на случайный фильм"
        )

    opener = random.choice(EXPLANATION_OPENERS)
    closer = random.choice(EXPLANATION_CLOSERS)

    if len(fragments) == 1:
        middle = fragments[0]
    elif len(fragments) == 2:
        middle = f"{fragments[0]}, и одновременно {fragments[1]}"
    else:
        middle = f"{fragments[0]}, {fragments[1]} и {fragments[2]}"

    return f"✨ <b><i>{opener} Похоже, {middle}. {closer}</i></b>"


def recommend_movies(
    user_id: int,
    answer_history: list[dict],
    excluded_titles: set[str] | None = None,
) -> list[dict]:
    movies = load_movies(include_premium_collection_only=False)
    answer_weights = accumulate_answer_weights(answer_history)
    positive_profile, negative_profile, blocked_titles = build_preference_profile(user_id)
    blocked_titles |= excluded_titles or set()
    blocked_titles |= get_recently_seen_titles(user_id, "movie")

    scored_movies = []
    fallback_movies = []

    for movie in movies:
        if movie["title"] in blocked_titles:
            continue

        score, tag_scores = score_movie(
            movie,
            answer_weights,
            positive_profile,
            negative_profile,
        )
        fallback_movies.append((score, tag_scores, movie))

        if score > 0:
            scored_movies.append((score, tag_scores, movie))

    candidates = scored_movies or fallback_movies
    candidates.sort(key=lambda item: item[0], reverse=True)

    return [
        {
            "movie": movie,
            "score": score,
            "explanation": build_explanation(movie, tag_scores),
        }
        for score, tag_scores, movie in candidates[:5]
    ]
