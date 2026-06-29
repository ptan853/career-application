#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from urllib.parse import quote


def load_design(skill_root: Path, design_id: str) -> tuple[str, str]:
    designs = json.loads((skill_root / "templates" / "designs.json").read_text(encoding="utf-8"))
    design = designs["designs"].get(design_id)
    if design is None:
        raise SystemExit(f"Unknown design_id: {design_id}")
    css = (skill_root / "templates" / design["style_file"]).read_text(encoding="utf-8")
    return design["label"], bundled_font_face(skill_root) + typography_variables(design.get("typography_budget", {})) + css


def bundled_font_face(skill_root: Path) -> str:
    font_path = skill_root / "assets" / "fonts" / "NotoSansCJKsc-Regular.otf"
    if not font_path.exists():
        return ""
    return (
        "@font-face {\n"
        "  font-family: 'CareerApplicationCJK';\n"
        f"  src: url('{font_path.resolve().as_uri()}') format('opentype');\n"
        "  font-weight: 400;\n"
        "  font-style: normal;\n"
        "  font-display: swap;\n"
        "}\n"
    )


def format_pt(value: object) -> str:
    number = float(value)
    return str(int(number)) if number.is_integer() else str(number)


def typography_variables(budget: dict) -> str:
    if not budget:
        return ""
    return (
        ":root {\n"
        f"  --resume-body-font-size: {format_pt(budget.get('body_font_pt', 10.5))}pt;\n"
        f"  --resume-min-body-font-size: {format_pt(budget.get('minimum_body_font_pt', 10))}pt;\n"
        f"  --resume-heading-font-size: {format_pt(budget.get('heading_font_pt', 12))}pt;\n"
        f"  --resume-name-font-size: {format_pt(budget.get('name_font_pt', 20))}pt;\n"
        f"  --resume-line-height: {budget.get('line_height', 1.24)};\n"
        f"  --resume-page-margin: {format_pt(budget.get('page_margin_mm', 16))}mm;\n"
        "}\n"
    )


def editable(text: str, key: str, tag: str = "span") -> str:
    return f'<{tag} class="editable" contenteditable="false" data-edit-key="{html.escape(key)}">{html.escape(text)}</{tag}>'


def photo_uri(document: dict) -> str:
    if document.get("design_id") == "ats-classic":
        return ""
    if document.get("photo_policy") not in {"optional", "provided"}:
        return ""
    profile = document.get("profile", {}) if isinstance(document.get("profile"), dict) else {}
    raw = document.get("photo_path") or profile.get("photo_path")
    photo = profile.get("photo")
    if not raw and isinstance(photo, dict):
        raw = photo.get("path")
    if not raw:
        return ""
    text = str(raw).strip()
    if not text:
        return ""
    if text.startswith(("http://", "https://", "data:", "file:")):
        return text
    path = Path(text).expanduser()
    if path.exists():
        return path.resolve().as_uri()
    return quote(text, safe="/:#?&=%")


def render_header(document: dict) -> str:
    profile = document["profile"]
    photo = photo_uri(document)
    header_class = "resume-header" if photo else "resume-header no-photo"
    name = editable(str(profile.get("display_name", "")), "profile.display_name", "h1")
    contact = f'<p class="contact editable" contenteditable="false" data-edit-key="profile.contact">{render_contact(profile)}</p>'
    image = f'<img class="profile-photo" src="{html.escape(photo)}" alt="Profile photo">' if photo else ""
    return f'<header class="{header_class}"><div class="identity">{name}{contact}</div>{image}</header>'


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
  </div>
  <main class="page">
    {render_header(document)}
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
