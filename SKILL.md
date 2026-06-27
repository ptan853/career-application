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

```text
target research -> candidate positioning -> section strategy -> evidence mapping
-> plan confirmation -> section-by-section drafting -> event-by-event rewriting
-> render/export -> revision loop
```

Never start by dumping all timeline events into a resume.

## Required Boundary With Career Timeline

Before drafting final application text:

1. Read the local career vault, usually `~/.career-vault`.
2. Check profile basics: name, email, phone, location.
3. Check whether relevant events are confirmed or user-approved.
4. If facts are missing, stop and ask to use `career-timeline` to fill them.
5. Do not create or confirm long-term facts inside this skill.

## Workflow

1. **Target intake**: collect missing role, company, JD/link, language, region, application channel, artifact type, page limit, and deadline.
2. **Target research**: if current company, role, URL, or market facts matter, research them and record source URLs.
3. **Target profile**: write a structured target understanding before planning content.
4. **Timeline readiness**: compare target evidence needs with available vault events.
5. **Candidate positioning**: state the application narrative in one or two sentences.
6. **Section strategy first**: choose sections before choosing events. Read `references/section-strategy.md`.
7. **Evidence mapping**: map timeline events into planned sections and list omitted relevant events.
8. **Plan confirmation**: show the section order, selected events, gaps, risks, page count, and design mode. Wait for user approval.
9. **Drafting**: draft one section at a time. For experience/project sections, rewrite one event at a time. Read `references/event-rewrite.md`.
10. **Artifact generation**: generate `resume_document.json`, editable HTML, optional Markdown, and PDF only when rendering is available and the user has approved the draft.

## References

- Target and company research: `references/target-research.md`
- Section selection: `references/section-strategy.md`
- Event rewriting: `references/event-rewrite.md`
- Artifact generation: `references/artifact-generation.md`
- ATS and page layout: `references/ats-and-layout.md`

## Approval Gates

Ask for user approval before:

- using inferred target claims as durable target profile fields
- moving from resume plan to prose drafting
- dropping a planned section or selected event
- using a visual non-ATS template for a formal application
- exporting a final PDF

No approval is needed for reading local timeline files, producing research drafts, generating previews, or validating intermediate JSON.
