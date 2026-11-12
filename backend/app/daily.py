import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .db import get_conn, init_db
from .edition import get_or_create

BACKEND_DIR = Path(__file__).resolve().parent.parent
INTERVAL_HOURS = 12
CHECK_EVERY_SECONDS = 30 * 60


def _run(module):
    print(f"[daily] running {module} ...")
    subprocess.run([sys.executable, "-m", module], cwd=BACKEND_DIR, check=True)


def _last_run():
    with get_conn() as c:
        c.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)")
        row = c.execute("SELECT value FROM meta WHERE key='last_daily'").fetchone()
    return datetime.fromisoformat(row["value"]) if row else None


def _set_last_run():
    with get_conn() as c:
        c.execute(
            "INSERT INTO meta (key, value) VALUES ('last_daily', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (datetime.now(timezone.utc).isoformat(),))


def run_daily():
    init_db()
    _run("app.ingest")
    _run("app.embed_articles")
    with get_conn() as c:
        uids = [r["id"] for r in c.execute("SELECT id FROM users")]
    for uid in uids:
        try:
            get_or_create(uid, force=False)
            print(f"[daily] edition ready for user {uid}")
        except Exception as e:
            print(f"[daily] user {uid} failed: {e}")
    _set_last_run()
    print("[daily] done")


def _loop():
    while True:
        try:
            last = _last_run()
            due = last is None or datetime.now(timezone.utc) - last >= timedelta(hours=INTERVAL_HOURS)
            if due:
                run_daily()
        except Exception as e:
            print(f"[daily] scheduler error: {e}")
        time.sleep(CHECK_EVERY_SECONDS)


def start_scheduler():
    threading.Thread(target=_loop, daemon=True, name="daily-refresh").start()
    print("[daily] scheduler started")


if __name__ == "__main__":
    run_daily()