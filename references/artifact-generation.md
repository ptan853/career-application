# Artifact Generation

The first output path is structured JSON plus editable HTML.

## Artifacts

- `resume_document.json`: source-traceable structured document.
- `resume.html`: editable browser output.
- `resume.md`: optional quick review draft.
- `resume.docx`: editable Word-compatible export for manual revision.
- `resume.pdf`: optional export after HTML verification.
- `change_report.md`: what changed and why.

## Rendering Rule

HTML/CSS is the primary layout format. Render HTML first, review or edit it in the browser, then export PDF only after the user approves the draft and layout verification passes. Use DOCX when the user needs direct word-processor editing; treat DOCX as a content-editing export, not the highest-fidelity visual output.

## Template Selection

- ATS applications default to `ats-classic`.
- Engineering roles can use `engineer-modern` if ATS constraints allow it.
- Visual/networking materials can use visual templates, but mark ATS risk.

Do not claim a visual template is ATS-safe unless it is single-column, text-copyable, and uses conventional headings.

## Export Commands

- `render-resume` writes editable `drafts/resume.html` with an in-browser edit toolbar.
- `export-docx` writes editable `drafts/resume.docx` from `resume_document.json`.
- `export-pdf` writes `drafts/resume.pdf` from `resume.html` and requires Playwright/Chromium.
