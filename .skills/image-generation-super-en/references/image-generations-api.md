# Image Generation API

## Endpoint

`POST https://app-f58c4fdcbbpd-api-Aa2P8vvAdWOL.gateway.appmedo.com/v1/images/generations`

Content-Type: `application/json`  
Authentication: `Authorization: Bearer ${INTEGRATIONS_API_KEY}`

## Request body

| Field | Type | Required | Notes |
|---|---|---|---|
| `model` | string | yes | `gpt-image-2` or `gpt-image-2.5-flare`; default `gpt-image-2` |
| `prompt` | string | yes | Image description |
| `size` | string | no | `1024x1024`, `1536x1024`, `1024x1536` or `2848x1152` |
| `n` | integer | no | Fixed to `1` by this Skill |
| `quality` | string | no | Image-2: `low/medium/high/auto`; Flare also supports `xhigh/max` |
| `background` | string | no | `opaque` or `auto`; Flare also supports `transparent` |
| `output_format` | string | no | PNG for Flare |
| `response_format` | string | yes | `b64` for the current gateway wrapper |

## Response

`data[0].b64_json` is raw Base64 image data without a data URI prefix. `data[0].revised_prompt` is optional. Decode and save the image immediately. Do not print Base64 to the model context.

This overseas Skill uses platform API ID `api-Aa2P8vvAdWOL` for image generation. The upstream endpoint, method and request schema remain unchanged.
