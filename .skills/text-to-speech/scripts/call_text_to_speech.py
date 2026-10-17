#!/usr/bin/env python3
"""Call the LemonFox text-to-speech API and save the resulting audio to a file."""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


ENDPOINT = "https://app-f58c4fdcbbpd-api-GYX1lzGw01Xa.gateway.appmedo.com/v1/audio/speech"


def fail(message):
    """Print an error to stderr and exit non-zero."""
    print(message, file=sys.stderr)
    sys.exit(1)


def report_error_body(raw_bytes):
    """Parse a JSON/text error body and exit with a readable message."""
    text = raw_bytes.decode("utf-8", errors="replace")
    try:
        data = json.loads(text)
    except ValueError:
        fail("API error: " + text)
        return
    msg = data.get("message") or data.get("error") or json.dumps(data, ensure_ascii=False)
    fail("API error: " + str(msg))


def main():
    """Entry point: synthesize text to speech and save the audio file."""
    parser = argparse.ArgumentParser(description="Synthesize text to speech and save the audio file.")
    parser.add_argument("--input", required=True, help="Text content to convert to speech.")
    parser.add_argument("--output", required=True, help="Local file path to save the synthesized audio to.")
    parser.add_argument("--voice", default="heart", help="Voice type, e.g. heart. Default: heart.")
    parser.add_argument("--response-format", dest="response_format", default="mp3",
                        help="Output audio format: mp3, wav, ogg. Default: mp3.")
    parser.add_argument("--timeout", type=int, default=600, help="Request timeout in seconds. Default: 600.")
    args = parser.parse_args()

    api_key = os.environ.get("INTEGRATIONS_API_KEY")
    if not api_key:
        fail("INTEGRATIONS_API_KEY is required")

    body = {
        "input": args.input,
        "voice": args.voice,
        "response_format": args.response_format,
    }
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Gateway-Authorization": "Bearer " + api_key,
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            raw = response.read()
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        content_type = exc.headers.get("Content-Type", "") if exc.headers else ""
        if "json" in content_type or "text" in content_type:
            report_error_body(raw)
        else:
            fail("HTTP %s: %s" % (exc.code, raw.decode("utf-8", errors="replace")))
        return
    except urllib.error.URLError as exc:
        fail("Request failed: " + str(exc.reason))
        return
    except TimeoutError:
        fail("Request timed out")
        return

    # If the API returned JSON/text, it's an error message wrapped in a normal 200
    if "json" in content_type or "text" in content_type:
        report_error_body(raw)
        return

    try:
        with open(args.output, "wb") as fh:
            fh.write(raw)
    except OSError as exc:
        fail("Failed to write audio file %s: %s" % (args.output, exc))
        return

    print(json.dumps(
        {"status": "succeed", "file": args.output, "bytes": len(raw)},
        ensure_ascii=False,
        separators=(",", ":"),
    ))


if __name__ == "__main__":
    main()
