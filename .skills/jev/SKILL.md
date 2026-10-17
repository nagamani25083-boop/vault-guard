---
name: jev
description: "Build Jev-powered apps to classify, score, route, and gate inputs with calibrated probabilities, not generated text."
license: MIT
---

# Jev (TypeSafe System One)

## Overview

Jev is a System One model: it turns unstructured state into **typed, probabilistic decisions**
instead of text. It answers named questions, each with an explicit answer, a calibrated
confidence, and a full probability distribution over the allowed outcomes.

- **Endpoint**: `POST https://app-f58c4fdcbbpd-api-79jKnBxVg4oL.gateway.appmedo.com/v1/systemone`
- **Auth**: `platform_managed` — header `X-Gateway-Authorization: Bearer ${INTEGRATIONS_API_KEY}`
- **Body**: `{ "model": "jev-1.13.0", "state": <string | object>, "questions": <object> }`
  (pinned version; `jev-latest` and `jev-preview` are aliases, see
  [references/systemone-api.md](references/systemone-api.md))
- **Language**: English is Jev's primary language. Write `instructions` and `criteria` in English;
  a non-English `state` works but is less accurate, so check `confidence` before acting on it.
- **Response time**: typically 100–600 ms end-to-end
- **Billing**: TypeSafe bills input tokens (output tokens are free); the platform applies its own
  quota on top (HTTP 429 when exhausted)

### What Jev is for, and what it is not

| Use Jev for | Do not use Jev for |
| --- | --- |
| Classifying text or app state into fixed categories | Writing copy, replies, summaries or any prose |
| Scoring a candidate on an ordered rubric | Open-ended reasoning or multi-step planning |
| Routing to one of N branches, with probabilities | Anything where the output must be a free string |
| Extracting known fields from messy input | Translating or rewriting user content |
| Guardrails: judging a draft before it is used or sent | Replacing a normal LLM where text is the product |

**Jev cannot generate strings.** If a feature needs text, generate it elsewhere and use Jev to
**rank or gate** the candidates. This is the single most important design constraint.

### Three question types

| Type | Answers | Shape |
| --- | --- | --- |
| `choice` | one label from a named set | `{choice, confidence, probabilities}` |
| `score` | one point on an ordered rubric | `{score, confidence, probabilities}` |
| `noul` | yes / no, as a probability | `{noul}` (0–1) |

Every question gets a **stable name**; answers come back keyed by that name. Question authoring,
calibration thresholds and the failure modes are in
[references/question-types.md](references/question-types.md).

A fourth type, `box` (find an object in an image), and image input are experimental upstream
features, not enabled by default; see the last section of
[references/systemone-api.md](references/systemone-api.md) before using them.

## Generation-Time Usage (Agent Direct Call)

The request/response logic lives in `scripts/call_jev.py`; do not re-implement the HTTP call.

1. Write the request to a JSON file — `state` (the data to judge) and `questions` (named questions).
2. Run the script and read the one-line JSON it prints.

```bash
python3 <skill-path>/scripts/call_jev.py --request /tmp/jev-request.json
```

Script prints `{"model": ..., "answers": {<name>: {...}}, "usage": {...}}` on success.
Read the fields the app branches on — do not paste the whole JSON back verbatim.
`--raw` prints the full upstream response instead; `--header NAME:VALUE` adds a request header
(needed for the experimental features in [references/systemone-api.md](references/systemone-api.md)).

**The Bash tool timeout must be set to 600000ms (600 seconds)** when running this script;
the default 120s will cut off slower calls.

A request file:

```json
{
  "model": "jev-1.13.0",
  "state": { "message": "How is your cat doing lately?", "history": [] },
  "questions": {
    "intent": {
      "type": "choice",
      "instructions": "What is the sender's main communicative intent?",
      "criteria": {
        "ask": "asking for information",
        "share": "sharing their own news",
        "care": "checking in on the other person"
      }
    },
    "urgency": {
      "type": "score",
      "instructions": "How time-sensitive is this message?",
      "criteria": ["not at all", "whenever", "this week", "today", "right now"]
    },
    "needs_reply": { "type": "noul", "instructions": "Does this expect a reply?" }
  }
}
```

## Post-Generation Usage (In-App via Edge Function)

The generated app must never hold the TypeSafe key. Proxy the call through an Edge Function that
reads `INTEGRATIONS_API_KEY` from the Deno environment; the raw gateway key never reaches the
browser. Full boilerplate (Edge Function + frontend invoke, quota/balance handling) is in
[references/systemone-api.md](references/systemone-api.md).

## Notes

- **Key security**: `INTEGRATIONS_API_KEY` is read only server-side in the Edge Function or by the
  generation-time script. Never expose it to the frontend, never log it, never put it in a prompt.
- **Error handling**: `429` means the platform quota is exhausted or TypeSafe's rate limit was hit:
  retry at most twice with backoff, then forward the body to the user as-is. Forward `402`
  (insufficient balance) as-is. Retry `529` and `5xx` with backoff (Jev is read-only, so retries are
  safe); fix the request on `400` and `422`. Full table in
  [references/systemone-api.md](references/systemone-api.md).
- **Billing**: Jev is billed by input tokens, and the `state` is counted once per request. Batch
  independent questions about the same `state` into **one** request instead of issuing several
  calls; do not re-ask a question whose answer has not changed.
- **Cost of a wrong question**: Jev never returns a type error, but it will happily answer a badly
  worded question. Low `confidence` means the question or the `state` was ambiguous — check
  `confidence` before acting on an answer.

## References

- [references/systemone-api.md](references/systemone-api.md) — full request/response contract,
  parameter tables, error codes, models and limits, Edge Function boilerplate, generation-time
  script usage, and the experimental Images / Box / long-context features.
- [references/question-types.md](references/question-types.md) — how to write `choice` / `score` /
  `noul` questions, limits, confidence thresholds, and the pitfalls that silently ruin a rubric.
- [references/use-cases.md](references/use-cases.md) — worked examples, including a full chat
  analysis pipeline that shows Jev being used as a judge rather than a generator.
- Upstream docs: <https://docs.typesafe.ai> — API reference, architecture patterns (fan-out,
  confidence-gated routing, composite scoring, intent routing) and cookbooks.
