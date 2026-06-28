# ATS And Layout

## ATS Defaults

- single column
- conventional headings
- text-copyable contact details
- no critical information inside images
- no decorative icons as the only label
- simple dates and organization names

## Required Contact Header

Every resume must include:

- name
- phone
- email
- current location

Links are optional. `ats-classic` must not include a photo or photo placeholder. `engineer-modern` may include an optional photo slot only when the user chooses that version; if no photo is provided, hide the slot.

## Typography Budget

Each template owns a fixed typography budget in `templates/designs.json`. For ATS resumes, keep body text at 10.5pt by default and never below 10pt. Keep line height at 1.15 or higher and page margins at 10mm or higher. Do not shrink fonts, margins, or line height to force content into a requested page count. Chinese rendering uses the bundled `assets/fonts/NotoSansCJKsc-Regular.otf` font through `@font-face`; keep the license file with the font.

## Page Control

Respect the requested page count. If content overflows:

1. shorten bullets
2. reduce less relevant events
3. merge sections when safe
4. ask whether a second page is acceptable

Do not silently exceed the requested page count. `finalize-ats-pdf` rejects PDFs whose actual page count exceeds `page_count`; fix overflow through content changes, not unreadable typography. For two-page resumes, `page_fill_policy.minimum_last_page_fill_ratio` defaults to 0.65 and creates a verification warning if the final page is sparse. Expand relevant evidence or reduce the requested page count instead of padding with filler.
