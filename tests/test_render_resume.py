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
