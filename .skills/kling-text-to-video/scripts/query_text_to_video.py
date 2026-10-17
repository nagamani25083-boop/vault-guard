#!/usr/bin/env python3
"""
Poll an already-submitted Kling text-to-video task by task_id (does NOT submit a new task).

Use this when generate_text_to_video.py returned {"status": "processing", "task_id": "..."}.

Exit codes:
    0 - success, prints JSON:
        {"status":"succeed","task_id":"...","videos":[{"url":"...","file":"/path"}]}
        or, if not finished within the safe time limit:
        {"status":"processing","task_id":"..."}
    1 - API or argument error
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


QUERY_URL_BASE = "https://app-f58c4fdcbbpd-api-oLpZ7eD5j2Pa.gateway.appmedo.com/v1/videos/text2video"
POLL_INTERVAL_S = 7
SAFE_LIMIT_S = 550


def fail(message):
    """Print an error message to stderr and exit non-zero."""
    print(message, file=sys.stderr)
    sys.exit(1)


def api_key():
    """Read the API key from the environment; exit if unset."""
    key = os.environ.get("INTEGRATIONS_API_KEY")
    if not key:
        fail("INTEGRATIONS_API_KEY is required")
    return key


def get_json(url, key):
    """Send a GET request and return the parsed JSON response."""
    req = urllib.request.Request(
        url,
        headers={"X-Gateway-Authorization": "Bearer " + key},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError("HTTP %s: %s" % (e.code, body))


def unwrap(data):
    """Validate the response code and extract the data payload."""
    if data.get("code") not in (None, 0):
        raise RuntimeError("API error %s: %s" % (data.get("code"), data.get("message")))
    payload = data.get("data", data)
    if isinstance(payload, list):
        if not payload:
            raise RuntimeError("Task not found")
        return payload[0]
    return payload


def extract_videos(data):
    """Extract the generated video list from the task result."""
    result = data.get("task_result") or data.get("taskResult") or {}
    return result.get("videos") or []


def download_videos(videos, output_dir):
    """Download result videos into the output dir; return URLs only when no dir is given."""
    if not output_dir:
        return [{"url": v.get("url"), "file": None} for v in videos]
    os.makedirs(output_dir, exist_ok=True)
    downloaded = []
    for video in videos:
        url = video.get("url")
        idx = len(downloaded)
        ext = os.path.splitext(urllib.parse.urlparse(url).path)[1] or ".mp4"
        file_path = os.path.join(output_dir, "video_%s%s" % (idx, ext))
        urllib.request.urlretrieve(url, file_path)
        downloaded.append({"url": url, "file": file_path})
    return downloaded


def poll_task(task_id, key, output_dir):
    """Poll the task status until it succeeds, fails, or the safe limit is reached."""
    deadline = time.time() + SAFE_LIMIT_S
    while time.time() < deadline:
        data = unwrap(get_json(QUERY_URL_BASE + "/" + urllib.parse.quote(task_id), key))
        status = data.get("task_status") or data.get("status")
        if status == "succeed":
            videos = extract_videos(data)
            if not videos:
                raise RuntimeError("succeed response missing videos: %s" % json.dumps(data, ensure_ascii=False))
            print(json.dumps(
                {"status": "succeed", "task_id": task_id, "videos": download_videos(videos, output_dir)},
                ensure_ascii=False,
            ))
            return
        if status in ("failed", "failure"):
            msg = data.get("task_status_msg") or data.get("message") or "unknown error"
            raise RuntimeError("Task %s failed: %s" % (task_id, msg))
        time.sleep(POLL_INTERVAL_S)
    print(json.dumps({"status": "processing", "task_id": task_id}, ensure_ascii=False))


def main():
    """Entry point: poll an existing text-to-video task and print the result JSON."""
    parser = argparse.ArgumentParser(description="Poll a Kling text-to-video task.")
    parser.add_argument("--task-id", required=True, dest="task_id", help="task ID to poll")
    parser.add_argument("--output-dir", dest="output_dir", help="output directory for result videos")
    args = parser.parse_args()

    key = api_key()
    try:
        poll_task(args.task_id, key, args.output_dir)
    except Exception as e:
        fail(str(e))


if __name__ == "__main__":
    main()
