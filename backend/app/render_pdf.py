import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

html_path, pdf_path = sys.argv[1], sys.argv[2]

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    try:
        page.goto(Path(html_path).as_uri(), wait_until="networkidle", timeout=25000)
    except Exception:
        pass  # a slow image shouldn't block the PDF
    page.pdf(path=pdf_path, prefer_css_page_size=True, print_background=True)
    browser.close()