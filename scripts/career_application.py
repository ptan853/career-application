#!/usr/bin/env python3
"""File-based CLI for target-specific career applications."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
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


def has_target_context(args: argparse.Namespace) -> bool:
    return any(
        str(getattr(args, field, "") or "").strip()
        for field in ("role", "company", "domain", "industry", "jd_text")
    )


def target_mode(args: argparse.Namespace) -> str:
    if args.company and args.role:
        return "company_role"
    if args.role:
        return "role"
    return "target_context"


def resolve_photo_policy(template: str, requested: str) -> str:
    if template == "ats-classic":
        return "disabled"
    if requested == "auto":
        return "optional"
    if requested == "none":
        return "disabled"
    return requested


def design_typography_budget(design_id: str) -> dict[str, Any]:
    designs_path = Path(__file__).resolve().parents[1] / "templates" / "designs.json"
    designs = read_json(designs_path)
    design = designs.get("designs", {}).get(design_id)
    if not design:
        raise SystemExit(f"Unknown design_id: {design_id}")
    return dict(design.get("typography_budget", {}))


def page_fill_policy(target: dict[str, Any]) -> dict[str, Any]:
    if int(target.get("page_count") or 1) < 2:
        return {"mode": "fit_within_requested_pages"}
    return {"mode": "near_full_requested_pages", "minimum_last_page_fill_ratio": 0.65}


def command_init_target(args: argparse.Namespace) -> None:
    if not has_target_context(args):
        raise SystemExit("Provide at least one target context: --role, --company, --domain, --industry, or --jd-text")

    root = root_path(args)
    root.mkdir(parents=True, exist_ok=True)
    target_slug = args.role or args.company or args.domain or args.industry or "target"
    target_id = f"target_{compact_date()}_{slugify(args.company or 'target')}_{slugify(target_slug)}"
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
        "mode": target_mode(args),
        "company": args.company or "",
        "role": args.role or "",
        "domain": args.domain or "",
        "industry": args.industry or "",
        "language": args.language,
        "region": args.region or "",
        "application_channel": args.channel,
        "artifact_goals": [args.artifact],
        "page_count": args.page_count,
        "template_preference": args.template,
        "photo_policy": resolve_photo_policy(args.template, args.photo),
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
    design_id = target.get("template_preference", "ats-classic")
    plan = {
        "schema_version": 1,
        "target_id": target["target_id"],
        "positioning": positioning,
        "page_count": target.get("page_count", 1),
        "design_id": design_id,
        "photo_policy": target.get("photo_policy", "disabled"),
        "layout_budget": design_typography_budget(design_id),
        "page_fill_policy": page_fill_policy(target),
        "sections": sections,
        "gaps": [],
        "risks": ["Plan requires user approval before prose drafting."],
        "approval_status": "needs_user_approval",
    }
    write_json(target_dir / "resume_plan.json", plan)
    update_state(target_dir, resume_plan={"path": "resume_plan.json"}, status="planning_resume")
    print(target_dir / "resume_plan.json")


def command_record_research(args: argparse.Namespace) -> None:
    target_dir = target_dir_from_args(args)
    research = load_research_input(Path(args.file).expanduser().resolve())
    source_id = f"research_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    record = {
        "schema_version": 1,
        "id": source_id,
        "recorded_at": now_iso(),
        "source_url": args.source_url or "",
        "source_type": args.source_type,
        "confidence": args.confidence,
        "research": research,
    }
    source_path = target_dir / "sources" / f"{source_id}.json"
    write_json(source_path, record)
    append_research_markdown(target_dir / "research.md", record)
    update_state(target_dir, status="researching_target")
    print(source_path)


def load_research_input(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
        if not isinstance(data, dict):
            raise SystemExit("Research JSON must be an object")
        return data
    return {"summary": text.strip()}


def append_research_markdown(path: Path, record: dict[str, Any]) -> None:
    research = record["research"]
    lines = [
        f"## {record['id']}",
        "",
        f"- Source type: {record['source_type']}",
        f"- Source URL: {record['source_url'] or 'n/a'}",
        f"- Recorded at: {record['recorded_at']}",
        f"- Confidence: {record['confidence']}",
        "",
        str(research.get("summary", "")).strip(),
        "",
    ]
    for key in ("hiring_priorities", "must_have", "nice_to_have", "keywords", "company_context", "risks"):
        values = [str(value) for value in research.get(key, []) if str(value).strip()]
        if values:
            lines.extend([f"### {key}", ""])
            lines.extend(f"- {value}" for value in values)
            lines.append("")
    existing = path.read_text(encoding="utf-8") if path.exists() else "# Target Research\n\n"
    path.write_text(existing.rstrip() + "\n\n" + "\n".join(lines), encoding="utf-8")


def command_update_target(args: argparse.Namespace) -> None:
    target_dir = target_dir_from_args(args)
    target_path = target_dir / "target.json"
    target = read_json(target_path)
    source_records = [read_json(path) for path in sorted((target_dir / "sources").glob("research_*.json"))]
    for record in source_records:
        research = record.get("research", {})
        for field in ("hiring_priorities", "must_have", "nice_to_have", "keywords", "company_context", "risks"):
            target[field] = merge_unique(research.get(field, []), target.get(field, []))
        source_summary = {
            "id": record.get("id"),
            "source_type": record.get("source_type"),
            "source_url": record.get("source_url", ""),
            "recorded_at": record.get("recorded_at"),
            "confidence": record.get("confidence"),
        }
        target["research_sources"] = merge_source_summaries([source_summary], target.get("research_sources", []))
    target["updated_at"] = now_iso()
    write_json(target_path, target)
    update_state(target_dir, status="planning")
    print(target_path)


def merge_unique(existing: Any, incoming: Any) -> list[str]:
    values: list[str] = []
    for collection in (existing if isinstance(existing, list) else [], incoming if isinstance(incoming, list) else []):
        for item in collection:
            text = str(item).strip()
            if text and text not in values:
                values.append(text)
    return values


def merge_source_summaries(primary: Any, secondary: Any) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    for collection in (primary if isinstance(primary, list) else [], secondary if isinstance(secondary, list) else []):
        for item in collection:
            if not isinstance(item, dict):
                continue
            key = (item.get("id"), item.get("source_url"), item.get("label"))
            if any((value.get("id"), value.get("source_url"), value.get("label")) == key for value in values):
                continue
            values.append(item)
    return values


def command_create_rewrite_drafts(args: argparse.Namespace) -> None:
    target_dir = target_dir_from_args(args)
    vault = Path(args.vault).expanduser().resolve() if args.vault else Path.home() / ".career-vault"
    plan_path = target_dir / "resume_plan.json"
    if not plan_path.exists():
        raise SystemExit("Run create-plan before create-rewrite-drafts")
    plan = read_json(plan_path)
    events = {event.get("id"): event for event in load_events(vault) if event.get("id")}
    items: list[dict[str, Any]] = []
    for section in plan.get("sections", []):
        for event_id in section.get("selected_events", []):
            event = events.get(event_id)
            if not event:
                continue
            items.append(build_rewrite_item(plan, section, event))
    drafts = {
        "schema_version": 1,
        "target_id": plan["target_id"],
        "created_at": now_iso(),
        "approval_status": "needs_event_approval" if items else "no_events_selected",
        "items": items,
    }
    output = target_dir / "drafts" / "rewrite_drafts.json"
    write_json(output, drafts)
    update_state(target_dir, status="rewriting_events")
    print(output)


def build_rewrite_item(plan: dict[str, Any], section: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    claims = [str(claim) for claim in event.get("claims", []) if str(claim).strip()]
    first_claim = claims[0] if claims else f"Worked on {event.get('title', 'this experience')}."
    bullet = adapt_claim_to_target(first_claim, plan)
    return {
        "event_id": event["id"],
        "section_id": section["section_id"],
        "status": "needs_user_approval",
        "target_relevance": section.get("purpose", ""),
        "source_title": event.get("title", ""),
        "heading": event.get("title", ""),
        "meta": format_event_meta(event),
        "factual_inputs_used": {
            "claims": claims,
            "details": event.get("details", {}),
        },
        "bullets": [
            {
                "text": bullet,
                "source_event_ids": [event["id"]],
                "source_claims": claims[:1],
                "risk": "confirmed" if event.get("status") == "confirmed" else "needs_review",
            }
        ],
        "unsupported_or_weak_claims": [],
    }


def adapt_claim_to_target(claim: str, plan: dict[str, Any]) -> str:
    text = claim.strip().rstrip(".")
    priorities = []
    for section in plan.get("sections", []):
        if section.get("section_id") in {"summary", "skills"}:
            continue
        purpose = section.get("purpose", "")
        if purpose:
            priorities.append(purpose)
    if "using" in text.lower() or "with" in text.lower():
        return text + "."
    return text + " for the target role's evidence needs."


def format_event_meta(event: dict[str, Any]) -> str:
    parts = []
    organization = event.get("organization") or event.get("company")
    role = event.get("role")
    if organization:
        parts.append(str(organization))
    if role:
        parts.append(str(role))
    time = event.get("time") if isinstance(event.get("time"), dict) else {}
    start = time.get("start")
    end = time.get("end")
    if start or end:
        parts.append(f"{start or ''} - {end or 'Present'}")
    return " | ".join(parts)


def command_approve_rewrite(args: argparse.Namespace) -> None:
    target_dir = target_dir_from_args(args)
    drafts_path = target_dir / "drafts" / "rewrite_drafts.json"
    if not drafts_path.exists():
        raise SystemExit("Run create-rewrite-drafts before approve-rewrite")
    drafts = read_json(drafts_path)
    matched = False
    for item in drafts.get("items", []):
        if item.get("event_id") == args.event_id:
            item["status"] = "approved"
            item["approved_at"] = now_iso()
            matched = True
    if not matched:
        raise SystemExit(f"No rewrite draft for event_id: {args.event_id}")
    drafts["approval_status"] = (
        "approved" if all(item.get("status") == "approved" for item in drafts.get("items", [])) else "needs_event_approval"
    )
    write_json(drafts_path, drafts)
    print(drafts_path)


def command_build_resume_document(args: argparse.Namespace) -> None:
    target_dir = target_dir_from_args(args)
    target = read_json(target_dir / "target.json")
    plan = read_json(target_dir / "resume_plan.json")
    drafts_path = target_dir / "drafts" / "rewrite_drafts.json"
    if not drafts_path.exists():
        raise SystemExit("Run create-rewrite-drafts before build-resume-document")
    drafts = read_json(drafts_path)
    unapproved = [item.get("event_id") for item in drafts.get("items", []) if item.get("status") != "approved"]
    if unapproved:
        raise SystemExit("Unapproved rewrite drafts: " + ", ".join(str(item) for item in unapproved))
    readiness = read_json(target_dir / "timeline_readiness.json")
    vault = Path(readiness["vault"])
    profile = read_profile(vault).get("user", {})
    draft_items = {(item["section_id"], item["event_id"]): item for item in drafts.get("items", [])}
    sections: list[dict[str, Any]] = []
    for section in plan.get("sections", []):
        items = [
            draft_items[(section["section_id"], event_id)]
            for event_id in section.get("selected_events", [])
            if (section["section_id"], event_id) in draft_items
        ]
        sections.append(
            {
                "section_id": section["section_id"],
                "title": section["title"],
                "purpose": section.get("purpose", ""),
                "items": [
                    {
                        "source_event_ids": [item["event_id"]],
                        "heading": item.get("heading", ""),
                        "meta": item.get("meta", ""),
                        "bullets": item.get("bullets", []),
                    }
                    for item in items
                ],
            }
        )
    document = {
        "schema_version": 1,
        "target_id": target["target_id"],
        "artifact_type": "resume",
        "language": target.get("language", "en"),
        "page_count": plan.get("page_count", 1),
        "design_id": plan.get("design_id", "ats-classic"),
        "photo_policy": plan.get("photo_policy", "disabled"),
        "layout_budget": plan.get("layout_budget", {}),
        "page_fill_policy": plan.get("page_fill_policy", {}),
        "profile": {
            "display_name": profile.get("display_name", ""),
            "email": profile.get("email", ""),
            "phone": profile.get("phone", ""),
            "location": profile.get("location", ""),
            "links": [],
        },
        "sections": sections,
        "risks": plan.get("risks", []),
        "change_report": ["Built from approved rewrite drafts."],
    }
    output = target_dir / "drafts" / "resume_document.json"
    write_json(output, document)
    update_state(target_dir, artifact_versions=[{"type": "resume_document", "path": "drafts/resume_document.json"}], status="ready_for_review")
    print(output)


def command_render_resume(args: argparse.Namespace) -> None:
    target_dir = target_dir_from_args(args)
    render_resume_to_html(target_dir)
    print(target_dir / "drafts" / "resume.html")


def render_resume_to_html(target_dir: Path) -> None:
    document_path = target_dir / "drafts" / "resume_document.json"
    if not document_path.exists():
        raise SystemExit("Run build-resume-document before render-resume")
    output = target_dir / "drafts" / "resume.html"
    renderer = load_resume_renderer()
    document = read_json(document_path)
    _, css = renderer.load_design(Path(__file__).resolve().parents[1], document.get("design_id", "ats-classic"))
    output.write_text(renderer.render_resume(document, css), encoding="utf-8")
    append_artifact(target_dir, {"type": "resume_html", "path": "drafts/resume.html"})


def command_revise_resume_document(args: argparse.Namespace) -> None:
    target_dir = target_dir_from_args(args)
    document_path = target_dir / "drafts" / "resume_document.json"
    if not document_path.exists():
        raise SystemExit("Run build-resume-document before revise-resume-document")
    document = read_json(document_path)
    apply_resume_edit(document, args.edit_key, args.text)
    reason = args.reason or f"Updated {args.edit_key}."
    document.setdefault("change_report", []).append(reason)
    write_json(document_path, document)
    render_resume_to_html(target_dir)
    print(document_path)


def command_apply_resume_patch(args: argparse.Namespace) -> None:
    target_dir = target_dir_from_args(args)
    document_path = target_dir / "drafts" / "resume_document.json"
    if not document_path.exists():
        raise SystemExit("Run build-resume-document before apply-resume-patch")
    patch = read_json(Path(args.patch).expanduser().resolve())
    document = read_json(document_path)
    apply_resume_patch(document, patch)
    reason = str(patch.get("reason") or "Applied resume patch.").strip()
    if reason:
        document.setdefault("change_report", []).append(reason)
    write_json(document_path, document)
    render_resume_to_html(target_dir)
    print(document_path)


def apply_resume_patch(document: dict[str, Any], patch: dict[str, Any]) -> None:
    operations = patch.get("operations")
    if not isinstance(operations, list):
        raise SystemExit("Resume patch must contain an operations list")
    for operation in operations:
        if not isinstance(operation, dict):
            raise SystemExit("Resume patch operation must be an object")
        apply_resume_patch_operation(document, operation)


def apply_resume_patch_operation(document: dict[str, Any], operation: dict[str, Any]) -> None:
    op = operation.get("op")
    if op == "rename-section":
        find_section(document, required_str(operation, "section_id"))["title"] = required_str(operation, "title")
        return
    if op == "add-section":
        section = operation.get("section")
        if not isinstance(section, dict):
            raise SystemExit("add-section requires section object")
        section = normalize_section(section)
        sections = document.setdefault("sections", [])
        index = bounded_insert_index(operation.get("index", len(sections)), len(sections))
        sections.insert(index, section)
        return
    if op == "remove-section":
        sections = document.get("sections", [])
        index = section_index(document, required_str(operation, "section_id"))
        sections.pop(index)
        return
    if op == "move-section":
        sections = document.get("sections", [])
        index = section_index(document, required_str(operation, "section_id"))
        section = sections.pop(index)
        sections.insert(bounded_insert_index(operation.get("to_index"), len(sections)), section)
        return
    if op == "add-item":
        section = find_section(document, required_str(operation, "section_id"))
        item = operation.get("item")
        if not isinstance(item, dict):
            raise SystemExit("add-item requires item object")
        items = section.setdefault("items", [])
        items.insert(bounded_insert_index(operation.get("index", len(items)), len(items)), normalize_item(item))
        return
    if op == "remove-item":
        items = find_section(document, required_str(operation, "section_id")).setdefault("items", [])
        items.pop(required_index(operation, "item_index", len(items)))
        return
    if op == "move-item":
        items = find_section(document, required_str(operation, "section_id")).setdefault("items", [])
        item = items.pop(required_index(operation, "from_index", len(items)))
        items.insert(bounded_insert_index(operation.get("to_index"), len(items)), item)
        return
    if op == "update-item":
        item = get_item(document, operation)
        for field in ("heading", "meta"):
            if field in operation:
                item[field] = str(operation[field])
        if "source_event_ids" in operation:
            item["source_event_ids"] = list_of_strings(operation["source_event_ids"], "source_event_ids")
        return
    if op == "add-bullet":
        item = get_item(document, operation)
        bullets = item.setdefault("bullets", [])
        bullet = {
            "text": required_str(operation, "text"),
            "source_event_ids": list_of_strings(operation.get("source_event_ids", item.get("source_event_ids", [])), "source_event_ids"),
            "source_claims": list_of_strings(operation.get("source_claims", []), "source_claims"),
            "risk": str(operation.get("risk", "needs_review")),
        }
        bullets.insert(bounded_insert_index(operation.get("index", len(bullets)), len(bullets)), bullet)
        return
    if op == "remove-bullet":
        bullets = get_item(document, operation).setdefault("bullets", [])
        bullets.pop(required_index(operation, "bullet_index", len(bullets)))
        return
    if op == "move-bullet":
        bullets = get_item(document, operation).setdefault("bullets", [])
        bullet = bullets.pop(required_index(operation, "from_index", len(bullets)))
        bullets.insert(bounded_insert_index(operation.get("to_index"), len(bullets)), bullet)
        return
    if op == "update-bullet":
        bullets = get_item(document, operation).setdefault("bullets", [])
        bullet = bullets[required_index(operation, "bullet_index", len(bullets))]
        if "text" in operation:
            bullet["text"] = str(operation["text"])
        if "source_event_ids" in operation:
            bullet["source_event_ids"] = list_of_strings(operation["source_event_ids"], "source_event_ids")
        if "source_claims" in operation:
            bullet["source_claims"] = list_of_strings(operation["source_claims"], "source_claims")
        if "risk" in operation:
            bullet["risk"] = str(operation["risk"])
        return
    raise SystemExit(f"Unsupported patch operation: {op}")


def normalize_section(section: dict[str, Any]) -> dict[str, Any]:
    section_id = required_str(section, "section_id")
    return {
        "section_id": section_id,
        "title": str(section.get("title") or section_id.replace("_", " ").title()),
        "purpose": str(section.get("purpose", "")),
        "items": [normalize_item(item) for item in section.get("items", []) if isinstance(item, dict)],
    }


def normalize_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_event_ids": list_of_strings(item.get("source_event_ids", []), "source_event_ids"),
        "heading": str(item.get("heading", "")),
        "meta": str(item.get("meta", "")),
        "bullets": [normalize_bullet(bullet, item) for bullet in item.get("bullets", []) if isinstance(bullet, dict)],
    }


def normalize_bullet(bullet: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    return {
        "text": str(bullet.get("text", "")),
        "source_event_ids": list_of_strings(bullet.get("source_event_ids", item.get("source_event_ids", [])), "source_event_ids"),
        "source_claims": list_of_strings(bullet.get("source_claims", []), "source_claims"),
        "risk": str(bullet.get("risk", "needs_review")),
    }


def get_item(document: dict[str, Any], operation: dict[str, Any]) -> dict[str, Any]:
    section = find_section(document, required_str(operation, "section_id"))
    items = section.setdefault("items", [])
    return items[required_index(operation, "item_index", len(items))]


def section_index(document: dict[str, Any], section_key: str) -> int:
    sections = document.get("sections", [])
    for index, section in enumerate(sections):
        if str(section.get("section_id")) == section_key:
            return index
    try:
        index = int(section_key)
    except ValueError:
        raise SystemExit(f"Unknown section in patch: {section_key}") from None
    if index < 0 or index >= len(sections):
        raise SystemExit(f"Unknown section in patch: {section_key}")
    return index


def required_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if value is None or str(value).strip() == "":
        raise SystemExit(f"Missing required patch field: {key}")
    return str(value)


def required_index(data: dict[str, Any], key: str, length: int) -> int:
    value = data.get(key)
    try:
        index = int(value)
    except (TypeError, ValueError):
        raise SystemExit(f"Missing or invalid index field: {key}") from None
    if index < 0 or index >= length:
        raise SystemExit(f"Index out of range for {key}: {index}")
    return index


def bounded_insert_index(value: Any, length: int) -> int:
    try:
        index = int(value)
    except (TypeError, ValueError):
        raise SystemExit("Missing or invalid insert index") from None
    if index < 0:
        return 0
    if index > length:
        return length
    return index


def list_of_strings(value: Any, field_name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise SystemExit(f"Patch field must be a list: {field_name}")
    return [str(item) for item in value if str(item).strip()]


def apply_resume_edit(document: dict[str, Any], edit_key: str, text: str) -> None:
    parts = edit_key.split(".")
    if parts == ["profile", "display_name"]:
        document.setdefault("profile", {})["display_name"] = text
        return
    if len(parts) < 3 or parts[0] != "sections":
        raise SystemExit(f"Unsupported edit key: {edit_key}")
    section = find_section(document, parts[1])
    if parts[2] == "title" and len(parts) == 3:
        section["title"] = text
        return
    if len(parts) < 6 or parts[2] != "items":
        raise SystemExit(f"Unsupported edit key: {edit_key}")
    try:
        item = section.get("items", [])[int(parts[3])]
    except (ValueError, IndexError):
        raise SystemExit(f"Unknown item in edit key: {edit_key}") from None
    field = parts[4]
    if field in {"heading", "meta"} and len(parts) == 5:
        item[field] = text
        return
    if field == "bullets" and len(parts) == 6:
        try:
            bullet = item.get("bullets", [])[int(parts[5])]
        except (ValueError, IndexError):
            raise SystemExit(f"Unknown bullet in edit key: {edit_key}") from None
        bullet["text"] = text
        return
    raise SystemExit(f"Unsupported edit key: {edit_key}")


def find_section(document: dict[str, Any], section_key: str) -> dict[str, Any]:
    sections = document.get("sections", [])
    for section in sections:
        if str(section.get("section_id")) == section_key:
            return section
    try:
        return sections[int(section_key)]
    except (ValueError, IndexError):
        raise SystemExit(f"Unknown section in edit key: {section_key}") from None


def command_deliver_artifacts(args: argparse.Namespace) -> None:
    target_dir = target_dir_from_args(args)
    output_root = resolve_delivery_root(args, target_dir)
    target = read_json(target_dir / "target.json") if (target_dir / "target.json").exists() else {}
    delivery_dir = output_root / delivery_slug(target, target_dir)
    delivery_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    for name in ("resume.pdf", "resume.html", "resume_document.json", "resume_pdf_verification.json"):
        src = target_dir / "drafts" / name
        if src.exists():
            shutil.copy2(src, delivery_dir / name)
            copied.append(name)
    if not copied:
        raise SystemExit("No deliverable resume artifacts found. Run render-resume and finalize-ats-pdf first.")
    update_state(
        target_dir,
        delivery={"path": str(delivery_dir), "files": copied, "delivered_at": now_iso()},
        status="delivered",
    )
    print(delivery_dir)


def resolve_delivery_root(args: argparse.Namespace, target_dir: Path) -> Path:
    if args.output_root:
        return Path(args.output_root).expanduser().resolve()
    cwd = Path.cwd().resolve()
    if is_unsuitable_delivery_cwd(cwd):
        return Path.home() / "Documents" / "Career Applications"
    if (cwd / "outputs").exists():
        return cwd / "outputs"
    if (cwd / "deliverables").exists():
        return cwd / "deliverables"
    return cwd / "outputs"


def is_unsuitable_delivery_cwd(cwd: Path) -> bool:
    hidden_parts = {part for part in cwd.parts if part.startswith(".")}
    if hidden_parts:
        return True
    if cwd.name in {"career-application", "career-timeline"}:
        return True
    return False


def delivery_slug(target: dict[str, Any], target_dir: Path) -> str:
    label = " ".join(str(target.get(field) or "").strip() for field in ("company", "role") if str(target.get(field) or "").strip())
    if not label:
        label = str(target.get("domain") or target.get("industry") or target.get("target_id") or target_dir.name)
    return slugify(label, fallback=target_dir.name.replace("target_", ""))


def command_finalize_ats_pdf(args: argparse.Namespace) -> None:
    target_dir = target_dir_from_args(args)
    html_path = target_dir / "drafts" / "resume.html"
    document_path = target_dir / "drafts" / "resume_document.json"
    if not html_path.exists():
        raise SystemExit("Run render-resume before finalize-ats-pdf")
    finalizer = load_script_module("finalize-ats-pdf.py", "finalize_ats_pdf")
    output = target_dir / "drafts" / "resume.pdf"
    finalizer.finalize_ats_pdf(document_path, html_path, output)
    append_artifact(target_dir, {"type": "resume_pdf", "path": "drafts/resume.pdf"})
    update_state(target_dir, status="exported")
    print(output)


def append_artifact(target_dir: Path, artifact: dict[str, str]) -> None:
    state = read_json(target_dir / "application-state.json")
    versions = list(state.get("artifact_versions", []))
    versions.append(artifact)
    update_state(target_dir, artifact_versions=versions, status="ready_for_review")


def load_resume_renderer() -> Any:
    return load_script_module("render-resume.py", "render_resume")


def load_script_module(filename: str, module_name: str) -> Any:
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
    init.add_argument("--role", default="")
    init.add_argument("--domain", default="")
    init.add_argument("--industry", default="")
    init.add_argument("--language", required=True)
    init.add_argument("--region", default="")
    init.add_argument("--artifact", default="resume")
    init.add_argument("--channel", default="unspecified")
    init.add_argument("--page-count", type=int, required=True)
    init.add_argument("--template", choices=["ats-classic", "engineer-modern", "peifeng-standard"], default="ats-classic")
    init.add_argument("--photo", choices=["auto", "none", "optional", "provided"], default="auto")
    init.add_argument("--jd-text", default="")
    init.set_defaults(func=command_init_target)

    readiness = sub.add_parser("check-timeline", help="Check career-timeline vault readiness")
    readiness.add_argument("--vault")
    readiness.add_argument("--target-dir", required=True)
    readiness.set_defaults(func=command_check_timeline)

    plan = sub.add_parser("create-plan", help="Create a section-first resume plan")
    plan.add_argument("--target-dir", required=True)
    plan.set_defaults(func=command_create_plan)

    record = sub.add_parser("record-research", help="Record agent-produced target research")
    record.add_argument("--target-dir", required=True)
    record.add_argument("--file", required=True, help="JSON or Markdown research draft produced by the agent")
    record.add_argument("--source-url", default="")
    record.add_argument("--source-type", default="agent_research")
    record.add_argument("--confidence", default="medium")
    record.set_defaults(func=command_record_research)

    update_target = sub.add_parser("update-target", help="Merge recorded research into target.json")
    update_target.add_argument("--target-dir", required=True)
    update_target.set_defaults(func=command_update_target)

    rewrite = sub.add_parser("create-rewrite-drafts", help="Create per-event rewrite drafts from an approved plan")
    rewrite.add_argument("--target-dir", required=True)
    rewrite.add_argument("--vault")
    rewrite.set_defaults(func=command_create_rewrite_drafts)

    approve = sub.add_parser("approve-rewrite", help="Approve one event rewrite draft")
    approve.add_argument("--target-dir", required=True)
    approve.add_argument("--event-id", required=True)
    approve.set_defaults(func=command_approve_rewrite)

    build_resume = sub.add_parser("build-resume-document", help="Build resume_document.json from approved rewrites")
    build_resume.add_argument("--target-dir", required=True)
    build_resume.set_defaults(func=command_build_resume_document)

    render = sub.add_parser("render-resume", help="Render approved resume_document.json to editable HTML")
    render.add_argument("--target-dir", required=True)
    render.set_defaults(func=command_render_resume)

    revise = sub.add_parser("revise-resume-document", help="Update resume_document.json by edit key and rerender HTML")
    revise.add_argument("--target-dir", required=True)
    revise.add_argument("--edit-key", required=True)
    revise.add_argument("--text", required=True)
    revise.add_argument("--reason", default="")
    revise.set_defaults(func=command_revise_resume_document)

    patch = sub.add_parser("apply-resume-patch", help="Apply a reviewed structural patch to resume_document.json")
    patch.add_argument("--target-dir", required=True)
    patch.add_argument("--patch", required=True)
    patch.set_defaults(func=command_apply_resume_patch)

    finalize_pdf = sub.add_parser("finalize-ats-pdf", help="Generate a verified text-based ATS PDF from rendered HTML")
    finalize_pdf.add_argument("--target-dir", required=True)
    finalize_pdf.set_defaults(func=command_finalize_ats_pdf)

    deliver = sub.add_parser("deliver-artifacts", help="Copy final resume artifacts to a visible output directory")
    deliver.add_argument("--target-dir", required=True)
    deliver.add_argument("--output-root", default="")
    deliver.set_defaults(func=command_deliver_artifacts)

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
