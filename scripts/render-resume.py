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


def editable(text: str, key: str, tag: str = "span") -> str:
    return f'<{tag} class="editable" contenteditable="false" data-edit-key="{html.escape(key)}">{html.escape(text)}</{tag}>'


EDIT_MODE_CSS = """
.resume-edit-toolbar {
  position: fixed;
  top: 12px;
  right: 12px;
  z-index: 10;
  display: flex;
  gap: 6px;
  padding: 6px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid #c8d0d4;
  border-radius: 6px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}
.resume-edit-toolbar button {
  border: 1px solid #8a969d;
  background: #fff;
  color: #172026;
  border-radius: 4px;
  padding: 4px 8px;
  font: 12px Arial, sans-serif;
  cursor: pointer;
}
body.editing .editable {
  outline: 1px dashed #0f5f75;
  outline-offset: 2px;
}
@media print {
  .resume-edit-toolbar { display: none; }
  body { background: #fff; }
  .page { box-shadow: none; margin: 0; }
}
"""

EDIT_MODE_JS = r"""
(() => {
  const setEditing = (enabled) => {
    document.body.classList.toggle('editing', enabled);
    document.querySelectorAll('[contenteditable]').forEach((node) => {
      node.setAttribute('contenteditable', enabled ? 'true' : 'false');
    });
  };
  const saveHtml = () => {
    setEditing(false);
    const blob = new Blob(['<!doctype html>\n' + document.documentElement.outerHTML], { type: 'text/html' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'resume-edited.html';
    link.click();
    URL.revokeObjectURL(link.href);
  };
  document.querySelector('[data-action="toggle-edit"]')?.addEventListener('click', () => {
    setEditing(!document.body.classList.contains('editing'));
  });
  document.querySelector('[data-action="save-html"]')?.addEventListener('click', saveHtml);
  document.querySelector('[data-action="print-pdf"]')?.addEventListener('click', () => window.print());
  document.addEventListener('keydown', (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 's') {
      event.preventDefault();
      saveHtml();
    }
    if (event.key.toLowerCase() === 'e' && !event.metaKey && !event.ctrlKey && !event.altKey) {
      const active = document.activeElement;
      if (!active || active === document.body) setEditing(!document.body.classList.contains('editing'));
    }
  });
})();
"""


def render_contact(profile: dict) -> str:
    parts = [profile.get("phone", ""), profile.get("email", ""), profile.get("location", "")]
    for link in profile.get("links", []):
        if isinstance(link, dict) and link.get("url"):
            parts.append(link["url"])
    return " | ".join(html.escape(part) for part in parts if part)


def render_resume(document: dict, css: str) -> str:
    profile = document["profile"]
    sections = []
    for section_index, section in enumerate(document.get("sections", [])):
        items = []
        section_id = str(section.get("section_id") or section_index)
        for item_index, item in enumerate(section.get("items", [])):
            key_prefix = f"sections.{section_id}.items.{item_index}"
            heading = editable(str(item.get("heading", "")), f"{key_prefix}.heading")
            meta = editable(str(item.get("meta", "")), f"{key_prefix}.meta")
            bullets = "".join(
                f"<li>{editable(str(b.get('text', '')), f'{key_prefix}.bullets.{bullet_index}')}</li>"
                for bullet_index, b in enumerate(item.get("bullets", []))
            )
            items.append(
                f"<div class=\"item\"><div class=\"item-header\">{heading}{meta}</div><ul>{bullets}</ul></div>"
            )
        section_title = editable(str(section.get("title", "")), f"sections.{section_id}.title", "h2")
        sections.append(f"<section>{section_title}{''.join(items)}</section>")
    return f"""<!doctype html>
<html lang="{html.escape(document.get("language", "en"))}">
<head>
  <meta charset="utf-8">
  <title>{html.escape(profile.get("display_name", "Resume"))}</title>
  <style>{css}
{EDIT_MODE_CSS}</style>
</head>
<body>
  <div class="resume-edit-toolbar" aria-label="Resume edit toolbar">
    <button type="button" data-action="toggle-edit">Edit</button>
    <button type="button" data-action="save-html">Save HTML</button>
    <button type="button" data-action="print-pdf">Print PDF</button>
  </div>
  <main class="page">
    {editable(str(profile.get("display_name", "")), "profile.display_name", "h1")}
    <p class="contact editable" contenteditable="false" data-edit-key="profile.contact">{render_contact(profile)}</p>
    {''.join(sections)}
  </main>
  <script>{EDIT_MODE_JS}</script>
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
