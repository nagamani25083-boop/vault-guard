# System One API — Full Specification & Code

Gateway marker host uses Traefik rewrite: `api-<id>@app-f58c4fdcbbpd-api-79jKnBxVg4oL.gateway.appmedo.com` → `{app_id}-api-<id>{gateway_suffix}`.

## Endpoint Information

| Item | Value |
|------|-------|
| Endpoint | `POST https://app-f58c4fdcbbpd-api-79jKnBxVg4oL.gateway.appmedo.com/v1/systemone` |
| Models | `GET https://app-f58c4fdcbbpd-api-eLMlzKkOd7V9.gateway.appmedo.com/v1/models` |
| Auth | `platform_managed` — header `X-Gateway-Authorization: Bearer ${INTEGRATIONS_API_KEY}` |
| Content type | `application/json` |
| Billing | TypeSafe bills input tokens (output tokens are free); the platform applies its own quota on top |

## Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | `string` | Yes | Model id, e.g. `jev-1.13.0`. Use `GET /v1/models` to list what the account can call. |
| `state` | `string` \| `object` \| `array` \| `null` | Yes | The data to judge. Prefer a structured object over a prose blob — nested keys are understood as structure, not as text. |
| `questions` | `object` | Yes | Non-empty map of question name → question. Names are the keys of the answers you get back. |
| `questions.<name>.type` | `"choice"` \| `"score"` \| `"noul"` | Yes | Question type. |
| `questions.<name>.instructions` | `string` \| `object` \| `array` \| `null` | No | The question itself. It may be structured, so you can attach per-answer context here. |
| `questions.<name>.criteria` | `object` \| `array` | For `choice`/`score` | `choice`: map of label → description (`null` when a label needs no description), up to 255 labels. `score`: ordered array of level descriptions, index = score from 0. `noul`: optional `{ "true": ..., "false": ... }` describing what yes and no mean. |

