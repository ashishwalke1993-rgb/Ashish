import json
import os
from datetime import date, timedelta
from typing import List

SENT_CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "sent_movies.json")


def _load_sent() -> dict:
    """Load {tmdb_id: date_sent} cache from disk."""
    try:
        with open(SENT_CACHE_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_sent(cache: dict) -> None:
    with open(SENT_CACHE_FILE, "w") as f:
        json.dump(cache, f)


def _purge_old(cache: dict, keep_days: int = 30) -> dict:
    """Remove entries older than keep_days to keep the file small."""
    cutoff = str(date.today() - timedelta(days=keep_days))
    return {k: v for k, v in cache.items() if v >= cutoff}


class MovieFilter:
    def filter_recent(
        self,
        movies: List[dict],
        days_lookback: int = 14,
        max_movies: int = 5,
    ) -> List[dict]:
        today = date.today()
        cutoff = today - timedelta(days=days_lookback)

        # Load previously sent movies
        sent_cache = _load_sent()
        sent_cache = _purge_old(sent_cache)

        seen_ids = set()
        filtered = []
        for movie in movies:
            tmdb_id = str(movie.get("id", ""))
            release_str = movie.get("release_date", "")
            if not release_str or tmdb_id in seen_ids:
                continue
            try:
                release = date.fromisoformat(release_str)
            except ValueError:
                continue

            # Only include movies within lookback window
            if not (cutoff <= release <= today):
                continue

            # Skip movies already sent before
            if tmdb_id in sent_cache:
                continue

            filtered.append(movie)
            seen_ids.add(tmdb_id)

        filtered.sort(key=lambda m: m.get("release_date", ""), reverse=True)
        result = filtered[:max_movies]

        # Mark these movies as sent today
        today_str = str(today)
        for movie in result:
            sent_cache[str(movie.get("id", ""))] = today_str
        _save_sent(sent_cache)

        return result
