import re
import time
import logging
from typing import List

logger = logging.getLogger(__name__)

SUBREDDITS = "india+bollywood+movies+MovieSuggestions+IndianCinema"


class RedditFetcher:
    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        import praw
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )

    def get_audience_reviews(self, title: str, year: int) -> List[str]:
        queries = [
            f'"{title}" review {year}',
            f'"{title}" discussion',
            f"{title} movie thoughts",
        ]
        snippets: List[str] = []
        seen_ids = set()

        for query in queries:
            if len(snippets) >= 5:
                break
            try:
                results = self.reddit.subreddit(SUBREDDITS).search(
                    query, sort="relevance", time_filter="month", limit=10
                )
                for submission in results:
                    if len(snippets) >= 5:
                        break
                    if submission.id in seen_ids:
                        continue
                    seen_ids.add(submission.id)
                    submission.comments.replace_more(limit=0)
                    for comment in submission.comments.list():
                        if self._is_valid_comment(comment):
                            text = self._clean(comment.body)
                            if text:
                                snippets.append(text[:250])
                                if len(snippets) >= 5:
                                    break
                time.sleep(0.5)
            except Exception as e:
                logger.warning(f"Reddit search failed for '{query}': {e}")

        return snippets

    def _is_valid_comment(self, comment) -> bool:
        try:
            return (
                hasattr(comment, "body")
                and comment.author is not None
                and str(comment.author) != "AutoModerator"
                and comment.score > 3
                and len(comment.body) > 60
            )
        except Exception:
            return False

    def _clean(self, text: str) -> str:
        text = re.sub(r">!.*?!<", "", text, flags=re.DOTALL)
        text = re.sub(r"\[.*?\]\(.*?\)", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text


class RedditFallbackFetcher:
    """Fallback that uses Reddit's public JSON API without credentials."""

    def __init__(self):
        import requests
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "MovieBot/1.0"})

    def get_audience_reviews(self, title: str, year: int) -> List[str]:
        import requests
        snippets = []
        try:
            resp = self.session.get(
                "https://www.reddit.com/search.json",
                params={"q": f"{title} movie review", "sort": "relevance", "t": "month", "limit": 10},
                timeout=10,
            )
            resp.raise_for_status()
            posts = resp.json().get("data", {}).get("children", [])
            for post in posts[:3]:
                selftext = post["data"].get("selftext", "").strip()
                if len(selftext) > 80:
                    snippets.append(selftext[:250])
        except Exception as e:
            logger.warning(f"Reddit fallback failed: {e}")
        return snippets
