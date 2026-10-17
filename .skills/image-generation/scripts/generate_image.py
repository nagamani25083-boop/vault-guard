#!/usr/bin/env python3
"""
Submit an image generation task and poll until done.

Usage:
    # Text to image
    python3 generate_image.py --prompt "..." [--output /path/to/output.png]

    # Image editing / multi-image input
    python3 generate_image.py --prompt "..." --image /path/a.png --image /path/b.jpg \
        [--output /path/to/output.png]

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
import mimetypes
import argparse
import urllib.request
import urllib.error


SUBMIT_URL = "https://app-f58c4fdcbbpd-api-zYkZzKQJrBdL.gateway.appmedo.com/image-generation/submit"
QUERY_URL = "https://app-f58c4fdcbbpd-api-GYX1lzGw0DQa.gateway.appmedo.com/image-generation/task"

POLL_INTERVAL_S = 7
SAFE_LIMIT_S = 550  # stay under the default timeout


def parse_args():
    """Parse command-line arguments."""
    p = argparse.ArgumentParser(description="Submit and poll an image generation task.")
    p.add_argument("--prompt", required=True, help="Text prompt for generation or editing")
    p.add_argument("--image", action="append", default=[], help="Local image file path (repeatable for multi-image)")
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


def image_part(path: str) -> dict:
    """Read a local image and encode it as an inline_data part for the request."""
    mime, _ = mimetypes.guess_type(path)
    if mime not in {"image/png", "image/jpeg", "image/webp"}:
        mime = "image/png" if path.lower().endswith(".png") else "image/jpeg"
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return {"inline_data": {"mime_type": mime, "data": data}}


def submit(api_key: str, args) -> str:
    """Submit the image generation task and return the task ID."""
    parts = [{"text": args.prompt}]
    parts.extend(image_part(path) for path in args.image)
    d = request_json(SUBMIT_URL, api_key, {"contents": [{"parts": parts}]})
    task_id = d.get("data", {}).get("taskId") or d.get("taskId")
    if not task_id:
        print(f"Submit failed: {json.dumps(d, ensure_ascii=False)}", file=sys.stderr)
        sys.exit(1)
    return task_id


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
    """Entry point: submit the task, poll until completion or timeout, output JSON."""
    args = parse_args()
    api_key = os.environ.get("INTEGRATIONS_API_KEY", "")
    if not api_key:
        print("INTEGRATIONS_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    task_id = submit(api_key, args)
    safe_limit = min(args.timeout - 50, SAFE_LIMIT_S)  # leave buffer before timeout
    start = time.time()
    while time.time() - start < safe_limit:
        time.sleep(POLL_INTERVAL_S)
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

    # Timeout - report processing so caller can resume with query_image.py
    print(json.dumps({"status": "processing", "task_id": task_id}))


if __name__ == "__main__":
    main()
