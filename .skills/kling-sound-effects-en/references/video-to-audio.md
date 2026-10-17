# Create Video to Audio Task

**Source**: Kling AI Audio API

Generate sound effects and background music for an existing video.

- **Method**: `POST`
- **Endpoint**: `https://app-f58c4fdcbbpd-api-NLZ1R6MBQ4J9.gateway.appmedo.com/v1/audio/video-to-audio`
- **Headers**:
  - `Content-Type`: `application/json` (Required)

### Request Body

| Parameter | Type | Required | Description |
|---|---|---|---|
| `video_id` | string | Optional | Kling video ID (within 30 days, 3.0s-20.0s). Exactly one of video_id or video_url required. |
| `video_url` | string | Optional | Link to .mp4/.mov video (<=100MB, 3.0s-20.0s). Exactly one of video_id or video_url required. |
| `sound_effect_prompt` | string | Optional | Sound effect prompt (<=200 chars) |
| `bgm_prompt` | string | Optional | Background music prompt (<=200 chars) |
| `asmr_mode` | boolean | Optional | Enable ASMR mode (default false) |
| `external_task_id` | string | No | Customized unique task ID |
| `callback_url` | string | No | Callback notification address |

### Example Request

```bash
curl --request POST \
  --url https://app-f58c4fdcbbpd-api-NLZ1R6MBQ4J9.gateway.appmedo.com/v1/audio/video-to-audio \
  --header 'Content-Type: application/json' \
  --data '{
    "video_url": "https://p1-kling.klingai.com/kcdn/cdn-kcdn112452/kling-qa-test/20fps-7s.mov"
  }'
```

### Example Response (200)

```json
{
  "code": 0,
  "message": "string",
  "request_id": "string",
  "data": {
    "task_id": "string",
    "task_info": {
      "external_task_id": "string"
    },
    "task_status": "submitted",
    "created_at": 1722769557708,
    "updated_at": 1722769557708
  }
}
```

### Task and result handling

- Check both the HTTP result and business `code`; HTTP 200 alone does not mean generation succeeded.
- Task states are `submitted`, `processing`, `succeed`, and `failed`. Only `succeed` with nonempty media is a completed result. On failure, show `task_status_msg` when available.
- Retain the returned `data.task_id` and use the matching single-task query API. A submitted task is not a playable result.
- If provided, `external_task_id` must be unique within the upstream account. It does not replace user ownership checks. Omit unused optional fields.
- Omit `callback_url` unless a verified server-side callback handler is configured. Otherwise query the existing task.
- A creation timeout may have occurred after the upstream accepted the request. Do not automatically create another paid task.

### Shared-account applications

- Persist the application user and task association on the server. Query, history and save operations must check that association for the current user.
- Do not expose upstream account-wide task lists to end users. Knowing a task ID is not proof of ownership.

---

# Query Video to Audio Task

**Source**: Kling AI Audio API

Query status and generated video/audio outputs of a video-to-audio generation task.

- **Method**: `GET`
- **Endpoint**: `https://app-f58c4fdcbbpd-api-NLZ1R6MBQ4J9.gateway.appmedo.com/v1/audio/video-to-audio/{task_id}`
### Path Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `task_id` | string | Yes | Task ID for audio/video generation |

### Example Request

```bash
curl --request GET \
  --url https://app-f58c4fdcbbpd-api-NLZ1R6MBQ4J9.gateway.appmedo.com/v1/audio/video-to-audio/{task_id}
```

### Example Response (200)

```json
{
  "code": 0,
  "message": "string",
  "request_id": "string",
  "data": {
    "task_id": "string",
    "task_status": "succeed",
    "task_status_msg": "string",
    "task_info": {
      "external_task_id": "string",
      "parent_video": {
        "id": "string",
        "url": "string",
        "duration": "string"
      }
    },
    "task_result": {
      "videos": [
        {
          "id": "string",
          "url": "string",
          "duration": "string"
        }
      ],
      "audios": [
        {
          "id": "string",
          "url_mp3": "string",
          "url_wav": "string",
          "duration_mp3": "string",
          "duration_wav": "string"
        }
      ]
    },
    "final_unit_deduction": "string",
    "final_balance_deduction": {
      "quota": "string",
      "list_price": "string"
    },
    "created_at": 1722769557708,
    "updated_at": 1722769557708
  }
}
```

### Task and result handling

- Check both the HTTP result and business `code`; HTTP 200 alone does not mean generation succeeded.
- Task states are `submitted`, `processing`, `succeed`, and `failed`. Only `succeed` with nonempty media is a completed result. On failure, show `task_status_msg` when available.
- Replace `{task_id}` with the system task ID returned by the corresponding creation API, encoded as one path segment. Verify the response task ID matches.
- Poll without overlapping requests; stop at a terminal state or timeout, and resume the same task rather than regenerating.
- Read audio links from `data.task_result.audios[].url_mp3` and `url_wav`. Read video links from `data.task_result.videos[].url`.
- Render returned media directly for preview and open/download. Provider files are retained for 30 days; download promptly. History records are not permanent file storage.
- Private transfer is optional. A transfer failure must preserve the generated result and must not trigger generation again.

### Shared-account applications

- Persist the application user and task association on the server. Query, history and save operations must check that association for the current user.
- Do not expose upstream account-wide task lists to end users. Knowing a task ID is not proof of ownership.

Runtime calls use the managed API mapping in api.md; examples document request bodies and responses, not direct provider access.
