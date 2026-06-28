---
name: career-application
description: Use when the user asks to apply for a job, analyze a JD, target a company or role, tailor a resume/CV, prepare application materials, generate a cover letter, prepare interview stories, or create role-specific portfolio content.
---

# Career Application

## Purpose

Use this skill for target-specific job application work. It researches the target, checks the user's verified `career-timeline` vault, plans application materials, rewrites selected evidence, and generates editable artifacts.

Do not use this skill as the long-term source of professional facts. Verified identity, sources, events, claims, and timeline data belong in `career-timeline`.

## Operating Rule

Target decides structure. Sections define evidence needs. Timeline events supply evidence.

Do not output standalone Markdown resumes, Markdown review files, or ad-hoc resume drafts. Use chat for user confirmation and write durable state only to the structured workspace artifacts: `target.json`, `research.md`, `resume_plan.json`, `drafts/rewrite_drafts.json`, `drafts/resume_document.json`, `drafts/resume.html`, optional `drafts/resume_patch.json`, verified `drafts/resume.pdf`, and `drafts/resume_pdf_verification.json`.

```text
target research -> candidate positioning -> section strategy -> evidence mapping
-> plan confirmation -> section-by-section drafting -> event-by-event rewriting
-> render editable ATS HTML -> structured revision loop -> verified ATS PDF
```

Never start by dumping all timeline events into a resume.

## Required Boundary With Career Timeline

Before drafting final application text:

1. Read the local career vault, usually `~/.career-vault`.
2. Check profile basics: name, email, phone, location.
3. Check whether relevant events are confirmed or user-approved.
4. If facts are missing, invoke the `career-timeline` skill/workflow yourself to fill the gaps.
5. Do not create or confirm long-term facts inside this skill.

Do not tell the user to run `/career timeline` or any other slash command. The
agent is responsible for switching to the installed `career-timeline` skill,
reading its `SKILL.md`, saving sources or extracting events as needed, and then
returning here after timeline readiness passes. Ask the user only for missing
personal facts or source material that cannot be inferred from local files.

## Workflow

1. **Target intake**: collect the target context, language, page count, and resume version before initializing. Target context can be a role, company, domain, industry, or JD/link. Language and page count must be explicit. Ask whether the user wants `ats-classic`, `engineer-modern`, or `peifeng-standard`: ATS has no photo; modern is a light technical design; Peifeng Standard is a Chinese visual PDF-oriented design with an optional fixed photo slot. Region, channel, artifact type, and deadline are optional refinements.
2. **Target research**: if current company, role, URL, or market facts matter, research them and record source URLs.
3. **Target profile**: write a structured target understanding before planning content.
4. **Timeline readiness**: compare target evidence needs with available vault events.
   If readiness fails, use `career-timeline` directly to collect missing profile
   fields, preserve source material, or create reviewed event drafts. Resume
   this workflow only after the vault is ready or the user explicitly chooses to
   continue with known gaps.
5. **Candidate positioning**: state the application narrative in one or two sentences.
6. **Section strategy first**: choose sections before choosing events. Read `references/section-strategy.md`.
7. **Evidence mapping**: map timeline events into planned sections and list omitted relevant events.
8. **Plan confirmation**: show the section order, selected events, omitted events, gaps, risks, page count, design mode, and photo policy in chat. Wait for user approval. Do not create a Markdown confirmation file.
9. **Drafting**: draft one section at a time. For experience/project sections, rewrite one event at a time. Read `references/event-rewrite.md`.
10. **Artifact generation**: generate `resume_document.json` and editable HTML only after the user has approved the draft. For small text revisions, update `resume_document.json` by edit key. For section/item/bullet additions, removals, or ordering changes, present a resume patch summary to the user, then run `apply-resume-patch` only after approval. Do not patch HTML directly and do not ask the user to manually print HTML. Finalize ATS PDF through `finalize-ats-pdf` only after user approval; review `resume_pdf_verification.json` for page count, ASCII text-layer checks, CJK extraction warnings, and page-fill warnings. Then run `deliver-artifacts` to copy final files to a user-visible output folder. Do not produce DOCX from this skill.

## References

- Target and company research: `references/target-research.md`
- Section selection: `references/section-strategy.md`
- Event rewriting: `references/event-rewrite.md`
- Artifact generation: `references/artifact-generation.md`
- ATS and page layout: `references/ats-and-layout.md`

## CLI Helpers

Use `scripts/career_application.py` for deterministic file operations:

- `init-target`: create a target workspace with `target.json`, `application-state.json`, `jd.md`, `drafts/`, and `sources/`. Requires explicit `--language`, `--page-count`, and at least one of `--role`, `--company`, `--domain`, `--industry`, or `--jd-text`.
- `record-research`: save agent-produced JD/company/role research into `research.md` and `sources/research_*.json`.
- `update-target`: merge recorded research into `target.json` for planning.
- `check-timeline`: inspect a `career-timeline` vault and write `timeline_readiness.json`.
- `create-plan`: generate a section-first `resume_plan.json` only after timeline readiness passes.
- `create-rewrite-drafts`: create per-event rewrite drafts from selected plan events.
- `approve-rewrite`: mark one event rewrite as user-approved.
- `build-resume-document`: build `drafts/resume_document.json` only after all selected rewrites are approved.
- `render-resume`: render `drafts/resume_document.json` to editable ATS `drafts/resume.html`.
- `revise-resume-document`: update one structured edit key in `resume_document.json` and rerender HTML.
- `apply-resume-patch`: apply a reviewed structural patch for section/item/bullet changes and rerender HTML.
- `finalize-ats-pdf`: generate `drafts/resume.pdf` only when Playwright and PDF text verification are available.
- `deliver-artifacts`: copy final resume artifacts to a user-visible output directory based on explicit `--output-root` or the current working directory.
- `validate-state`: check required workspace files and supported statuses.

## Approval Gates

Ask for user approval before:

- using inferred target claims as durable target profile fields
- moving from resume plan to prose drafting
- applying a structural resume patch that adds, removes, moves, or renames sections/items/bullets
- using a visual non-ATS template such as `peifeng-standard` for a formal application
- finalizing ATS PDF after the editable HTML review
- requesting DOCX handoff to another artifact finalizer

No approval is needed for reading local timeline files, producing research drafts, generating previews, or validating intermediate JSON.
