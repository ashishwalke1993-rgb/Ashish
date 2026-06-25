from datetime import date
from typing import List
from movie_bot.models.movie import MovieData

MAX_MSG_LEN = 3800


class TelegramFormatter:
    def format_header(self, movie_count: int, today: date) -> str:
        date_str = today.strftime("%A, %d %B %Y")
        return (
            f"🍿 <b>New Movies in Theaters</b>\n"
            f"📆 {date_str}\n"
            f"Covering <b>{movie_count}</b> new release(s) this week — let's help you decide!\n"
            f"{'─' * 30}"
        )

    def format_movie(self, movie: MovieData) -> str:
        sequel_badge = f" 🔄 <i>({movie.belongs_to_collection})</i>" if movie.is_sequel and movie.belongs_to_collection else ""
        genres_str = ", ".join(movie.genres) if movie.genres else "N/A"
        runtime_str = f"{movie.runtime} min" if movie.runtime else "N/A"
        release_str = movie.release_date.strftime("%d %b %Y")

        prev_works = ", ".join(movie.director_previous_works) if movie.director_previous_works else "N/A"
        cast_str = ", ".join(movie.lead_cast) if movie.lead_cast else "N/A"

        overview = movie.overview
        if len(overview) > 350:
            overview = overview[:347] + "..."

        ratings_line = f"TMDB: <b>{movie.tmdb_score}/10</b>"
        if movie.imdb_score:
            ratings_line += f" | IMDb: <b>{movie.imdb_score}/10</b>"

        reviews_section = self._format_reviews(movie.reddit_reviews, movie.imdb_user_reviews)

        box_office_line = ""
        if movie.box_office and movie.box_office > 0:
            crore = movie.box_office / 10_000_000
            box_office_line = f"\n💰 <b>Box Office:</b> ₹{crore:.1f} Cr"

        trailer_line = ""
        if movie.trailer_url:
            trailer_line = f'\n🎞 <a href="{movie.trailer_url}">Watch Trailer</a>'

        msg = (
            f"🎬 <b>{movie.title}</b>{sequel_badge}\n"
            f"📅 {release_str} | 🌐 {movie.language} | ⏱ {runtime_str}\n"
            f"🎭 {genres_str}\n\n"
            f"🎬 <b>Director:</b> {movie.director}\n"
            f"   <i>Previous works: {prev_works}</i>\n"
            f"👥 <b>Cast:</b> {cast_str}\n\n"
            f"📖 <b>About (no spoilers):</b>\n{overview}\n\n"
            f"⭐ <b>Ratings:</b> {ratings_line}\n\n"
            f"{reviews_section}\n"
            f"📊 <b>Verdict:</b> {movie.verdict}\n\n"
            f"🎟 <b>Theater or OTT?</b>\n{movie.theater_recommendation}"
            f"{box_office_line}"
            f"{trailer_line}"
        )

        return self.truncate(msg)

    def format_no_movies(self) -> str:
        return (
            "🎬 <b>No new movie releases this week.</b>\n\n"
            "Nothing dropped in Indian theaters in the past 7 days. Check back tomorrow!"
        )

    def _format_reviews(self, reddit: List[str], imdb: List[str]) -> str:
        combined = []
        for r in reddit[:3]:
            combined.append(f"• <i>{self._escape(r)}</i>")
        for r in imdb[:2]:
            combined.append(f"• <i>{self._escape(r)}</i>")

        if combined:
            return "💬 <b>What real audiences are saying:</b>\n" + "\n".join(combined) + "\n\n"
        return "💬 <b>Audience reviews:</b> Not yet available — movie just released!\n\n"

    def _escape(self, text: str) -> str:
        return text.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")

    def truncate(self, text: str) -> str:
        if len(text) <= MAX_MSG_LEN:
            return text
        return text[:MAX_MSG_LEN - 3] + "..."
