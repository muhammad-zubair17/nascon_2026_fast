"""Daily job: ingest news, embed it, then rebuild every reader's edition.

Run manually:  python -m app.daily   (from the backend folder)
"""
import subprocess
import sys
from pathlib import Path

from .db import get_conn, init_db
from .edition import get_or_create

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _run(module):
    print(f"[daily] running {module} ...")
    subprocess.run([sys.executable, "-m", module], cwd=BACKEND_DIR, check=True)


def run_daily():
    init_db()
    _run("app.ingest")
    _run("app.embed_articles")
    with get_conn() as c:
        uids = [r["id"] for r in c.execute("SELECT id FROM users")]
    for uid in uids:
        try:
            get_or_create(uid, force=True)
            print(f"[daily] edition ready for user {uid}")
        except Exception as e:
            print(f"[daily] user {uid} failed: {e}")
    print("[daily] done")


if __name__ == "__main__":
    run_daily()