`instructions` and every entry in `criteria` accept a string, an object or an array, so a question can
carry its own data. See [Structured Instructions](#structured-instructions).

## Response Fields

| Field Path | Type | Description |
|------------|------|-------------|
| `model` | `string` | Model that answered the request. |
| `answers` | `object` | Answers keyed by question name. |
| `answers.<name>.type` | `string` | Echoes the question type. |
| `answers.<name>.choice` | `string` | `choice` only — the selected label. |
| `answers.<name>.score` | `number` | `score` only — expected score; may fall between rubric levels. |
| `answers.<name>.noul` | `number` | `noul` only — probability of "yes", 0–1. |
| `answers.<name>.confidence` | `number` | `choice`/`score` only — confidence in the selected answer, 0–1. |
| `answers.<name>.probabilities` | `object` | `choice`/`score` only — full distribution over labels/scores. |
| `answers.<name>.legend` | `object` | `score` only — the rubric keyed by score. |
| `answers.<name>.box` | `object` | `box` only (experimental) — `top`, `bottom`, `left`, `right`, each 0–1. |
| `usage.input_tokens` | `number` | Input tokens (billed). Images count as input tokens. |
| `usage.output_tokens` | `number` | Output tokens (not billed). |

### Response codes

| Status | Meaning | Action |
|--------|---------|--------|
| `200` | Answered | Read `answers`; check each `confidence` before branching |
| `400` | The request breaks a rule: empty `questions`, a `score` outside 2 to 10 levels, too much nesting, a non-finite number, an image or `box` question without the images header, or input longer than the context length (`max_tokens_exceeded`) | Fix the request; do not retry |
| `401` / `403` | Gateway key missing, wrong or unauthorized | Check `INTEGRATIONS_API_KEY` binding; do not retry |
| `413` / `415` | Body over 32 MiB / unsupported `Content-Encoding` | Shrink the body or fix the encoding; do not retry |
| `422` | Validation failed, for example a missing field or malformed question; the body names the field | Fix the request; do not retry |
| `429` | Platform quota exhausted, or TypeSafe rate limit | Retry at most twice with exponential backoff; if it persists, surface the response body to the user |
| `402` | Insufficient balance | Surface the response body to the user |
| `408` / `529` / `5xx` | Transient or overloaded | Retry with backoff; Jev is safe to retry (read-only, no side effects) |

## Models and Versions

| Model id | Meaning |
|----------|---------|
| `jev-1.13.0` | The version this skill pins. Confidence values stay comparable across calls. |
| `jev-1.14.0` | Newest release, available from 2026-10-14. Required for `box` questions. |
| `jev-latest` | Alias for the latest stable release. Points to `jev-1.13.0` on 2026-10-15 and moves when a new release ships. |
| `jev-preview` | Alias for the newest release, official or not. Points to `jev-1.14.0` on 2026-10-15. |

Pin a version id in generated apps: an alias can change its answers without any change to your code,
and confidence thresholds tuned on one version may not carry over. Each response's `model` field
names the version that answered. Source: <https://docs.typesafe.ai/models> (read 2026-10-15).

## Limits

| Limit | Value |
|-------|-------|
| Context | 64k tokens per request and 32k per question (the `state` plus one question). There is no separate cap on the number of questions. |
| Long context | Send the header `TypeSafe-Danger-Zone-Long-Context: true` to raise both limits to 262k tokens. Same price per token, but slower and less accurate; use it only when a request needs it. |
| Body | 32 MiB of UTF-8 JSON; at most 64 nesting levels in each of `state`, `instructions` and `criteria`; finite numbers only (send ids and very large numbers as strings). `gzip` and `zstd` `Content-Encoding` are accepted. |
| Choice labels | Up to 255 |
| Score levels | 2 to 10 |

## Language

English is Jev's primary training language and where accuracy is best. Other languages, including
CJK scripts, are handled but not equally well. Write `instructions` and `criteria` in English, test a
non-English `state` on real samples before relying on it, and gate on `confidence`.

## Structured Instructions

`instructions`, Choice label descriptions, Score level entries and Noul `criteria.true` / `false`
accept a string, an object, an array or `null`. Put the question in one field and the data it needs
in others, then refer to the data by field name in backticks. Backtick references also reach into
`state` by path, for example `` `ticket.sender.email` `` or `` `frames[2].frame` ``.

```json
"instructions": {
  "candidate": { "name": "John Smith", "city": "Oakland" },
  "question": "Is the resume in `state` for the same person as `candidate`?"
}
```

A Choice label can carry a definition plus what it does not cover, which sharpens the boundary
between similar labels:

```json
"criteria": {
  "billing": { "what": "Charges, refunds, subscriptions", "not_for": "Order tracking" },
  "orders": { "what": "Delivery, cancellation, returns", "not_for": "Charges" }
}
```

## Experimental: Images, Box and Long Context

TypeSafe marks Images and `box` questions as not yet production-ready: the request format, answers and
limits can change between releases. Nothing here has been verified through the MeDo gateway (custom
headers, request size). Test on DEV before putting any of it in a generated app.

- **Images.** Send the header `TypeSafe-Danger-Zone-Images: true`. List each image once in a top-level
  `assets` map, `{ "<reference>": { "type": "image", "format": "png" | "jpg", "data_base64": "..." } }`,
  and write the same reference string wherever the image belongs in `state`, `instructions` or
  `criteria`. Every reference must appear in the request. PNG or JPEG only, 256 to 1568 px per side,
  at most 16 MiB per file, upright pixels (metadata is stripped and EXIF rotation is not applied).
  Jev 1.13 and 1.14 accept images. Upstream recommends multipart upload for large images; this skill's
  script sends base64 JSON only.
- **Box.** Finds one target in an image; takes `instructions` and no `criteria`, for example
  ``"instructions": "the coffee mug in `photo`"``. Needs
  `jev-1.14.0` or `jev-preview` and the images header. The answer is
  `{ "type": "box", "box": { "top", "bottom", "left", "right" }, "confidence" }`, each edge a fraction
  from 0 to 1 measured from the top-left corner. A box is always returned, even when the target is
  absent, so pair it with a `noul` ("Is there a coffee mug in `photo`?") and ignore the box when that
  is low.
- **Long context.** See [Limits](#limits).

Run any of these from the script with extra headers:

```bash
python3 <skill-path>/scripts/call_jev.py --request /tmp/jev-request.json \
  --header TypeSafe-Danger-Zone-Images:true --raw
```

More: <https://docs.typesafe.ai/images>, <https://docs.typesafe.ai/primitives/box>. |

## Generation-Time Usage (Direct Agent Call)

`scripts/call_jev.py` owns the HTTP call. Write the request to a file and invoke the script:

```bash
python3 <skill-path>/scripts/call_jev.py --request /tmp/jev-request.json
```

Inline form, for small requests:

```bash
python3 <skill-path>/scripts/call_jev.py \
  --state '{"text":"I was charged twice"}' \
  --questions '{"billing":{"type":"noul","instructions":"Is this about billing?"}}'
```

List callable models:

```bash
python3 <skill-path>/scripts/call_jev.py --models
```

**The Bash tool timeout must be set to 600000ms (600 seconds)**, or the default 120s may cut a
slow call off.

## Post-Generation Usage (In-App via Edge Function)

The Edge Function holds the **question set** (authored at generation time) and accepts only the
`state` from the client. Do not let the browser send arbitrary `questions` — that would give the
frontend control over what the model is asked, which is this API's equivalent of raw SQL.

```typescript
// edge-functions/<api-name>.ts
import { serve } from "https://deno.land/std/http/server.ts";

// Authored once at generation time and locked here — never taken from the request body.
const QUESTIONS = {
  intent: {
    type: "choice",
    instructions: "What is the sender's main communicative intent?",
    criteria: {
      ask: "asking for information",
      share: "sharing their own news",
      care: "checking in on the other person",
    },
  },
} as const;

serve(async (req: Request): Promise<Response> => {
  if (req.method !== "POST") {
    return new Response("Method Not Allowed", { status: 405 });
  }

  // --- Parse client request ---
  let state: unknown;
  try {
    const body = await req.json();
    state = body.state;
    if (state === undefined || state === null) throw new Error("Missing state");
  } catch {
    return new Response(JSON.stringify({ error: "Invalid request body" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  // --- Inject platform key (never expose to client) ---
  const apiKey = Deno.env.get("INTEGRATIONS_API_KEY");
  if (!apiKey) {
    return new Response(JSON.stringify({ error: "Server configuration error" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }

  // --- Call upstream ---
  const upstream = await fetch("https://app-f58c4fdcbbpd-api-79jKnBxVg4oL.gateway.appmedo.com/v1/systemone", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Gateway-Authorization": `Bearer ${apiKey}`,
    },
    body: JSON.stringify({ model: "jev-1.13.0", state, questions: QUESTIONS }),
  });

  // Forward quota/balance errors verbatim
  if (upstream.status === 429 || upstream.status === 402) {
    const errText = await upstream.text();
    return new Response(errText, {
      status: upstream.status,
      headers: { "Content-Type": "application/json" },
    });
  }

  if (!upstream.ok) {
    return new Response(
      JSON.stringify({ error: `Upstream error: ${upstream.status}` }),
      { status: 502, headers: { "Content-Type": "application/json" } }
    );
  }

  const data = await upstream.json();
  return new Response(JSON.stringify(data), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
});
```

### Frontend → Edge Function

```typescript
type JevAnswer =
  | { type: "choice"; choice: string; confidence: number; probabilities: Record<string, number> }
  | { type: "score"; score: number; confidence: number; probabilities: Record<string, number> }
  | { type: "noul"; noul: number };

async function judge(state: unknown): Promise<Record<string, JevAnswer>> {
  const res = await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/<api-name>`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ state }),
  });

  if (res.status === 429) {
    const err = await res.json();
    throw new Error(`Quota exceeded: ${err.message ?? res.statusText}`);
  }
  if (res.status === 402) {
    const err = await res.json();
    throw new Error(`Insufficient balance: ${err.message ?? res.statusText}`);
  }
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);

  const json = (await res.json()) as { answers: Record<string, JevAnswer> };
  return json.answers;
}
```

## Notes

- **Key security**: `INTEGRATIONS_API_KEY` must only be read server-side in the Edge Function or by
  the generation-time script; never expose it to the frontend, never log it.
- **Error handling**: always handle `429` (platform quota exhausted or TypeSafe rate limit; retry at
  most twice with backoff, then surface it) and `402` (insufficient balance; surface it).
- **Billing**: Jev is billed by input tokens and output tokens are free. The `state` is counted once
  per request, so combine independent questions about it into one request; a single `systemone` call
  with ten questions costs far less than ten calls.
- **Retries are safe**: `systemone` has no side effects, so retrying a transient failure cannot
  duplicate an action. This is not true of APIs with write semantics.
