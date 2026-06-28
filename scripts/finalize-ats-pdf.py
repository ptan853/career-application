#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def dependency_error(message: str) -> None:
    print(f"Cannot create verified ATS PDF: {message}", file=sys.stderr)
    raise SystemExit(3)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def finalize_ats_pdf(document_path: Path, html_path: Path, output_pdf: Path) -> None:
    document = json.loads(document_path.read_text(encoding="utf-8"))
    ensure_ats_document(document)
    verification: dict[str, Any] = {"ok": False, "warnings": [], "checks": {}}
    try:
        render_pdf_with_playwright(html_path, output_pdf)
        page_count = count_pdf_pages(output_pdf)
        verify_pdf_page_count(document, page_count)
        text_by_page = extract_pdf_text_by_page(output_pdf)
        text = "\n".join(text_by_page)
        text_result = verify_pdf_text(document, text)
        fill_result = verify_page_fill_policy(document, [count_visible_lines(page_text) for page_text in text_by_page])
        warnings = list(text_result.get("warnings", []))
        if fill_result.get("status") == "warning":
            warnings.append(fill_result.get("message", "Last page appears sparse."))
        verification = {
            "ok": True,
            "pdf_path": str(output_pdf),
            "page_count": page_count,
            "warnings": warnings,
            "checks": {
                "page_count": "passed",
                "ascii_text_layer": "passed",
                "cjk_text_extraction": "warning" if text_result.get("warnings") else "passed",
                "page_fill": fill_result.get("status", "passed"),
            },
            "page_fill": fill_result,
        }
    except BaseException:
        if output_pdf.exists():
            output_pdf.unlink()
        raise
    finally:
        if verification.get("ok"):
            write_json(output_pdf.with_name("resume_pdf_verification.json"), verification)


def ensure_ats_document(document: dict[str, Any]) -> None:
    if document.get("design_id") != "ats-classic":
        raise SystemExit("finalize-ats-pdf requires design_id=ats-classic")
    profile = document.get("profile", {})
    missing = [field for field in ("display_name", "email", "phone", "location") if not str(profile.get(field) or "").strip()]
    if missing:
        raise SystemExit("Cannot finalize ATS PDF with missing profile fields: " + ", ".join(missing))
    verify_layout_budget(document)


def verify_layout_budget(document: dict[str, Any]) -> None:
    budget = document.get("layout_budget") if isinstance(document.get("layout_budget"), dict) else {}
    body_font = float(budget.get("body_font_pt", 10.5))
    minimum_body_font = float(budget.get("minimum_body_font_pt", 10))
    line_height = float(budget.get("line_height", 1.24))
    page_margin = float(budget.get("page_margin_mm", 16))
    failures = []
    if minimum_body_font < 10:
        failures.append("minimum body font below 10pt")
    if body_font < minimum_body_font:
        failures.append("body font below declared minimum")
    if line_height < 1.15:
        failures.append("line height below 1.15")
    if page_margin < 10:
        failures.append("page margin below 10mm")
    if failures:
        raise SystemExit("Cannot finalize ATS PDF with unreadable layout budget: " + ", ".join(failures))


def render_pdf_with_playwright(html_path: Path, output_pdf: Path) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        dependency_error("Playwright is required for verified ATS PDF. Install Playwright and Chromium first.")

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch()
        except Exception as exc:
            dependency_error(f"Playwright Chromium is unavailable: {exc}")
        try:
            page = browser.new_page()
            page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
            page.emulate_media(media="print")
            page.pdf(
                path=str(output_pdf),
                format="A4",
                print_background=True,
                prefer_css_page_size=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
        finally:
            browser.close()
    if not output_pdf.exists() or not output_pdf.read_bytes().startswith(b"%PDF"):
        dependency_error("PDF generation did not produce a valid PDF file.")


def count_pdf_pages(pdf_path: Path) -> int:
    try:
        from pypdf import PdfReader
    except ImportError:
        dependency_error("pypdf is required to verify PDF page count.")
    return len(PdfReader(str(pdf_path)).pages)


def verify_pdf_page_count(document: dict[str, Any], actual_page_count: int) -> None:
    requested = int(document.get("page_count") or 1)
    if actual_page_count > requested:
        raise SystemExit(
            f"Verified ATS PDF has {actual_page_count} pages, exceeds requested page count {requested}; "
            "shorten or remove content instead of shrinking typography."
        )


def extract_pdf_text(pdf_path: Path) -> str:
    return "\n".join(extract_pdf_text_by_page(pdf_path))


def extract_pdf_text_by_page(pdf_path: Path) -> list[str]:
    try:
        from pypdf import PdfReader
    except ImportError:
        if shutil.which("pdftotext"):
            result = subprocess.run(["pdftotext", str(pdf_path), "-"], check=True, text=True, capture_output=True)
            return [result.stdout]
        dependency_error("pypdf or pdftotext is required to verify the PDF text layer.")
    reader = PdfReader(str(pdf_path))
    return [page.extract_text() or "" for page in reader.pages]


def count_visible_lines(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.strip())


def verify_page_fill_policy(document: dict[str, Any], line_counts: list[int]) -> dict[str, Any]:
    requested = int(document.get("page_count") or 1)
    policy = document.get("page_fill_policy") if isinstance(document.get("page_fill_policy"), dict) else {}
    default_threshold = 0.65 if requested >= 2 else 0.0
    threshold = float(policy.get("minimum_last_page_fill_ratio", default_threshold) or 0.0)
    if requested < 2 or threshold <= 0 or len(line_counts) < requested:
        return {"status": "passed", "last_page_fill_ratio": None}
    reference = max(line_counts[:-1] or [1])
    last = line_counts[-1]
    ratio = last / reference if reference else 1.0
    if ratio < threshold:
        return {
            "status": "warning",
            "last_page_fill_ratio": round(ratio, 3),
            "minimum_last_page_fill_ratio": threshold,
            "message": f"Last page fill ratio {ratio:.0%} is below requested minimum {threshold:.0%}; expand relevant evidence or reduce page_count.",
        }
    return {
        "status": "passed",
        "last_page_fill_ratio": round(ratio, 3),
        "minimum_last_page_fill_ratio": threshold,
    }


def verify_pdf_text(document: dict[str, Any], text: str) -> dict[str, Any]:
    normalized = " ".join(text.split())
    profile = document.get("profile", {})
    required = [
        profile.get("display_name", ""),
        profile.get("email", ""),
        profile.get("phone", ""),
        profile.get("location", ""),
    ]
    missing = [str(value) for value in required if value and str(value) not in normalized]
    missing_ascii = [value for value in missing if is_ascii_text(value)]
    missing_cjk_or_unicode = [value for value in missing if not is_ascii_text(value)]
    if missing_ascii:
        raise SystemExit("Verified ATS PDF text layer is missing required ASCII fields: " + ", ".join(missing_ascii))
    return {"ok": True, "warnings": missing_cjk_or_unicode}


def is_ascii_text(value: str) -> bool:
    try:
        value.encode("ascii")
    except UnicodeEncodeError:
        return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Finalize rendered ATS HTML as a verified text-based PDF.")
    parser.add_argument("document", type=Path)
    parser.add_argument("html", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    finalize_ats_pdf(args.document, args.html, args.output)
    print(args.output)


if __name__ == "__main__":
    main()
