import json
import random
from pathlib import Path

MOVIES_PATH = Path(__file__).parent / "movies.json"


def load_movies(include_premium_collection_only: bool = True):
    with open(MOVIES_PATH, "r", encoding="utf-8") as f:
        movies = json.load(f)

    if include_premium_collection_only:
        return movies

    return [
        movie for movie in movies
        if not movie.get("premium_collection_only", False)
    ]


def get_random_movie(vibe: str | None = None, excluded_titles: set[str] | None = None):
    movies = load_movies(include_premium_collection_only=False)
    excluded_titles = excluded_titles or set()

    if vibe:
        matching = [movie for movie in movies if vibe in movie.get("tags", [])]
        if not matching:
            return None

        available_matching = [
            movie for movie in matching
            if movie["title"] not in excluded_titles
        ]
        return random.choice(available_matching) if available_matching else None

    available_movies = [movie for movie in movies if movie["title"] not in excluded_titles]
    source = available_movies or movies

    return random.choice(source) if source else None
