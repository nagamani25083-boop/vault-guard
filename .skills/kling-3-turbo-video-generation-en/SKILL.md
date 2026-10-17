---
name: kling-3-turbo-video-generation-en
description: Generate videos with the overseas Kling 3.0 Turbo APIs, including text-to-video, first-frame image-to-video, prompt-based multi-shot video, asynchronous task polling, and persistent result transfer. Use only the APIs defined by this skill.
license: MIT
---

## Capabilities

Use the Singapore-region Kling 3.0 Turbo model for:

- **Text to Video**: generate a video from an ordinary text prompt.
- **Image to Video**: generate a video from exactly one first-frame image and an optional prompt.
- **Prompt-Based Multi-Shot Video**: describe 1–6 shots with the official prompt syntax; do not use separate multi-shot API fields.
- **Asynchronous Tasks**: submit a task, query its status, and retrieve its result.
- **Persistent Video Transfer**: copy temporary upstream video URLs into application storage.

| Property | Value |
|---|---|
| Provider | KlingAI |
| Region | Singapore |
| Model | Kling 3.0 Turbo, selected by endpoint path |
| Response mode | Asynchronous polling |
| Duration | 3–15 seconds |
| Text-to-video aspect ratio | `16:9`, `9:16`, `1:1` |
| Resolution | `720p`, `1080p` |
| Result | Temporary video URL that must be persisted |

---

## Endpoints

- Text task creation: `POST https://app-f58c4fdcbbpd-api-l9nZxREvJ6V9.gateway.appmedo.com/text-to-video/kling-3.0-turbo`
- Image task creation: `POST https://app-f58c4fdcbbpd-api-e94GlB86xpEa.gateway.appmedo.com/image-to-video/kling-3.0-turbo`
- Unified task query: `GET https://app-f58c4fdcbbpd-api-GaDwzVOqmRNY.gateway.appmedo.com/tasks`

All API Plugin requests use server-side gateway authentication:

```text
X-Gateway-Authorization: Bearer ${INTEGRATIONS_API_KEY}
```

Read `INTEGRATIONS_API_KEY` only in a server process or Edge Function. Never expose it to frontend code, Skill output, returned data, or logs.

These are API Plugin gateway endpoints. Do not replace them with the raw upstream URL, domestic Beijing endpoints, guessed API IDs, or legacy `/v1/videos/...` paths. `INTEGRATIONS_API_KEY` is the platform gateway credential; it is not a Kling AK/SK pair and must not be sent as raw upstream `Authorization` from frontend code.

---

## Capability Boundaries

Use only the three overseas Kling 3.0 Turbo APIs defined by this Skill: text creation, first-frame image creation, and unified task query.

Supported capabilities:

- ordinary text-to-video prompts;
- 1–6 shots expressed with the official prompt syntax;
- image-to-video with exactly one first frame;
- asynchronous query and persistent video transfer.

The multi-shot capability is prompt-level behavior, not an Omni-style API parameter. Request bodies remain `prompt/settings/options` or `contents/settings/options`. Do not add `model`, `model_name`, `multi_shot`, `shot_type`, or `multi_prompt`.

Do not generate unsupported last-frame, first-and-last-frame, multiple-reference-image, reference-video, subject-library, or video-editing fields, UI, database columns, or response structures. Do not switch to or invoke another Skill automatically.

---

## Complete Asynchronous Workflow

This API is asynchronous. Submit a creation request, save the system task ID from `data.id`, and poll until the task succeeds or fails.

```typescript
const apiKey = process.env["INTEGRATIONS_API_KEY"]!;

interface TurboVideoTask {
  taskId: string;
  externalTaskId?: string;
  status: "submitted" | "processing" | "succeeded" | "failed";
}

interface TurboVideoOutput {
  id: string;
  url: string;
  watermarkUrl?: string;
  duration?: string;
}

interface TurboVideoResult extends TurboVideoTask {
  outputs?: TurboVideoOutput[];
  message?: string;
}

async function readJson(response: Response) {
  const text = await response.text();
  try {
    return JSON.parse(text);
  } catch {
    throw new Error(`Upstream returned non-JSON data (HTTP ${response.status})`);
  }
}

async function queryTurboVideoTask(
  taskId?: string,
  externalTaskId?: string,
): Promise<TurboVideoResult> {
  if ((taskId && externalTaskId) || (!taskId && !externalTaskId)) {
    throw new Error("taskId and externalTaskId are mutually exclusive and one is required");
  }

  const query = taskId
    ? `task_ids=${encodeURIComponent(taskId)}`
    : `external_task_ids=${encodeURIComponent(externalTaskId!)}`;

  const response = await fetch(
    `https://app-f58c4fdcbbpd-api-GaDwzVOqmRNY.gateway.appmedo.com/tasks?${query}`,
    {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "X-Gateway-Authorization": `Bearer ${apiKey}`,
      },
    },
  );

  const json = await readJson(response);
  if (!response.ok || json.code !== 0) {
    throw new Error(
      `API error ${json.code ?? response.status}: ${json.message ?? "Task query failed"}`,
    );
  }

  const tasks = Array.isArray(json.data) ? json.data : [];
  const task = tasks.find((item: { id?: string; external_id?: string }) =>
    taskId
      ? String(item.id) === String(taskId)
      : item.external_id === externalTaskId
  );

  if (!task) throw new Error("The query response does not contain the target task");

  return {
    taskId: String(task.id),
    externalTaskId: task.external_id,
    status: task.status,
    message: task.message,
    outputs: task.outputs
      ?.filter((output: { type?: string }) => output.type === "video")
      .map((output: {
        id: string;
        url: string;
        watermark_url?: string;
        duration?: string;
      }) => ({
        id: output.id,
        url: output.url,
        watermarkUrl: output.watermark_url,
        duration: output.duration,
      })),
  };
}

