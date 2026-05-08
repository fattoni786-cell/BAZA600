import json
import random
from pathlib import Path
from typing import Optional, Dict, Any, List

DATA_PATH = Path("data/movies.json")


# =========================
# 🎬 ЗАГРУЗКА ФИЛЬМОВ
# =========================
def load_movies() -> List[Dict[str, Any]]:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# =========================
# 🎲 СЛУЧАЙНЫЙ ФИЛЬМ
# =========================
def get_random_movie(vibe: Optional[str] = None) -> Dict[str, Any]:
    """
    Возвращает случайный фильм.
    Если передан vibe — фильтрует по тегам.
    """
    movies = load_movies()

    if not movies:
        raise ValueError("Movies database is empty")

    if vibe:
        filtered = [
            m for m in movies
            if vibe in m.get("tags", [])
        ]
        if filtered:
            return random.choice(filtered)

    return random.choice(movies)
