#!/usr/bin/env python3
"""
Poll an existing image generation task until done (for resuming).

Usage:
    python3 query_image.py --task-id <id> [--output /path/to/output.png] [--timeout 600]

Environment:
    INTEGRATIONS_API_KEY - platform-injected API key (required)

Exit codes:
    0 - success, prints JSON:
        {"status": "succeed", "task_id": "...", "file": "<path or null>"}
        or, if not finished within the safe time limit:
        {"status": "processing", "task_id": "..."}
    1 - API or argument error
"""

import os
import sys
import json
import time
import re
import base64
import argparse
import urllib.request
import urllib.error


QUERY_URL = "https://app-f58c4fdcbbpd-api-GYX1lzGw0DQa.gateway.appmedo.com/image-generation/task"

POLL_INTERVAL_S = 7
SAFE_LIMIT_S = 550  # stay under the default timeout


def parse_args():
    """Parse command-line arguments."""
    p = argparse.ArgumentParser(description="Poll an image generation task by ID.")
    p.add_argument("--task-id", required=True, help="Task ID to poll")
    p.add_argument("--output", help="Local path to save the generated image (optional)")
    p.add_argument("--timeout", type=int, default=600, help="Timeout in seconds (default 600)")
    return p.parse_args()


def request_json(url: str, api_key: str, payload: dict) -> dict:
    """Send a POST request and return the parsed JSON response."""
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "X-Gateway-Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Network error: {e}", file=sys.stderr)
        sys.exit(1)


def query(api_key: str, task_id: str) -> dict:
    """Query the current status and result of a given task."""
    return request_json(QUERY_URL, api_key, {"taskId": task_id}).get("data", {})


def extract_and_save_image(data: dict, output: str) -> str | None:
    """Extract the base64 image from the result and save to file.

    The result format is:
        candidates[0].content.parts[0].text == "![image](data:image/jpeg;base64,...)"
    Returns the output file path on success, None otherwise.
    """
    try:
        text = data["result"]["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        return None

    # Extract base64 data from markdown image syntax
    match = re.search(r"!\[.*?\]\(data:image/[^;]+;base64,([A-Za-z0-9+/=\s]+)\)", text)
    if not match:
        return None

    img_bytes = base64.b64decode(match.group(1))
    with open(output, "wb") as f:
        f.write(img_bytes)
    return output


def main():
    """Entry point: poll the task until completion or timeout, output JSON."""
    args = parse_args()
    api_key = os.environ.get("INTEGRATIONS_API_KEY", "")
    if not api_key:
        print("INTEGRATIONS_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    task_id = args.task_id
    safe_limit = min(args.timeout - 50, SAFE_LIMIT_S)  # leave buffer before timeout
    start = time.time()
    while True:
        data = query(api_key, task_id)
        status = data.get("status")
        if status == "SUCCESS":
            file_path = None
            if args.output:
                file_path = extract_and_save_image(data, args.output)
            print(json.dumps({"status": "succeed", "task_id": task_id, "file": file_path}))
            return
        if status in ("FAILED", "TIMEOUT"):
            err_msg = data.get("error") or json.dumps(data, ensure_ascii=False)
            print(f"Task failed ({status}): {err_msg}", file=sys.stderr)
            sys.exit(1)
        if time.time() - start >= safe_limit:
            break
        time.sleep(POLL_INTERVAL_S)

    # Timeout - report processing so caller can resume with another query_image.py run
    print(json.dumps({"status": "processing", "task_id": task_id}))


if __name__ == "__main__":
    main()
