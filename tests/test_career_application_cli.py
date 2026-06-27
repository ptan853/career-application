from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "career_application.py"


def run_cli(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        check=check,
        text=True,
        capture_output=True,
    )


def write_vault(vault: Path, *, complete_profile: bool = True, event_status: str = "confirmed") -> None:
    (vault / "events").mkdir(parents=True)
    profile = {
        "display_name": "Pat Example" if complete_profile else "",
        "email": "pat@example.com",
        "phone": "+1 555 0100",
        "location": "San Francisco, CA",
    }
    (vault / "profile.yaml").write_text(
        "\n".join(
            [
                "schema_version: 1",
                "user:",
                f"  display_name: \"{profile['display_name']}\"",
                f"  email: {profile['email']}",
                f"  phone: \"{profile['phone']}\"",
                f"  location: \"{profile['location']}\"",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    event = {
        "schema_version": 1,
        "id": "evt_agent_platform",
        "title": "Agent Platform",
        "type": "project",
        "time": {"start": "2026-05", "end": "2026-06"},
        "status": event_status,
        "claims": ["Built tool orchestration and validation workflow."],
        "details": {"methods": "Python, tools, validation"},
    }
    (vault / "events" / "evt_agent_platform.json").write_text(
        json.dumps(event, indent=2), encoding="utf-8"
    )



def test_cli_exposes_only_html_rendering_for_resume_artifacts() -> None:
    result = run_cli("--help")
    assert "render-resume" in result.stdout
    assert "export-pdf" not in result.stdout
    assert "export-docx" not in result.stdout


def test_init_target_creates_workspace_state_and_jd(tmp_path: Path) -> None:
    root = tmp_path / "apps"
    result = run_cli(
        "--root",
        str(root),
        "init-target",
        "--company",
        "Example Corp",
        "--role",
        "AI Engineer",
        "--language",
        "en",
        "--artifact",
        "resume",
        "--channel",
        "ats",
        "--page-count",
        "1",
        "--jd-text",
        "Build LLM agent systems and evaluation workflows.",
    )

    target_dir = Path(result.stdout.strip())
    assert target_dir.exists()
    target = json.loads((target_dir / "target.json").read_text(encoding="utf-8"))
    state = json.loads((target_dir / "application-state.json").read_text(encoding="utf-8"))
    assert target["company"] == "Example Corp"
    assert target["role"] == "AI Engineer"
    assert target["artifact_goals"] == ["resume"]
    assert state["status"] == "planning"
    assert (target_dir / "jd.md").read_text(encoding="utf-8").startswith("Build LLM")
    assert (target_dir / "drafts").is_dir()
    assert (target_dir / "sources").is_dir()


def test_check_timeline_writes_readiness_and_reports_missing_profile(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    write_vault(vault, complete_profile=False)
    target_dir = tmp_path / "target"
    target_dir.mkdir()

    result = run_cli(
        "check-timeline",
        "--vault",
        str(vault),
        "--target-dir",
        str(target_dir),
        check=False,
    )

    readiness = json.loads((target_dir / "timeline_readiness.json").read_text(encoding="utf-8"))
    assert result.returncode == 2
    assert readiness["ready"] is False
    assert readiness["missing_profile_fields"] == ["display_name"]
    assert readiness["event_counts"]["confirmed"] == 1
    assert "display_name" in result.stdout


def test_create_plan_requires_ready_timeline_and_maps_sections_to_events(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    write_vault(vault)
    root = tmp_path / "apps"
    init = run_cli(
        "--root",
        str(root),
        "init-target",
        "--company",
        "Example Corp",
        "--role",
        "AI Engineer",
        "--language",
        "en",
        "--artifact",
        "resume",
        "--channel",
        "ats",
        "--page-count",
        "1",
        "--jd-text",
        "Need LLM agent engineering, tool orchestration, and evaluation.",
    )
    target_dir = Path(init.stdout.strip())
    run_cli("check-timeline", "--vault", str(vault), "--target-dir", str(target_dir))

    run_cli("create-plan", "--target-dir", str(target_dir))

    plan = json.loads((target_dir / "resume_plan.json").read_text(encoding="utf-8"))
    assert plan["page_count"] == 1
    assert [section["section_id"] for section in plan["sections"]] == [
        "summary",
        "skills",
        "projects",
        "education",
    ]
    projects = next(section for section in plan["sections"] if section["section_id"] == "projects")
    assert projects["selected_events"] == ["evt_agent_platform"]
    state = json.loads((target_dir / "application-state.json").read_text(encoding="utf-8"))
    assert state["status"] == "planning_resume"


def test_create_plan_refuses_when_timeline_is_not_ready(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    write_vault(vault, complete_profile=False)
    root = tmp_path / "apps"
    init = run_cli(
        "--root",
        str(root),
        "init-target",
        "--company",
        "Example Corp",
        "--role",
        "AI Engineer",
        "--language",
        "en",
        "--artifact",
        "resume",
        "--channel",
        "ats",
        "--page-count",
        "1",
        "--jd-text",
        "Need LLM agent engineering.",
    )
    target_dir = Path(init.stdout.strip())
    run_cli("check-timeline", "--vault", str(vault), "--target-dir", str(target_dir), check=False)

    result = run_cli("create-plan", "--target-dir", str(target_dir), check=False)

    assert result.returncode != 0
    assert not (target_dir / "resume_plan.json").exists()
    assert "Timeline is not ready" in result.stderr


def test_record_research_and_update_target_merge_agent_findings(tmp_path: Path) -> None:
    root = tmp_path / "apps"
    init = run_cli(
        "--root",
        str(root),
        "init-target",
        "--company",
        "Example Corp",
        "--role",
        "AI Engineer",
        "--language",
        "en",
        "--artifact",
        "resume",
        "--channel",
        "ats",
        "--page-count",
        "1",
        "--jd-text",
        "Initial JD text.",
    )
    target_dir = Path(init.stdout.strip())
    research = tmp_path / "research.json"
    research.write_text(
        json.dumps(
            {
                "summary": "Example Corp needs production LLM agent engineers.",
                "hiring_priorities": ["LLM agent engineering", "evaluation systems"],
                "must_have": ["Python", "tool orchestration"],
                "nice_to_have": ["LangGraph"],
                "keywords": ["LLM", "agent", "evaluation", "Python"],
                "company_context": ["Builds enterprise AI systems."],
                "risks": ["No explicit model training evidence found."],
            }
        ),
        encoding="utf-8",
    )

    run_cli(
        "record-research",
        "--target-dir",
        str(target_dir),
        "--file",
        str(research),
        "--source-url",
        "https://example.com/jobs/ai-engineer",
        "--source-type",
        "job_posting",
    )

    research_md = (target_dir / "research.md").read_text(encoding="utf-8")
    source_files = sorted((target_dir / "sources").glob("research_*.json"))
    assert "Example Corp needs production LLM agent engineers." in research_md
    assert len(source_files) == 1
    source = json.loads(source_files[0].read_text(encoding="utf-8"))
    assert source["source_url"] == "https://example.com/jobs/ai-engineer"
    assert source["source_type"] == "job_posting"

    run_cli("update-target", "--target-dir", str(target_dir))

    target = json.loads((target_dir / "target.json").read_text(encoding="utf-8"))
    assert target["hiring_priorities"][:2] == ["LLM agent engineering", "evaluation systems"]
    assert "tool orchestration" in target["must_have"]
    assert "LangGraph" in target["nice_to_have"]
    assert "No explicit model training evidence found." in target["risks"]
    assert target["research_sources"][0]["source_url"] == "https://example.com/jobs/ai-engineer"
    state = json.loads((target_dir / "application-state.json").read_text(encoding="utf-8"))
    assert state["status"] == "planning"


def test_rewrite_drafts_require_plan_and_build_resume_requires_approval(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    write_vault(vault)
    root = tmp_path / "apps"
    init = run_cli(
        "--root",
        str(root),
        "init-target",
        "--company",
        "Example Corp",
        "--role",
        "AI Engineer",
        "--language",
        "en",
        "--artifact",
        "resume",
        "--channel",
        "ats",
        "--page-count",
        "1",
        "--jd-text",
        "Need LLM agent engineering, tool orchestration, and evaluation.",
    )
    target_dir = Path(init.stdout.strip())
    run_cli("check-timeline", "--vault", str(vault), "--target-dir", str(target_dir))
    run_cli("create-plan", "--target-dir", str(target_dir))

    run_cli("create-rewrite-drafts", "--target-dir", str(target_dir), "--vault", str(vault))

    drafts = json.loads((target_dir / "drafts" / "rewrite_drafts.json").read_text(encoding="utf-8"))
    assert drafts["approval_status"] == "needs_event_approval"
    assert drafts["items"][0]["event_id"] == "evt_agent_platform"
    assert drafts["items"][0]["section_id"] == "projects"
    assert drafts["items"][0]["status"] == "needs_user_approval"
    assert "source_event_ids" in drafts["items"][0]["bullets"][0]

    blocked = run_cli("build-resume-document", "--target-dir", str(target_dir), check=False)
    assert blocked.returncode != 0
    assert "Unapproved rewrite drafts" in blocked.stderr

    run_cli("approve-rewrite", "--target-dir", str(target_dir), "--event-id", "evt_agent_platform")
    run_cli("build-resume-document", "--target-dir", str(target_dir))
    run_cli("render-resume", "--target-dir", str(target_dir))

    document = json.loads((target_dir / "drafts" / "resume_document.json").read_text(encoding="utf-8"))
    assert document["artifact_type"] == "resume"
    assert document["profile"]["display_name"] == "Pat Example"
    assert document["sections"][2]["section_id"] == "projects"
    assert document["sections"][2]["items"][0]["source_event_ids"] == ["evt_agent_platform"]
    html = (target_dir / "drafts" / "resume.html").read_text(encoding="utf-8")
    assert "Pat Example" in html
    assert "Agent Platform" in html
    assert not (target_dir / "drafts" / "resume.docx").exists()
    assert not (target_dir / "drafts" / "resume.pdf").exists()
    state = json.loads((target_dir / "application-state.json").read_text(encoding="utf-8"))
    assert state["status"] == "ready_for_review"
    artifact_paths = [artifact["path"] for artifact in state["artifact_versions"]]
    assert artifact_paths == ["drafts/resume_document.json", "drafts/resume.html"]
