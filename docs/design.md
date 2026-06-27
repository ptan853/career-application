# Career Application Skill Design

## Purpose

Design a second skill, tentatively named `career-application`, for concrete job
application work. It should sit above `career-timeline`: it understands the
specific target role, researches the company/JD, plans the application narrative,
selects timeline evidence, rewrites events section by section, and renders
application artifacts such as resumes, cover letters, interview stories, and
portfolio summaries.

The first stable output should be a tailored editable resume, but the skill
should not be narrowly named or structured as a resume-only renderer.

## Design Inputs

This design draws from:

- `ptan853/career-timeline`: local source of identity, events, claims, evidence,
  and `agent_identity.md`.
- `zarazhangrui/frontend-slides`: visual preview workflow, progressive template
  disclosure, HTML-first output, fixed canvas verification, and export scripts.
- `mikehenken/resume-tailor-agent-skill`: JSON Resume/state ideas, design
  registry, ATS-vs-visual templates, change reports, decision logs, validation,
  and Puppeteer PDF export.

The second skill should selectively borrow patterns, not copy either project
wholesale.

## Core Principle

Target decides structure. Sections define the evidence needed. Timeline events
supply evidence.

```text
Target research -> Candidate positioning -> Section strategy -> Evidence mapping
-> Resume plan -> User confirmation -> Section-by-section drafting
-> Event-by-event rewriting -> Render/export -> Revision loop
```

Do not start by dumping all events into a resume. A resume is a persuasion
structure for a specific target, not a chronological event list.

## Scope

### In Scope

- Parse or receive a JD, role target, company target, or role family.
- Research target role/company using available web/GitHub/job-source tools.
- Build a durable `TargetProfile` for the application.
- Check `career-timeline` readiness before drafting.
- Select section strategy before choosing events.
- Map timeline events into sections as evidence.
- Rewrite one section and one event at a time with approval loops.
- Generate editable HTML and structured JSON for resumes.
- Export PDF when renderer dependencies are available.
- Maintain application state, decisions, change report, and artifact versions.

### Out of Scope

- Long-term professional fact storage. That belongs to `career-timeline`.
- Inventing facts, metrics, tools, employers, awards, or credentials.
- Updating timeline events without invoking the `career-timeline` workflow.
- Bulk-generating final materials without a plan confirmation gate.
- Treating visual resumes as ATS-safe by default.

## Proposed Skill Name

Recommended: `career-application`

Alternative names:

- `job-application`: clear but narrower and less portfolio/interview-friendly.
- `application-designer`: emphasizes artifacts but less clearly career-specific.
- `resume-designer`: too narrow; should be reserved for a renderer-only skill if
  the system later splits further.

## Relationship With Career Timeline

`career-timeline` owns verified user facts:

- profile basics
- raw sources
- events
- claims
- evidence references
- identity summary

`career-application` owns target-specific state:

- target profile
- research notes
- section strategy
- evidence mapping
- resume plan
- rewritten bullets
- generated artifacts
- user decisions and change reports

When timeline is missing required facts, `career-application` should stop and
ask the agent to use `career-timeline` to fill the gap. It should not silently
create or confirm long-term facts.

## Storage Layout

Use a separate application workspace:

```text
~/.career-applications/
  targets/
    target_YYYYMMDD_company_role/
      target.json
      jd.md
      research.md
      timeline_readiness.json
      section_strategy.json
      resume_plan.json
      decisions.log
      change_report.md
      drafts/
        resume_v1.json
        resume_v1.html
        resume_v1.pdf
        resume_v2.json
      sources/
        jd_original.md
        company_notes.md
        web_research.md
```

This directory is private by default. It may contain JDs, company research,
custom drafts, and private decision history.

## Skill Directory Structure

Recommended repository layout:

```text
career-application/
  SKILL.md
  README.md
  references/
    target-research.md
    section-strategy.md
    event-rewrite.md
    artifact-generation.md
    ats-and-layout.md
  schemas/
    target-profile.schema.json
    timeline-readiness.schema.json
    section-strategy.schema.json
    resume-plan.schema.json
    resume-document.schema.json
    application-state.schema.json
  templates/
    designs.json
    styles/
      ats-classic.css
      engineer-modern.css
      research-academic.css
      visual-profile.css
    previews/
      ats-classic.html
      engineer-modern.html
      research-academic.html
      visual-profile.html
  scripts/
    init-target.py
    validate-state.py
    render-resume.py
    export-pdf.py
  examples/
    target-profile.example.json
    resume-plan.example.json
    resume-document.example.json
  evals/
    manual-skill-evals.md
  tests/
    test_render_resume.py
    test_validate_state.py
```

