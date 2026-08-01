import json
import os
from datetime import date, timedelta
from typing import List

SENT_CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "sent_movies.json")

# Days after release to send each review
FIRST_REVIEW_WINDOW = (1, 3)   # day 1–3 after release
SECOND_REVIEW_WINDOW = (4, 6)  # day 4–6 after release


def _load_sent() -> dict:
    try:
        with open(SENT_CACHE_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_sent(cache: dict) -> None:
    with open(SENT_CACHE_FILE, "w") as f:
        json.dump(cache, f)


def remove_from_sent(tmdb_id: str) -> None:
    """Remove a movie from the sent cache so it can be retried."""
    cache = _load_sent()
    cache.pop(str(tmdb_id), None)
    _save_sent(cache)


def _normalize_record(v) -> dict:
    """Migrate old string format {"id": "date"} → {"id": {"first": "date"}}."""
    if isinstance(v, str):
        return {"first": v}
    return v if isinstance(v, dict) else {}


def _purge_old(cache: dict, keep_days: int = 30) -> dict:
    cutoff = date.today() - timedelta(days=keep_days)
    result = {}
    for k, v in cache.items():
        record = _normalize_record(v)
        dates = []
        for d in record.values():
            try:
                dates.append(date.fromisoformat(d))
            except (ValueError, TypeError):
                pass
        if dates and max(dates) >= cutoff:
            result[k] = record
    return result


class MovieFilter:
    def filter_recent(
        self,
        movies: List[dict],
        days_lookback: int = 14,  # kept for API compatibility
        max_movies: int = 5,
    ) -> List[dict]:
        today = date.today()
        sent_cache = _load_sent()
        sent_cache = _purge_old(sent_cache)

        seen_ids = set()
        candidates = []

        for movie in movies:
            tmdb_id = str(movie.get("id", ""))
            release_str = movie.get("release_date", "")
            if not release_str or tmdb_id in seen_ids:
                continue
            try:
                release = date.fromisoformat(release_str)
            except ValueError:
                continue

            days_since = (today - release).days
            record = _normalize_record(sent_cache.get(tmdb_id, {}))

            lo1, hi1 = FIRST_REVIEW_WINDOW
            lo2, hi2 = SECOND_REVIEW_WINDOW

            if lo1 <= days_since <= hi1 and "first" not in record:
                candidates.append(movie)
                seen_ids.add(tmdb_id)
            elif lo2 <= days_since <= hi2 and "first" in record and "second" not in record:
                candidates.append(movie)
                seen_ids.add(tmdb_id)

        candidates.sort(key=lambda m: m.get("release_date", ""), reverse=True)
        result = candidates[:max_movies]

        today_str = str(today)
        for movie in result:
            tmdb_id = str(movie.get("id", ""))
            record = _normalize_record(sent_cache.get(tmdb_id, {}))
            days_since = (today - date.fromisoformat(movie["release_date"])).days
            lo1, hi1 = FIRST_REVIEW_WINDOW
            if lo1 <= days_since <= hi1:
                record["first"] = today_str
            else:
                record["second"] = today_str
            sent_cache[tmdb_id] = record

        _save_sent(sent_cache)
        return result
