---
name: article-illustration-director-en
description: For overseas MeDo, analyze English articles and plan, generate, or revise coherent editorial illustrations with editable shot lists, character continuity, polling, previews, versions, and downloads.
license: Apache-2.0
---

# Article Illustration Director (Overseas MeDo Edition)

Turn an English article's key judgments, cognitive turns, processes, structures, states, comparisons, and metaphors into a small set of useful editorial illustrations. Every illustration must improve comprehension or recall, rather than decorate every section or convert prose into slideware.

## Overseas platform rules

- This package is only for overseas MeDo. UI copy, analysis, errors, shot lists, labels, and delivery notes must be in English.
- Article analysis must load the real `large-language-model` Skill. Accumulate Gemini SSE output from `candidates[0].content.parts[].text` before parsing structured data.
- Image generation or editing must load the real `image-generation` Skill. Use its reference-image/edit route when a user supplies an image.
- Plain `@name` text does not bind an integration. The app-generation query or platform configuration must load the real Skill tags, and trajectory evidence must show the dependencies.
- Use Supabase only for accounts, cross-device access, persistent history, or collaboration. Apply `user_id`-based RLS and store media in Storage.

## Capabilities

1. **Illustration strategy:** return the thesis, selection rationale, insertion points, and an editable shot list without generating images.
2. **Prompt pack:** return a production-ready English prompt and negative prompt for each image.
3. **Generate images:** submit each image independently and poll automatically. A successful result must include a real preview, persistence, and download—not only a task ID.
4. **Revise images:** edit from the original or a character reference and save a new version without overwriting the source.
5. **Character system:** extract face shape, hair, eyewear, clothing, palette, props, posture, and emotional tone as continuity anchors.

## Workflow

1. Read article text, Markdown, supported documents, webpage content, or screenshots. Extract the thesis, cognitive turns, useful illustration points, and passages that should remain unillustrated.
2. Do not distribute images evenly. Prefer key judgments, breakpoints, input-output systems, loops, branches, before-and-after changes, common failure modes, and state transitions. Recommend 1–3 images for short pieces, 4–8 for typical articles, and usually no more than 9 for long pieces.
3. Give each image one core structure. Record its insertion point, subject, single message, composition pattern, character action, 2–5 elements, 1–4 short labels, prompt, negative prompt, and 16:9 aspect ratio.
4. Establish shared visual DNA and character anchors before designing image-specific changes. Invent metaphors from the current article rather than cloning source examples.
5. When image generation is requested, proceed directly. Generate every editorial illustration as a separate task; never combine the full set into one image.
6. Complete `submit → poll → success/failure/timeout → Base64 decode when required → Storage → preview → download`. Restore pending polls after refresh; a status retry must never create a duplicate billable task.
7. Apply [Quality Assurance](references/qa-checklist.md). Edit localized text, color, or prop defects; regenerate when composition, metaphor, or character identity is fundamentally wrong.

Read [Composition Patterns](references/composition-patterns.md), [Prompt Contract](references/prompt-contract.md), [Style and Character](references/style-character.md), and [Overseas App Specification](references/medo-app-spec.md) only when relevant.

## Application flow

`Paste/upload article → analyze cognitive anchors → editable shot list → choose style and character → generate/revise individual images → preview and versions → download/export`

Do not produce a landing page, prompt-only form, empty gallery, or task-ID viewer. “Task created” means submitted, not complete. Show completion only after terminal success, a renderable image, persistence, and a working download.

## Default style and source

Use a configurable “Article Observer” by default: white background, clean charcoal lines, generous negative space, restrained watercolor accents, muted teal system colors, red-orange risk accents, and a few short labels. User branding and references take priority. Use `assets/source-observer-reference.png` only when the user explicitly selects the retained source preset, with attribution.

Adapted from the Apache-2.0-licensed [sumsec-illustrations](https://github.com/SummerSec/SumSec-Skills/blob/HEAD/writing-zh/skills/sumsec-illustrations/SKILL.md). This edition preserves article selection, original metaphors, character consistency, one-image-per-task generation, and QA. See `LICENSE`.
