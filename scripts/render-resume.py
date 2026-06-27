#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


def load_design(skill_root: Path, design_id: str) -> tuple[str, str]:
    designs = json.loads((skill_root / "templates" / "designs.json").read_text(encoding="utf-8"))
    design = designs["designs"].get(design_id)
    if design is None:
        raise SystemExit(f"Unknown design_id: {design_id}")
    css = (skill_root / "templates" / design["style_file"]).read_text(encoding="utf-8")
    return design["label"], css


def render_contact(profile: dict) -> str:
    parts = [profile.get("phone", ""), profile.get("email", ""), profile.get("location", "")]
    for link in profile.get("links", []):
        if isinstance(link, dict) and link.get("url"):
            parts.append(link["url"])
    return " | ".join(html.escape(part) for part in parts if part)


def render_resume(document: dict, css: str) -> str:
    profile = document["profile"]
    sections = []
    for section in document.get("sections", []):
        items = []
        for item in section.get("items", []):
            heading = html.escape(item.get("heading", ""))
            meta = html.escape(item.get("meta", ""))
            bullets = "".join(f"<li>{html.escape(b.get('text', ''))}</li>" for b in item.get("bullets", []))
            items.append(
                f"<div class=\"item\"><div class=\"item-header\"><span>{heading}</span><span>{meta}</span></div><ul>{bullets}</ul></div>"
            )
        sections.append(f"<section><h2>{html.escape(section.get('title', ''))}</h2>{''.join(items)}</section>")
    return f"""<!doctype html>
<html lang="{html.escape(document.get("language", "en"))}">
<head>
  <meta charset="utf-8">
  <title>{html.escape(profile.get("display_name", "Resume"))}</title>
  <style>{css}</style>
</head>
<body>
  <main class="page">
    <h1>{html.escape(profile.get("display_name", ""))}</h1>
    <p class="contact">{render_contact(profile)}</p>
    {''.join(sections)}
  </main>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Render resume_document.json to editable HTML.")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()

    document = json.loads(args.input.read_text(encoding="utf-8"))
    _, css = load_design(args.skill_root, document.get("design_id", "ats-classic"))
    args.output.write_text(render_resume(document, css), encoding="utf-8")


if __name__ == "__main__":
    main()
