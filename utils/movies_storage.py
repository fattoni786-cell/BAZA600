import json
from pathlib import Path

MOVIES_PATH = Path("data/movies.json")


def load_movies():
    if not MOVIES_PATH.exists():
        return []
    with open(MOVIES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_movie(movie: dict):
    movies = load_movies()
    movies.append(movie)
    with open(MOVIES_PATH, "w", encoding="utf-8") as f:
        json.dump(movies, f, ensure_ascii=False, indent=2)
