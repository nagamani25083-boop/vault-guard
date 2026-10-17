# Error Handling and Retry Boundaries

A request succeeds only when the HTTP response is successful and JSON `code` equals `0`.

Return safe structured application errors:

```json
{
  "error": "Motion-control task failed",
  "type": "upstream_error",
  "code": 1200,
  "message": "Upstream error message",
  "request_id": "request-id"
}
```

- Invalid application input: HTTP 400 with a field-level message.
- Authentication or permission errors: do not retry automatically.
- HTTP 429 or temporary server failures: use bounded backoff for query only.
- Ambiguous creation response: query the unique `external_task_id` before another creation attempt.
- Failed transfer: retry transfer only; never recreate the billable video task.
- Non-JSON, network, or timeout failures: return `gateway_error` or `upstream_unavailable` with HTTP 502/504.
- Never return credentials, Authorization values, raw plugin configuration, prices, or billing details to the frontend.
