# Unified Exact Task Query

## Registered API Plugin

```http
GET https://app-f58c4fdcbbpd-api-qYGWzQv1x4GY.gateway.appmedo.com/tasks?task_ids=TASK_ID
GET https://app-f58c4fdcbbpd-api-qYGWzQv1x4GY.gateway.appmedo.com/tasks?external_task_ids=EXTERNAL_ID
X-Gateway-Authorization: Bearer ${INTEGRATIONS_API_KEY}
```

API ID: `api-qYGWzQv1x4GY`. Region: Singapore. Authentication is platform-managed.

Exactly one of `task_ids` and `external_task_ids` is required. Both accept comma-separated batch values. This Skill uses exact task query only.

## Response Shape

```json
{
  "code": 0,
  "message": "success",
  "request_id": "string",
  "data": [
    {
      "id": "string",
      "status": "succeeded",
      "message": "string",
      "external_id": "string",
      "outputs": [
        {
          "type": "video",
          "id": "string",
          "url": "string",
          "watermark_url": "string",
          "duration": "string"
        }
      ]
    }
  ]
}
```

## Application Consumption

- Match the requested `id` or `external_id`; never assume `data[0]` is the target.
- `submitted` / `processing`: continue automatic polling and do not display generation success.
- `failed`: stop polling and show the task `message`.
- `succeeded`: filter for `outputs[].type === "video"` and require at least one `url`.
- Persist the temporary URL, render a video player, and expose download/save.
- Upstream results are cleared after 30 days.

See `app-complete-workflow.md` for the complete implementation.
