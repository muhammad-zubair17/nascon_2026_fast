import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE = Path(__file__).resolve().parent
env = Environment(loader=FileSystemLoader(BASE / "templates"),
                  autoescape=select_autoescape(["html"]))


def build_pdf(content, skipped_ids=()):
    stories = [s for s in content["stories"] if s["id"] not in skipped_ids]

    def role(r):
        return [s for s in stories if s["role"] == r]

    hero = role("hero")
    html = env.get_template("paper.html").render(
        paper_name=content["paper_name"],
        date=date.fromisoformat(content["date"]).strftime("%A, %d %B %Y"),
        reader=content["reader"],
        editor_note=content.get("editor_note", ""),
        three_things=content.get("three_things", []),
        hero=hero[0] if hero else None,
        secondary=role("secondary"),
        stretch=role("stretch"),
        briefs=role("brief"),
    )
    with tempfile.TemporaryDirectory() as tmp:
        html_path = Path(tmp) / "paper.html"
        pdf_path = Path(tmp) / "paper.pdf"
        html_path.write_text(html, encoding="utf-8")
        subprocess.run(
            [sys.executable, "-m", "app.render_pdf", str(html_path), str(pdf_path)],
            cwd=BASE.parent, check=True, timeout=90,
        )
        return pdf_path.read_bytes()