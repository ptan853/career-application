# Artifact Generation

The first output path is structured JSON plus editable HTML.

## Artifacts

- `resume_document.json`: source-traceable structured document.
- `resume.html`: editable browser output.
- `resume.md`: optional quick review draft.
- `resume.pdf`: optional export after HTML verification.
- `change_report.md`: what changed and why.

## Rendering Rule

HTML/CSS is the primary format. Use PDF export only after the user approves the draft and layout verification passes.

## Template Selection

- ATS applications default to `ats-classic`.
- Engineering roles can use `engineer-modern` if ATS constraints allow it.
- Visual/networking materials can use visual templates, but mark ATS risk.

Do not claim a visual template is ATS-safe unless it is single-column, text-copyable, and uses conventional headings.
