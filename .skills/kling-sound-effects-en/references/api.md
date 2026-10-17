# Overseas managed API contract

| API ID | Method | Endpoint |
|---|---|---|
| api-ELbW03DAPQrY | POST | https://app-f58c4fdcbbpd-api-ELbW03DAPQrY.gateway.appmedo.com/v1/audio/text-to-audio |
| api-wYqgkBmrQvw9 | GET | https://app-f58c4fdcbbpd-api-ELbW03DAPQrY.gateway.appmedo.com/v1/audio/text-to-audio/{task_id} |
| api-NLZ1R6MBQ4J9 | POST | https://app-f58c4fdcbbpd-api-ELbW03DAPQrY.gateway.appmedo.com/v1/audio/video-to-audio |
| api-zYm4DrmyA0eL | GET | https://app-f58c4fdcbbpd-api-ELbW03DAPQrY.gateway.appmedo.com/v1/audio/video-to-audio/{task_id} |

Calls use `https://<API_ID>@app-f58c4fdcbbpd-api-ELbW03DAPQrY.gateway.appmedo.com/<path>` with `X-Gateway-Authorization: Bearer ${INTEGRATIONS_API_KEY}` in the platform gateway-enabled runtime. Provider credentials remain in the backend definition. App sessions authenticate app users only.

Only the four listed operations are exposed. App history comes from user-owned database rows, not an upstream account-wide list. Query the exact system task ID returned by create. Preserve endpoint methods and paths.

Read [text-to-audio](text-to-audio.md) and [video-to-audio](video-to-audio.md) for complete parameters and response examples. Callback verification remains unimplemented; omit callbacks and poll.
