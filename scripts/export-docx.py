#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import zipfile
from pathlib import Path
from typing import Any


CONTENT_TYPES = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>
'''

RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
'''

DOCUMENT_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>
'''

STYLES = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:rPr><w:sz w:val="21"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:rPr><w:b/><w:sz w:val="32"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="Heading 1"/><w:rPr><w:b/><w:sz w:val="24"/></w:rPr></w:style>
</w:styles>
'''


def esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=False)


def paragraph(text: str, style: str | None = None, bold: bool = False) -> str:
    style_xml = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    bold_xml = "<w:rPr><w:b/></w:rPr>" if bold else ""
    return f"<w:p>{style_xml}<w:r>{bold_xml}<w:t>{esc(text)}</w:t></w:r></w:p>"


def bullet(text: str) -> str:
    return paragraph("- " + text)


def document_xml(document: dict[str, Any]) -> str:
    profile = document.get("profile", {})
    parts: list[str] = []
    parts.append(paragraph(profile.get("display_name", ""), "Title"))
    contact = " | ".join(str(profile.get(key, "")) for key in ("phone", "email", "location") if profile.get(key))
    if contact:
        parts.append(paragraph(contact))
    for section in document.get("sections", []):
        parts.append(paragraph(section.get("title", ""), "Heading1"))
        for item in section.get("items", []):
            heading = item.get("heading", "")
            meta = item.get("meta", "")
            parts.append(paragraph(" | ".join(part for part in (heading, meta) if part), bold=True))
            for item_bullet in item.get("bullets", []):
                parts.append(bullet(item_bullet.get("text", "")))
    body = "".join(parts)
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>{body}<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134"/></w:sectPr></w:body>
</w:document>
'''


def export_docx(document_path: Path, output_path: Path) -> None:
    document = json.loads(document_path.read_text(encoding="utf-8"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", CONTENT_TYPES)
        docx.writestr("_rels/.rels", RELS)
        docx.writestr("word/_rels/document.xml.rels", DOCUMENT_RELS)
        docx.writestr("word/styles.xml", STYLES)
        docx.writestr("word/document.xml", document_xml(document))


def main() -> None:
    parser = argparse.ArgumentParser(description="Export resume_document.json to editable DOCX.")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    export_docx(args.input, args.output)
    print(args.output)


if __name__ == "__main__":
    main()
