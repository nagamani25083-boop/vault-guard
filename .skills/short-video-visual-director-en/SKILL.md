---
name: short-video-visual-director-en
description: Build a coherent visual direction for short videos, music videos, promos, and vertical content; generate visual bibles, beat-aware storyboards, AI media prompts, and edit plans when users need art direction, shot design, pacing, asset planning, or edit diagnosis.
license: MIT
---

# Short-Video Visual Director (MeDo English Edition)

Decide what the piece should look and feel like before generating assets or editing. Color, light, texture, composition, movement, sound, and cuts must execute one creative thesis rather than form a pile of unrelated “cinematic” effects.

## Prerequisites

- Direct creative-direction responses require no external service.
- **When generating a MeDo app, combine `@Large Language Model` (slug: `large-language-model`)**. Visual direction, storyboards, and prompts are open-ended generation capabilities; without an LLM, the app becomes a manual form rather than a useful product.
- Add an image or video generation Skill only when the user requests actual media generation. Resolve the exact Skill from the current MeDo Skill catalog; do not invent names.
- Use Supabase only for accounts, cross-device projects, assets, or version history. Isolate all records by authenticated user and store media in Storage.

## Core Workflow

1. Extract purpose, audience, platform, aspect ratio, duration, audio structure, brand constraints, reference material, and intended emotion. If missing details do not change the core direction, state assumptions and produce a first pass.
2. Write one creative thesis. Select one primary style and no more than one accent style.
3. Build a visual bible covering palette, lighting, texture, composition, shot scale, camera movement, typography, transitions, audio cues, and explicit exclusions. Read [Aesthetic System](references/aesthetic-system.md).
4. Build a timing grid from music sections, BPM, narration, transients, or emotional turns. For generation-time verification, run:

   ```bash
   python3 scripts/beat_grid.py --bpm 120 --fps 30 --beats-per-bar 4 --bars 8 --json
   ```

   This Python script is for the Skill agent at generation/task time only. It is not deployed with a MeDo app. Browser and Edge Function code must use the equivalent TypeScript formula and must not invoke Python, shell commands, FFmpeg, local Skill paths, or `/Users/...` paths.
5. Produce a chronological storyboard. Every shot includes timecode, visible action, shot scale, camera, motion, audio cue, transition, source type, and a production-ready generation prompt.
6. When media generation is enabled, reuse the same visual bible and identity anchors across every request. Generate options and reject style drift.
7. Diagnose the cut by listing what to keep, what breaks the direction, shot-level changes, priority, and expected impact. Remove beautiful shots that do not belong to the piece.

## MeDo App Requirement

When asked to build a visual-director app, read [MeDo App Specification](references/medo-app-spec.md) and [LLM Output Contract](references/llm-output-contract.md). Implement the complete flow:

`brief/reference input → Generate Visual Plan → visual bible and timeline storyboard → edit or regenerate one section → copy prompts/export`

The primary generation action must call the actual Large Language Model integration. Do not generate a landing page, empty editor, fixed-template result, or settings-only experience.

## Execution Priorities

1. User references and brand constraints override presets.
2. Coherence beats novelty: one primary style, at most one accent.
3. Hard cuts land on beats, transients, or semantic turns; transitions need a reason.
4. Prompts describe visible subjects, action, camera, light, material, color, and motion—not only vague words such as “premium.”
5. Do not directly imitate the distinctive style of a living creator. Translate references into general visual attributes.
6. Deliver outputs that a shooter, editor, or media model can execute immediately.

## References

- [Aesthetic System](references/aesthetic-system.md)
- [Direction Deliverable Template](references/direction-template.md)
- [MeDo App Specification](references/medo-app-spec.md)
- [LLM Structured Output Contract](references/llm-output-contract.md)

## Communication Rules

- Lead with the chosen direction and rationale, then the storyboard and prompts.
- Separate user facts, creative assumptions, and replaceable choices.
- State BPM, FPS, beats per bar, and frame-rounding rules with every beat grid.
- If media generation is not connected, still deliver complete prompts and an asset list; never fabricate generated results.

## Common Failures

- Mixing incompatible styles in one piece.
- Hard-coding the source project's 138 BPM, 9:16 ratio, or angelcore palette.
- Treating example Remotion/FFmpeg code as a mandatory runtime dependency.
- Assuming an `@Skill` name written in this file automatically binds that Skill; MeDo generation must load the real Skill tag/integration.
- Parsing individual SSE chunks as complete JSON instead of accumulating all model text first.
- Calling the packaged Python script from a generated app; it exists only in the agent environment.
- Showing a task ID without preview, persistence, and download when media generation is enabled.

## Source and Adaptation

Adapted from the MIT-licensed [taste](https://github.com/gongyijie85/dsh-ecc/blob/HEAD/skills/taste/SKILL.md). It preserves the source principles of direction-first design, sound-driven editing, and ruthless selection while replacing project-specific dependencies with a configurable MeDo workflow. See `LICENSE`.
