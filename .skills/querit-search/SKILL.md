---
name: querit-search
description: Querit real-time web search API for overseas apps. Returns structured results (title, URL, snippet, site name, page age) with optional site, time range, country, and language filters. Use this skill whenever a user wants to add a web search feature, a news or research link list, fact-checking lookup, multilingual web retrieval, or any in-app feature that needs raw search result lists. For Gemini-style summarized answers with citations, prefer the ai-search skill instead.
license: MIT
---

# Querit Search

## Overview

Call Querit `POST /v1/search` through the Miaoda app gateway to retrieve real-time web results.

- **Upstream**: `https://app-f58c4fdcbbpd-api-w9Rb5Jdedqq9.gateway.appmedo.com/v1/search`
- **Gateway marker URL (rewritten per app)**: `POST https://app-f58c4fdcbbpd-api-w9Rb5Jdedqq9.gateway.appmedo.com/v1/search`
- **Auth**: `platform_managed` — use `X-Gateway-Authorization: Bearer ${INTEGRATIONS_API_KEY}` (never hard-code Querit keys; never expose keys to the browser)
- **Response**: JSON list under `results.result[]` (`url`, `title`, `snippet`, `site_name`, `page_age`, optional `site_icon`)
- **Billing**: This endpoint is billed per call — avoid redundant calls with identical query parameters.
- **Coexistence**: default structured web search skill for overseas apps; use `@ai-search` when the user wants Gemini grounded summaries with citations

Official docs: https://www.querit.ai/en/docs/reference/post

### Core request parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Search query |
| `count` | integer | No | Max number of results |
| `chunksPerDoc` | integer | No | Summary chunks per result; **use `1`** on Free/PAYG (Enterprise may allow up to 3). This is not `count`. |
| `filters.sites.include` / `exclude` | string[] | No | Site allow/deny lists |
| `filters.timeRange.date` | string | No | `dN` / `wN` / `mN` / `yN` or `YYYY-MM-DDtoYYYY-MM-DD` |
| `filters.geo.countries.include` | string[] | No | e.g. `united states`, `japan`, `germany` (see docs enum) |
| `filters.languages.include` | string[] | No | e.g. `english`, `japanese`, `german`, `french`, `spanish`, `portuguese`, `korean` |

### Response envelope

| Field | Type | Description |
|-------|------|-------------|
| `took` | string | Server latency (e.g. `385ms`) |
| `error_code` | integer/string | `200` on success; aligns with HTTP errors |
| `error_msg` | string | Error detail |
| `search_id` | number | Support correlation id — log on failures |
| `query_context.query` | string | Echoed query |
| `results.result[]` | array | Hits |

---

## End-to-End Workflow

```
User enters a search query
    ↓
Frontend calls Edge Function (POST JSON)
    ↓
Edge Function injects INTEGRATIONS_API_KEY
    ↓
Gateway rewrites the marker host and forwards to Querit /v1/search
    ↓
Edge Function returns results.result[] to the frontend
    ↓
Frontend renders title / snippet / site_name / page_age with a link to url
```

> See `references/querit-search-api.md` for the full parameter table, generation-time code, and Edge Function code.

---

## Generation-time usage (Agent direct call)

See `references/querit-search-api.md` for full TypeScript helpers.

Summary: `POST` the gateway marker URL with a JSON body and `X-Gateway-Authorization`. Prefer `chunksPerDoc: 1`. On repeated `429` / `5xx`, stop after bounded retries and fall back to `@ai-search` if the user still needs results.

```bash
curl -s -X POST \
  -H "X-Gateway-Authorization: Bearer ${INTEGRATIONS_API_KEY}" \
  -H "Content-Type: application/json" \
  "https://app-f58c4fdcbbpd-api-w9Rb5Jdedqq9.gateway.appmedo.com/v1/search" \
  -d '{"query":"latest AI news","count":10,"chunksPerDoc":1,"filters":{"timeRange":{"date":"d7"},"languages":{"include":["english"]}}}'
```

---

## Runtime usage (in-app via Edge Function)

Proxy through an Edge Function so `INTEGRATIONS_API_KEY` never reaches the client. Full Edge Function + frontend invoke examples: `references/querit-search-api.md`.

---

## Notes

- **Key security**: only Edge Functions / server-side generation may read `INTEGRATIONS_API_KEY`; never expose it to the frontend.
- **Overseas only**: do not publish this skill into CN `managed` / `system` catalogs.
- **Errors**: handle `401` (auth), `429` (rate/quota), `400` / `500`; always log `search_id` on failures so support can correlate.
- **Fallback**: on repeated `429` / `5xx`, fall back to `@ai-search`.
- **Schema caveat**: the request supports `chunksPerDoc`; the response exposes `snippet` (not a separate chunks array). Keep `chunksPerDoc=1` — the platform is on Free / PAYG, where 1 is the cap.
- **Billing**: this endpoint is billed per call; cache results at the application layer for identical queries and avoid polling loops.
