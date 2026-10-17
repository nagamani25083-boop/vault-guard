# Motion Control 3.0 — Create Task

## Registered API Plugin

```http
POST https://app-f58c4fdcbbpd-api-m9xKdopkqvMa.gateway.appmedo.com/motion-control/kling-3.0
X-Gateway-Authorization: Bearer ${INTEGRATIONS_API_KEY}
Content-Type: application/json
```

| Property | Value |
|---|---|
| API ID | `api-m9xKdopkqvMa` |
| Method and upstream path | `POST /motion-control/kling-3.0` |
| Region | Singapore |
| Authentication | Platform-managed gateway |

## Request

```json
{
  "contents": [
    { "type": "prompt", "text": "The character wears a loose gray T-shirt and denim shorts." },
    { "type": "image", "url": "https://example.com/character.png" },
    { "type": "video", "url": "https://example.com/motion.mp4" }
  ],
  "settings": {
    "character_orientation": "video",
    "audio": "original",
    "resolution": "1080p"
  },
  "options": {
    "callback_url": "https://example.com/callback",
    "external_task_id": "motion-unique-id",
    "watermark_info": { "enabled": false }
  }
}
```

| Field | Type | Required | Contract |
|---|---|---:|---|
| `contents` | array | yes | Must contain one image and one video |
| `contents[].type` | string | yes | `prompt`, `image`, `video`, or `element` |
| `prompt.text` | string | conditional | Maximum 2500 characters |
| `image.url` | string | conditional | URL or supported Base64 input |
| `video.url` | string | conditional | Reachable media URL |
| `element.element_id` | string | conditional | System-generated Element ID |
| `element.id` | string | conditional | Unique prompt reference index |
| `settings.character_orientation` | string | yes | `image` or `video` |
| `settings.audio` | string | no | `original` or `off`; default `original` |
| `settings.resolution` | string | no | `720p` or `1080p`; default `720p` |
| `options.callback_url` | string | no | Server callback URL |
| `options.external_task_id` | string | no | Unique within the upstream account |
| `options.watermark_info.enabled` | boolean | no | Default `false` |

## Response

```json
{
  "code": 0,
  "message": "string",
  "request_id": "string",
  "data": {
    "id": "string",
    "status": "submitted",
    "create_time": 1781080778802,
    "update_time": 1781080794151,
    "external_id": "string"
  }
}
```

Save `data.id`. The creation response means “submitted,” not “video ready.” Immediately enter the query workflow.