Use Python standard library for first version where possible. Add Playwright or
browser export only when PDF rendering becomes part of the implementation phase.

## Skill Trigger Design

`SKILL.md` description should contain only trigger conditions:

```yaml
description: Use when the user asks to apply for a job, analyze a JD, target a company or role, tailor a resume/CV, prepare application materials, generate a cover letter, prepare interview stories, or create role-specific portfolio content.
```

Do not summarize the whole workflow in the description. Agents must read the
skill body for process details.

## Primary Workflow

### Phase 1: Target Intake

Collect only what is missing:

- target role
- company
- JD text or link
- language
- target country/region
- seniority
- application channel: ATS, recruiter, referral, networking, portfolio
- artifact requested: resume, cover letter, interview prep, portfolio summary
- page limit and deadline when known

If user provides only a role family, create a role-only target and mark company
research as unavailable.

### Phase 2: Target Research

Use internet/job research tools when URLs, companies, current roles, or market
context are involved. Research should produce a structured `TargetProfile`, not
just a prose summary.

Research dimensions:

- company/product/domain context
- role responsibilities
- must-have skills
- nice-to-have skills
- seniority signals
- domain language and keywords
- likely hiring screen criteria
- disqualifying gaps or risks
- application-channel implications
- useful interview/cover-letter hooks

Research output should cite sources or record `source_type: user_provided` when
based only on the JD.

### Phase 3: Target Profile

`target.json` should become the reusable target understanding:

```json
{
  "target_id": "target_20260627_company_role",
  "created_at": "2026-06-27T00:00:00Z",
  "mode": "company_role",
  "company": "Example Corp",
  "role": "AI Algorithm Engineer",
  "language": "zh",
  "region": "China",
  "application_channel": "ats",
  "artifact_goals": ["resume"],
  "hiring_priorities": [
    "LLM Agent engineering",
    "tool orchestration",
    "model evaluation",
    "safe deployment"
  ],
  "must_have": [],
  "nice_to_have": [],
  "keywords": [],
  "company_context": [],
  "candidate_positioning": "",
  "risks": [],
  "research_sources": []
}
```

### Phase 4: Timeline Readiness

Read from `~/.career-vault` or the nearest configured vault:

- `profile.yaml`
- `exports/agent_identity.md` if present
- confirmed and `needs_review` events
- event details: context, contribution, implementation, outcome, evidence,
  claims

Readiness checks:

- profile basics exist: name, email, phone, location
- enough `confirmed` or user-approved events exist for target sections
- relevant events have `Resume-usable` detail where possible
- uncertain metrics or ownership are marked
- photo path exists only if selected template or region needs one

If readiness fails, produce a gap list and hand back to `career-timeline`.

### Phase 5: Candidate Positioning

Before sections, state the narrative:

```text
Candidate positioning: AI Agent / algorithm engineering candidate with evidence
in tool orchestration, algorithm service integration, evaluation/benchmarking,
and safety-aware engineering.
```

This drives section selection and bullet emphasis.

### Phase 6: Section Strategy First

The skill should use a controlled Section Registry. It may choose from standard
sections and only create custom sections when justified.

Recommended registry:

```json
{
  "summary": { "zh": "个人简介", "en": "Summary", "ats_safe": true },
  "skills": { "zh": "专业技能", "en": "Skills", "ats_safe": true },
  "work_experience": { "zh": "工作经历", "en": "Work Experience", "event_types": ["work"] },
  "internship_experience": { "zh": "实习经历", "en": "Internship Experience", "event_types": ["internship"] },
  "projects": { "zh": "项目经历", "en": "Projects", "event_types": ["project", "open_source"] },
  "research": { "zh": "研究经历", "en": "Research Experience", "event_types": ["research"] },
  "education": { "zh": "教育背景", "en": "Education", "event_types": ["education"] },
  "publications": { "zh": "论文发表", "en": "Publications", "event_types": ["publication"] },
  "awards": { "zh": "获奖经历", "en": "Awards", "event_types": ["award", "scholarship"] },
  "certifications": { "zh": "证书", "en": "Certifications", "event_types": ["certification"] },
  "portfolio": { "zh": "作品集", "en": "Portfolio", "event_types": ["project", "open_source"] }
}
```

Section selection rules:

- Target/JD decides the section strategy.
- Sections define evidence needs.
- Timeline events are selected after sections exist.
- One-page resumes should usually use 4-5 main sections.
- Two-page resumes can use 5-7 sections.
- ATS mode uses conventional headings.
- Visual/networking mode can use slightly richer section titles, but avoid
  gimmicky titles.
