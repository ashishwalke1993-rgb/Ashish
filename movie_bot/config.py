import os
from dotenv import load_dotenv


class Config:
    def __init__(self, env_file: str = ".env"):
        load_dotenv(env_file)

        self.telegram_token = self._require("TELEGRAM_BOT_TOKEN")
        self.chat_id = self._require("TELEGRAM_CHAT_ID")
        self.tmdb_api_key = self._require("TMDB_API_KEY")

        self.reddit_client_id = os.getenv("REDDIT_CLIENT_ID", "")
        self.reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET", "")
        self.reddit_user_agent = os.getenv("REDDIT_USER_AGENT", "MovieBot/1.0")
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY", "")

        self.timezone = os.getenv("TIMEZONE", "Asia/Kolkata")
        self.send_hour = int(os.getenv("SEND_HOUR", "10"))
        self.send_minute = int(os.getenv("SEND_MINUTE", "0"))
        self.days_lookback = int(os.getenv("DAYS_LOOKBACK", "7"))
        self.max_movies = int(os.getenv("MAX_MOVIES_PER_RUN", "5"))

    def _require(self, key: str) -> str:
        val = os.getenv(key)
        if not val:
            raise EnvironmentError(f"Missing required env var: {key}")
        return val

    @property
    def reddit_enabled(self) -> bool:
        return bool(self.reddit_client_id and self.reddit_client_secret)

    @property
    def youtube_enabled(self) -> bool:
        return bool(self.youtube_api_key)
