import logging
from typing import List

import requests

logger = logging.getLogger(__name__)

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
COMMENTS_URL = "https://www.googleapis.com/youtube/v3/commentThreads"
VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"


class YouTubeFetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_reviews(self, title: str, max_comments: int = 5) -> List[str]:
        """Search for a review video with highest views and return top comments."""
        try:
            video_id = self._find_top_review_video(title)
            if not video_id:
                logger.warning(f"No YouTube review video found for '{title}'")
                return []
            comments = self._fetch_comments(video_id, max_comments)
            logger.info(f"Fetched {len(comments)} YouTube comments for '{title}'")
            return comments
        except Exception as e:
            logger.warning(f"YouTube fetch failed for '{title}': {e}")
            return []

    def _find_top_review_video(self, title: str) -> str | None:
        """Search YouTube for '{title} movie review' and return the video ID with highest views."""
        params = {
            "part": "snippet",
            "q": f"{title} movie review",
            "type": "video",
            "maxResults": 5,
            "relevanceLanguage": "en",
            "key": self.api_key,
        }
        resp = requests.get(SEARCH_URL, params=params, timeout=10)
        resp.raise_for_status()
        items = resp.json().get("items", [])
        if not items:
            return None

        video_ids = [item["id"]["videoId"] for item in items]
        return self._pick_most_viewed(video_ids)

    def _pick_most_viewed(self, video_ids: List[str]) -> str | None:
        """From a list of video IDs, return the one with the highest view count."""
        params = {
            "part": "statistics",
            "id": ",".join(video_ids),
            "key": self.api_key,
        }
        resp = requests.get(VIDEOS_URL, params=params, timeout=10)
        resp.raise_for_status()
        items = resp.json().get("items", [])
        if not items:
            return None

        best = max(
            items,
            key=lambda v: int(v.get("statistics", {}).get("viewCount", 0)),
        )
        return best["id"]

    def _fetch_comments(self, video_id: str, max_comments: int) -> List[str]:
        """Fetch top comments from a YouTube video, filtered for relevance."""
        params = {
            "part": "snippet",
            "videoId": video_id,
            "order": "relevance",
            "maxResults": 50,
            "key": self.api_key,
        }
        resp = requests.get(COMMENTS_URL, params=params, timeout=10)
        resp.raise_for_status()
        items = resp.json().get("items", [])

        comments = []
        for item in items:
            text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            text = text.strip()
            if self._is_relevant_comment(text):
                comments.append(text)
            if len(comments) >= max_comments:
                break

        return comments

    _SPAM_PATTERNS = [
        "subscribe", "sub to me", "check out my", "visit my channel",
        "follow me", "like and subscribe", "hit the bell", "notification",
        "giveaway", "click here", "link in bio", "promo code",
        "who is watching", "anyone watching in", "watching in 20",
        "early squad", "first comment", "came here from",
    ]

    _REVIEW_KEYWORDS = [
        "movie", "film", "acting", "actor", "actress", "director", "scene",
        "story", "plot", "character", "performance", "watch", "cinema",
        "theatre", "theater", "screenplay", "dialogue", "climax",
        "interval", "first half", "second half", "bgm", "music",
        "visuals", "direction", "rating", "recommend", "worth",
        "must watch", "boring", "amazing", "excellent", "average",
        "disappointing", "entertaining", "emotional", "action", "comedy",
        "drama", "thriller", "good", "bad", "great", "worst", "best",
        "overall", "review", "opinion", "verdict",
    ]

    def _is_relevant_comment(self, text: str) -> bool:
        if len(text) < 50 or len(text) > 400:
            return False

        lower = text.lower()

        # Reject spam / self-promotion
        if any(p in lower for p in self._SPAM_PATTERNS):
            return False

        # Reject if more than 40% of characters are emojis/non-ASCII
        non_ascii = sum(1 for c in text if ord(c) > 127)
        if non_ascii / len(text) > 0.4:
            return False

        # Must contain at least one review-related keyword
        if not any(kw in lower for kw in self._REVIEW_KEYWORDS):
            return False

        return True
