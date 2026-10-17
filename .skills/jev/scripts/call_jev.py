#!/usr/bin/env python3
"""
Call the Jev (TypeSafe System One) endpoint and print the structured answers as JSON.

Usage:
    python3 call_jev.py --request request.json [--model jev-1.13.0]
    python3 call_jev.py --state '{"text":"..."}' --questions '{"q":{...}}'
    python3 call_jev.py --models
    python3 call_jev.py --request request.json --raw --header NAME:VALUE

Environment:
    INTEGRATIONS_API_KEY - platform-injected gateway key (required)

Exit codes:
    0 - success, prints one line of JSON
    1 - argument, network or API error
"""
import os
import sys
import json
import argparse
import urllib.request
import urllib.error

# The api-<id> marker is this endpoint's gateway API id (gateway_apis[].id in the
# skill definition). It is assigned when the API row is created in the console.
ENDPOINT = "https://app-f58c4fdcbbpd-api-79jKnBxVg4oL.gateway.appmedo.com/v1/systemone"
MODELS_ENDPOINT = "https://app-f58c4fdcbbpd-api-eLMlzKkOd7V9.gateway.appmedo.com/v1/models"
DEFAULT_MODEL = "jev-1.13.0"


def fail(message):
    """Print an error message to stderr and exit non-zero."""
    print(message, file=sys.stderr)
    sys.exit(1)


def parse_headers(items):
    """Turn repeated NAME:VALUE strings into a header dict; exit on malformed input."""
    headers = {}
    for item in items or []:
        name, sep, value = item.partition(":")
        if not sep or not name.strip():
            fail(f"--header must look like NAME:VALUE, got: {item}")
        headers[name.strip()] = value.strip()
    return headers


def build_payload(args):
    """Build the request body from --request or --state/--questions; exit on invalid input."""
    if args.request:
        try:
            with open(args.request, "r", encoding="utf-8") as fh:
                payload = json.load(fh)
        except OSError as err:
            fail(f"cannot read --request: {err}")
        except json.JSONDecodeError as err:
            fail(f"--request is not valid JSON: {err}")
    else:
        if not args.state or not args.questions:
            fail("provide --request FILE, or both --state and --questions")
        try:
            payload = {"state": json.loads(args.state),
                       "questions": json.loads(args.questions)}
        except json.JSONDecodeError as err:
            fail(f"--state/--questions must be inline JSON: {err}")

    if "questions" not in payload or not payload["questions"]:
        fail("payload must contain a non-empty 'questions' object")
    if "state" not in payload:
        payload["state"] = None
    payload.setdefault("model", args.model or DEFAULT_MODEL)
    return payload


def call(url, api_key, body=None, extra_headers=None):
    """POST (or GET when body is None) to the gateway and return decoded JSON; exit on error."""
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = dict(extra_headers or {})
    headers["Content-Type"] = "application/json"
    headers["X-Gateway-Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as err:
        detail = err.read().decode(errors="replace")[:400]
        fail(f"HTTP {err.code}: {detail}")
    except urllib.error.URLError as err:
        fail(f"network error: {err}")


def summarize(result):
    """Flatten answers into the fields a caller actually branches on."""
    answers = result.get("answers") or {}
    out = {"model": result.get("model"), "answers": {}}
    for name, ans in answers.items():
        kind = ans.get("type")
        if kind == "choice":
            out["answers"][name] = {
                "choice": ans.get("choice"),
                "confidence": ans.get("confidence"),
                "probabilities": ans.get("probabilities"),
            }
        elif kind == "score":
            out["answers"][name] = {
                "score": ans.get("score"),
                "confidence": ans.get("confidence"),
                "probabilities": ans.get("probabilities"),
            }
        elif kind == "noul":
            out["answers"][name] = {"noul": ans.get("noul")}
        else:
            out["answers"][name] = ans
    out["usage"] = result.get("usage")
    return out


def main():
    """Entry point: parse arguments, call Jev (or list models) and print one line of JSON."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", help="path to a JSON file with state/questions/model")
    parser.add_argument("--state", help="inline JSON state")
    parser.add_argument("--questions", help="inline JSON questions object")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--models", action="store_true", help="list available models and exit")
    parser.add_argument("--raw", action="store_true", help="print the full response, not the summary")
    parser.add_argument("--header", action="append", metavar="NAME:VALUE",
                        help="extra request header, repeatable (e.g. TypeSafe-Danger-Zone-Images:true)")
    args = parser.parse_args()

    api_key = os.environ.get("INTEGRATIONS_API_KEY", "")
    if not api_key:
        fail("INTEGRATIONS_API_KEY not set")

    extra_headers = parse_headers(args.header)

    if args.models:
        print(json.dumps(call(MODELS_ENDPOINT, api_key, extra_headers=extra_headers)))
        return

    result = call(ENDPOINT, api_key, build_payload(args), extra_headers)
    print(json.dumps(result if args.raw else summarize(result)))


if __name__ == "__main__":
    main()
