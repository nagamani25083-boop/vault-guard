---
name: kling-sound-effects-en
description: Generate short sound effects from text or add sound effects and background music to existing videos with Kling. Use for game sounds, ambience, short-video sound design and ASMR. Supports text-to-audio durations of 3–10 seconds, video inputs of 3–20 seconds, progress tracking, MP3/WAV playback, downloads and private saving. Applications must enforce per-user task ownership when sharing an upstream credential.
license: MIT
---

# Sound Effects Generation (Kling)

## Overview and scope
Create sound effects from text, or generate sound effects and background music for an existing video. Suitable for web and task-based projects. This skill does not offer voice customization, voice cloning, speech synthesis or song generation.
Read [API contract](references/api.md) and [integration guide](references/integration.md) before implementing. Preserve the provided scripts and assets rather than replacing them with an untested implementation.

## Package stage and prerequisites
This overseas package is configured from the supplied backend definition with four real API IDs. Server and generation-time operator calls use `https://<API_ID>@app-f58c4fdcbbpd-api-ELbW03DAPQrY.gateway.appmedo.com/...` and `X-Gateway-Authorization: Bearer ${INTEGRATIONS_API_KEY}` in the platform gateway-enabled runtime. Provider credentials stay in backend configuration, never in this package or the browser. Application user sessions remain separate from gateway credentials.
See references/api.md for the exact route mapping. Gateway deployment, paid generation and QA playback still require live acceptance; local checks are not evidence of those results.

## Input contract
### Text to audio
- `prompt`: required nonempty string, maximum 200 characters.
- `duration`: required number from 3.0 to 10.0 seconds inclusive, one decimal place.
- `external_task_id`: optional unique custom task ID within the upstream account; the app generates its own UUID to prevent collisions between users.
- `callback_url`: optional task-status callback. Only use a server-configured trusted URL after implementing the provider's callback verification protocol. Otherwise omit it and poll.

### Video to audio
- Exactly one of `video_id` and `video_url` must be supplied.
- `video_id`: Kling-generated video within the last 30 days, duration 3.0–20.0 seconds. Verify its ownership using a trusted local source mapping before accepting it.
- `video_url`: MP4/MOV, no more than 100 MB, duration 3.0–20.0 seconds. The application uses HTTPS-accessible URLs for delivery. Check actual uploaded file metadata; a URL suffix alone is not validation.
- `sound_effect_prompt` and `bgm_prompt`: optional strings, each at most 200 characters.
- `asmr_mode`: optional boolean, default false.
- `external_task_id` and `callback_url`: same rules as above.
- Do not add a text-to-audio `duration` parameter to video requests. Video metadata is not a user-supplied generation duration override.

## Execution paths
- Application: deploy `assets/edge.ts` as `kling-audio/index.ts` together with `assets/core.mjs` and `assets/media-policy.mjs`, run `assets/schema.sql`, and integrate `assets/client.js` using the existing authenticated Supabase client.
- App-user tasks: execute `python3 scripts/task.py --help`, then use the deployed ownership-checking Edge endpoint and the actual user's session.
- Generation-time operator tasks: execute `python3 scripts/upstream_task.py --help`. Create a private receipt once; query only that receipt. This operator tool is not a public app endpoint or a replacement for app authentication. Its local receipt is not a security boundary between app users.
- Provide actual login when using shared credentials and per-user history. Do not silently enable anonymous authentication.

## Shared-credential isolation
Validate each application's real session on the server. Derive user identity from authentication, never a supplied user_id. Save ownership before submitting a paid task. Query, list, save and signed-link operations must verify ownership every time. RLS and private storage are required; service-role use does not remove ownership checks.
Never expose the upstream account-wide task list. “My creations” reads only locally owned database rows. Knowing task_id/external_task_id does not authorize access. Return 404 for another user's task. Do not allow arbitrary upstream video IDs without a trusted ownership mapping.

## Asynchronous result contract
Check HTTP and `code === 0`. Save `data.task_id`; query that exact ID. Upstream states are `submitted`, `processing`, `succeed`, `failed`; map `succeed` to UI `succeeded`. Unknown states, ID mismatch and empty successful results are protocol errors.
Use non-overlapping polling with a delay and a deadline. Stop on terminal states or unmount; restore existing tasks after refresh. Never recreate a paid task because polling or saving failed. Creation timeout may mean an accepted task: reconcile the stored external ID before resubmission.
On success, render actual audio/video players and download links. Private storage is optional and only enabled when can_save is true; do not automatically call save. Provider media is cleared after 30 days, so download promptly. Retry storage independently of generation. Success requires usable media, not merely a task ID.
The UI must distinguish idle, submitting, submitted, processing, succeeded, failed and timeout. Failed tasks display task_status_msg. Preserve input and task context on errors.

## Limits and dependencies
No extra language-model skill is needed to submit the user's description. Add one only for an explicitly requested open-ended text capability, using the overseas platform's actual available skill.
The supplied transfer implementation caps each file at 32 MiB and 20 seconds; these are application resource budgets, not provider limits. Larger results require a verified supported transfer worker. Do not claim that every allowed input guarantees a result fitting these budgets.


## Media delivery contract
Deploy assets/media-policy.mjs beside core.mjs and index.ts. Default delivery uses the provider media URLs for playback and open/download; never automatically call save after success. MEDIA_HOSTS is optional and must not be requested as a required application secret. Only show private transfer when can_save is true. Preserve successful media if transfer fails. Clearly show the 30-day provider retention; history is not permanent media storage. Verify actual playback/download in QA. This does not remove the private-transfer implementation or its exact-host restrictions.
