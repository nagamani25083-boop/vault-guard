# Image Editing API

## Description
Edits one reference image with a prompt. Keep the original content as requested and change its background, style, or specified details.

## Method
POST

## Endpoint
`https://app-f58c4fdcbbpd-api-rY7JzWWDg5RL.gateway.appmedo.com/v1/images/edits`

## Headers
- `Content-Type`: `application/json`
- `Authorization`: `Bearer ${INTEGRATIONS_API_KEY}`

## Request Body
| Field | Type | Required | Description |
|---|---|---|---|
| `model` | string | Yes | `gpt-image-2` or `gpt-image-2.5-flare`; default `gpt-image-2` |
| `images` | array | Yes | Exactly one reference image |
| `images[0].image_url` | string | Yes | Image data URL (`data:image/png;base64,...`) or a provider-accessible image URL; preserve the actual PNG/JPEG/WebP MIME type |
| `prompt` | string | Yes | Edit instructions describing what to keep and change |
| `size` | string | No | `1024x1024`, `1536x1024`, `1024x1536` or `2848x1152` |
| `n` | integer | No | Fixed to 1 |
| `quality` | string | No | Same model-specific settings as image generation |
| `background` | string | No | Same model-specific settings as image generation |
| `output_format` | string | No | Output format (PNG for Flare) |

This Skill uses JSON with `images[].image_url`. Do not send the input as `images[].b64_json` or a bare file-path string. The bundled script reads the single local image and creates a MIME-correct data URL. Keep encoded image data out of logs and model context.

## Response
```json
{"data":[{"b64_json":"...","revised_prompt":"..."}],"usage":{}}
```
Decode `data[0].b64_json` and save without overwriting the source image. The existing URL-response fallback remains available in the script.

## Example
```bash
curl -X POST https://app-f58c4fdcbbpd-api-rY7JzWWDg5RL.gateway.appmedo.com/v1/images/edits \
  -H "Authorization: Bearer ${INTEGRATIONS_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-image-2.5-flare","prompt":"Keep the product and replace the background with a white studio","size":"1024x1024","n":1,"images":[{"image_url":"data:image/png;base64,<IMAGE_BASE64>"}]}'
```

Platform API ID: `api-rY7JzWWDg5RL`. This JSON contract follows the supplier's stated format; platform end-to-end acceptance still requires a real editing test.
