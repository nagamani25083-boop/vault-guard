#!/usr/bin/env python3
"""
Generate or edit an image via Miaoda-ImageGen-Super and save the result to disk.
Base64 data never enters the LLM context.

Usage:
    # Text-to-image
    python3 generate_image.py --prompt "a cat" --output image.png [--size 1024x1024]

    # Image editing (one input image)
    python3 generate_image.py --prompt "make it anime" --output image_v2.png \
        --images /path/to/img1.png

Environment:
    INTEGRATIONS_API_KEY - platform-injected API key (required)

Exit codes:
    0 - success, prints JSON: {"file": "...", "revised_prompt": "...", "size": "..."}
    1 - API or argument error
"""

import os
import sys
import json
import base64
import argparse
import time
import tempfile
import re
import socket
import ipaddress
from urllib.parse import urlsplit
import urllib.request
import urllib.error


GENERATIONS_URL = os.environ.get(
    "IMAGE_GENERATIONS_URL",
    "https://app-f58c4fdcbbpd-api-Aa2P8vvAdWOL.gateway.appmedo.com/v1/images/generations",
)
EDITS_URL = os.environ.get(
    "IMAGE_EDITS_URL",
    "https://app-f58c4fdcbbpd-api-Aa2P8vvAdWOL.gateway.appmedo.com/v1/images/edits",
)


def parse_args():
    """Parse command-line arguments."""
    p = argparse.ArgumentParser()
    p.add_argument("--prompt", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--size", default="1024x1024")
    p.add_argument("--model", choices=["gpt-image-2", "gpt-image-2.5-flare"], default="gpt-image-2")
    p.add_argument("--quality", choices=["low", "medium", "high", "xhigh", "max", "auto"], default=None)
    p.add_argument("--background", choices=["opaque", "transparent", "auto"], default=None)
    p.add_argument("--images", nargs="+", default=[])
    return p.parse_args()


class ImageFailure(Exception):
    def __init__(self, code, retryable=False, details=None):
        self.code, self.retryable = code, retryable
        self.details = details or {}
        super().__init__(code)



def safe_error(value):
    text = str(value)
    for name in ("INTEGRATIONS_API_KEY", "IMAGE_UPSTREAM_AUTH"):
        secret = os.environ.get(name)
        if secret: text = text.replace(secret, "[REDACTED]")
    text = re.sub(r"(?i)Bearer\s+[^\s\"<>]+", "Bearer [REDACTED]", text)
    text = re.sub(r"sk-[A-Za-z0-9_-]+", "[REDACTED]", text)
    # Signed result URLs and embedded image payloads must not enter diagnostics.
    text = re.sub(r"https?://[^\s\"<>]+", "[URL_REDACTED]", text)
    text = re.sub(r"[A-Za-z0-9+/=]{256,}", "[PAYLOAD_REDACTED]", text)
    text = re.sub(r'(?i)((?:token|secret|api[_-]?key|signature)["\']?\s*[:=]\s*["\']?)[^\s,}\"\']+', r'\1[REDACTED]', text)
    return text[:4096]


def error_details(stage, exc=None, body=None, headers=None, **extra):
    out = {"stage": stage, **extra}
    if exc is not None:
        out["exception_type"] = type(exc).__name__
        out["message"] = safe_error(getattr(exc, "reason", exc))
        if isinstance(exc, urllib.error.HTTPError): out["http_status"] = exc.code
    if headers:
        for name in ("X-Request-Id", "X-Hyan-Request-Id", "Request-Id", "Retry-After"):
            value = headers.get(name)
            if value: out[name.lower().replace("-", "_")] = safe_error(value)
    if body is not None:
        text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False)
        out["upstream_error_body"] = safe_error(text)
        out["body_truncated"] = len(text) > 4096
    return out


def save_image(b64: str, path: str):
    try:
        raw = base64.b64decode(b64, validate=True)
    except (ValueError, TypeError):
        raise ImageFailure("invalid_base64_no_regeneration")
    save_bytes(raw, path)


def save_bytes(raw, path):
    valid = (raw.startswith(b"\x89PNG\r\n\x1a\n") or raw.startswith(b"\xff\xd8\xff")
             or (raw[:4] == b"RIFF" and raw[8:12] == b"WEBP"))
    if not valid:
        raise ImageFailure("invalid_image_no_regeneration")
    dest = os.path.abspath(path)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(dest), prefix=".image-")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(raw)
        os.replace(tmp, dest)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


