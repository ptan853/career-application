from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_render_resume_example(tmp_path: Path) -> None:
    output = tmp_path / "resume.html"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "render-resume.py"),
            str(ROOT / "examples" / "resume-document.example.json"),
            str(output),
        ],
        check=True,
    )
    html = output.read_text(encoding="utf-8")
    assert "Example Candidate" in html
    assert "Projects" in html
    assert "Agent Workflow Platform" in html
    assert "contenteditable" in html
    assert 'data-edit-key="sections.projects.items.0.heading"' in html
    assert 'data-edit-key="sections.projects.items.0.bullets.0"' in html
    assert "resume-edit-toolbar" in html
    assert "window.print()" in html
    assert "@media print" in html


def test_export_pdf_cli_writes_pdf_when_playwright_is_available(tmp_path: Path) -> None:
    html_file = tmp_path / "resume.html"
    pdf_file = tmp_path / "resume.pdf"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "render-resume.py"),
            str(ROOT / "examples" / "resume-document.example.json"),
            str(html_file),
        ],
        check=True,
    )
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "export-pdf.py"),
            str(html_file),
            str(pdf_file),
        ],
        text=True,
        capture_output=True,
    )
    if result.returncode == 3:
        assert "Playwright" in result.stderr
        return
    assert result.returncode == 0, result.stderr
    assert pdf_file.exists()
    assert pdf_file.read_bytes().startswith(b"%PDF")


def test_export_docx_cli_writes_editable_docx(tmp_path: Path) -> None:
    output = tmp_path / "resume.docx"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "export-docx.py"),
            str(ROOT / "examples" / "resume-document.example.json"),
            str(output),
        ],
        check=True,
    )
    assert output.exists()
    data = output.read_bytes()
    assert data.startswith(b"PK")
    import zipfile
    with zipfile.ZipFile(output) as archive:
        document_xml = archive.read("word/document.xml").decode("utf-8")
    assert "Example Candidate" in document_xml
    assert "Agent Workflow Platform" in document_xml
