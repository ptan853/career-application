---
name: career-application
description: Use when the user asks to apply for a job, analyze a JD, target a company or role, tailor a resume/CV, prepare application materials, generate a cover letter, prepare interview stories, or create role-specific portfolio content.
---

# Career Application

## Overview

Target-first job application skill. Target → research → section strategy → evidence
mapping → per-event rewriting → editable HTML → verified PDF. Never start by
dumping all timeline events into a resume.

Long-term facts live in `career-timeline` (vault at `~/.career-vault`). This
skill only applies them to a specific target.

## When NOT to Use

- No concrete target (role, JD, company, domain) exists — build the timeline
  first with `career-timeline`
- Creating or editing long-term profile facts, events, or claims — those belong
  in `career-timeline`
- Just browsing career history — use `career-timeline`

## Quick Reference

| Term | Meaning |
|------|---------|
| ATS | Applicant Tracking System — automated parser; needs single-column, text-based layout |
| JD | Job Description |
| CAR / STAR | Context-Action-Result / Situation-Task-Action-Result — bullet structures |
| Vault | `~/.career-vault` — career-timeline source of truth |

## Workflow

### Phase 0 — Target Intake

Collect target context (role, company, domain, industry, or JD/link), language,
page count, and design mode before any research. Ask: `ats-classic` (default, no
photo), `engineer-modern` (optional photo), or `peifeng-standard` (Chinese
visual, photo slot). Region, channel, artifact type, and deadline are optional.

### Phase 1 — Research & Readiness

1. Research target (see `references/target-research.md`). Record with
   `record-research`, merge with `update-target`.
2. Check timeline vault: `check-timeline`.
3. If vault is missing profile fields or usable events, invoke `career-timeline`
   directly — do NOT tell the user to run a slash command. Resume only after the
   vault is ready or the user explicitly accepts gaps.

### Phase 2 — Strategy & Plan

1. State candidate positioning in 1-2 sentences.
2. Choose sections before selecting events (see `references/section-strategy.md`).
3. Map timeline events into sections. List omitted relevant events.
4. Show plan in chat: section order, selected/omitted events, gaps, risks, page
   count, design mode, photo policy. **Wait for user approval.** Do not create a
   Markdown confirmation file.

### Phase 3 — Drafting

Draft one section at a time. For experience/project sections, rewrite one event
at a time (see `references/event-rewrite.md`). Approve each with
`approve-rewrite`. `build-resume-document` only after all selected rewrites are
approved.

### Phase 4 — Render & Revise

1. `build-resume-document` → `render-resume` → user reviews editable HTML.
2. Small text changes: `revise-resume-document` by edit key.
3. Structural changes (add/remove/move sections/items/bullets): present patch
   summary → **user approval** → `apply-resume-patch`.
4. ATS PDF: **user approval of HTML** → `finalize-ats-pdf` → review
   `resume_pdf_verification.json` for page count, ASCII text-layer checks, CJK
   warnings, and page-fill warnings.
5. `deliver-artifacts` copies final files to a visible output folder. Never
   place deliverables in `~/.career-vault`.

## Artifact Rules

Only structured workspace files: `target.json`, `research.md`,
`resume_plan.json`, `drafts/rewrite_drafts.json`, `drafts/resume_document.json`,
`drafts/resume.html`, optional `drafts/resume_patch.json`, verified
`drafts/resume.pdf`, `drafts/resume_pdf_verification.json`.

- Never output standalone Markdown resumes, review files, or ad-hoc resume drafts.
- Never ask the user to manually print HTML to PDF.
- No DOCX output from this skill.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Dumping all timeline events into a resume template | Follow target → sections → events order |
| Creating Markdown resume drafts | Use only structured JSON → HTML → PDF path |
| Telling user to run `/career-timeline` | Agent invokes `career-timeline` skill directly |
| Skipping section strategy | Choose sections BEFORE selecting events |
| Generating PDF without HTML review | Require user approval on editable HTML first |
| Inventing metrics, employers, or credentials | Preserve source traceability; mark weak claims |
| Silently exceeding requested page count | Shorten bullets, reduce events, or ask user |
| Using `peifeng-standard` for ATS applications | Default to `ats-classic`; mark ATS risk otherwise |
| Mixing Chinese headings with English metadata translations | Keep one primary language; use `meta` only for dates, location, or role details not already in `heading` |

## Red Flags

These thoughts mean STOP — you are about to skip a required step:

- "The timeline has enough events — let me just draft a resume"
- "I'll create a quick Markdown version first"
- "The user can run career-timeline themselves"
- "This looks good, let me generate the PDF directly"
- "I'll squeeze in more content by shrinking the font"
- "This JD is simple, I can skip the section strategy"

**All of these mean: follow the workflow. Do not skip phases.**

## Approval Gates

Ask for user approval before:
- Moving from resume plan to prose drafting
- Applying a structural resume patch (add/remove/move/rename sections, items, or
  bullets)
- Using a non-ATS template (`peifeng-standard`) for a formal ATS application
- Finalizing ATS PDF after HTML review
- Using inferred target claims as durable target profile fields

No approval needed for: reading vault files, research drafts, previews, or
validating intermediate JSON.

## CLI Helpers

Core CLI via `scripts/career_application.py`:

| Command | Purpose |
|---------|---------|
| `init-target` | Create target workspace (requires `--language`, `--page-count`, target context) |
| `record-research` | Save agent research into `research.md` and `sources/` |
| `update-target` | Merge recorded research into `target.json` |
| `check-timeline` | Inspect vault; write `timeline_readiness.json` |
| `create-plan` | Generate `resume_plan.json` (only after timeline ready) |
| `create-rewrite-drafts` | Per-event rewrite drafts from approved plan |
| `approve-rewrite` | Mark one event rewrite as user-approved |
| `build-resume-document` | Build `resume_document.json` (only after all rewrites approved) |
| `render-resume` | Render `resume_document.json` to editable `resume.html` |
| `revise-resume-document` | Update by edit key; rerender HTML |
| `apply-resume-patch` | Apply reviewed structural patch; rerender HTML |
| `finalize-ats-pdf` | Generate verified `resume.pdf` (needs Playwright + text verifier) |
| `deliver-artifacts` | Copy final files to user-visible output directory |
| `validate-state` | Check required workspace files and statuses |

## References

- `references/target-research.md` — Research questions and target profile
- `references/section-strategy.md` — Section registry and selection rules
- `references/event-rewrite.md` — Bullet standards, guardrails, approval loop
- `references/artifact-generation.md` — Rendering rules, template selection,
  patch operations
- `references/ats-and-layout.md` — ATS defaults, typography budget, page control