def request_json(req):
    # Exact same Request/body on retry. Never retry ambiguous successful responses.
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                raw = resp.read(96 * 1024 * 1024 + 1)
            if len(raw) > 96 * 1024 * 1024:
                raise ImageFailure("response_too_large_no_regeneration")
            try:
                d = json.loads(raw)
            except (ValueError, UnicodeError):
                raise ImageFailure("invalid_json_outcome_uncertain", details=error_details("generation_response", body=raw))
            if not isinstance(d, dict):
                raise ImageFailure("invalid_schema_outcome_uncertain")
            if d.get("error"):
                err = d["error"]
                code = err.get("code") if isinstance(err, dict) else None
                # Only explicitly identified transient failures; no blanket error retry.
                transient = code in ("server_error", "internal_server_error", "service_unavailable", "rate_limit_exceeded")
                raise ImageFailure("upstream_error", transient and not d.get("data"), error_details("generation_response", body=err, headers=resp.headers, http_status=resp.status))
            return d
        except urllib.error.HTTPError as e:
            raw_error = e.read(65536)
            try: error_body = json.loads(raw_error)
            except (ValueError, UnicodeError): error_body = {}
            explicit = isinstance(error_body, dict) and error_body.get("error") and not error_body.get("data")
            retry = e.code == 429 or (e.code in (500, 502, 503, 504) and bool(explicit))
            failure = ImageFailure("http_" + str(e.code), retry, error_details("generation_request", e, raw_error, e.headers))
        except ImageFailure as e:
            failure = e
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            raise ImageFailure("network_outcome_uncertain_no_regeneration", details=error_details("generation_request", e))
        if not failure.retryable or attempt == 1:
            raise failure
        print(json.dumps({"event":"retry", "attempt":2, "reason":failure.code}), file=sys.stderr)
        time.sleep(2)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def download_image(url):
    u = urlsplit(url)
    if u.scheme != "https" or not u.hostname or u.username or u.password or u.port not in (None, 443):
        raise ImageFailure("unsafe_result_url")
    addresses = socket.getaddrinfo(u.hostname, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ImageFailure("unsafe_result_host")
    # No gateway credentials sent to the media host; redirects intentionally refused.
    opener = urllib.request.build_opener(NoRedirect())
    for attempt in range(2):
        try:
            with opener.open(urllib.request.Request(url), timeout=60) as r:
                data = r.read(64 * 1024 * 1024 + 1)
            if len(data) > 64 * 1024 * 1024: raise ImageFailure("image_too_large")
            return data
        except (urllib.error.URLError, TimeoutError) as e:
            raw_error = e.read(65536) if isinstance(e, urllib.error.HTTPError) else None
            details = error_details("result_download", e, raw_error, getattr(e, "headers", None),
                                    attempt=attempt+1, media_host=u.hostname, regenerated=False)
            # Permanent HTTP errors and redirects are not retried; never retry generation.
            retryable = not isinstance(e, urllib.error.HTTPError) or e.code in (500,502,503,504)
            if attempt or not retryable:
                raise ImageFailure("result_download_failed_no_regeneration", details=details)
            time.sleep(2)


def persist_result(d, output):
    data = d.get("data")
    if not isinstance(data, list) or not data or not isinstance(data[0], dict):
        raise ImageFailure("missing_image_outcome_uncertain")
    item = data[0]
    if isinstance(item.get("b64_json"), str) and item["b64_json"]:
        save_image(item["b64_json"], output)
    elif isinstance(item.get("url"), str) and item["url"]:
        save_bytes(download_image(item["url"]), output)
        print(json.dumps({"event":"url_fallback", "regenerated":False}), file=sys.stderr)
    else:
        raise ImageFailure("missing_image_outcome_uncertain")



def model_options(model="gpt-image-2", quality=None, background=None):
    if model not in ("gpt-image-2", "gpt-image-2.5-flare"):
        raise ImageFailure("unsupported_model")
    allowed = ("low", "medium", "high", "auto") if model == "gpt-image-2" else ("low", "medium", "high", "xhigh", "max", "auto")
    if quality is not None and quality not in allowed:
        raise ImageFailure("unsupported_quality_for_model")
    if background not in (None, "opaque", "transparent", "auto"):
        raise ImageFailure("unsupported_background")
    if background == "transparent" and model != "gpt-image-2.5-flare":
        raise ImageFailure("transparent_requires_flare")
    options = {"model": model}
    if quality is not None: options["quality"] = quality
    if background is not None: options["background"] = background
    if model == "gpt-image-2.5-flare": options["output_format"] = "png"
    return options


def create_image(api_key: str, prompt: str, size: str, output: str, model="gpt-image-2", quality=None, background=None):
    """Call the text-to-image endpoint and save the output."""
    payload = json.dumps({**model_options(model, quality, background), "prompt": prompt, "size": size, "n": 1, "response_format": "b64"}).encode()
    req = urllib.request.Request(
        GENERATIONS_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    d = request_json(req)
    persist_result(d, output)
    return d


def edit_image(api_key: str, prompt: str, size: str, images: list, output: str, model="gpt-image-2", quality=None, background=None):
    """Edit exactly one reference image using JSON images[].image_url."""
    if len(images) != 1:
        raise ImageFailure("expected_exactly_1_image")
    src = images[0]
    with open(src, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("ascii")
    ext = os.path.splitext(src)[1].lower()
    content_type = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}.get(ext, "image/png")
    payload = {
        **model_options(model, quality, background),
        "prompt": prompt, "size": size, "n": 1,
        "images": [{"image_url": "data:" + content_type + ";base64," + encoded}],
    }
    req = urllib.request.Request(
        EDITS_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    d = request_json(req)
    persist_result(d, output)
    return d


def main():
    """Select generation or editing based on --images and print a result JSON."""
    args = parse_args()
    if not args.prompt.strip() or len(args.images) > 1:
        raise ImageFailure("invalid_arguments")
    if any(os.path.realpath(args.output) == os.path.realpath(i) for i in args.images):
        raise ImageFailure("output_must_not_overwrite_input")
    model_options(args.model, args.quality, args.background)
    api_key = os.environ.get("INTEGRATIONS_API_KEY", "")
    if not api_key:
        print("INTEGRATIONS_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    if args.images:
        d = edit_image(api_key, args.prompt, args.size, args.images, args.output, args.model, args.quality, args.background)
    else:
        d = create_image(api_key, args.prompt, args.size, args.output, args.model, args.quality, args.background)

    print(json.dumps({
        "file": args.output,
        "revised_prompt": d["data"][0].get("revised_prompt", ""),
        "size": d.get("size", args.size),
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({"error": e.code if isinstance(e, ImageFailure) else type(e).__name__, "action":"stop_do_not_bypass_script", "details": e.details if isinstance(e, ImageFailure) else error_details("local_execution", e)}), file=sys.stderr)
        sys.exit(1)
