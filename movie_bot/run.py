#!/usr/bin/env python3
"""
Daily Movie Review Telegram Bot

Usage:
  python -m movie_bot.run            # Start scheduler (fires daily at 10 AM IST)
  python -m movie_bot.run --now      # Run immediately (great for testing)
  python -m movie_bot.run --test     # Send a test ping to verify Telegram setup
"""

import argparse
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Daily Movie Review Telegram Bot")
    parser.add_argument("--now", action="store_true", help="Run the job immediately")
    parser.add_argument("--test", action="store_true", help="Send a test Telegram message")
    args = parser.parse_args()

    from movie_bot.config import Config
    config = Config()

    if args.test:
        from movie_bot.bot.telegram_sender import TelegramSender
        sender = TelegramSender(config.telegram_token, config.chat_id)
        sender.run_sync(sender.send_test())
        print("Test message sent! Check your Telegram.")

    elif args.now:
        from movie_bot.scheduler import MovieBotScheduler
        scheduler = MovieBotScheduler(config)
        scheduler.run_daily_job()

    else:
        from movie_bot.scheduler import MovieBotScheduler
        scheduler = MovieBotScheduler(config)
        scheduler.start()


if __name__ == "__main__":
    main()
