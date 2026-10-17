#!/usr/bin/env python3
"""Call the Google Cloud Translation API v2 and print the JSON result.

Reads INTEGRATIONS_API_KEY from the environment and sends it via the
X-Gateway-Authorization header with a "Bearer " prefix.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


ENDPOINT = "https://app-f58c4fdcbbpd-api-GaDwZ8DX7jPY.gateway.appmedo.com/language/translate/v2"


def fail(message):
    """Print an error message to stderr and exit with a non-zero status."""
    print(message, file=sys.stderr)
    sys.exit(1)


def main():
    """Entry point: parse arguments, translate text, and print JSON to stdout."""
    parser = argparse.ArgumentParser(description="Translate text via Google Cloud Translation API v2.")
    parser.add_argument("--q", required=True, help="Text content to be translated.")
    parser.add_argument("--target", required=True, help="Target language code (e.g. en, zh, fr).")
    parser.add_argument("--source", help="Source language code (omit for auto-detection).")
    parser.add_argument(
        "--format",
        dest="fmt",
        choices=["text", "html"],
        help="Text format: text (default) or html.",
    )
    parser.add_argument("--timeout", type=int, default=600, help="Request timeout in seconds.")
    args = parser.parse_args()

    api_key = os.environ.get("INTEGRATIONS_API_KEY")
    if not api_key:
        fail("INTEGRATIONS_API_KEY is required")

    payload = {"q": args.q, "target": args.target}
    if args.source:
        payload["source"] = args.source
    if args.fmt:
        payload["format"] = args.fmt

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Gateway-Authorization": "Bearer " + api_key,
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=args.timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        fail("HTTP %s: %s" % (exc.code, detail))
    except urllib.error.URLError as exc:
        fail("Request failed: " + str(exc.reason))
    except TimeoutError:
        fail("Request timed out")

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail("Invalid JSON response from upstream: " + str(exc))

    print(json.dumps(
        {"status": "succeed", "result": result},
        ensure_ascii=False,
        separators=(",", ":"),
    ))


if __name__ == "__main__":
    main()