async function pollTurboVideoTask(
  taskId: string,
  timeoutMs = 10 * 60 * 1000,
): Promise<TurboVideoResult> {
  const pollIntervalMs = 7000;
  const deadline = Date.now() + timeoutMs;

  while (Date.now() < deadline) {
    await new Promise((resolve) => setTimeout(resolve, pollIntervalMs));
    const result = await queryTurboVideoTask(taskId);

    if (result.status === "succeeded" || result.status === "failed") {
      return result;
    }
  }

  throw new Error(`Task ${taskId} did not finish within 10 minutes`);
}
```

Never read `data.task_id`, assume `data[0]` is the target task, or accept a non-video output as the final result. For `submitted` and `processing`, continue polling. For `failed`, return the task `message` and do not create another task.

Upstream video URLs expire after 30 days. Persist successful video outputs before returning the final application result. Use `task.id + output.id` as the transfer idempotency key. If transfer fails, retry only the transfer and never regenerate the video.

---

## Generation-Time Usage (Direct Server-Side Call)

Use the platform-injected `INTEGRATIONS_API_KEY` and the configured overseas `API_ID@host` endpoints. Do not construct another gateway base URL and do not use legacy `/v1/videos/...` paths. Creation must run server-side.

### Text to Video

```typescript
const apiKey = process.env["INTEGRATIONS_API_KEY"]!;
const externalTaskId = `overseas-text-${crypto.randomUUID()}`;

const response = await fetch(
  "https://app-f58c4fdcbbpd-api-l9nZxREvJ6V9.gateway.appmedo.com/text-to-video/kling-3.0-turbo",
  {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Gateway-Authorization": `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      prompt: "A rainy Singapore street at night, neon reflections, slow cinematic camera movement.",
      settings: { duration: 5, resolution: "1080p", aspect_ratio: "16:9" },
      options: {
        external_task_id: externalTaskId,
        watermark_info: { enabled: false },
      },
    }),
  },
);

const json = await response.json();
if (!response.ok || json.code !== 0) {
  throw new Error(`Create failed: ${json.message ?? response.status}`);
}
if (!json.data?.id) throw new Error("Creation response is missing data.id");
const taskId = String(json.data.id);
// Store taskId and externalTaskId, then call pollTurboVideoTask(taskId).
```

### Image to Video

```typescript
const response = await fetch(
  "https://app-f58c4fdcbbpd-api-e94GlB86xpEa.gateway.appmedo.com/image-to-video/kling-3.0-turbo",
  {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Gateway-Authorization": `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      contents: [
        { type: "prompt", text: "The product slowly rotates toward the camera." },
        { type: "first_frame", url: firstFrameUrl },
      ],
      settings: { duration: 5, resolution: "1080p" },
      options: {
        external_task_id: `overseas-image-${crypto.randomUUID()}`,
        watermark_info: { enabled: false },
      },
    }),
  },
);

