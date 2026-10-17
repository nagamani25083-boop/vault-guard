---
name: image-generation-super-en
description: Image Generation and Editing (Super). Generate and edit images with Miaoda-ImageGen-Super for text-to-image, image-to-image, background replacement, style transfer, product visuals, posters and illustrations.
license: MIT
---

# Image Generation and Editing (Super)

This overseas package uses its own platform-generated API IDs for image generation and editing. The upstream endpoints and request methods remain unchanged. Editing uses the supplier-supported JSON images[].image_url field.

## Models

| Display label | API value | Default |
|---|---|---|
| Image-2 | `gpt-image-2` | Yes |
| Image-2.5-Flare | `gpt-image-2.5-flare` | No |

Keep display labels separate from API values. Do not expose raw provider model names in user-facing errors. Flare supports `xhigh` and `max` quality and transparent PNG backgrounds; Image-2 supports `low`, `medium`, `high` and `auto`. Do not add Sunburst.

## Capabilities

- Text-to-image generation
- Image editing with a single reference image (one image only), sent as JSON `images[0].image_url`
- Background replacement, style transfer and local repainting on the reference image
- Mask-based erasing through the bundled two-step `erase_prepare.py` → `generate_image.py` flow
- PNG output and revised prompt reporting
- Web, task, mini-program and app projects

## API contract

| Operation | Method | Endpoint |
|---|---|---|
| Image generation | POST | `https://app-f58c4fdcbbpd-api-Aa2P8vvAdWOL.gateway.appmedo.com/v1/images/generations` |
| Image editing | POST | `https://app-f58c4fdcbbpd-api-Aa2P8vvAdWOL.gateway.appmedo.com/v1/images/edits` |

Authentication is platform-managed. Read `INTEGRATIONS_API_KEY` and send `Authorization: Bearer <key>`. Image generation uses a JSON body. Image editing uses a JSON body with exactly one `images[0].image_url` string containing a MIME-correct data URL or provider-accessible image URL; do not use `images[].b64_json` as input. Responses contain `data[].b64_json` and may contain `revised_prompt` and `usage`.

## Generation-time workflow

Use `scripts/generate_image.py` for every generation or edit. Do not bypass the script, switch endpoints, or retry an uncertain paid request. Base64 must be decoded and written directly to the requested output file, never printed to the model context.

```bash
python3 scripts/generate_image.py --prompt "A golden retriever in a sunlit garden, editorial illustration, high detail" --output result.png --size 1024x1024
python3 scripts/generate_image.py --model gpt-image-2.5-flare --quality high --prompt "A cinematic product poster" --output poster.png --size 1536x1024
python3 scripts/generate_image.py --prompt "Keep the product and replace the background with a white studio" --images product.png --output product_edited.png --size 1024x1024
```

Use a 600-second tool timeout. Generate one output per call (`n=1`). Never overwrite an input image. Use `_edited`, `_v2`, or `_erased` for new output files.

## Mask erasing

When the user supplies an original image and a mask, white means erase and black means preserve. Run `erase_prepare.py` first, then pass its JSON `prompt`, `prepared_image` and `size` unchanged to `generate_image.py`. Run the two commands separately. Do not deliver the prepared intermediate image.

## Prompt guidance

Rewrite the request into a concise English visual description: subject, action, environment, lighting, style and quality. When editing, describe what must remain before describing the requested change. When a reference image is present, use the edit path rather than text-to-image.

## Failure handling

Retry only explicit transient errors (429 or an identified empty-result 5xx) once with the identical request. Network timeouts, invalid JSON, missing results and download failures are outcome-uncertain and must not trigger a new paid generation. Return sanitized diagnostics without keys, signed URLs or Base64.

## References

- `references/image-generations-api.md`
- `references/image-edits-api.md`
- `references/app.md`
