import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from typing import Optional

from movie_bot.models.movie import MovieData
from movie_bot.fetchers.tmdb_fetcher import TMDBFetcher
from movie_bot.processors.sentiment import SentimentProcessor

logger = logging.getLogger(__name__)

LANGUAGE_MAP = {
    "hi": "Hindi", "en": "English", "ta": "Tamil", "te": "Telugu",
    "ml": "Malayalam", "kn": "Kannada", "mr": "Marathi", "bn": "Bengali",
}


class MovieEnricher:
    def __init__(
        self,
        tmdb: TMDBFetcher,
        sentiment: SentimentProcessor,
        reddit_fetcher=None,
    ):
        self.tmdb = tmdb
        self.sentiment = sentiment
        self.reddit = reddit_fetcher

    def enrich(self, raw_movie: dict) -> Optional[MovieData]:
        tmdb_id = raw_movie["id"]
        title = raw_movie.get("title", "Unknown")

        try:
            details = self.tmdb.get_movie_details(tmdb_id)
        except Exception as e:
            logger.error(f"Failed to fetch details for {title}: {e}")
            return None

        director, director_id = self.tmdb.extract_director(details)
        lead_cast = self.tmdb.extract_lead_cast(details)
        trailer_url = self.tmdb.extract_trailer_url(details)
        poster_url = self.tmdb.extract_poster_url(details)
        imdb_id = details.get("external_ids", {}).get("imdb_id")
        collection = details.get("belongs_to_collection")
        genres = [g["name"] for g in details.get("genres", [])]
        release_str = details.get("release_date", "")
        release_date = date.fromisoformat(release_str) if release_str else date.today()
        lang_code = details.get("original_language", "en")
        language = LANGUAGE_MAP.get(lang_code, lang_code.upper())

        director_works: list = []
        reddit_reviews: list = []
        imdb_reviews: list = []

        def fetch_director_works():
            if director_id:
                return self.tmdb.get_director_filmography(director_id, tmdb_id)
            return []

        def fetch_reddit():
            if self.reddit:
                return self.reddit.get_audience_reviews(title, release_date.year)
            return []

        def fetch_imdb():
            return self._get_imdb_reviews(imdb_id) if imdb_id else []

        tasks = {
            "director": fetch_director_works,
            "reddit": fetch_reddit,
            "imdb": fetch_imdb,
        }

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(fn): name for name, fn in tasks.items()}
            for future in as_completed(futures):
                name = futures[future]
                try:
                    result = future.result()
                    if name == "director":
                        director_works.extend(result)
                    elif name == "reddit":
                        reddit_reviews.extend(result)
                    elif name == "imdb":
                        imdb_reviews.extend(result)
                except Exception as e:
                    logger.warning(f"Fetch '{name}' failed for {title}: {e}")

        tmdb_score = details.get("vote_average", 0.0)
        imdb_score = self._get_imdb_score(imdb_id)

        verdict, theater_rec = self.sentiment.compute_verdict(
            reddit_reviews, imdb_reviews, tmdb_score, imdb_score, genres
        )

        return MovieData(
            tmdb_id=tmdb_id,
            title=title,
            original_title=details.get("original_title", title),
            release_date=release_date,
            language=language,
            runtime=details.get("runtime", 0),
            genres=genres,
            overview=details.get("overview", ""),
            director=director,
            director_id=director_id,
            director_previous_works=director_works,
            lead_cast=lead_cast,
            tmdb_score=round(tmdb_score, 1),
            imdb_id=imdb_id,
            imdb_score=imdb_score,
            reddit_reviews=reddit_reviews[:5],
            imdb_user_reviews=imdb_reviews[:5],
            verdict=verdict,
            theater_recommendation=theater_rec,
            trailer_url=trailer_url,
            poster_url=poster_url,
            is_sequel=bool(collection),
            belongs_to_collection=collection.get("name") if collection else None,
            budget=details.get("budget") or None,
            box_office=details.get("revenue") or None,
        )

    def _get_imdb_reviews(self, imdb_id: str) -> list:
        try:
            from imdb import Cinemagoer
            ia = Cinemagoer()
            numeric_id = imdb_id.lstrip("tt")
            movie = ia.get_movie(numeric_id, info=["reviews"])
            reviews = movie.get("reviews", [])
            snippets = []
            for r in reviews[:5]:
                text = r.get("content", "")
                rating = r.get("rating")
                if rating and int(rating) < 5:
                    continue
                if len(text) > 60:
                    snippets.append(text[:250])
            return snippets
        except Exception as e:
            logger.warning(f"IMDb fetch failed for {imdb_id}: {e}")
            return []

    def _get_imdb_score(self, imdb_id: str) -> Optional[float]:
        if not imdb_id:
            return None
        try:
            from imdb import Cinemagoer
            ia = Cinemagoer()
            movie = ia.get_movie(imdb_id.lstrip("tt"), info=["main"])
            rating = movie.get("rating")
            return float(rating) if rating else None
        except Exception:
            return None
