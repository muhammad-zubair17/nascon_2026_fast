import numpy as np

from .db import get_conn

CLICK_PULL = 0.15
SKIP_PUSH = 0.08
TOPIC_CLICK = 0.10
TOPIC_SKIP = -0.10
MAX_WEIGHT = 2.0


def apply_event(uid, article_id, etype):
    with get_conn() as c:
        art = c.execute("SELECT topic, embedding FROM articles WHERE id=?",
                        (article_id,)).fetchone()
        user = c.execute("SELECT vector FROM users WHERE id=?", (uid,)).fetchone()
        if not art or not user or art["embedding"] is None:
            return

        v = np.frombuffer(user["vector"], dtype=np.float32).copy()
        a = np.frombuffer(art["embedding"], dtype=np.float32)
        v = v + CLICK_PULL * a if etype == "click" else v - SKIP_PUSH * a
        v /= np.linalg.norm(v)
        c.execute("UPDATE users SET vector=? WHERE id=?",
                  (v.astype(np.float32).tobytes(), uid))

        row = c.execute("SELECT weight FROM user_topics WHERE user_id=? AND topic=?",
                        (uid, art["topic"])).fetchone()
        delta = TOPIC_CLICK if etype == "click" else TOPIC_SKIP
        if row:
            w = min(MAX_WEIGHT, max(0.0, row["weight"] + delta))
            c.execute("UPDATE user_topics SET weight=? WHERE user_id=? AND topic=?",
                      (w, uid, art["topic"]))
        elif etype == "click":
            c.execute("INSERT INTO user_topics (user_id, topic, weight) VALUES (?, ?, ?)",
                      (uid, art["topic"], 0.1))