const json = await response.json();
if (!response.ok || json.code !== 0) {
  throw new Error(`Create failed: ${json.message ?? response.status}`);
}
if (!json.data?.id) throw new Error("Creation response is missing data.id");
const taskId = String(json.data.id);
// Store taskId and continue through the same query and transfer workflow.
```

Do not place API keys, Authorization headers, Base64 image data, or temporary video URLs in frontend code, logs, or user-facing errors.

---

## Post-Generation Usage (Application Edge Functions)

Use two application Edge Functions:

| Edge Function | Reference | Responsibility |
|---|---|---|
| `kling-3-turbo-overseas-create` | `references/text-to-video-api.md`, `references/image-to-video-api.md` | Validate input, submit a text or image task, and return `data.id` |
| `kling-3-turbo-overseas-query` | `references/task-query-api.md` | Query status, persist successful video output, and return a persistent URL |

The frontend implements separate submission and polling steps:

1. Invoke `kling-3-turbo-overseas-create` and save the returned task ID.
2. Every 7 seconds, invoke `kling-3-turbo-overseas-query` with a POST body; do not send GET query-string parameters through `supabase.functions.invoke()`.
3. The query Edge Function parses the JSON body once, accepts exactly one of `task_id` and `external_task_id`, and returns HTTP 400 otherwise.
4. The Edge Function converts the body to upstream `GET /tasks?task_ids=...` or `GET /tasks?external_task_ids=...`.
5. Continue polling for `submitted` or `processing`.
6. For `succeeded`, return the persistent application-storage URL only after transfer succeeds.
7. For `failed`, return the task `message`; do not create another task.

```typescript
const { data, error } = await supabase.functions.invoke(
  "kling-3-turbo-overseas-query",
  {
    method: "POST",
    body: { task_id: taskId },
  },
);
if (error) throw error;
```

The create Edge Function must not block while polling, downloading, or transferring. The query Edge Function must never create a generation task.

---

## Prompt and Parameter Constraints

### Text to Video

- `prompt` is required and must not exceed 3072 characters; keeping it within 2500 characters is recommended.
- `settings.resolution` must be `720p` or `1080p`.
- `settings.aspect_ratio` must be `16:9`, `9:16`, or `1:1`.
- `settings.duration` must be an integer from 3 to 15.
- Prompt-based multi-shot format: `shot n, m, words; shot n, m, words;`.
- `n` is the shot sequence number; use 1–6 shots.
- `m` is the shot duration; each shot must be at least one second and all shot durations must sum to `settings.duration`.
- `words` is the shot prompt and must not exceed 512 characters per shot.
- Use half-width semicolons and submit the entire sequence as the ordinary `prompt` string.
- Do not add separate `multi_shot`, `shot_type`, or `multi_prompt` fields.

### Image to Video

- `contents` is required and must contain exactly one `first_frame` item.
- An optional prompt uses `{ type: "prompt", text: "..." }`.
- The first frame uses `{ type: "first_frame", url: "..." }` and accepts URL or Base64 input.
- Prompt-based multi-shot text, when used, remains inside the ordinary `contents[].text` prompt object.
- Supported image formats are JPG, JPEG, and PNG.
- Maximum image size is 50MB.
- Width and height must each be at least 300px.
- Image aspect ratio must be between `1:2.5` and `2.5:1`.
- Last-frame, first-and-last-frame, reference-video, subject-library, and video-editing inputs are not supported.
- Never place Base64 input in logs, console output, error messages, or model context.

---

## Error Handling and Propagation

Do not collapse failures into an unqualified “unknown error.” Creation and query Edge Functions return safe structured errors:

```json
{
  "error": "Safe user-facing message",
  "type": "gateway_error",
  "code": 1002,
  "message": "Upstream error message",
  "request_id": "request-id"
}
```

- Invalid application input: return HTTP 400 with a field-level message.
- Upstream HTTP 400, 401, 403, 404, 429, and 5xx: preserve the applicable HTTP status.
- HTTP 200 with `code != 0`: treat it as failure and preserve `code`, `message`, and `request_id`.
- Network, timeout, or non-JSON response: return `gateway_error` or `upstream_unavailable` with HTTP 502 or 504.
- Ambiguous creation failure: query by the unique `external_task_id` before considering another creation request.
- Transfer failure: return a pending transfer state and retry transfer only.
- Frontend output: expose a safe `error`; retain `code`, `request_id`, and HTTP status for diagnosis.
- Never return API keys, Authorization values, internal gateway URLs, API IDs, raw Plugin configuration, prices, or billing fields to the frontend.

The latest backend metadata reports `billing_mode: billing`, API-level `enable_billing: false`, `need_count_calls: true`, and `enable_internal_gateway_forwarding: true` for the registered Plugin. Treat this only as backend configuration metadata: do not infer the final settlement behavior without platform verification, and do not expose amounts or formulas in this Skill.

---

## Notes

- **Credential security**: read `INTEGRATIONS_API_KEY` only on the server.
- **Asynchronous tasks**: query submitted tasks instead of creating duplicates.
- **Temporary URLs**: generated URLs expire after 30 days; persist successful outputs promptly.
- **Transfer idempotency**: use `task.id + output.id` as the transfer idempotency key.
- **Retry boundary**: query with bounded backoff; do not blindly retry creation; retry transfer without regenerating.
- **Billing**: the API Plugin backend controls metering and settlement. Do not expose prices or billing details.
- **References**: read `references/text-to-video-api.md`, `references/image-to-video-api.md`, `references/task-query-api.md`, and `references/error-codes.md` for complete contracts.