- Custom sections require `title`, `purpose`, `source_events`, and `ats_risk`.

Example strategy:

```json
{
  "target_positioning": "AI Agent engineering candidate for algorithm platform work",
  "sections": [
    {
      "section_id": "summary",
      "title": "个人简介",
      "purpose": "Establish AI Agent + algorithm engineering positioning in 3 lines",
      "evidence_need": "Synthesize strongest target-matching events"
    },
    {
      "section_id": "work_experience",
      "title": "工作经历",
      "purpose": "Prove enterprise delivery and algorithm service experience",
      "evidence_need": "Confirmed work events with agent/algorithm deployment claims"
    },
    {
      "section_id": "projects",
      "title": "项目经历",
      "purpose": "Show target-specific depth in tools, evaluation, sandboxing, or systems",
      "evidence_need": "Project/open-source events matching target priorities"
    }
  ]
}
```

### Phase 7: Evidence Mapping

After section strategy, select events for each section:

```json
{
  "section_id": "projects",
  "selected_events": [
    {
      "event_id": "evt_infplane_shell",
      "reason": "Matches tool routing and safety sandbox priorities",
      "strength": "strong",
      "risks": ["public visibility not confirmed", "metrics missing"]
    }
  ]
}
```

If a section has insufficient evidence, the skill should either remove the
section or ask the user to enrich timeline events through `career-timeline`.

### Phase 8: Resume Plan Confirmation

Before drafting prose, show a `ResumePlan`:

- target positioning
- selected sections in order
- each section purpose
- selected events per section
- omitted but relevant events and why
- gaps/risks
- planned page count
- planned template/design mode

Ask for approval before rewriting. User options:

```text
Approve plan / edit section order / add or remove event / fill gaps first
```

### Phase 9: Section-By-Section Drafting

Draft one section at a time. Within experience/project sections, rewrite one
event at a time.

For each event rewrite, show:

- source event id and title
- target relevance
- factual inputs used
- proposed heading/meta
- proposed bullets
- unsupported or weak claims
- options: approve, edit, regenerate, skip, ask for more detail

This supports many rounds without losing traceability.

Bullet rules:

- Use CAR/PAR/STAR material from timeline event details.
- Do not copy event claims verbatim by default; adapt to target.
- Preserve truth and evidence links.
- No invented metrics.
- Prefer action + method + result.
- Keep bullets concise enough for the selected page count.
- Track `source_event_ids` for every rewritten item.

### Phase 10: Artifact Generation

First-version resume artifacts:

- `resume_document.json`: structured, source-traceable document.
- `resume.md`: quick review and diff-friendly draft.
- `resume.html`: editable browser output.
- `resume.pdf`: optional export after HTML verification.
- `change_report.md`: what changed and why.

Future artifact types:

- cover letter
- interview prep stories
- LinkedIn summary
- portfolio/project one-pagers
- recruiter email
- application tracker notes

## Resume Document Model

Do not use JSON Resume as the primary model in v1. Use a source-traceable model
that can later export to JSON Resume if needed.

```json
{
  "schema_version": 1,
  "target_id": "target_20260627_company_role",
  "artifact_type": "resume",
  "language": "zh",
  "page_count": 1,
  "design_id": "ats-classic",
  "profile": {
    "display_name": "",
    "email": "",
    "phone": "",
    "location": "",
    "links": []
  },
  "sections": [
    {
      "section_id": "work_experience",
      "title": "工作经历",
      "purpose": "",
      "items": [
        {
          "source_event_ids": ["evt_..."],
          "heading": "",
          "meta": "",
          "bullets": [
            {
              "text": "",
              "source_event_ids": ["evt_..."],
              "source_claims": [],
              "risk": "confirmed"
            }
          ]
        }
      ]
    }
  ],
  "risks": [],
  "change_report": []
}
```

## Template And Rendering Design

Use HTML/CSS as the primary output path, not LaTeX.

Reasons:

- easier for agents to generate and revise
- browser-editable
- good CSS control for ATS and visual layouts
- PDF export via browser automation
- easier Chinese/English support than LaTeX in agent workflows

Template registry:

```json
{
  "default_design_id": "ats-classic",
  "designs": {
    "ats-classic": {
      "label": "ATS classic single-column",
      "ats_safe": true,
      "style_file": "ats-classic.css",
      "preview_file": "previews/ats-classic.html"
    },
    "engineer-modern": {
      "label": "Engineer modern",
      "ats_safe": true,
      "style_file": "engineer-modern.css",
      "preview_file": "previews/engineer-modern.html"
    },
    "research-academic": {
      "label": "Research academic",
      "ats_safe": true,
      "style_file": "research-academic.css",
      "preview_file": "previews/research-academic.html"
    },
    "visual-profile": {
      "label": "Visual profile",
      "ats_safe": false,
      "style_file": "visual-profile.css",
      "preview_file": "previews/visual-profile.html"
    }
  }
}
```

