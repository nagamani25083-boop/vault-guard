---
name: kling-omni-video-generation
description: Generate videos using Kling AI's Omni model via API gateway, supporting text-to-video, image-to-video, video editing, multi-shot storyboard, and video reference modes. Use this skill whenever the user wants to create a video from a text prompt or reference image/video — for creative content, marketing, short-video production, or any scenario involving AI video generation with Kling's omni model.
license: MIT
---

# Kling Omni Video Generation

## Overview

Generate videos using only O3 / Kling V3 Omni (`kling-v3-omni`), supporting text-to-video, image-to-video, video editing, video reference, and multi-shot storyboard modes. Uses an asynchronous task pattern: submit a task to obtain a `task_id`, then poll the query endpoint until completion.

| Property | Value |
|----------|-------|
| Submit Endpoint | `POST https://app-f58c4fdcbbpd-api-k93RvqRrRZba.gateway.appmedo.com/v1/videos/omni-video` |
| Query Endpoint | `GET https://app-f58c4fdcbbpd-api-pLVzAEz1ZQOL.gateway.appmedo.com/v1/videos/omni-video/{task_id}` |
| Authentication | Bearer Token (platform_managed — key injected by platform) |
| Request Format | `application/json` |
| Response Format | JSON (includes video URL) |
| Note | The submit endpoint is used to create the task and is billed; the query endpoint is used to poll for results and is free |

### Key Capability Modes

| Mode | Description |
|------|-------------|
| Text-to-video | Generate video using `prompt` only |
| Image-to-video | Generate video using `prompt` + `image_list` reference images |
| Video editing | Modify existing video content using `prompt` + `video_list` |
| Video reference | Generate new video by referencing the motion/cinematography of an existing video |
| First/last frame | Generate video by specifying a start frame or both start and end frames |
| Multi-shot | Enable `multi_shot: true` + `multi_prompt` to support up to 6 storyboard shots |

> For full parameter details and code examples, see `references/submit-api.md` and `references/query-api.md`.

---

## End-to-End Async Workflow

Kling Omni video generation is **asynchronous**: submit a task to obtain a `task_id`, then poll the query endpoint until the status becomes `succeed` or `failed`.

```typescript
// Full async workflow: submit → poll → retrieve video URL
async function generateAndWait(submitFn: () => Promise<{ taskId: string }>) {
  const { taskId } = await submitFn();

  const POLL_INTERVAL_MS = 7000;          // recommended 5–10 seconds
  const TIMEOUT_MS = 10 * 60 * 1000;     // maximum 10 minutes
  const deadline = Date.now() + TIMEOUT_MS;

  while (Date.now() < deadline) {
    await new Promise(r => setTimeout(r, POLL_INTERVAL_MS));
    const result = await queryTask(taskId);
    if (result.task_status === "succeed") return result;
    if (result.task_status === "failed")  throw new Error(`Task failed: ${result.task_status_msg}`);
    // submitted / processing → continue polling
  }
  throw new Error(`Task ${taskId} timed out after 10 minutes`);
}
```

Task status descriptions:
- `submitted` — task has been submitted, awaiting processing
- `processing` — task is being processed
- `succeed` — task completed successfully; `task_result.videos` contains the video URL
- `failed` — task failed

---

## Generation-time Usage (Direct Agent Call)

Use the built-in scripts for generation-time calls. The scripts read `INTEGRATIONS_API_KEY` from the environment.

**The Bash tool timeout MUST be set to 600000ms (600 seconds).**

**Submit + poll (all-in-one):**

```bash
# Text-to-video
python3 <skill-path>/scripts/generate_omni_video.py \
  --prompt "A futuristic city with flying cars at dusk" \
  --aspect-ratio 16:9 \
  --duration 5 \
  --output-dir /tmp/omni_video

# Image-to-video (repeat --image / --image-url for multiple references)
python3 <skill-path>/scripts/generate_omni_video.py \
  --prompt "Animate this scene" \
  --image /path/to/ref.jpg \
  --output-dir /tmp/omni_video
```

**Resume polling an existing task:**

```bash
python3 <skill-path>/scripts/query_omni_video.py --task-id "<task_id>" --output-dir /tmp/omni_video
```

The scripts print one JSON line:
- On success: `{"status":"succeed","task_id":"...","videos":[{"url":"...","file":"..."}]}`
- If still processing: `{"status":"processing","task_id":"..."}`

On failure they print an error to stderr and exit with a non-zero code.

**Generation-time file download (required):**

Video URLs are ephemeral CDN links (expire after 30 days). If `--output-dir` is not passed, download immediately:

```bash
curl -L -o /tmp/generated_omni_video.mp4 "<task_result.videos[0].url>"
```

> For full parameter details, see `references/submit-api.md` (submit) and `references/query-api.md` (query).

---

## Post-generation Usage (In-app via Edge Function)

In the application, proxy requests through two separate Edge Functions: one for submitting tasks and one for querying status. The query Edge Function transfers the video URL to Supabase Storage once the task is complete, returning a persistent public URL to the frontend.

> For complete Edge Function code and frontend call patterns, see the "Post-generation Usage" sections in `references/submit-api.md` and `references/query-api.md`.


## Fixed Model and Resolution (Required for Generated Apps)

- Expose only O3 / Kling V3 Omni. Always send `model_name: "kling-v3-omni"`; show a fixed model label instead of a model switcher.
- The server fills the same model when omitted and rejects any other model before calling upstream. The CLI accepts only `--model kling-v3-omni` and defaults to it.
- Offer 720P, 1080P and 4K, mapped to top-level `mode: "std"`, `"pro"` and `"4k"`. Default to `pro`; do not send the newer protocol's `settings.resolution`.
- Show resolution and scenario limitations beside the generation controls. Report upstream rejection accurately; never silently downgrade or automatically create another billed task.
- Verification boundary: the Beijing endpoint produced 3840×2160 for an O3 + feature-reference-video + 4K test. This is not a live verification of the Singapore endpoint or base-video editing.
- Validate default O3/pro, all three mode mappings, invalid-model rejection and unchanged overseas endpoint IDs. A submitted task is not a successful render; confirm terminal success and the actual output dimensions.
