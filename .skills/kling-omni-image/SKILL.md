---
name: kling-omni-image
description: Generate high-quality AI images using Kling's Omni-Image model via an async submit→poll workflow. Supports text prompts, reference images (URL or Base64), element library composition, resolutions up to 2k, flexible aspect ratios, and single/series output modes. Use this skill whenever the user wants to generate, create, or produce images with Kling AI, asks about Omni-Image, wants multi-modal image generation with reference images or elements, or needs batch image series output.
license: MIT
---

# Kling Omni-Image — Image Generation

## Overview

Based on Kling AI's Omni-Image model, supports generating high-quality images via text prompts, reference images (URL or Base64), and element library resources. Supports 1k/2k resolution, multiple aspect ratios, and two output modes: single image (single) and image series (series).

**Workflow (async):**

1. Call the submit endpoint (POST) to create a generation task and obtain a `task_id`
2. Poll the query endpoint (GET) until `task_status` becomes `succeed` or `failed`
3. Retrieve image URLs from `task_result.images` (single mode) or `task_result.series_images` (series mode)
4. Transfer image URLs to Supabase Storage (CDN links expire after 30 days)

> Read `references/submit-api.md` for the full specification and code for the submit endpoint.
> Read `references/query-api.md` for the full specification and code for the query endpoint.

---

## Complete Async Workflow

Use the built-in scripts for generation-time calls. The scripts read `INTEGRATIONS_API_KEY` from the environment.

**The Bash tool timeout MUST be set to 600000ms (600 seconds).**

**Submit + poll (all-in-one):**

```bash
# Text-to-image
python3 <skill-path>/scripts/generate_omni_image.py \
  --prompt "A fantasy landscape with dragons" \
  --aspect-ratio 16:9 \
  --resolution 2k \
  -n 1 \
  --output-dir /tmp/omni_images

# With reference images
python3 <skill-path>/scripts/generate_omni_image.py \
  --prompt "Same style as <<<1>>>" \
  --image /path/to/ref1.jpg \
  --image-url "https://example.com/ref2.png" \
  --output-dir /tmp/omni_images
```

**Resume polling an existing task:**

```bash
python3 <skill-path>/scripts/query_omni_image.py --task-id "<task_id>" --output-dir /tmp/omni_images
```

The scripts print one JSON line:
- On success: `{"status":"succeed","task_id":"...","images":[{"url":"...","file":"..."}]}`
- If still processing: `{"status":"processing","task_id":"..."}`

On failure they print an error to stderr and exit with a non-zero code.

**Important constraints (must be followed):**
- When `result_type = single`: the `series_amount` field **must NOT appear** in the request body
- When `result_type = series`: `series_amount` **must be provided**, range [2, 9]
- Base64 images must be raw encoded content, **without** prefixes like `data:image/jpeg;base64,`

---

## Generation-time File Download (Required)

Image URLs are temporary CDN links (expire after 30 days). If `--output-dir` is not passed to the script, download immediately:

```bash
curl -L -o <local-path>.jpg "<generated image URL>"
```

> For detailed parameter descriptions, see `references/submit-api.md` (submit) and `references/query-api.md` (query).

---

## Generation-time Usage (Agent Direct Call)

See the "Generation-time Usage" section in `references/submit-api.md` for the complete TypeScript call example.

See the "Generation-time Usage" section in `references/query-api.md` for the query endpoint call example.

---

## Post-generation Usage (In-app via Edge Function)

See the "Post-generation Usage" section in `references/submit-api.md` for the Edge Function code for the submit endpoint (including Supabase Storage transfer logic).

See the "Post-generation Usage" section in `references/query-api.md` for the Edge Function code for the query endpoint.

---

## Notes

- **Key security**: `INTEGRATIONS_API_KEY` may only be read server-side in an Edge Function — never expose it to the frontend.
- **Error handling**: Always handle 429 (quota exceeded) and 402 (insufficient balance).
- **Note**: The submit (create task) endpoint is billed. The query endpoint (polling) is not billed. Avoid unnecessary duplicate submissions.
- **Image storage**: Generated image URLs are valid for 30 days — transfer them to Supabase Storage or another persistent store promptly.
- **series_amount constraint**: When `result_type=single`, passing `series_amount` is strictly forbidden and will cause the request to fail.
- **Base64 images**: Must not include the `data:image/...;base64,` prefix — pass only the raw encoded string.
- **Image size limits**: Each reference image must not exceed 10MB, minimum size 300px, aspect ratio between 1:2.5 and 2.5:1.