Use `mikehenken/resume-tailor-agent-skill` as inspiration for design registry,
ATS CSS, render-body separation, and Puppeteer PDF export. Do not copy hardcoded
profile assumptions. Preserve MIT license notice if code or CSS is reused.

Use `frontend-slides` as inspiration for visual style discovery:

- ATS mode: default to `ats-classic`, no preview choice required.
- Visual/networking mode: generate or show 2-3 resume style previews before
  rendering the full resume.
- Read only lightweight template index first; load full design notes only after
  user selects a visual direction.

## Page And Layout Verification

Before delivery, verify:

- requested page count is met or explain why not
- contact header has name, phone, email, and current location
- no unsupported claims remain unmarked
- all bullets trace to `source_event_ids`
- no text overflow in HTML
- PDF export succeeds when requested
- ATS mode is single-column and text-copyable
- visual mode is clearly marked as not guaranteed ATS-safe

## State Model

`application-state.json` should include:

```json
{
  "schema_version": 1,
  "application_id": "app_...",
  "created_at": "",
  "updated_at": "",
  "target": {},
  "timeline_readiness": {},
  "section_strategy": {},
  "resume_plan": {},
  "artifact_versions": [],
  "decisions": [],
  "status": "planning"
}
```

Suggested statuses:

```text
planning
researching_target
needs_timeline
planning_resume
rewriting_events
rendering
ready_for_review
exported
archived
```

## Approval Gates

Approval is required before:

- writing or overwriting `target.json` when research contains inferred claims
- applying event rewrites to a draft artifact
- removing a section from a resume after it was planned
- dropping a selected event
- using a visual non-ATS template for a formal application
- exporting final PDF for delivery

Approval is not required for:

- reading timeline files
- producing a target research draft
- reordering bullets inside a not-yet-approved draft
- generating preview styles
- validating files

## Research Strategy

When target details involve current company/role facts, use the available web or
platform research tools. Record source URLs and dates. Research should be
specific enough to influence section strategy.

Research output should answer:

- What does this target hire for?
- What evidence would pass the initial screen?
- What evidence would make the candidate stand out?
- What vocabulary should be used naturally?
- What risks or missing evidence should not be hidden?

## Error Handling

Failure should be explicit:

- Missing timeline vault: ask to initialize/fill `career-timeline` first.
- Missing profile basics: ask only for missing fields.
- Insufficient events: list missing evidence needs by section.
- Unsupported claims: mark risk and ask user to confirm or remove.
- Renderer failure: keep JSON/Markdown draft and report PDF failure.
- Template overflow: split content, reduce section scope, or ask user to allow a
  second page.

## First Version Implementation Plan

Minimum viable `career-application`:

1. `SKILL.md` with trigger, boundary, and workflow.
2. `references/section-strategy.md` and `references/event-rewrite.md`.
3. JSON schemas for `target-profile`, `resume-plan`, and `resume-document`.
4. `templates/designs.json` with `ats-classic` and `engineer-modern`.
5. `scripts/render-resume.py` that converts `resume-document.json` to editable
   HTML.
6. Manual evals for target research, timeline readiness, section-first plan,
   event-by-event rewrite, and render verification.

Do not implement PDF export in the first commit unless HTML rendering is already
stable. PDF can be the second milestone.

## Manual Evals

Required eval scenarios:

1. User gives only a JD link: agent researches target and creates target profile.
2. Timeline missing profile basics: agent stops and asks for missing fields.
3. Timeline has events but no target strategy: agent creates section strategy
   before selecting events.
4. Resume plan maps sections to events and asks for confirmation.
5. Event rewrite loop rewrites one event and waits for approval.
6. User asks for ATS resume: uses ATS-safe template and conventional headings.
7. User asks for designed resume: shows style previews or asks to choose design
   mode, and marks ATS risk.
8. User asks for final PDF before review: agent refuses and asks to confirm draft
   first.

## Key Design Decisions

- The second skill should be target-first, not resume-first.
- Section strategy must happen before event selection.
- `career-timeline` remains the long-term fact source.
- HTML/CSS is the primary rendering path.
- JSON Resume may be an export format, not the internal source of truth.
- Approval loops are required for section plan and event rewrites.
- Templates should use a registry and progressive disclosure rather than one
  giant hardcoded prompt.
