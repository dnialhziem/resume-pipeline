"""
compile.py — Convert resume HTML to PDF via Playwright (headless Chromium).

Usage:
    python compile.py <html_path> <pdf_path>

Requires: pip install playwright && python -m playwright install chromium
"""

import sys
from pathlib import Path

if len(sys.argv) != 3:
    print("Usage: python compile.py <html_path> <pdf_path>")
    sys.exit(1)

html_path = Path(sys.argv[1]).resolve()
pdf_path  = Path(sys.argv[2]).resolve()

if not html_path.exists():
    print(f"ERROR: HTML file not found: {html_path}")
    sys.exit(1)

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(html_path.as_uri(), wait_until="networkidle")
    page.pdf(
        path=str(pdf_path),
        format="A4",
        print_background=True,
        margin={"top": "0.5in", "bottom": "0.5in", "left": "0.5in", "right": "0.5in"},
    )
    browser.close()

print(f"SUCCESS: {pdf_path}")
