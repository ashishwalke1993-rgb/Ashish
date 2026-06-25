from datetime import date, timedelta
from typing import List


class MovieFilter:
    def filter_recent(
        self,
        movies: List[dict],
        days_lookback: int = 7,
        max_movies: int = 5,
    ) -> List[dict]:
        today = date.today()
        cutoff = today - timedelta(days=days_lookback)

        seen_ids = set()
        filtered = []
        for movie in movies:
            tmdb_id = movie.get("id")
            release_str = movie.get("release_date", "")
            if not release_str or tmdb_id in seen_ids:
                continue
            try:
                release = date.fromisoformat(release_str)
            except ValueError:
                continue
            if cutoff <= release <= today:
                filtered.append(movie)
                seen_ids.add(tmdb_id)

        filtered.sort(key=lambda m: m.get("release_date", ""), reverse=True)
        return filtered[:max_movies]
