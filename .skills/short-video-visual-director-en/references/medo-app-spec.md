# MeDo App Specification: Short-Video Visual Director

## Required Experience

1. Brief intake: subject/product, goal, platform, duration, audience, emotion, brand constraints, references, and optional image/video/audio uploads.
2. A prominent **Generate Visual Plan** action that calls `@Large Language Model`. Show progress, preserve inputs on failure, and offer retry.
3. Result overview: creative thesis, style rationale, visible color swatches, light, texture, composition, movement, typography, transitions, and exclusions.
4. Timeline storyboard: each card contains purpose, visible action, shot scale, camera, audio cue, transition, source, and copyable prompt.
5. Targeted regeneration: regenerate only the visual bible or one shot while preserving locked fields.
6. Editable timing settings: aspect ratio, duration, FPS, BPM, and beats per bar. Recalculate timing without silently overwriting edited shots.
7. Storyboard editor: add, delete, reorder, edit, and lock shots. Support one-click copy for a prompt or all prompts.
8. Checks: palette conflict, timing overlap/gap, missing audio cue, mixed aspect ratio, and caption safe-area violations.
9. Real JSON and CSV downloads. A success toast without a downloaded file is incomplete.

The first screen may include a clickable sample brief, but never fake a generated result. Empty state should guide users to submit a brief instead of showing a wall of empty fields.

## Model Integration

- The MeDo generation request must load the actual `large-language-model` Skill. Plain `@Large Language Model` text inside generated UI does not bind an integration.
- Use its SSE Edge Function proxy. Accumulate `candidates[0].content.parts[].text` across every SSE event, remove an optional Markdown code fence, then parse the complete JSON once.
- Do not call `response.json()` on an SSE response and do not parse each delta as a complete result.
- Allow at least 60 seconds for first-token latency and expose 402/429/model/parse errors to the user.

## Runtime Boundary

- Never execute `scripts/beat_grid.py`, Python, shell, FFmpeg, child processes, Skill paths, or local workstation paths from the app.
- The Python script is only a generation-time verifier. Runtime timing uses TypeScript:

```ts
const secondsPerBeat = 60 / bpm;
const secondsPerBar = secondsPerBeat * beatsPerBar;
const frameAtBeat = (beat: number) => Math.round(beat * secondsPerBeat * fps);
```

Acceptance case: `120 BPM, 30 FPS, 4 beats/bar, 2 bars` gives `0.5 sec/beat`, `2 sec/bar`, `4 sec total`, final frame `120`.

## Persistence

Use local browser persistence for a simple single-user tool. Add Supabase Auth + Database for accounts, cross-device history, or collaboration; all rows require user isolation and RLS. Use Storage for uploaded media with progress, preview/player, and delete controls. Use Edge Functions only for server-side integrations and secrets.
