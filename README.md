# Daily Movie Review Telegram Bot

Sends you a Telegram message every morning at **10 AM IST** covering new movies releasing in Indian theaters (Bollywood + Hollywood).

Each movie message includes:
- Release date, language, runtime, and genres
- Director with their previous notable works
- Lead cast
- What the movie is about (zero spoilers)
- Real audience reactions from Reddit and IMDb
- Verdict (Highly Recommended / Worth Watching / Mixed / Skip)
- Theater or OTT recommendation
- Box office numbers (if available)
- Trailer link

---

## Setup

### 1. Clone and install

```bash
cd /path/to/repo
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure credentials

```bash
cp .env.example .env
```

Edit `.env` and fill in:

| Variable | Where to get it |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Message [@BotFather](https://t.me/BotFather) → `/newbot` |
| `TELEGRAM_CHAT_ID` | Send any message to your bot, then visit `https://api.telegram.org/bot<TOKEN>/getUpdates` → find `chat.id` |
| `TMDB_API_KEY` | [themoviedb.org/settings/api](https://www.themoviedb.org/settings/api) (free) |
| `REDDIT_CLIENT_ID` | [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) → Create app → type: **script** |
| `REDDIT_CLIENT_SECRET` | Same Reddit app page |

> Reddit credentials are optional. Without them, the bot uses Reddit's public search as a fallback (fewer reviews, but still works).

### 3. Test the connection

```bash
python -m movie_bot.run --test
```

You should receive a "MovieBot is alive!" message on Telegram within seconds.

### 4. Run once immediately

```bash
python -m movie_bot.run --now
```

This runs the full pipeline right now — fetches movies, gathers reviews, and sends the digest to your Telegram.

### 5. Start the daily scheduler

```bash
python -m movie_bot.run
```

The bot will fire every day at 10:00 AM IST. Keep this process running (e.g., via `screen`, `tmux`, or a systemd service).

---

## Running as a background service (Linux)

Create `/etc/systemd/system/moviebot.service`:

```ini
[Unit]
Description=Daily Movie Review Telegram Bot
After=network.target

[Service]
User=youruser
WorkingDirectory=/path/to/repo
ExecStart=/path/to/repo/.venv/bin/python -m movie_bot.run
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable moviebot
sudo systemctl start moviebot
```

---

## Configuration

All settings are in `.env`:

| Variable | Default | Description |
|---|---|---|
| `TIMEZONE` | `Asia/Kolkata` | Timezone for the 10 AM schedule |
| `SEND_HOUR` | `10` | Hour to send (24h format) |
| `SEND_MINUTE` | `0` | Minute to send |
| `DAYS_LOOKBACK` | `7` | Only cover movies released in last N days |
| `MAX_MOVIES_PER_RUN` | `5` | Max movies per daily digest |
