import json
import time
from datetime import date, datetime, timedelta, timezone

import numpy as np
from google.genai import errors, types

from .ai import GEN_MODEL, client
from .db import get_conn

PAPER_NAME = "The Daily You"
TOTAL = 14          # 1 hero + 4 secondary + 9 briefs
MAX_PER_TOPIC = 4


def _candidates(days=4):
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    with get_conn() as c:
        rows = c.execute(
            "SELECT * FROM articles WHERE embedding IS NOT NULL "
            "AND (published IS NULL OR published >= ?)", (cutoff,)).fetchall()
        if len(rows) < 30:  # quiet news period: widen the window
            rows = c.execute(
                "SELECT * FROM articles WHERE embedding IS NOT NULL").fetchall()
    return rows


def _recent_edition_ids(uid, n=3):
    ids = set()
    today = date.today().isoformat()
    with get_conn() as c:
        for r in c.execute(
                "SELECT content FROM editions WHERE user_id=? AND date != ? "
                "ORDER BY date DESC LIMIT ?", (uid, today, n)):
            data = json.loads(r["content"])
            for a in data["stories"]:
                ids.add(a["id"])
    return ids


def _rank(uid):
    with get_conn() as c:
        u = c.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
        topics = {r["topic"]: r["weight"] for r in c.execute(
            "SELECT topic, weight FROM user_topics WHERE user_id=?", (uid,))}
        skipped = {r["article_id"] for r in c.execute(
            "SELECT article_id FROM events WHERE user_id=? AND type='skip'",
            (uid,))}
    user_vec = np.frombuffer(u["vector"], dtype=np.float32)
    seen = skipped | _recent_edition_ids(uid)
    now = datetime.now(timezone.utc)

    scored = []
    for r in _candidates():
        if r["id"] in seen:
            continue
        sim = float(np.dot(user_vec, np.frombuffer(r["embedding"], dtype=np.float32)))
        score = sim + 0.15 * topics.get(r["topic"], 0.0)
        if r["published"]:
            age_h = (now - datetime.fromisoformat(r["published"])).total_seconds() / 3600
            score += 0.10 * max(0.0, 1 - age_h / 72)
        scored.append((score, sim, r))
    scored.sort(key=lambda x: x[0], reverse=True)
    return u, topics, scored


def _select(topics, scored):
    chosen, per_topic = [], {}
    for score, sim, r in scored:
        if per_topic.get(r["topic"], 0) >= MAX_PER_TOPIC:
            continue
        chosen.append(r)
        per_topic[r["topic"]] = per_topic.get(r["topic"], 0) + 1
        if len(chosen) >= TOTAL:
            break
    chosen_ids = {r["id"] for r in chosen}
    stretch = None
    for score, sim, r in sorted(scored, key=lambda x: x[1], reverse=True):
        if r["topic"] not in topics and r["id"] not in chosen_ids:
            stretch = r
            break
    return chosen, stretch


def _llm_write(user, items):
    listing = "\n".join(
        f"[{i}] ({r['source']} / {r['topic']}) {r['title']} | {(r['summary'] or '')[:350]}"
        for i, r in enumerate(items))
    prompt = f"""You are the editor of a personal daily newspaper for {user['name']}.
Reader interests: {user['free_text'] or 'general news'}.

Articles (index in brackets):
{listing}

Return JSON only, in this shape:
{{"articles": [{{"i": 0, "headline": "...", "blurb": "..."}}],
 "editor_note": "...",
 "three_things": ["...", "...", "..."]}}

Rules:
- Use ONLY facts from the articles above. Never invent details.
- headline: punchy newspaper headline, max 12 words.
- blurb: article 0 gets 3 sentences, articles 1-4 get 2 sentences, all others 1 sentence.
- Include an entry for every article index.
- editor_note: 2 warm sentences addressed to {user['name']} about today's edition.
- three_things: exactly 3 short facts the reader will have learned by reading this paper."""
    for attempt in range(3):
        try:
            res = client.models.generate_content(
                model=GEN_MODEL, contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json", temperature=0.4))
            return json.loads(res.text)
        except errors.ClientError as e:
            print(f"LLM ClientError (attempt {attempt + 1}): {e}")
            if getattr(e, "code", None) == 429 and attempt < 2:
                print("rate limited, waiting 45s...")
                time.sleep(45)
            else:
                break
        except Exception as e:
            print(f"LLM error: {type(e).__name__}: {e}")
            break
        return None


def generate(uid):
    user, topics, scored = _rank(uid)
    chosen, stretch = _select(topics, scored)
    items = chosen + ([stretch] if stretch else [])
    if not items:
        raise ValueError("No articles available. Run ingest + embed first.")

    out = _llm_write(user, items) or {}
    by_i = {a.get("i"): a for a in out.get("articles", [])}

    stories = []
    for i, r in enumerate(items):
        ai = by_i.get(i, {})
        if stretch and r["id"] == stretch["id"]:
            role = "stretch"
        elif i == 0:
            role = "hero"
        elif i <= 4:
            role = "secondary"
        else:
            role = "brief"
        stories.append({
            "id": r["id"], "role": role, "url": r["url"],
            "headline": ai.get("headline") or r["title"],
            "original_title": r["title"],
            "blurb": ai.get("blurb") or (r["summary"] or "")[:200],
            "source": r["source"], "topic": r["topic"],
            "image_url": r["image_url"], "published": r["published"],
        })

    return {
        "paper_name": PAPER_NAME,
        "date": date.today().isoformat(),
        "reader": user["name"],
        "editor_note": out.get("editor_note", ""),
        "three_things": out.get("three_things", []),
        "stories": stories,
    }


def get_or_create(uid, force=False):
    today = date.today().isoformat()
    with get_conn() as c:
        row = c.execute("SELECT * FROM editions WHERE user_id=? AND date=?",
                        (uid, today)).fetchone()
    if row and not force:
        return {"id": row["id"], "date": row["date"],
                "content": json.loads(row["content"])}

    content = generate(uid)
    with get_conn() as c:
        c.execute(
            "INSERT INTO editions (user_id, date, content) VALUES (?, ?, ?) "
            "ON CONFLICT(user_id, date) DO UPDATE SET content=excluded.content",
            (uid, today, json.dumps(content)))
        row = c.execute("SELECT id FROM editions WHERE user_id=? AND date=?",
                        (uid, today)).fetchone()
    return {"id": row["id"], "date": today, "content": content}