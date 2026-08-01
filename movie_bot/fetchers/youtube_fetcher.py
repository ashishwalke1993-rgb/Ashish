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
        """Fetch top comments from a YouTube video, filtered for quality."""
        params = {
            "part": "snippet",
            "videoId": video_id,
            "order": "relevance",
            "maxResults": 20,
            "key": self.api_key,
        }
        resp = requests.get(COMMENTS_URL, params=params, timeout=10)
        resp.raise_for_status()
        items = resp.json().get("items", [])

        comments = []
        for item in items:
            text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            text = text.strip()
            # Filter: meaningful length, not just emojis or very short
            if len(text) >= 40 and len(text) <= 400:
                comments.append(text)
            if len(comments) >= max_comments:
                break

        return comments
