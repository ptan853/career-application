# Career Application

<p align="center">
  <em>路漫漫其修远兮，吾将上下而求索。</em><br>
  <sub>The road ahead is long and far; I will keep searching high and low.</sub>
</p>

Career Application is a target-first job application skill for local coding
agents. It helps an agent understand a specific role or JD, record target
research, check verified career facts from `career-timeline`, plan resume
sections, rewrite selected events one by one, and render an editable resume
draft.

It is not the long-term source of truth for your professional history. Use
`career-timeline` for profile, sources, events, claims, and identity memory.
Use this skill when there is a concrete application target.

## Why This Exists

Most resume drafts fail because they start by dumping every experience into a
template. A strong application starts from the target: what the company screens
for, which evidence matters, which sections belong on the page, and which facts
are safe to claim.

This skill keeps that process explicit and inspectable.

## What It Does

- Creates one workspace per target role or JD.
- Records agent-produced JD/company research into local files.
- Merges research into `target.json` for later planning.
- Checks `career-timeline` readiness before drafting.
- Creates a section-first resume plan before selecting event prose.
- Generates per-event rewrite drafts and requires approval before final draft
  assembly.
- Builds `resume_document.json` and renders editable HTML.

Current limits: the agent performs internet research; the Python CLI only
records and validates research results. PDF export and visual layout checking
are not implemented yet.

## How It Works

```text
JD / role / company target
        |
        v
agent researches target
        |
        v
record-research -> update-target
        |
        v
check career-timeline vault
        |
        v
section-first plan -> per-event rewrite -> approved resume document -> HTML
```

The agent handles judgment-heavy work such as JD interpretation and event
rewriting. The CLI handles deterministic state, files, approvals, and rendering.

## Install

Install as a Codex-discoverable local skill:

```bash
ln -s /Users/pt623/Documents/career-application \
  /Users/pt623/.codex/skills/career-application
```

The CLI uses only the Python standard library and targets Python 3.10+.
Development tests use `pytest`.

## Quick Start

Create a target workspace:

```bash
python scripts/career_application.py --root ~/.career-applications/targets \
  init-target \
  --company "Example Corp" \
  --role "AI Engineer" \
  --language en \
  --artifact resume \
  --channel ats \
  --page-count 1 \
  --jd-text "Paste the JD or a short target description here."
```

After the agent researches the JD/company, save its structured findings:

```bash
python scripts/career_application.py record-research \
  --target-dir ~/.career-applications/targets/target_YYYYMMDD_example_ai-engineer \
  --file research.json \
  --source-url "https://example.com/jobs/ai-engineer" \
  --source-type job_posting

python scripts/career_application.py update-target \
  --target-dir ~/.career-applications/targets/target_YYYYMMDD_example_ai-engineer
```

Check timeline readiness and create a section-first plan:

```bash
python scripts/career_application.py check-timeline \
  --target-dir ~/.career-applications/targets/target_YYYYMMDD_example_ai-engineer \
  --vault ~/.career-vault

python scripts/career_application.py create-plan \
  --target-dir ~/.career-applications/targets/target_YYYYMMDD_example_ai-engineer
```

Then create and approve event rewrites:

```bash
python scripts/career_application.py create-rewrite-drafts \
  --target-dir ~/.career-applications/targets/target_YYYYMMDD_example_ai-engineer \
  --vault ~/.career-vault

python scripts/career_application.py approve-rewrite \
  --target-dir ~/.career-applications/targets/target_YYYYMMDD_example_ai-engineer \
  --event-id evt_example
```

Build and render the editable resume draft:

```bash
python scripts/career_application.py build-resume-document \
  --target-dir ~/.career-applications/targets/target_YYYYMMDD_example_ai-engineer

python scripts/career_application.py render-resume \
  --target-dir ~/.career-applications/targets/target_YYYYMMDD_example_ai-engineer
```

Run `python scripts/career_application.py --help` for all commands.

## Target Workspace Files

```text
target_YYYYMMDD_company_role/
  target.json                  # structured role/company target
  jd.md                        # original JD or target description
  research.md                  # readable research log
  timeline_readiness.json      # career-timeline readiness check
  resume_plan.json             # section-first plan
  application-state.json       # workflow status
  decisions.log                # reserved for user decisions
  sources/
    research_*.json            # agent research records
  drafts/
    rewrite_drafts.json        # per-event rewrite drafts
    resume_document.json       # structured resume document
    resume.html                # editable rendered resume
```

## Agent Workflow

1. Use this skill only after there is a target role, JD, company, or
   application artifact request.
2. Research the target with available agent tools when current information or a
   URL is involved.
3. Record research with `record-research`, then merge it with `update-target`.
4. Check `career-timeline` readiness before drafting. If the vault is
   missing profile fields or usable events, the agent should invoke
   `career-timeline` directly; do not ask the user to run a slash command.
5. Create and show the section-first plan. Wait for user approval before prose
   drafting.
6. Rewrite one event at a time and keep source event traceability.
7. Build `resume_document.json` only after selected rewrites are approved.
8. Render editable HTML for user review.

## Project Layout

```text
career-application/
  SKILL.md
  scripts/
    career_application.py
    render-resume.py
  references/
    target-research.md
    section-strategy.md
    event-rewrite.md
    artifact-generation.md
    ats-and-layout.md
  schemas/
  templates/
  examples/
  evals/
  tests/
```

## Status

This is an early skill-first MVP. It currently supports target workspace
creation, research recording, target updating, timeline readiness checks,
section-first planning, per-event rewrite approval, structured resume document
generation, and editable HTML rendering.

Planned next steps:

- richer target research examples
- stronger section strategy selection
- interactive event rewrite review cards
- PDF export
- page overflow and ATS layout verification
