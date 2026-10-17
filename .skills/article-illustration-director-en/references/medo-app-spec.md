# Overseas MeDo App Specification

## Screens

1. Article input: paste text or Markdown, or upload a supported document.
2. AI analysis: thesis, cognitive turns, proposed illustration points, and passages that should remain unillustrated.
3. Shot list: editable, sortable, and individually enabled; include topic, insertion point, message, composition, action, elements, labels, and prompt.
4. Style and character: default Article Observer, uploaded custom reference, or explicit source preset.
5. Generation queue: show `idle/submitting/submitted/processing/succeeded/failed/timeout`; do not resubmit successful tasks.
6. Gallery: real previews, purpose, version, download, localized editing, and regeneration.
7. Export: shot-list JSON/CSV, prompt pack, and image ZIP with working downloads.

## Technical integration

- Analysis: load `large-language-model`; accumulate `candidates[0].content.parts[].text` from SSE before parsing.
- Generation/editing: load `image-generation`; implement submit → poll → Base64 decode → Storage → preview/download.
- Plain `@name` text does not bind integrations. Load real Skill tags in the app-generation query or platform configuration.
- Frontend state is enough for one-off sessions. For cloud history, use Supabase tables such as `projects`, `article_sources`, `style_profiles`, `character_profiles`, `illustration_shots`, `generation_tasks`, and `image_versions`, isolated by `user_id` RLS.
- Show completion only after terminal success, preview, persistence, and download. Surface real 402, 429, parse, and timeout errors.
