# Artifact Generation

The first output path is structured JSON plus editable HTML.

## Artifacts

- `resume_document.json`: source-traceable structured document.
- `resume.html`: editable ATS browser output.
- `resume.md`: optional quick review draft.
- `change_report.md`: what changed and why.

## Rendering Rule

HTML/CSS is the only artifact format produced by this skill. Render HTML first, review or edit it in the browser, and keep it ATS-friendly: single-column, text-based, conventional headings, and no layout tricks needed for parsing. Final PDF or DOCX output requires a separate artifact finalizer with rendered-output verification; do not treat this skill as the final file generator.

## Template Selection

- ATS applications default to `ats-classic`.
- Engineering roles can use `engineer-modern` if ATS constraints allow it.
- Visual/networking materials can use visual templates, but mark ATS risk.

Do not claim a visual template is ATS-safe unless it is single-column, text-copyable, and uses conventional headings.

## Render Command

- `render-resume` writes editable ATS `drafts/resume.html` with an in-browser edit toolbar.
