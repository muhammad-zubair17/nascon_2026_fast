import html
import re
from datetime import datetime, timezone
from time import mktime

import feedparser
import httpx

from .db import get_conn, init_db
from .feeds import FEEDS

HEADERS = {"User-Agent": "Mozilla/5.0 (MorningPaper hackathon project)"}
TAG = re.compile(r"<[^>]+>")


def clean(text):
    text = html.unescape(TAG.sub("", text or ""))
    return re.sub(r"\s+", " ", text).strip()


def find_image(entry):
    for key in ("media_content", "media_thumbnail"):
        for m in entry.get(key) or []:
            if m.get("url"):
                return m["url"]
    for link in entry.get("links", []):
        if link.get("type", "").startswith("image"):
            return link.get("href")
    return None


def to_iso(entry):
    t = entry.get("published_parsed") or entry.get("updated_parsed")
    if not t:
        return None
    return datetime.fromtimestamp(mktime(t), tz=timezone.utc).isoformat()


def ingest_feed(topic, source, url):
    try:
        r = httpx.get(url, headers=HEADERS, timeout=15, follow_redirects=True)
        feed = feedparser.parse(r.content)
    except Exception as ex:
        print(f"  FAIL {source}: {ex}")
        return 0

    added = 0
    with get_conn() as c:
        for e in feed.entries[:25]:
            link, title = e.get("link"), clean(e.get("title"))
            if not link or not title:
                continue
            cur = c.execute(
                """INSERT OR IGNORE INTO articles
                   (url, title, summary, source, topic, image_url, published)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (link, title, clean(e.get("summary"))[:800], source, topic,
                 find_image(e), to_iso(e)),
            )
            added += cur.rowcount
    print(f"  OK   {source}: {added} new")
    return added


def run():
    init_db()
    total = 0
    for topic, feeds in FEEDS.items():
        print(topic)
        for source, url in feeds:
            total += ingest_feed(topic, source, url)
    print(f"\nDone. {total} new articles.")


if __name__ == "__main__":
    run()