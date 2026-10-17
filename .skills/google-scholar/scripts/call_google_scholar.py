#!/usr/bin/env python3
"""Call the Google Scholar search API (via SerpApi) and print the JSON result.

Reads INTEGRATIONS_API_KEY from the environment and sends it via the
X-Gateway-Authorization header WITHOUT a "Bearer " prefix (raw key value),
matching the SerpApi gateway convention documented for this skill.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


ENDPOINT = "https://app-f58c4fdcbbpd-api-Xa6JZq2055oa.gateway.appmedo.com/search"


def fail(message):
    """Print an error message to stderr and exit with a non-zero status."""
    print(message, file=sys.stderr)
    sys.exit(1)


def main():
    """Entry point: parse arguments, call Google Scholar, and print JSON to stdout."""
    parser = argparse.ArgumentParser(
        description="Search Google Scholar via SerpApi (google_scholar engine)."
    )
    parser.add_argument("--q", help="Search keywords (supports author:, source: operators).")
    parser.add_argument("--cites", help="Article ID for citation retrieval.")
    parser.add_argument("--cluster", help="Article cluster ID for related versions.")
    parser.add_argument("--as-ylo", dest="as_ylo", help="Start year (inclusive), e.g. 2020.")
    parser.add_argument("--as-yhi", dest="as_yhi", help="End year (inclusive), e.g. 2024.")
    parser.add_argument("--hl", help="Interface language code, e.g. en, zh-CN.")
    parser.add_argument("--lr", help="Search language restriction, e.g. lang_en|lang_zh-CN.")
    parser.add_argument("--start", help="Pagination offset (0, 10, 20, ...).")
    parser.add_argument("--as-sdt", dest="as_sdt", help="Search scope: 0/7/4.")
    parser.add_argument("--as-vis", dest="as_vis", help="0-all results, 1-reviews only.")
    parser.add_argument("--no-cache", dest="no_cache", help="'true' to force real-time fetch.")
    parser.add_argument("--timeout", type=int, default=600, help="Request timeout in seconds.")
    args = parser.parse_args()

    api_key = os.environ.get("INTEGRATIONS_API_KEY")
    if not api_key:
        fail("INTEGRATIONS_API_KEY is required")

    if not (args.q or args.cites or args.cluster):
        fail("At least one of --q, --cites, or --cluster is required")

    query = {"engine": "google_scholar"}
    optional = {
        "q": args.q,
        "cites": args.cites,
        "cluster": args.cluster,
        "as_ylo": args.as_ylo,
        "as_yhi": args.as_yhi,
        "hl": args.hl,
        "lr": args.lr,
        "start": args.start,
        "as_sdt": args.as_sdt,
        "as_vis": args.as_vis,
        "no_cache": args.no_cache,
    }
    for key, value in optional.items():
        if value is not None and value != "":
            query[key] = value

    url = ENDPOINT + "?" + urllib.parse.urlencode(query)
    req = urllib.request.Request(
        url,
        method="GET",
        headers={
            "Accept": "application/json",
            # Google Scholar gateway expects the raw key value (no "Bearer " prefix).
            "X-Gateway-Authorization": api_key,
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
