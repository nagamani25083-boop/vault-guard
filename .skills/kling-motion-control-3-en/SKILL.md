---
name: kling-motion-control-3-en
description: Generate character motion-transfer videos with the overseas Kling Motion Control 3.0 API using an appearance reference image and a motion reference video. Supports prompts, one optional Element, image/video orientation, original audio or mute, 720p/1080p output, automatic asynchronous polling, video preview, download, and persistent storage. Use for overseas Kling motion control, motion transfer, reference-video-driven animation, or making an image character perform a video's motion.
license: MIT
---

# Kling Motion Control 3.0 — Overseas

## Capabilities

Use the Singapore-region Kling Motion Control 3.0 API to transfer motion from a reference video to a character from a reference image or Element:

- the image defines appearance, clothing, character, and background;
- the video supplies motion and optional original audio;
- an optional prompt adds clothing, environment, visual elements, or camera instructions;
- at most one Element may improve character consistency;
- the application automatically polls the asynchronous task;
- a successful result must include playable preview and download controls;
- upstream video URLs expire after 30 days and should be persisted promptly.

## Registered API Plugin Endpoints

| Purpose | Endpoint |
|---|---|
| Create motion-control task | `POST https://app-f58c4fdcbbpd-api-m9xKdopkqvMa.gateway.appmedo.com/motion-control/kling-3.0` |
| Query exact task IDs | `GET https://app-f58c4fdcbbpd-api-qYGWzQv1x4GY.gateway.appmedo.com/tasks` |
| Gateway authentication | `X-Gateway-Authorization: Bearer ${INTEGRATIONS_API_KEY}` |
| Statuses | `submitted`, `processing`, `succeeded`, `failed` |

This Skill intentionally defines exactly two APIs. User history must come from the application's own authenticated, user-scoped database records.

Datawheel registered API IDs are `api-m9xKdopkqvMa` for creation and `api-qYGWzQv1x4GY` for exact query. Preserve this two-interface set and these methods and paths.

## Prerequisites

- Read the platform gateway credential from server-side `INTEGRATIONS_API_KEY` only.
- Never place the key, Authorization value, image Base64, or full upstream response in frontend code or logs.
- Image and video inputs must be reachable by Kling. The image field also accepts API-supported Base64 input.
- For generation-time calls, use `scripts/kling_motion_control.py` instead of rewriting an ad hoc client.

## Mandatory Execution Contract

1. Validate the reference image, motion video, orientation, and duration constraints.
2. Create exactly one task and save `data.id` plus the optional `external_id`.
3. Treat creation as submission, not generation success.
4. Poll the exact task by system ID; when a query returns an array, match `id` or `external_id` instead of reading `data[0]`.
5. Continue for `submitted` and `processing`; stop on `failed`; on `succeeded`, require at least one `outputs[type=video].url`.
6. Render the successful video in a player and expose a download/save action.
7. Persist temporary outputs to application storage unless the upstream contract explicitly provides durable hosted storage. This API does not: results are cleared after 30 days.
8. A transfer failure retries only transfer, never the billable generation task.
9. Check both HTTP status and business `code`; success requires an HTTP success and `code=0`.

A page that shows only “success” and a task ID is incomplete and fails acceptance.

## Input Contract

### `contents`

Required:

- exactly one `{ "type": "image", "url": "..." }`;
- exactly one `{ "type": "video", "url": "..." }`.

Optional:

- one `{ "type": "prompt", "text": "..." }`, up to 2500 characters;
- at most one `{ "type": "element", "element_id": "...", "id": "..." }`.

`element.id` is the prompt reference index and must be unique within the task. When an Element is used, `settings.character_orientation` must be `video`.

### `settings`

- `character_orientation` is required:
  - `image`: follow the image orientation; motion video maximum 10 seconds;
  - `video`: follow the video orientation; motion video maximum 30 seconds.
- `audio`: `original` by default, or `off`.
- `resolution`: `720p` by default, or `1080p`.

### Media Constraints

- Image: JPG/JPEG/PNG, at most 50MB, width and height at least 300px, aspect ratio from `1:2.5` to `2.5:1`.
- Video: MP4/MOV, at least 3 seconds, at most 10 or 30 seconds according to orientation, at most 100MB, width and height from 340px through 3850px.
- Prefer one person, one continuous take, a clear upper body or full body with all limbs and head visible, limited occlusion, smooth motion, and proportions similar to the reference image.

## Generation-Time Usage

```bash
export INTEGRATIONS_API_KEY='<server-side platform gateway credential>'

python3 scripts/kling_motion_control.py create \
  --image-url 'https://example.com/character.png' \
  --video-url 'https://example.com/motion.mp4' \
  --prompt 'The character wears a loose gray T-shirt and denim shorts.' \
  --character-orientation video \
  --resolution 1080p \
  --audio original \
  --external-task-id 'motion-unique-id'
```

Creation returns a task ID. Continue automatically through polling and download:

```bash
python3 scripts/kling_motion_control.py wait \
  --task-id '<TASK_ID>' \
  --interval 7 \
  --timeout 600 \
  --download '/absolute/path/result.mp4'
```

Exact query is also available:

```bash
python3 scripts/kling_motion_control.py query --task-ids '<TASK_ID_1>,<TASK_ID_2>'
python3 scripts/kling_motion_control.py query --external-task-ids '<EXTERNAL_ID>'
```

## Application Workflow — Mandatory Complete Result

The generated application must implement two server-side Edge Functions:

1. `kling-motion-control-overseas-create`: validate inputs, create one task, and return `task_id`;
2. `kling-motion-control-overseas-query`: accept exactly one of `task_id` and `external_task_id`, query upstream, precisely match the task, persist successful video outputs, and return application-storage URLs.

The frontend must execute:

`submit once → save task ID → poll every 3 seconds for the first 30 seconds → poll every 7 seconds afterward → extract video output → render video player → enable download/save`

Only display “Generation complete” after `status=succeeded`, a video URL exists, the preview is rendered, and download/save is actionable. For `failed`, show the task `message`. After ten minutes, retain the task ID and provide “Continue checking.” Restore polling or the final result after page refresh.

Read and implement `references/app-complete-workflow.md`. It contains directly usable Edge Function, React polling, player, download, storage transfer, and state UI code. Natural-language reminders alone are insufficient.

## State and Idempotency

- Generate a unique `external_task_id` per upstream account.
- Disable duplicate submission while creating.
- Store ownership using the authenticated application user ID and reject task IDs not owned by that user.
- Use `task.id + output.id` as the transfer idempotency key.
- Allow only forward state progress: `submitted → processing → succeeded|failed`.
- A media download failure does not change a succeeded generation into a failed generation.

## References

- `references/motion-control-create-api.md`: creation request and response contract.
- `references/task-query-api.md`: exact task query and output mapping.
- `references/app-complete-workflow.md`: mandatory Edge Function, polling, preview, download, and persistence implementation.
- `references/error-handling.md`: safe propagation and retry boundaries.
- `scripts/kling_motion_control.py`: reusable generation-time CLI.

## Notes

- Use English for application copy, code comments, messages, and documentation.
- Do not add unsupported APIs, models, or fields from Omni/Turbo skills.
- Use only the registered API IDs and gateway endpoints documented in this Skill.
- Backend metering metadata is controlled by the API Plugin. Do not expose pricing, raw plugin configuration, or billing details to the application frontend.
