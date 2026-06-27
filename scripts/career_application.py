#!/usr/bin/env python3
"""File-based CLI for target-specific career applications."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROFILE_REQUIRED_FIELDS = ("display_name", "email", "phone", "location")
READY_EVENT_STATUSES = {"confirmed", "needs_review"}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def compact_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d")


def slugify(value: str, fallback: str = "target") -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug[:64] or fallback


def root_path(args: argparse.Namespace) -> Path:
    if args.root:
        return Path(args.root).expanduser().resolve()
    return Path.home() / ".career-applications" / "targets"


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_yaml_scalar(value: str) -> Any:
    raw = value.strip()
    if raw == "null":
        return None
    if raw == "true":
        return True
    if raw == "false":
        return False
    if raw.startswith('"') and raw.endswith('"'):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw.strip('"')
    return raw


def read_profile(vault: Path) -> dict[str, Any]:
    profile = {"user": {field: "" for field in PROFILE_REQUIRED_FIELDS}}
    path = vault / "profile.yaml"
    if not path.exists():
        return profile

    current_section: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith(" ") and line.endswith(":"):
            current_section = line[:-1].strip()
            profile.setdefault(current_section, {})
            continue
        if ":" not in line:
            continue
        key, raw = line.split(":", 1)
        key = key.strip()
        value = parse_yaml_scalar(raw)
        if line.startswith("  ") and current_section:
            profile.setdefault(current_section, {})[key] = value
        else:
            profile[key] = value
            current_section = None
    return profile


def load_events(vault: Path) -> list[dict[str, Any]]:
    events_dir = vault / "events"
    if not events_dir.exists():
        return []
    events: list[dict[str, Any]] = []
    for path in sorted(events_dir.glob("evt_*.json")):
        try:
            event = read_json(path)
        except json.JSONDecodeError:
            continue
        events.append(event)
    return events


def target_dir_from_args(args: argparse.Namespace) -> Path:
    return Path(args.target_dir).expanduser().resolve()


def command_init_target(args: argparse.Namespace) -> None:
    root = root_path(args)
    root.mkdir(parents=True, exist_ok=True)
    target_id = f"target_{compact_date()}_{slugify(args.company or 'company')}_{slugify(args.role)}"
    target_dir = root / target_id
    suffix = 2
    while target_dir.exists():
        target_dir = root / f"{target_id}_{suffix}"
        suffix += 1
    target_dir.mkdir(parents=True)
    (target_dir / "drafts").mkdir()
    (target_dir / "sources").mkdir()

    target = {
        "schema_version": 1,
        "target_id": target_dir.name,
        "created_at": now_iso(),
        "mode": "company_role" if args.company else "role",
        "company": args.company or "",
        "role": args.role,
        "language": args.language,
        "region": args.region or "",
        "application_channel": args.channel,
        "artifact_goals": [args.artifact],
        "page_count": args.page_count,
        "hiring_priorities": extract_hiring_priorities(args.jd_text or ""),
        "must_have": [],
        "nice_to_have": [],
        "keywords": extract_keywords(args.jd_text or ""),
        "company_context": [],
        "candidate_positioning": "",
        "risks": [],
        "research_sources": [{"source_type": "user_provided", "label": "jd_text"}] if args.jd_text else [],
    }
    state = {
        "schema_version": 1,
        "application_id": target_dir.name.replace("target_", "app_", 1),
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "target": {"target_id": target_dir.name},
        "timeline_readiness": {},
        "section_strategy": {},
        "resume_plan": {},
        "artifact_versions": [],
        "decisions": [],
        "status": "planning",
    }

    write_json(target_dir / "target.json", target)
    write_json(target_dir / "application-state.json", state)
    (target_dir / "jd.md").write_text(args.jd_text or "", encoding="utf-8")
    (target_dir / "decisions.log").write_text("", encoding="utf-8")
    print(target_dir)


def extract_keywords(text: str) -> list[str]:
    candidates = [
        "LLM",
        "agent",
        "tool orchestration",
        "evaluation",
        "benchmark",
        "safety",
        "Python",
        "LangChain",
        "LangGraph",
        "RAG",
    ]
    lower = text.lower()
    return [item for item in candidates if item.lower() in lower]


def extract_hiring_priorities(text: str) -> list[str]:
    keywords = extract_keywords(text)
    if keywords:
        return keywords[:5]
    return ["target-relevant evidence"]


def command_check_timeline(args: argparse.Namespace) -> None:
    vault = Path(args.vault).expanduser().resolve() if args.vault else Path.home() / ".career-vault"
    target_dir = target_dir_from_args(args)
    profile = read_profile(vault)
    user = profile.get("user", {})
    missing = [field for field in PROFILE_REQUIRED_FIELDS if not str(user.get(field) or "").strip()]
    events = load_events(vault)
    confirmed = [event for event in events if event.get("status") == "confirmed"]
    needs_review = [event for event in events if event.get("status") == "needs_review"]
    ready_events = [event for event in events if event.get("status") in READY_EVENT_STATUSES]
    readiness = {
        "schema_version": 1,
        "ready": not missing and bool(ready_events),
        "vault": str(vault),
        "checked_at": now_iso(),
        "missing_profile_fields": missing,
        "event_counts": {
            "total": len(events),
            "confirmed": len(confirmed),
            "needs_review": len(needs_review),
            "usable": len(ready_events),
        },
        "usable_event_ids": [event.get("id") for event in ready_events if event.get("id")],
        "gaps": [],
    }
    if missing:
        readiness["gaps"].append("Missing required profile fields: " + ", ".join(missing))
    if not ready_events:
        readiness["gaps"].append("No confirmed or review-approved timeline events available.")
    write_json(target_dir / "timeline_readiness.json", readiness)
    update_state(target_dir, timeline_readiness=readiness, status="needs_timeline" if not readiness["ready"] else "planning")

    if readiness["ready"]:
        print("Timeline ready")
        return
    print("\n".join(readiness["gaps"]))
    raise SystemExit(2)


def update_state(target_dir: Path, **updates: Any) -> None:
    state_path = target_dir / "application-state.json"
    if state_path.exists():
        state = read_json(state_path)
    else:
        state = {"schema_version": 1, "status": "planning", "decisions": []}
    state.update(updates)
    state["updated_at"] = now_iso()
    write_json(state_path, state)


def command_create_plan(args: argparse.Namespace) -> None:
    target_dir = target_dir_from_args(args)
    target = read_json(target_dir / "target.json")
    readiness_path = target_dir / "timeline_readiness.json"
    if not readiness_path.exists():
        raise SystemExit("Run check-timeline before create-plan")
    readiness = read_json(readiness_path)
    if not readiness.get("ready"):
        raise SystemExit("Timeline is not ready. Fill gaps before creating a resume plan.")

    event_ids = readiness.get("usable_event_ids", [])
    sections = choose_sections(target, event_ids)
    positioning = build_positioning(target)
    plan = {
        "schema_version": 1,
        "target_id": target["target_id"],
        "positioning": positioning,
        "page_count": target.get("page_count", 1),
        "design_id": "ats-classic" if target.get("application_channel") == "ats" else "engineer-modern",
        "sections": sections,
        "gaps": [],
        "risks": ["Plan requires user approval before prose drafting."],
        "approval_status": "needs_user_approval",
    }
    write_json(target_dir / "resume_plan.json", plan)
    update_state(target_dir, resume_plan={"path": "resume_plan.json"}, status="planning_resume")
    print(target_dir / "resume_plan.json")


def build_positioning(target: dict[str, Any]) -> str:
    role = target.get("role") or "target role"
    priorities = target.get("hiring_priorities") or []
    if priorities:
        return f"Candidate positioned for {role} with evidence in {', '.join(priorities[:4])}."
    return f"Candidate positioned for {role} using verified career timeline evidence."


def choose_sections(target: dict[str, Any], event_ids: list[str]) -> list[dict[str, Any]]:
    sections = [
        {
            "section_id": "summary",
            "title": "Summary" if target.get("language") == "en" else "个人简介",
            "purpose": "State target-specific positioning in 2-3 lines.",
            "selected_events": [],
            "risks": [],
        },
        {
            "section_id": "skills",
            "title": "Skills" if target.get("language") == "en" else "专业技能",
            "purpose": "Surface keywords and capabilities required by the target.",
            "selected_events": [],
            "risks": [],
        },
        {
            "section_id": "projects",
            "title": "Projects" if target.get("language") == "en" else "项目经历",
            "purpose": "Show target-relevant implementation evidence from selected events.",
            "selected_events": event_ids[:4],
            "risks": [],
        },
        {
            "section_id": "education",
            "title": "Education" if target.get("language") == "en" else "教育背景",
            "purpose": "Include education credentials when available in the timeline.",
            "selected_events": [],
            "risks": ["No education event selected yet."],
        },
    ]
    return sections


def command_validate_state(args: argparse.Namespace) -> None:
    target_dir = target_dir_from_args(args)
    required = ["target.json", "application-state.json"]
    missing = [name for name in required if not (target_dir / name).exists()]
    if missing:
        print("Missing files: " + ", ".join(missing))
        raise SystemExit(2)
    state = read_json(target_dir / "application-state.json")
    if state.get("status") not in {
        "planning",
        "researching_target",
        "needs_timeline",
        "planning_resume",
        "rewriting_events",
        "rendering",
        "ready_for_review",
        "exported",
        "archived",
    }:
        print(f"Unsupported status: {state.get('status')}")
        raise SystemExit(2)
    print("State valid")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage target-specific career application workspaces.")
    parser.add_argument("--root", help="Application targets root. Defaults to ~/.career-applications/targets")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init-target", help="Create a target application workspace")
    init.add_argument("--company", default="")
    init.add_argument("--role", required=True)
    init.add_argument("--language", default="en")
    init.add_argument("--region", default="")
    init.add_argument("--artifact", default="resume")
    init.add_argument("--channel", default="ats")
    init.add_argument("--page-count", type=int, default=1)
    init.add_argument("--jd-text", default="")
    init.set_defaults(func=command_init_target)

    readiness = sub.add_parser("check-timeline", help="Check career-timeline vault readiness")
    readiness.add_argument("--vault")
    readiness.add_argument("--target-dir", required=True)
    readiness.set_defaults(func=command_check_timeline)

    plan = sub.add_parser("create-plan", help="Create a section-first resume plan")
    plan.add_argument("--target-dir", required=True)
    plan.set_defaults(func=command_create_plan)

    validate = sub.add_parser("validate-state", help="Validate target workspace state")
    validate.add_argument("--target-dir", required=True)
    validate.set_defaults(func=command_validate_state)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
