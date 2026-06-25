import requests
from typing import List, Optional


TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"


class TMDBFetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.params = {"api_key": api_key}

    def _get(self, path: str, **params) -> dict:
        resp = self.session.get(f"{TMDB_BASE}{path}", params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_now_playing(self, region: str = "IN") -> List[dict]:
        movies = []
        for page in range(1, 4):
            data = self._get("/movie/now_playing", region=region, page=page)
            movies.extend(data.get("results", []))
            if page >= data.get("total_pages", 1):
                break
        return movies

    def get_movie_details(self, tmdb_id: int) -> dict:
        return self._get(
            f"/movie/{tmdb_id}",
            append_to_response="credits,videos,external_ids",
        )

    def get_director_filmography(self, person_id: int, exclude_id: int) -> List[str]:
        data = self._get(f"/person/{person_id}/movie_credits")
        crew_movies = data.get("crew", [])
        directed = [
            m for m in crew_movies
            if m.get("job") == "Director" and m.get("id") != exclude_id
            and m.get("vote_count", 0) > 100
        ]
        directed.sort(key=lambda m: m.get("vote_count", 0), reverse=True)
        return [m["title"] for m in directed[:3]]

    def extract_director(self, details: dict) -> tuple[str, int]:
        for member in details.get("credits", {}).get("crew", []):
            if member.get("job") == "Director":
                return member["name"], member["id"]
        return "Unknown", 0

    def extract_lead_cast(self, details: dict) -> List[str]:
        cast = details.get("credits", {}).get("cast", [])
        return [m["name"] for m in cast[:3]]

    def extract_trailer_url(self, details: dict) -> Optional[str]:
        for video in details.get("videos", {}).get("results", []):
            if video.get("type") == "Trailer" and video.get("site") == "YouTube":
                return f"https://youtu.be/{video['key']}"
        return None

    def extract_poster_url(self, details: dict) -> Optional[str]:
        path = details.get("poster_path")
        return f"{TMDB_IMAGE_BASE}{path}" if path else None
