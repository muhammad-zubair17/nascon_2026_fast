import time

from .ai import embed_texts
from .db import get_conn

CHUNK = 80  # free tier allows 100 texts/min


def run():
    with get_conn() as c:
        rows = c.execute(
            "SELECT id, title, summary FROM articles WHERE embedding IS NULL"
        ).fetchall()
    if not rows:
        print("Nothing to embed.")
        return

    total = len(rows)
    print(f"{total} articles to embed")
    for i in range(0, total, CHUNK):
        chunk = rows[i:i + CHUNK]
        texts = [f"{r['title']}. {r['summary'] or ''}"[:1000] for r in chunk]
        vecs = embed_texts(texts)
        with get_conn() as c:
            for r, v in zip(chunk, vecs):
                c.execute("UPDATE articles SET embedding = ? WHERE id = ?",
                          (v.tobytes(), r["id"]))
        print(f"  saved {min(i + CHUNK, total)}/{total}")
        if i + CHUNK < total:
            print("  waiting 62s for rate limit...")
            time.sleep(62)
    print("Done.")


if __name__ == "__main__":
    run()