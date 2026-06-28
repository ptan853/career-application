# Artifact Generation

The first output path is structured JSON plus editable HTML.

## Artifacts

- `resume_document.json`: source-traceable structured document.
- `resume.html`: editable ATS browser output.
- `resume.pdf`: verified ATS PDF generated only after HTML approval.
- `resume_pdf_verification.json`: page count, ASCII text-layer checks, and any CJK extraction warnings.
- `resume_patch.json`: optional reviewed structural patch for section/item/bullet changes.

Do not create Markdown resume drafts, Markdown review files, or separate change-report files. Show review summaries in chat and keep durable state in JSON/HTML/PDF artifacts.

## Rendering Rule

HTML/CSS is the review and revision surface. Render HTML first, review or edit it in the browser, and keep it ATS-friendly: single-column, text-based, conventional headings, and no layout tricks needed for parsing. Do not ask users to manually print the HTML to PDF. Agent-driven text revisions must update `resume_document.json` by edit key, then rerender HTML. Structural revisions must use a reviewed patch file and `apply-resume-patch`. Final ATS PDF uses the scripted `finalize-ats-pdf` path and must verify required ASCII profile text, requested page count, and readable typography budget. CJK profile fields may produce extraction warnings because PDF text extractors can normalize glyphs differently; keep the PDF when ASCII checks and page count pass. DOCX output remains outside this skill.

## Template Selection

- Ask the user to choose a version before planning.
- `ats-classic` is the default for formal ATS applications, is single-column, and never uses a photo.
- `engineer-modern` can be used for modern review/networking versions and may include an optional photo slot. If no photo is provided, hide the slot rather than leaving a blank hole.
- `peifeng-standard` is a Chinese visual resume template adapted from the user-provided Peifeng reference layout. It supports a fixed photo slot, compact section dividers, and PDF-oriented human review. It is not the ATS default.
- Visual/networking materials can use visual templates, but mark ATS risk.

Do not claim a visual template is ATS-safe unless it is single-column, text-copyable, and uses conventional headings.

## Commands

- `render-resume` writes editable ATS `drafts/resume.html` with an in-browser edit toolbar.
- `revise-resume-document` updates one structured edit key and rerenders HTML.
- `apply-resume-patch` applies reviewed section/item/bullet changes and rerenders HTML.
- `finalize-ats-pdf` writes `drafts/resume.pdf` and `drafts/resume_pdf_verification.json` after scripted PDF export passes page count and ASCII text-layer verification.
- `deliver-artifacts` copies final files to a visible user output folder; do not place deliverables in `~/.career-vault`.

## Patch Operations

Use `apply-resume-patch` only after showing the user a summary and receiving approval. Supported operations: `rename-section`, `add-section`, `remove-section`, `move-section`, `add-item`, `remove-item`, `move-item`, `update-item`, `add-bullet`, `remove-bullet`, `move-bullet`, and `update-bullet`. See `schemas/resume-patch.schema.json` and `examples/resume-patch.example.json`.
