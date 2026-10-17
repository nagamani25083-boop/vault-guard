#!/usr/bin/env python3
"""Call the AI Search API (Gemini 2.5 Flash + Google grounding) and aggregate the SSE response."""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


ENDPOINT = "https://app-f58c4fdcbbpd-api-zYm4ze3j7XvL.gateway.appmedo.com/v1beta/models/gemini-2.5-flash:streamGenerateContent?alt=sse"


def fail(message):
    """Print an error message to stderr and exit non-zero."""
    print(message, file=sys.stderr)
    sys.exit(1)


def parse_json(value, name):
    """Parse a JSON string argument; exit on failure."""
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        fail("Invalid JSON for %s: %s" % (name, exc))


def iter_sse(response):
    """Iterate over an SSE response, yielding each data field value."""
    for raw_line in response:
        line = raw_line.decode("utf-8", errors="replace").strip()
        if not line or not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if data == "[DONE]":
            break
        yield data


def main():
    """Entry point: parse arguments, call AI Search and print aggregated JSON result."""
    parser = argparse.ArgumentParser(description="Call AI Search (Gemini + Google grounding).")
    parser.add_argument("--query", help="User search question. Ignored when --contents is provided.")
    parser.add_argument("--contents", help="JSON array of conversation contents (role/parts).")
    parser.add_argument("--timeout", type=int, default=600, help="request timeout in seconds")
    args = parser.parse_args()

    api_key = os.environ.get("INTEGRATIONS_API_KEY")
    if not api_key:
        fail("INTEGRATIONS_API_KEY is required")

    if args.contents:
        contents = parse_json(args.contents, "--contents")
    elif args.query:
        contents = [{"role": "user", "parts": [{"text": args.query}]}]
    else:
        fail("Either --query or --contents is required")

    body = json.dumps({"contents": contents}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "X-Gateway-Authorization": "Bearer " + api_key,
        },
    )

    text_parts = []
    grounding_chunks = []
    web_search_queries = []

    try:
        with urllib.request.urlopen(req, timeout=args.timeout) as response:
            for data in iter_sse(response):
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue
                for candidate in chunk.get("candidates", []):
                    content = candidate.get("content", {})
                    for part in content.get("parts", []):
                        text = part.get("text")
                        if text:
                            text_parts.append(text)
                    metadata = candidate.get("groundingMetadata")
                    if metadata:
                        chunks = metadata.get("groundingChunks")
                        if isinstance(chunks, list):
                            grounding_chunks = chunks
                        queries = metadata.get("webSearchQueries")
                        if isinstance(queries, list):
                            web_search_queries = queries
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        fail("HTTP %s: %s" % (exc.code, detail))
    except urllib.error.URLError as exc:
        fail("Request failed: " + str(exc.reason))
    except TimeoutError:
        fail("Request timed out")

    sources = []
    for gc in grounding_chunks:
        web = gc.get("web", {})
        if web.get("uri"):
            sources.append({"uri": web["uri"], "title": web.get("title", "")})

    print(json.dumps({
        "status": "succeed",
        "text": "".join(text_parts),
        "sources": sources,
        "webSearchQueries": web_search_queries,
    }, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
