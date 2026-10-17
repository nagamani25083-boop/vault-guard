#!/usr/bin/env python3
"""Call the OpenWeather One Call 3.0 and Weather Assistant APIs and print JSON.

Endpoints are selected via --endpoint:
    onecall            - current weather + forecast (GET)
    timemachine        - historical weather at a timestamp (GET)
    day_summary        - aggregated daily summary (GET)
    overview           - human-readable weather overview (GET)
    assistant_create   - start a conversational weather assistant session (POST)
    assistant_continue - continue an assistant session (POST)

Reads INTEGRATIONS_API_KEY from the environment and sends it via the
X-Gateway-Authorization header with a "Bearer " prefix.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


ONECALL_URL = "https://app-f58c4fdcbbpd-api-wL1zlmgJGAlY.gateway.appmedo.com/data/3.0/onecall"
TIMEMACHINE_URL = "https://app-f58c4fdcbbpd-api-Aa2PZmgJq5OL.gateway.appmedo.com/data/3.0/onecall/timemachine"
DAY_SUMMARY_URL = "https://app-f58c4fdcbbpd-api-2Y00zmgJ8lBY.gateway.appmedo.com/data/3.0/onecall/day_summary"
OVERVIEW_URL = "https://app-f58c4fdcbbpd-api-oYA6ZxVqenDa.gateway.appmedo.com/data/3.0/onecall/overview"
ASSISTANT_CREATE_URL = "https://app-f58c4fdcbbpd-api-79jKPlpvAJ0L.gateway.appmedo.com/assistant/session"
ASSISTANT_CONTINUE_URL = "https://app-f58c4fdcbbpd-api-oYA6ZxVqyK8a.gateway.appmedo.com/assistant/session"


def fail(message):
    """Print an error message to stderr and exit with a non-zero status."""
    print(message, file=sys.stderr)
    sys.exit(1)


def parse_args():
    """Parse command line arguments."""
    p = argparse.ArgumentParser(description="Query OpenWeather One Call 3.0 / Weather Assistant APIs.")
    p.add_argument("--endpoint", required=True,
                   choices=["onecall", "timemachine", "day_summary", "overview",
                            "assistant_create", "assistant_continue"],
                   help="which API endpoint to call")
    # GET (One Call) params
    p.add_argument("--lat", type=float, help="latitude (required for GET endpoints)")
    p.add_argument("--lon", type=float, help="longitude (required for GET endpoints)")
    p.add_argument("--dt", help="Unix timestamp (for timemachine)")
    p.add_argument("--date", help="date string YYYY-MM-DD (for day_summary)")
    p.add_argument("--units", choices=["standard", "metric", "imperial"], help="unit system")
    p.add_argument("--lang", help="language code for output text")
    p.add_argument("--exclude", help="comma-separated sections to exclude: current,minutely,hourly,daily,alerts")
    # POST (Assistant) params
    p.add_argument("--message", help="user message (required for assistant endpoints)")
    p.add_argument("--session-id", dest="session_id", help="existing session ID (for assistant_continue)")
    p.add_argument("--timeout", type=int, default=600, help="request timeout in seconds (default: 600)")
    args = p.parse_args()

    get_endpoints = ("onecall", "timemachine", "day_summary", "overview")
    if args.endpoint in get_endpoints:
        if args.lat is None or args.lon is None:
            p.error("--lat and --lon are required for the '%s' endpoint" % args.endpoint)
        if args.endpoint == "timemachine" and not args.dt:
            p.error("--dt is required for the 'timemachine' endpoint")
        if args.endpoint == "day_summary" and not args.date:
            p.error("--date is required for the 'day_summary' endpoint")
    elif args.endpoint == "assistant_create":
        if not args.message:
            p.error("--message is required for the 'assistant_create' endpoint")
    elif args.endpoint == "assistant_continue":
        if not args.session_id:
            p.error("--session-id is required for the 'assistant_continue' endpoint")
        if not args.message:
            p.error("--message is required for the 'assistant_continue' endpoint")

    return args


def build_get_request(args, api_key):
    """Build a GET request for the One Call family of endpoints."""
    if args.endpoint == "onecall":
        base_url = ONECALL_URL
    elif args.endpoint == "timemachine":
        base_url = TIMEMACHINE_URL
    elif args.endpoint == "day_summary":
        base_url = DAY_SUMMARY_URL
    else:
        base_url = OVERVIEW_URL

    params = {"lat": args.lat, "lon": args.lon}
    if args.dt:
        params["dt"] = args.dt
    if args.date:
        params["date"] = args.date
    if args.units:
        params["units"] = args.units
    if args.lang:
        params["lang"] = args.lang
    if args.exclude:
        params["exclude"] = args.exclude

    url = base_url + "?" + urllib.parse.urlencode(params)
    return urllib.request.Request(
        url,
        method="GET",
        headers={
            "Accept": "application/json",
            "X-Gateway-Authorization": "Bearer " + api_key,
        },
    )


def build_post_request(args, api_key):
    """Build a POST request for the Weather Assistant endpoints."""
    if args.endpoint == "assistant_create":
        url = ASSISTANT_CREATE_URL
        body = {"message": args.message}
        if args.units:
            body["units"] = args.units
    else:
        url = ASSISTANT_CONTINUE_URL + "/" + urllib.parse.quote(args.session_id)
        body = {"message": args.message}

    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    return urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Gateway-Authorization": "Bearer " + api_key,
        },
    )


def main():
    """Entry point: call the selected weather endpoint and print the result JSON."""
    args = parse_args()

    api_key = os.environ.get("INTEGRATIONS_API_KEY")
    if not api_key:
        fail("INTEGRATIONS_API_KEY is required")

    if args.endpoint in ("assistant_create", "assistant_continue"):
        req = build_post_request(args, api_key)
    else:
        req = build_get_request(args, api_key)

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
