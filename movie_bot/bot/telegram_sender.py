import asyncio
import logging
import time
from typing import List

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

from movie_bot.models.movie import MovieData
from movie_bot.formatters.telegram_formatter import TelegramFormatter

logger = logging.getLogger(__name__)


class TelegramSender:
    def __init__(self, token: str, chat_id: str):
        self.bot = Bot(token=token)
        self.chat_id = chat_id

    async def _send(self, text: str) -> None:
        for attempt in range(3):
            try:
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=False,
                )
                return
            except TelegramError as e:
                logger.warning(f"Telegram send attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
        logger.error("All Telegram send attempts failed.")

    async def send_daily_digest(
        self, movies: List[MovieData], formatter: TelegramFormatter
    ) -> None:
        from datetime import date

        if not movies:
            await self._send(formatter.format_no_movies())
            return

        header = formatter.format_header(len(movies), date.today())
        await self._send(header)
        await asyncio.sleep(1)

        for movie in movies:
            msg = formatter.format_movie(movie)
            await self._send(msg)
            await asyncio.sleep(1.5)

        await self._send("That's all for today! Enjoy the movie 🎬🍿")

    async def send_test(self) -> None:
        await self._send(
            "✅ <b>MovieBot is alive!</b>\n\nYour daily 10 AM movie reviews are set up correctly."
        )

    def run_sync(self, coro) -> None:
        asyncio.run(coro)
