# Event Rewrite

Rewrite one event at a time. Do not copy timeline bullets verbatim unless they are already ideal for the target.

## Inputs To Use

- event title, type, time range, organization, role, location
- context/problem
- user's contribution
- methods, tools, architecture, or process
- outcome and metrics
- evidence references
- uncertainty or claim risk

## Bullet Standard

Prefer action + method + result:

```text
Built <thing> using <method/tool> to solve <problem>, resulting in <verified outcome>.
```

Use CAR, PAR, or STAR logic when helpful:

- context/problem
- action/contribution
- result/impact

## Guardrails

- Do not invent metrics, employers, tools, awards, or credentials.
- Preserve source traceability with `source_event_ids`.
- Mark weak or unsupported claims instead of hiding them.
- Keep bullets short enough for the requested page count.
- Adapt wording to the target vocabulary.

## Heading And Meta Standard

Match the artifact language. Do not place a Chinese heading on the left and an English translation on the right, or vice versa. Technical proper nouns can remain in their standard spelling, but the resume should read as one language unless the user requested a bilingual version.

Use `heading` for the main visible label and `meta` only for compact non-redundant facts:

- Work: `heading = 机构 · 职位`, `meta = 日期` or `地点 | 日期`.
- Education: `heading = 学校 · 学位/专业`, `meta = 日期`.
- Project/open source: `heading = 项目名 · 贡献主题`, `meta = 角色 | 日期`.

Before approval, check that `meta` is not repeating or translating `heading`.

For each rewritten event, show heading/meta, proposed bullets, factual inputs used, unsupported claims, and options: approve, edit, regenerate, skip, or ask for more detail.
