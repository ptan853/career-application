#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def export_pdf(input_html: Path, output_pdf: Path) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright is required for PDF export. Install with: python -m pip install playwright && python -m playwright install chromium", file=sys.stderr)
        raise SystemExit(3)

    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch()
        except Exception as exc:
            print(f"Playwright Chromium is not available: {exc}", file=sys.stderr)
            raise SystemExit(3) from exc
        page = browser.new_page()
        page.goto(input_html.resolve().as_uri(), wait_until="networkidle")
        page.emulate_media(media="print")
        output_pdf.parent.mkdir(parents=True, exist_ok=True)
        page.pdf(path=str(output_pdf), format="A4", print_background=True, prefer_css_page_size=True)
        browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Export rendered resume HTML to PDF using Playwright.")
    parser.add_argument("input_html", type=Path)
    parser.add_argument("output_pdf", type=Path, nargs="?")
    args = parser.parse_args()
    output = args.output_pdf or args.input_html.with_suffix(".pdf")
    export_pdf(args.input_html, output)
    print(output)


if __name__ == "__main__":
    main()
