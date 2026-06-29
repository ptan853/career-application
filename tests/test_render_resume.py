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
    assert "@media print" in html
    assert "@font-face" in html
    assert "NotoSansCJKsc-Regular.otf" in html


def test_render_peifeng_standard_with_optional_photo(tmp_path: Path) -> None:
    photo = tmp_path / "photo.jpg"
    photo.write_bytes(b"fake image bytes")
    document = {
        "schema_version": 1,
        "target_id": "target_visual_cn",
        "artifact_type": "resume",
        "language": "zh",
        "page_count": 1,
        "design_id": "peifeng-standard",
        "photo_policy": "provided",
        "photo_path": str(photo),
        "profile": {
            "display_name": "谭沛烽",
            "email": "tan19991103@outlook.com",
            "phone": "178-0123-1696",
            "location": "长沙",
            "links": [],
        },
        "sections": [
            {
                "section_id": "work",
                "title": "工作经历",
                "items": [
                    {
                        "heading": "算法工程师",
                        "meta": "2025 - 2026",
                        "bullets": [{"text": "构建预测优化与 Agent 工具链。"}],
                    }
                ],
            }
        ],
    }
    input_path = tmp_path / "resume_document.json"
    output = tmp_path / "resume.html"
    input_path.write_text(__import__("json").dumps(document, ensure_ascii=False), encoding="utf-8")

    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "render-resume.py"), str(input_path), str(output)],
        check=True,
    )
    html = output.read_text(encoding="utf-8")

    assert "Peifeng" not in html
    assert "profile-photo" in html
    assert "resume-header" in html
    assert "工作经历" in html
    assert "长沙" in html
    assert "border-bottom: 1.2px solid #333" in html


def test_render_hides_photo_slot_without_photo(tmp_path: Path) -> None:
    document = {
        "schema_version": 1,
        "target_id": "target_visual_cn",
        "artifact_type": "resume",
        "language": "zh",
        "page_count": 1,
        "design_id": "peifeng-standard",
        "photo_policy": "optional",
        "profile": {
            "display_name": "谭沛烽",
            "email": "tan19991103@outlook.com",
            "phone": "178-0123-1696",
            "location": "长沙",
            "links": [],
        },
        "sections": [],
    }
    input_path = tmp_path / "resume_document.json"
    output = tmp_path / "resume.html"
    input_path.write_text(__import__("json").dumps(document, ensure_ascii=False), encoding="utf-8")

    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "render-resume.py"), str(input_path), str(output)],
        check=True,
    )
    html = output.read_text(encoding="utf-8")

    assert '<img class="profile-photo"' not in html
    assert "resume-header no-photo" in html


def test_ats_classic_never_renders_photo_even_if_path_is_present(tmp_path: Path) -> None:
    photo = tmp_path / "photo.jpg"
    photo.write_bytes(b"fake image bytes")
    document = {
        "schema_version": 1,
        "target_id": "target_ats",
        "artifact_type": "resume",
        "language": "zh",
        "page_count": 1,
        "design_id": "ats-classic",
        "photo_policy": "provided",
        "photo_path": str(photo),
        "profile": {
            "display_name": "谭沛烽",
            "email": "tan19991103@outlook.com",
            "phone": "178-0123-1696",
            "location": "长沙",
            "links": [],
        },
        "sections": [],
    }
    input_path = tmp_path / "resume_document.json"
    output = tmp_path / "resume.html"
    input_path.write_text(__import__("json").dumps(document, ensure_ascii=False), encoding="utf-8")

    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "render-resume.py"), str(input_path), str(output)],
        check=True,
    )
    html = output.read_text(encoding="utf-8")

    assert '<img class="profile-photo"' not in html
    assert "resume-header no-photo" in html



def test_render_embeds_latin_font_before_cjk_font(tmp_path: Path) -> None:
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

    assert "CareerApplicationLatin" in html
    assert "CareerApplicationCJK" in html
    assert "Inter-Regular" in html
    assert html.index("font-family: 'CareerApplicationLatin'") < html.index("font-family: 'CareerApplicationCJK'")
    assert 'font-family: Arial, "CareerApplicationLatin", "CareerApplicationCJK"' in html



def test_templates_use_language_specific_font_stacks(tmp_path: Path) -> None:
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

    assert 'html:lang(en)' in html
    assert 'html:lang(zh),' in html
    assert 'font-family: Arial, "CareerApplicationLatin", "CareerApplicationCJK"' in html
    assert 'font-family: "CareerApplicationCJK", "CareerApplicationLatin", Arial' in html

    modern_css = (ROOT / "templates" / "styles" / "engineer-modern.css").read_text(encoding="utf-8")
    assert 'html:lang(en)' in modern_css
    assert 'font-family: "CareerApplicationLatin", Arial, "CareerApplicationCJK"' in modern_css
    assert 'font-family: "CareerApplicationCJK", "CareerApplicationLatin", Arial' in modern_css
