from .learning import apply_event
from fastapi.responses import Response
from .pdf import build_pdf
import json
from .edition import get_or_create
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .ai import embed_texts
from .db import get_conn, init_db, seed_if_missing
from .feeds import FEEDS


@asynccontextmanager
async def lifespan(app):
    seed_if_missing()
    init_db()
    from .daily import start_scheduler
    start_scheduler()
    yield


app = FastAPI(title="Morning Paper", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])


class Onboard(BaseModel):
    name: str
    topics: list[str]
    free_text: str = ""


@app.get("/api/topics")
def topics():
    return list(FEEDS.keys())


@app.post("/api/onboard")
def onboard(body: Onboard):
    valid = [t for t in body.topics if t in FEEDS]
    if not valid:
        raise HTTPException(400, "Pick at least one topic")
    profile_text = f"Interested in {', '.join(valid)}. {body.free_text}".strip()
    vec = embed_texts([profile_text])[0]
    with get_conn() as c:
        cur = c.execute(
            "INSERT INTO users (name, free_text, vector) VALUES (?, ?, ?)",
            (body.name, body.free_text, vec.tobytes()),
        )
        uid = cur.lastrowid
        c.executemany(
            "INSERT INTO user_topics (user_id, topic, weight) VALUES (?, ?, 1.0)",
            [(uid, t) for t in valid],
        )
    return {"user_id": uid, "name": body.name, "topics": valid}


@app.get("/api/users/{uid}")
def get_user(uid: int):
    with get_conn() as c:
        u = c.execute("SELECT id, name, free_text FROM users WHERE id = ?",
                      (uid,)).fetchone()
        if not u:
            raise HTTPException(404, "User not found")
        t = c.execute("SELECT topic, weight FROM user_topics WHERE user_id = ?",
                      (uid,)).fetchall()
    return {**dict(u), "topics": [dict(x) for x in t]}
@app.post("/api/users/{uid}/edition")
def make_edition(uid: int, force: bool = False):
    with get_conn() as c:
        if not c.execute("SELECT 1 FROM users WHERE id=?", (uid,)).fetchone():
            raise HTTPException(404, "User not found")
    try:
        return get_or_create(uid, force)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/api/users/{uid}/editions")
def archive(uid: int):
    with get_conn() as c:
        rows = c.execute(
            "SELECT id, date, content FROM editions WHERE user_id=? "
            "ORDER BY date DESC", (uid,)).fetchall()
    out = []
    for r in rows:
        data = json.loads(r["content"])
        hero = next((s for s in data["stories"] if s["role"] == "hero"), None)
        out.append({"id": r["id"], "date": r["date"],
                    "headline": hero["headline"] if hero else ""})
    return out


@app.get("/api/editions/{eid}")
def one_edition(eid: int):
    with get_conn() as c:
        r = c.execute("SELECT * FROM editions WHERE id=?", (eid,)).fetchone()
    if not r:
        raise HTTPException(404, "Edition not found")
    return {"id": r["id"], "date": r["date"], "content": json.loads(r["content"])}
class EventIn(BaseModel):
    article_id: int
    type: str  # "click" or "skip"


@app.post("/api/users/{uid}/events")
def log_event(uid: int, body: EventIn):
    if body.type not in ("click", "skip"):
        raise HTTPException(400, "type must be click or skip")
    with get_conn() as c:
        c.execute("INSERT INTO events (user_id, article_id, type) VALUES (?, ?, ?)",
                  (uid, body.article_id, body.type))
    apply_event(uid, body.article_id, body.type)
    return {"ok": True}
@app.get("/api/editions/{eid}/pdf")
def edition_pdf(eid: int):
    with get_conn() as c:
        r = c.execute("SELECT * FROM editions WHERE id=?", (eid,)).fetchone()
        if not r:
            raise HTTPException(404, "Edition not found")
        skipped = {x["article_id"] for x in c.execute(
            "SELECT article_id FROM events WHERE user_id=? AND type='skip'",
            (r["user_id"],))}
    data = build_pdf(json.loads(r["content"]), skipped)
    return Response(
        data, media_type="application/pdf",
        headers={"Content-Disposition":
                 f'attachment; filename="the-daily-you-{r["date"]}.pdf"'})
from pathlib import Path

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

STATIC = Path(__file__).resolve().parent.parent / "static"
if STATIC.exists():
    app.mount("/assets", StaticFiles(directory=STATIC / "assets"), name="assets")

    @app.get("/{path:path}")
    def spa(path: str):
        f = STATIC / path
        if path and f.is_file():
            return FileResponse(f)
        return FileResponse(STATIC / "index.html")