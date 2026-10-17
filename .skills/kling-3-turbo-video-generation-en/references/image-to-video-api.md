# Kling 3.0 Turbo Overseas Image to Video API

## API Information

| Property | Value |
|---|---|
| Region | Singapore |
| Third-party domain | `app-f58c4fdcbbpd-api-e94GlB86xpEa.gateway.appmedo.com` |
| Method | `POST` |
| Upstream path | `/image-to-video/kling-3.0-turbo` |
| API Plugin ID | `73eecc62-33b0-48d6-aa34-7d309680476b` |
| API Plugin API ID | `api-e94GlB86xpEa` |
| API Plugin endpoint | `POST https://app-f58c4fdcbbpd-api-e94GlB86xpEa.gateway.appmedo.com/image-to-video/kling-3.0-turbo` |
| Content-Type | `application/json` |
| Response | Asynchronous task; read `data.id` |

Use only the configured overseas API ID shown above; never copy a domestic API ID. The raw overseas Kling API uses `Authorization: Bearer {apikey}`. Miaoda-generated applications must use the approved overseas API Plugin endpoint and platform-managed server authentication.

## Request Body

```json
{
  "contents": [
    { "type": "prompt", "text": "The person slowly turns toward the camera." },
    { "type": "first_frame", "url": "https://your-cdn.com/start-frame.jpg" }
  ],
  "settings": {
    "resolution": "1080p",
    "duration": 10
  },
  "options": {
    "callback_url": "https://example.com/callback",
    "external_task_id": "unique-task-id",
    "watermark_info": { "enabled": false }
  }
}
```

## Parameters

- `contents`: required array;
- `contents[].type`: `prompt` or `first_frame`;
- `contents[].text`: required for a `prompt` item, maximum 2500 characters;
- `contents[].url`: required for the `first_frame` item, URL or Base64;
- exactly one `first_frame` is supported;
- `settings.resolution`: optional, `720p` or `1080p`, default `720p`;
- `settings.duration`: optional integer from 3 to 15, default 5;
- `options.callback_url`: optional callback URL;
- `options.external_task_id`: optional, unique within one user account;
- `options.watermark_info.enabled`: optional boolean, default `false`;
- supported image formats: JPG, JPEG, PNG;
- maximum image size: 50MB;
- width and height must each be at least 300px;
- image aspect ratio must be between 1:2.5 and 2.5:1;
- only first-frame input is supported;
- first-and-last-frame and last-frame-only input are not supported;
- do not add a `model` field.

## Prompt-Based Multi-Shot Format

Multi-shot text is placed in the ordinary prompt object:

```json
{
  "type": "prompt",
  "text": "shot 1, 2, A railway platform; shot 2, 3, A close-up of the passenger;"
}
```

The same 1–6 shot, duration-sum, and 512-character-per-shot rules apply. Do not add separate multi-shot API fields.

## Creation Response

```json
{
  "code": 0,
  "message": "string",
  "request_id": "string",
  "data": {
    "id": "893605946402811985",
    "status": "submitted",
    "create_time": 1781080778802,
    "update_time": 1781080794151,
    "external_id": "unique-task-id"
  }
}
```

Use `data.id` as the system task ID.

## Complete Asynchronous Example

```typescript
const createEndpoint =
  "https://app-f58c4fdcbbpd-api-e94GlB86xpEa.gateway.appmedo.com/image-to-video/kling-3.0-turbo";
const apiKey = process.env["INTEGRATIONS_API_KEY"]!;
const externalTaskId = `overseas-image-${crypto.randomUUID()}`;

const createResponse = await fetch(createEndpoint, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-Gateway-Authorization": `Bearer ${apiKey}`,
  },
  body: JSON.stringify({
    contents: [
      { type: "prompt", text: "The person slowly turns toward the camera." },
      { type: "first_frame", url: firstFrameUrl },
    ],
    settings: { resolution: "1080p", duration: 5 },
    options: {
      external_task_id: externalTaskId,
      watermark_info: { enabled: false },
    },
  }),
});

const createJson = await createResponse.json();
if (!createResponse.ok || createJson.code !== 0) {
  throw new Error(`Create failed: ${createJson.message ?? createResponse.status}`);
}
if (!createJson.data?.id) throw new Error("Creation response is missing data.id");

const taskId = String(createJson.data.id);

while (true) {
  const queryResponse = await fetch(
    `https://app-f58c4fdcbbpd-api-GaDwzVOqmRNY.gateway.appmedo.com/tasks?task_ids=${encodeURIComponent(taskId)}`,
    {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "X-Gateway-Authorization": `Bearer ${apiKey}`,
      },
    },
  );
  const queryJson = await queryResponse.json();
  if (!queryResponse.ok || queryJson.code !== 0) {
    throw new Error(`Query failed: ${queryJson.message ?? queryResponse.status}`);
  }

  const task = queryJson.data.find(
    (item: { id: string }) => String(item.id) === taskId,
  );
  if (!task) throw new Error("Target task was not found");
  if (task.status === "failed") {
    throw new Error(task.message || "Video generation failed");
  }
  if (task.status === "succeeded") {
    const output = task.outputs?.find(
      (item: { type: string }) => item.type === "video",
    );
    if (!output?.url) throw new Error("Successful task has no video output");
    // Persist output.url using task.id + output.id before returning the final result.
    break;
  }
  await new Promise((resolve) => setTimeout(resolve, 7000));
}
```

Base64 data must not be written to logs, frontend error messages, or model context.
