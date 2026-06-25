from typing import List, Optional


POSITIVE = {
    "great", "amazing", "loved", "love", "fantastic", "excellent", "brilliant",
    "masterpiece", "stunning", "must watch", "outstanding", "superb", "enjoyed",
    "wonderful", "incredible", "awesome", "perfect", "beautiful", "powerful",
    "emotional", "gripping", "entertaining", "fun", "thrilling", "recommend",
    "worth", "good", "solid", "well done", "impressive", "engaging",
}

NEGATIVE = {
    "bad", "terrible", "waste", "boring", "disappointing", "awful", "horrible",
    "worst", "poor", "mediocre", "weak", "slow", "dull", "predictable",
    "overrated", "skip", "avoid", "mess", "disaster", "flop", "unwatchable",
    "drag", "confusing", "nonsense", "unnecessary", "failed", "shallow",
}

THEATER_GENRES = {"Action", "Adventure", "Science Fiction", "Horror", "Animation", "Fantasy", "Thriller"}


class SentimentProcessor:
    def compute_verdict(
        self,
        reddit_reviews: List[str],
        imdb_reviews: List[str],
        tmdb_score: float,
        imdb_score: Optional[float],
        genres: List[str],
    ) -> tuple[str, str]:
        all_reviews = reddit_reviews + imdb_reviews
        audience_score = self._score_reviews(all_reviews)

        tmdb_norm = (tmdb_score - 5.0) / 5.0 if tmdb_score else 0.0
        imdb_norm = ((imdb_score - 5.0) / 5.0) if imdb_score else tmdb_norm

        if all_reviews:
            composite = 0.5 * audience_score + 0.25 * tmdb_norm + 0.25 * imdb_norm
        else:
            composite = 0.5 * tmdb_norm + 0.5 * imdb_norm

        verdict = self._map_verdict(composite)
        theater_rec = self._theater_recommendation(composite, tmdb_score, genres)
        return verdict, theater_rec

    def _score_reviews(self, reviews: List[str]) -> float:
        if not reviews:
            return 0.0
        total = 0.0
        for review in reviews:
            words = set(review.lower().split())
            pos = len(words & POSITIVE)
            neg = len(words & NEGATIVE)
            total += (pos - neg) / max(pos + neg, 1)
        return max(-1.0, min(1.0, total / len(reviews)))

    def _map_verdict(self, score: float) -> str:
        if score >= 0.5:
            return "Highly Recommended — audiences are loving it!"
        elif score >= 0.2:
            return "Generally Positive — worth a watch."
        elif score >= -0.1:
            return "Mixed Reviews — depends on your taste."
        else:
            return "Disappointing — audience reactions are largely negative."

    def _theater_recommendation(
        self, composite: float, tmdb_score: float, genres: List[str]
    ) -> str:
        is_theater_genre = bool(set(genres) & THEATER_GENRES)
        if composite >= 0.3 and tmdb_score >= 6.5 and is_theater_genre:
            return "Yes, watch in theaters — the big-screen experience adds real value here."
        elif composite >= 0.1 and tmdb_score >= 6.0:
            return "Can watch in theaters if convenient, otherwise a good OTT pick."
        else:
            return "Wait for OTT — save the theater trip for something more worthwhile."
