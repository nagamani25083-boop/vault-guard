# Kling 3.0 Turbo Overseas Error Handling

Validate both the HTTP status and JSON `code`. A request is successful only when the HTTP request succeeds and `code=0`.

## Structured Error Propagation

Miaoda-generated Edge Functions must not collapse every failure into an unqualified “unknown error.” Return safe diagnostic fields:

```json
{
  "error": "Safe user-facing message",
  "type": "gateway_error",
  "code": 1002,
  "message": "Upstream error message",
  "request_id": "request-id"
}
```

- `error`: required, safe user-facing message;
- `type`: `gateway_error` or `upstream_unavailable`;
- `code`: upstream business code when available;
- `message`: upstream message when available and safe;
- `request_id`: upstream request ID when available;
- preserve upstream HTTP 400, 401, 403, 404, 429, and 5xx statuses;
- treat HTTP 200 with `code != 0` as failure;
- return 502 or 504 for network, timeout, or non-JSON upstream failures.

## Error Handling Matrix

| Condition | Handling |
|---|---|
| Invalid application input | Return HTTP 400 with a field-level message |
| HTTP 401 | Do not retry; verify the overseas API Plugin credential type |
| HTTP 403 | Do not retry; verify overseas model and region permissions |
| HTTP 404 | Do not retry; verify the overseas API ID, Singapore domain, and path |
| HTTP 429 | Back off query requests; check by `external_task_id` before retrying creation |
| HTTP 5xx or timeout | Query may back off; creation must not be blindly retried |
| Content safety failure | Ask the user to change the input; do not auto-rewrite and recreate |
| Transfer failure | Retry transfer only; do not regenerate the video |

## Creation Idempotency

Every creation request should use a user-scoped unique `external_task_id`. If creation returns a network error or ambiguous response:

1. keep the request record and `external_task_id`;
2. query by `external_task_ids` first;
3. if a task exists, continue polling it;
4. only consider another creation request after confirming no task exists.

## Security and Billing Boundaries

Never expose the following to the frontend or skill output:

- API keys, Authorization values, JWTs, or AK/SK values;
- internal gateway URLs or raw API Plugin configuration;
- API IDs in user-facing error messages;
- billing data, billing amount, list price, unit price, original price, discount price, or billing formulas.

The latest Plugin metadata reports `billing_mode: billing`, API-level `enable_billing: false`, `need_count_calls: true`, and `enable_internal_gateway_forwarding: true`. Treat these as backend metadata rather than proof of final settlement behavior. Query, polling, callback, download, and transfer must not create another generation task. Do not expose prices, amounts, or billing formulas.
