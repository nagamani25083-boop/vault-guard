#!/usr/bin/env python3
"""Call the OCR.space API and print the parsed OCR result as JSON.

Two modes are supported:

1. URL mode  (--url):  GET /parse/imageurl with query parameters
2. File mode (--file): POST /parse/image with a multipart/form-data body

Reads INTEGRATIONS_API_KEY from the environment and sends it via the
X-Gateway-Authorization header with a "Bearer " prefix.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


URL_ENDPOINT = "https://app-f58c4fdcbbpd-api-m9xKXDbRplNa.gateway.appmedo.com/parse/imageurl"
FILE_ENDPOINT = "https://app-f58c4fdcbbpd-api-W9z3M6eONl3L.gateway.appmedo.com/parse/image"


def fail(message):
    """Print an error message to stderr and exit with a non-zero status."""
    print(message, file=sys.stderr)
    sys.exit(1)


def parse_args():
    """Parse command line arguments."""
    p = argparse.ArgumentParser(description="Run OCR on an image URL or a local image file via OCR.space.")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", help="image URL to OCR (uses the GET /parse/imageurl endpoint)")
    group.add_argument("--file", help="local image file path (uses the POST /parse/image endpoint)")
    p.add_argument("--language", default="eng", help="OCR language code (default: eng)")
    p.add_argument("--engine", choices=["1", "2"], default="1", help="OCR engine: 1 or 2 (default: 1)")
    p.add_argument("--overlay", action="store_true", help="include word/line overlay coordinates")
    p.add_argument("--table", action="store_true", help="enable table recognition")
    p.add_argument("--scale", action="store_true", help="enable auto-scaling for low-resolution images")
    p.add_argument("--detect-orientation", dest="detect_orientation", action="store_true",
                   help="auto-detect and correct image orientation")
    p.add_argument("--searchable-pdf", dest="searchable_pdf", action="store_true",
                   help="return a searchable PDF instead of plain text")
    p.add_argument("--hide-text-layer", dest="hide_text_layer", action="store_true",
                   help="hide the text layer in the generated searchable PDF")
    p.add_argument("--filetype", help="override file type detection: PDF/GIF/PNG/JPG/TIF/BMP")
    p.add_argument("--timeout", type=int, default=600, help="request timeout in seconds (default: 600)")
    return p.parse_args()


def build_url_request(args, api_key):
    """Build a GET request for URL mode."""
    params = {
        "url": args.url,
        "language": args.language,
        "OCREngine": args.engine,
        "isOverlayRequired": str(args.overlay).lower(),
        "isTable": str(args.table).lower(),
        "scale": str(args.scale).lower(),
        "detectOrientation": str(args.detect_orientation).lower(),
        "isCreateSearchablePdf": str(args.searchable_pdf).lower(),
        "isSearchablePdfHideTextLayer": str(args.hide_text_layer).lower(),
    }
    if args.filetype:
        params["filetype"] = args.filetype
    url = URL_ENDPOINT + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        method="GET",
        headers={
            "X-Gateway-Authorization": "Bearer " + api_key,
        },
    )
    return req


def guess_content_type(path):
    """Guess the MIME type of a local image file."""
    lower = path.lower()
    if lower.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith(".gif"):
        return "image/gif"
    if lower.endswith(".bmp"):
        return "image/bmp"
    if lower.endswith((".tif", ".tiff")):
        return "image/tiff"
    if lower.endswith(".pdf"):
        return "application/pdf"
    return "application/octet-stream"


def build_multipart_body(fields, file_field, filename, file_content_type, file_bytes):
    """Hand-build a multipart/form-data body (standard library only)."""
    boundary = "----OcrSpaceBoundary" + str(int(time.time() * 1000))
    crlf = "\r\n"
    parts = []

    for name, value in fields.items():
        if value is None:
            continue
        parts.append(
            ("--" + boundary + crlf +
             'Content-Disposition: form-data; name="' + name + '"' + crlf + crlf +
             value + crlf).encode("utf-8")
        )

    if file_bytes is not None:
        header = (
            "--" + boundary + crlf +
            'Content-Disposition: form-data; name="' + file_field + '"; filename="' + filename + '"' + crlf +
            "Content-Type: " + file_content_type + crlf + crlf
        ).encode("utf-8")
        parts.append(header + file_bytes + crlf.encode("utf-8"))

    parts.append(("--" + boundary + "--" + crlf).encode("utf-8"))
    body = b"".join(parts)
    content_type_header = "multipart/form-data; boundary=" + boundary
    return body, content_type_header


def build_file_request(args, api_key):
    """Build a POST multipart request for local file mode."""
    filepath = args.file
    if not os.path.isfile(filepath):
        fail("File not found: " + filepath)
    with open(filepath, "rb") as f:
        file_bytes = f.read()

    filename = os.path.basename(filepath)
    content_type = guess_content_type(filepath)

    fields = {
        "language": args.language,
        "OCREngine": args.engine,
        "isOverlayRequired": str(args.overlay).lower(),
        "isTable": str(args.table).lower(),
        "scale": str(args.scale).lower(),
        "detectOrientation": str(args.detect_orientation).lower(),
        "isCreateSearchablePdf": str(args.searchable_pdf).lower(),
        "isSearchablePdfHideTextLayer": str(args.hide_text_layer).lower(),
    }
    if args.filetype:
        fields["filetype"] = args.filetype

    body, ct = build_multipart_body(fields, "file", filename, content_type, file_bytes)
    req = urllib.request.Request(
        FILE_ENDPOINT,
        data=body,
        method="POST",
        headers={
            "Content-Type": ct,
            "X-Gateway-Authorization": "Bearer " + api_key,
        },
    )
    return req


def main():
    """Entry point: call OCR.space and print the result JSON."""
    args = parse_args()

    api_key = os.environ.get("INTEGRATIONS_API_KEY")
    if not api_key:
        fail("INTEGRATIONS_API_KEY is required")

    if args.url:
        req = build_url_request(args, api_key)
    else:
        req = build_file_request(args, api_key)

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
