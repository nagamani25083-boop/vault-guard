# Kling 3.0 Turbo Overseas Task Query API

## API Information

| Property | Value |
|---|---|
| Region | Singapore |
| Third-party domain | `app-f58c4fdcbbpd-api-GaDwzVOqmRNY.gateway.appmedo.com` |
| Method | `GET` |
| Upstream path | `/tasks` |
| API Plugin ID | `73eecc62-33b0-48d6-aa34-7d309680476b` |
| API Plugin API ID | `api-GaDwzVOqmRNY` |
| API Plugin endpoint | `GET https://app-f58c4fdcbbpd-api-GaDwzVOqmRNY.gateway.appmedo.com/tasks` |

Use only the configured overseas query API ID shown above; never copy a domestic API ID.

## Query by System Task ID

```text
GET /tasks?task_ids=<system-task-id>
```

## Query by External Task ID

```text
GET /tasks?external_task_ids=<external-task-id>
```

`task_ids` and `external_task_ids` are mutually exclusive and one is required. Both support comma-separated batch values.

## Query Response

```json
{
  "code": 0,
  "message": "string",
  "request_id": "string",
  "data": [
    {
      "id": "893605946402811985",
      "status": "succeeded",
      "message": "",
      "create_time": 1781080778802,
      "update_time": 1781080794151,
      "external_id": "unique-task-id",
      "outputs": [
        {
          "type": "video",
          "id": "video-id",
          "url": "https://example.com/video.mp4",
          "watermark_url": "https://example.com/video-watermark.mp4",
          "duration": "5"
        }
      ]
    }
  ]
}
```

Match the target task by `data[].id` or `data[].external_id`. Never assume `data[0]` is the requested task. Select only outputs where `type=video`.

## Miaoda Query Boundary

The frontend must invoke the query Edge Function with a POST body. Do not rely on GET query-string parameters when using `supabase.functions.invoke()`.

```typescript
const { data, error } = await supabase.functions.invoke(
  "kling-3-turbo-overseas-query",
  {
    method: "POST",
    body: { task_id: "893605946402811985" },
  },
);
if (error) throw error;
```

An external ID may be sent instead:

```typescript
body: { external_task_id: "unique-task-id" }
```

The query Edge Function must parse the POST body once, enforce the mutually exclusive ID rule, and convert it to the upstream GET query. Read the gateway key only in the Edge Function:

```typescript
const apiKey = Deno.env.get("INTEGRATIONS_API_KEY");
if (!apiKey) {
  return Response.json({ error: "Gateway credential is not configured" }, { status: 500 });
}

const body = await req.json();
const taskId = body.task_id ? String(body.task_id) : undefined;
const externalTaskId = body.external_task_id
  ? String(body.external_task_id)
  : undefined;

if ((taskId && externalTaskId) || (!taskId && !externalTaskId)) {
  return Response.json(
    { error: "task_id and external_task_id are mutually exclusive and one is required" },
    { status: 400 },
  );
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
```

## Complete Polling Example

```typescript
async function waitForOverseasTask(taskId: string) {
  const deadline = Date.now() + 10 * 60 * 1000;

  while (Date.now() < deadline) {
    const { data, error } = await supabase.functions.invoke(
      "kling-3-turbo-overseas-query",
      {
        method: "POST",
        body: { task_id: taskId },
      },
    );
    if (error) throw error;

    if (data.status === "failed") {
      throw new Error(data.message || "Video generation failed");
    }
    if (data.status === "succeeded") {
      const video = data.outputs?.find(
        (item: { type: string }) => item.type === "video",
      );
      if (!video?.url) throw new Error("Successful task has no video output");
      return video;
    }

    await new Promise((resolve) => setTimeout(resolve, 7000));
  }

  throw new Error("Task polling timed out; keep the task ID for later querying");
}
```

## Status Handling

- `submitted`: continue polling;
- `processing`: continue polling;
- `succeeded`: select `outputs[type=video]` and transfer the result;
- `failed`: return the task `message` and do not create another task.

## Persistent Transfer

Generated URLs are removed after 30 days. The query backend must persist successful video outputs before returning a final application result.

- use `task.id + output.id` as the transfer idempotency key;
- return the persistent URL only after successful transfer;
- on transfer failure, return `transfer_status: "pending"` and retry transfer only;
- do not regenerate the video;
- do not treat the temporary 30-day URL as the final persistent result.

## Cursor Query

The overseas API also provides `POST /tasks` with `start_time`, `end_time`, `cursor`, `limit`, and `filters`. It is not part of the single-task generation flow and must not replace ID-based polling.
