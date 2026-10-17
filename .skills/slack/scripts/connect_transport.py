"""Fail-closed transport for managed Connect Skills.

The caller supplies only a fixed marker URL, managed environment values and
validated public arguments. This module never discovers tools or accepts URLs,
account IDs, or credentials from the command payload.
"""

import json
import socket
import ssl
import urllib.error
import urllib.parse
import urllib.request


MAX_INPUT_BYTES = 64 * 1024
MAX_RESPONSE_BYTES = 1024 * 1024
REQUEST_TIMEOUT_SECONDS = 30


class ConnectFailure(Exception):
    """Safe failure with a stable code, a fixed message and optional Provider detail."""

    def __init__(self, code, message, provider_detail=None):
        super().__init__(message)
        self.code = code
        self.safe_message = message
        self.provider_detail = provider_detail

    def as_result(self):
        """Convert the failure into the stable response envelope."""
        result = {
            "successful": False,
            "error": {"code": self.code, "message": self.safe_message},
        }
        if self.provider_detail:
            result["error"]["detail"] = self.provider_detail
            result["_meta"] = {"contentTrust": "untrusted_provider_content"}
        return result


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Reject HTTP redirects so credentials never reach another origin."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def build_opener():
    """Build an HTTPS-only opener with proxies and redirects disabled."""
    return urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        urllib.request.HTTPSHandler(context=ssl.create_default_context()),
        NoRedirectHandler(),
    )


def read_command(stream):
    """Read one size-limited JSON command from a binary stream."""
    raw = stream.read(MAX_INPUT_BYTES + 1)
    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    if len(raw) > MAX_INPUT_BYTES:
        raise ConnectFailure("ACTION_NOT_ALLOWED", "The request is too large")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ConnectFailure("ACTION_NOT_ALLOWED", "The request must be one JSON object")
    if not isinstance(value, dict):
        raise ConnectFailure("ACTION_NOT_ALLOWED", "The request must be one JSON object")
    return value


def managed_credentials(environ, connection_env):
    """Read and validate platform-managed runtime credentials."""
    jwt = (environ.get("INTEGRATIONS_API_KEY") or "").strip()
    connection = (environ.get(connection_env) or "").strip()
    if not connection:
        raise ConnectFailure("CONNECTION_REQUIRED", "Connect this provider and try again")
    if not jwt:
        raise ConnectFailure("CONNECT_DISABLED", "Connect is unavailable in this runtime")
    if not _safe_credential(jwt, 16_384) or not _safe_credential(connection, 2_048):
        raise ConnectFailure("CONNECT_DISABLED", "Connect runtime configuration is invalid")
    return jwt, connection


def execute(marker_url, gateway_jwt, connection, arguments, opener=None):
    """Execute one bounded request through the fixed gateway marker."""
    _validate_marker_url(marker_url)
    if not _safe_credential(gateway_jwt, 16_384) or not _safe_credential(connection, 2_048):
        raise ConnectFailure("CONNECT_DISABLED", "Connect runtime configuration is invalid")

    body = json.dumps(
        {"connected_account_id": connection, "arguments": arguments},
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    if len(body) > MAX_INPUT_BYTES:
        raise ConnectFailure("ACTION_NOT_ALLOWED", "The request is too large")

    request = urllib.request.Request(
        marker_url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Gateway-Authorization": "Bearer " + gateway_jwt,
        },
        method="POST",
    )
    if opener is None:
        opener = build_opener()

    try:
        with opener.open(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            if getattr(response, "status", 200) != 200:
                raise ConnectFailure("RESULT_UNKNOWN", "The provider request did not complete")
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as error:
        raise _http_failure(error.code)
    except (urllib.error.URLError, socket.timeout, TimeoutError):
        raise ConnectFailure("RESULT_UNKNOWN", "The provider result is unknown")

    if len(raw) > MAX_RESPONSE_BYTES:
        raise ConnectFailure("RESULT_UNKNOWN", "The provider response is too large")
    try:
        result = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ConnectFailure("RESULT_UNKNOWN", "The provider returned an invalid response")
    if not isinstance(result, dict) or type(result.get("successful")) is not bool:
        raise ConnectFailure("RESULT_UNKNOWN", "The provider returned an invalid response")
    if not result["successful"]:
        error = result.get("error") if isinstance(result.get("error"), dict) else {}
        code = str(error.get("code") or "")
        if code == "UPSTREAM_RESPONSE_ERROR":
            raise _provider_failure(error)
        raise _upstream_failure(code)
    return {"successful": True, "data": result.get("data")}


def mark_untrusted(result):
    """Mark successful Provider content as untrusted data."""
    output = dict(result)
    output["_meta"] = {"contentTrust": "untrusted_provider_content"}
    return output


def write_result(stream, result):
    """Write exactly one bounded JSON result line."""
    encoded = json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_RESPONSE_BYTES:
        encoded = json.dumps(
            ConnectFailure("RESULT_UNKNOWN", "The provider response is too large").as_result(),
            separators=(",", ":"),
        ).encode("utf-8")
    stream.write(encoded.decode("utf-8") + "\n")


def _safe_credential(value, maximum):
    return bool(value) and len(value) <= maximum and not any(ord(char) < 32 or ord(char) == 127 for char in value)


def _validate_marker_url(value):
    try:
        parsed = urllib.parse.urlsplit(value)
        port = parsed.port
    except (TypeError, ValueError):
        raise ConnectFailure("CONNECT_DISABLED", "The gateway route is invalid")
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or port not in (None, 443)
        or parsed.query
        or parsed.fragment
    ):
        raise ConnectFailure("CONNECT_DISABLED", "The gateway route is invalid")


def _http_failure(status):
    if status == 401:
        return ConnectFailure("CONNECT_DISABLED", "Connect is unavailable in this runtime")
    if status in (403, 404, 409, 422):
        return ConnectFailure("ACTION_NOT_ALLOWED", "The provider request was rejected")
    if status == 429:
        return ConnectFailure("CONNECT_RATE_LIMITED", "The provider rate limit was reached")
    if status in (408, 502, 503, 504):
        return ConnectFailure("PROVIDER_TIMEOUT", "The provider request timed out")
    return ConnectFailure("RESULT_UNKNOWN", "The provider result is unknown")


def _upstream_failure(code):
    status = None
    if code.startswith("UPSTREAM_"):
        try:
            status = int(code[len("UPSTREAM_"):])
        except ValueError:
            status = None
    return _http_failure(status) if status is not None else ConnectFailure(
        "RESULT_UNKNOWN", "The provider result is unknown"
    )


def _provider_failure(error):
    """Classify the gateway's HTTP 200 Provider failure and keep its detail."""
    detail = error.get("detail") if isinstance(error.get("detail"), str) else None
    if error.get("reason") == "INVALID_ARGUMENTS":
        return ConnectFailure(
            "INVALID_ARGUMENTS",
            "The provider rejected the arguments before running the action; nothing was changed. "
            "Correct the arguments using error.detail, then run the action again",
            detail,
        )
    return ConnectFailure("RESULT_UNKNOWN", "The provider result is unknown", detail)
