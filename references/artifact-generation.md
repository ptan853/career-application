# Artifact Generation

The first output path is structured JSON plus editable HTML.

## Artifacts

- `resume_document.json`: source-traceable structured document.
- `resume.html`: editable ATS browser output.
- `resume.pdf`: verified ATS PDF generated only after HTML approval.
- `resume.md`: optional quick review draft.
- `change_report.md`: what changed and why.

## Rendering Rule

HTML/CSS is the review and revision surface. Render HTML first, review or edit it in the browser, and keep it ATS-friendly: single-column, text-based, conventional headings, and no layout tricks needed for parsing. Agent-driven revisions must update `resume_document.json` by edit key, then rerender HTML. Final ATS PDF uses Chromium print PDF and must verify that required profile text exists in the PDF text layer. DOCX output remains outside this skill.

## Template Selection

- ATS applications default to `ats-classic`.
- Engineering roles can use `engineer-modern` if ATS constraints allow it.
- Visual/networking materials can use visual templates, but mark ATS risk.

Do not claim a visual template is ATS-safe unless it is single-column, text-copyable, and uses conventional headings.

## Commands

- `render-resume` writes editable ATS `drafts/resume.html` with an in-browser edit toolbar.
- `revise-resume-document` updates one structured edit key and rerenders HTML.
- `finalize-ats-pdf` writes `drafts/resume.pdf` only after text-layer verification passes.
