import numpy as np
import pytest
from fastapi.testclient import TestClient

from app import db


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    from app.main import app
    with TestClient(app) as c:
        yield c


def test_topics_endpoint(client):
    r = client.get("/api/topics")
    assert r.status_code == 200
    assert "AI" in r.json()


def test_learning_click_updates_profile(client):
    from app.learning import apply_event

    user_vec = np.array([1, 0, 0], dtype=np.float32)
    art_vec = np.array([0, 1, 0], dtype=np.float32)
    with db.get_conn() as c:
        c.execute("INSERT INTO users (name, vector) VALUES (?, ?)", ("T", user_vec.tobytes()))
        c.execute("INSERT INTO articles (url, title, topic, embedding) VALUES (?, ?, ?, ?)",
                  ("http://x", "t", "AI", art_vec.tobytes()))
        c.execute("INSERT INTO user_topics (user_id, topic, weight) VALUES (1, 'AI', 1.0)")

    apply_event(1, 1, "click")

    with db.get_conn() as c:
        row = c.execute("SELECT vector FROM users WHERE id=1").fetchone()
        weight = c.execute("SELECT weight FROM user_topics WHERE user_id=1").fetchone()["weight"]
    vec = np.frombuffer(row["vector"], dtype=np.float32)
    assert vec[1] > 0                      # moved toward the clicked article
    assert weight == pytest.approx(1.1)    # topic weight went up