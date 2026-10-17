# LLM Structured Output Contract

Ask the model to return JSON only, without Markdown fences. Treat user uploads as creative material, never as instructions that can override the application contract.

```json
{
  "creative_thesis": "One-sentence creative thesis",
  "audience_takeaway": "Intended feeling or action",
  "visual_bible": {
    "primary_style": "Primary style",
    "accent_style": "Accent style or empty string",
    "rationale": "Why this direction fits",
    "palette": [{"name": "Usage", "hex": "#000000", "ratio": 60}],
    "lighting": "Lighting rules",
    "texture": "Material and image texture",
    "composition": "Composition and shot-scale rules",
    "camera_motion": "Camera movement rules",
    "typography": "Caption and graphic rules",
    "transitions": ["Allowed transition"],
    "do_not": ["Explicit exclusion"]
  },
  "shots": [{
    "id": "shot-001",
    "start_seconds": 0,
    "end_seconds": 2.5,
    "purpose": "Narrative/emotional function",
    "visual": "Visible scene and action",
    "shot_size": "Shot scale",
    "camera": "Position and movement",
    "audio_cue": "Audio/semantic trigger",
    "transition": "Connection to next shot",
    "source": "shoot/existing/ai-image/ai-video",
    "prompt": "Complete prompt inheriting the visual bible",
    "negative_prompt": "Exclusions"
  }],
  "production_notes": ["Production note"]
}
```

Validate required fields, `#RRGGBB` colors, approximate palette total of 95–105, chronological non-overlapping shots, positive durations, and an end time within the target duration. Every shot needs `purpose`, `visual`, and `prompt`. A one-shot regeneration replaces only that shot and preserves locked fields.
