from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional


@dataclass
class MovieData:
    tmdb_id: int
    title: str
    original_title: str
    release_date: date
    language: str
    runtime: int
    genres: List[str]
    overview: str

    director: str
    director_id: int
    director_previous_works: List[str]
    lead_cast: List[str]

    tmdb_score: float
    imdb_id: Optional[str]
    imdb_score: Optional[float]

    reddit_reviews: List[str] = field(default_factory=list)
    imdb_user_reviews: List[str] = field(default_factory=list)

    verdict: str = ""
    theater_recommendation: str = ""

    trailer_url: Optional[str] = None
    poster_url: Optional[str] = None
    is_sequel: bool = False
    belongs_to_collection: Optional[str] = None
    budget: Optional[int] = None
    box_office: Optional[int] = None
