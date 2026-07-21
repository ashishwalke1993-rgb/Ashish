import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from movie_bot.config import Config
from movie_bot.fetchers.tmdb_fetcher import TMDBFetcher
from movie_bot.fetchers.reddit_fetcher import RedditFetcher, RedditFallbackFetcher
from movie_bot.processors.movie_filter import MovieFilter, remove_from_sent
from movie_bot.processors.sentiment import SentimentProcessor
from movie_bot.processors.enricher import MovieEnricher
from movie_bot.formatters.telegram_formatter import TelegramFormatter
from movie_bot.bot.telegram_sender import TelegramSender

logger = logging.getLogger(__name__)


class MovieBotScheduler:
    def __init__(self, config: Config):
        self.config = config
        tz = pytz.timezone(config.timezone)
        self.scheduler = BackgroundScheduler(timezone=tz)

    def run_daily_job(self) -> None:
        config = self.config
        logger.info("Starting daily movie review job...")

        tmdb = TMDBFetcher(config.tmdb_api_key)

        if config.reddit_enabled:
            try:
                reddit_fetcher = RedditFetcher(
                    config.reddit_client_id,
                    config.reddit_client_secret,
                    config.reddit_user_agent,
                )
            except Exception as e:
                logger.warning(f"PRAW init failed, using fallback: {e}")
                reddit_fetcher = RedditFallbackFetcher()
        else:
            logger.info("Reddit credentials not set — using public fallback.")
            reddit_fetcher = RedditFallbackFetcher()

        sentiment = SentimentProcessor()
        enricher = MovieEnricher(tmdb, sentiment, reddit_fetcher)
        movie_filter = MovieFilter()
        formatter = TelegramFormatter()
        sender = TelegramSender(config.telegram_token, config.chat_id)

        try:
            raw_movies = tmdb.get_now_playing(region="IN")
            logger.info(f"TMDB returned {len(raw_movies)} movies in theaters.")
        except Exception as e:
            logger.error(f"Failed to fetch now_playing: {e}")
            return

        recent = movie_filter.filter_recent(
            raw_movies, config.days_lookback, config.max_movies
        )
        logger.info(f"{len(recent)} movies released in last {config.days_lookback} days.")

        enriched = []
        for raw in recent:
            movie = enricher.enrich(raw)
            if not movie:
                continue
            if not (movie.reddit_reviews or movie.imdb_user_reviews):
                logger.info(f"Skipping '{movie.title}' — no reviews yet, will retry tomorrow.")
                remove_from_sent(str(movie.tmdb_id))
                continue
            enriched.append(movie)

        sender.run_sync(sender.send_daily_digest(enriched, formatter))
        logger.info(f"Daily digest sent with {len(enriched)} movies.")

    def setup(self) -> None:
        self.scheduler.add_job(
            func=self.run_daily_job,
            trigger=CronTrigger(
                hour=self.config.send_hour,
                minute=self.config.send_minute,
            ),
            id="daily_movie_review",
            replace_existing=True,
        )

    def start(self) -> None:
        self.setup()
        self.scheduler.start()
        tz = self.config.timezone
        h = self.config.send_hour
        m = self.config.send_minute
        print(f"MovieBot scheduled at {h:02d}:{m:02d} {tz} daily. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Shutting down scheduler.")
            self.scheduler.shutdown()
