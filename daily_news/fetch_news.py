"""
Daily Tech & AI News Email Script
Fetches top news from RSS feeds and sends a formatted HTML email via Gmail SMTP.
"""

import os
import smtplib
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.request import urlopen, Request
from urllib.error import URLError

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL", "ashishwalke1993@gmail.com")
SENDER_EMAIL    = os.environ.get("SENDER_EMAIL", "")
SENDER_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")

MAX_ITEMS_PER_FEED = 5   # articles per source

RSS_FEEDS = [
    # AI & Machine Learning
    {"name": "VentureBeat AI",     "url": "https://venturebeat.com/category/ai/feed/",            "tag": "AI"},
    {"name": "MIT Tech Review AI", "url": "https://www.technologyreview.com/feed/",                "tag": "AI"},
    {"name": "The Decoder",        "url": "https://the-decoder.com/feed/",                         "tag": "AI"},
    # Tech News
    {"name": "TechCrunch",         "url": "https://techcrunch.com/feed/",                          "tag": "Tech"},
    {"name": "The Verge",          "url": "https://www.theverge.com/rss/index.xml",                "tag": "Tech"},
    {"name": "Hacker News Top",    "url": "https://hnrss.org/frontpage?count=10",                  "tag": "Dev"},
    {"name": "Ars Technica",       "url": "https://feeds.arstechnica.com/arstechnica/technology-lab", "tag": "Tech"},
]

TAG_COLORS = {
    "AI":   "#7c3aed",
    "Tech": "#0ea5e9",
    "Dev":  "#059669",
}

# ──────────────────────────────────────────────
# RSS Fetcher
# ──────────────────────────────────────────────

def fetch_rss(feed: dict) -> list[dict]:
    """Fetch and parse an RSS/Atom feed, return list of article dicts."""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; DailyNewsBot/1.0)"}
    try:
        req = Request(feed["url"], headers=headers)
        with urlopen(req, timeout=15) as resp:
            raw = resp.read()
        root = ET.fromstring(raw)
    except (URLError, ET.ParseError) as exc:
        print(f"[WARN] Could not fetch {feed['name']}: {exc}")
        return []

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    items = []

    # RSS 2.0
    for item in root.findall(".//item")[:MAX_ITEMS_PER_FEED]:
        title = (item.findtext("title") or "").strip()
        link  = (item.findtext("link")  or "").strip()
        desc  = (item.findtext("description") or "").strip()
        # Strip HTML tags from description
        desc  = _strip_tags(desc)[:200]
        if title and link:
            items.append({"title": title, "link": link, "desc": desc})

    # Atom
    if not items:
        for entry in root.findall("atom:entry", ns)[:MAX_ITEMS_PER_FEED]:
            title = (entry.findtext("atom:title", namespaces=ns) or "").strip()
            link_el = entry.find("atom:link", ns)
            link    = link_el.get("href", "") if link_el is not None else ""
            summary = (entry.findtext("atom:summary", namespaces=ns) or "").strip()
            summary = _strip_tags(summary)[:200]
            if title and link:
                items.append({"title": title, "link": link, "desc": summary})

    return items


def _strip_tags(text: str) -> str:
    """Remove HTML/XML tags from a string."""
    import re
    clean = re.sub(r"<[^>]+>", "", text)
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()


# ──────────────────────────────────────────────
# HTML Email Builder
# ──────────────────────────────────────────────

def build_html(sections: list[dict]) -> str:
    today = datetime.now(timezone.utc).strftime("%A, %d %B %Y")

    articles_html = ""
    for section in sections:
        if not section["items"]:
            continue
        tag   = section["tag"]
        color = TAG_COLORS.get(tag, "#475569")
        badge = (
            f'<span style="background:{color};color:#fff;padding:2px 10px;'
            f'border-radius:12px;font-size:12px;font-weight:600;">{tag}</span>'
        )
        articles_html += f"""
        <tr>
          <td style="padding:24px 32px 4px 32px;">
            <p style="margin:0;font-size:13px;">{badge}
              &nbsp;<strong style="font-size:16px;color:#1e293b;">{section['source']}</strong>
            </p>
          </td>
        </tr>"""

        for art in section["items"]:
            desc_block = (
                f'<p style="margin:4px 0 0 0;font-size:13px;color:#64748b;">'
                f'{art["desc"]}…</p>'
                if art["desc"] else ""
            )
            articles_html += f"""
        <tr>
          <td style="padding:6px 32px 6px 40px;border-left:3px solid {color};margin-left:32px;">
            <a href="{art['link']}" style="color:#1d4ed8;font-size:14px;font-weight:500;
               text-decoration:none;">{art['title']}</a>
            {desc_block}
          </td>
        </tr>"""

        articles_html += """
        <tr><td style="padding:8px 32px;"><hr style="border:none;border-top:1px solid #e2e8f0;"></td></tr>"""

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f1f5f9;padding:32px 0;">
    <tr>
      <td align="center">
        <table width="640" cellpadding="0" cellspacing="0"
               style="background:#ffffff;border-radius:12px;overflow:hidden;
                      box-shadow:0 2px 12px rgba(0,0,0,0.08);">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#1e3a8a 0%,#7c3aed 100%);
                       padding:32px;text-align:center;">
              <h1 style="margin:0;color:#fff;font-size:26px;letter-spacing:-0.5px;">
                Daily Tech &amp; AI News
              </h1>
              <p style="margin:8px 0 0 0;color:#c7d2fe;font-size:14px;">{today}</p>
            </td>
          </tr>

          <!-- Intro -->
          <tr>
            <td style="padding:20px 32px 0 32px;">
              <p style="margin:0;color:#475569;font-size:14px;">
                Good morning! Here are today's top stories in <strong>AI, Tech &amp; Dev</strong>.
                Stay ahead of the curve.
              </p>
            </td>
          </tr>

          <!-- Articles -->
          {articles_html}

          <!-- Footer -->
          <tr>
            <td style="background:#f8fafc;padding:20px 32px;text-align:center;
                       border-top:1px solid #e2e8f0;">
              <p style="margin:0;color:#94a3b8;font-size:12px;">
                You're receiving this because you set up the Daily Tech News emailer.<br>
                Powered by open RSS feeds &bull; Sent automatically every morning.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
    return html


# ──────────────────────────────────────────────
# Email Sender
# ──────────────────────────────────────────────

def send_email(html_body: str) -> None:
    today_str = datetime.now(timezone.utc).strftime("%d %b %Y")
    subject   = f"Daily Tech & AI News — {today_str}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = SENDER_EMAIL
    msg["To"]      = RECIPIENT_EMAIL
    msg.attach(MIMEText(html_body, "html"))

    print(f"Connecting to Gmail SMTP as {SENDER_EMAIL}...")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
    print(f"Email sent to {RECIPIENT_EMAIL}")


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main() -> None:
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        raise EnvironmentError(
            "SENDER_EMAIL and GMAIL_APP_PASSWORD environment variables must be set."
        )

    print("Fetching news feeds...")
    sections = []
    for feed in RSS_FEEDS:
        items = fetch_rss(feed)
        print(f"  {feed['name']}: {len(items)} articles")
        sections.append({"source": feed["name"], "tag": feed["tag"], "items": items})

    total = sum(len(s["items"]) for s in sections)
    if total == 0:
        print("No articles fetched. Aborting email.")
        return

    print(f"Total articles: {total}. Building email...")
    html = build_html(sections)

    send_email(html)
    print("Done.")


if __name__ == "__main__":
    main()
