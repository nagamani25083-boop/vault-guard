#!/usr/bin/env python3
"""
Poll an already-submitted Kling image-to-video task by task_id.

Use this when generate_image_to_video.py returned {"status":"processing","task_id":"..."}.

Exit codes:
    0 - success, prints JSON:
        {"status":"succeed","task_id":"...","videos":[{"url":"...","duration":"...","file":"/path"}]}
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


QUERY_URL_BASE = "https://app-f58c4fdcbbpd-api-oYA6Z8wDBRDa.gateway.appmedo.com/v1/videos/image2video"
POLL_INTERVAL_S = 7
SAFE_LIMIT_S = 550


def fail(message):
    """Print an error message to stderr and exit non-zero."""
    print(message, file=sys.stderr)
    sys.exit(1)


def parse_args():
    """Parse command line arguments."""
    p = argparse.ArgumentParser(description="Poll a Kling image-to-video task.")
    p.add_argument("--task-id", required=True, help="task ID to query")
    p.add_argument("--output-dir", help="directory to download result videos into")
    return p.parse_args()


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
    return data.get("data", data)


def extract_videos(data):
    """Extract the generated video list from the task result."""
    result = data.get("task_result") or data.get("taskResult") or {}
    return result.get("videos") or []


def download_videos(videos, output_dir):
    """Download result videos into the output dir; return URLs only when no dir is given."""
    if not output_dir:
        return [{"url": v.get("url"), "duration": v.get("duration"), "file": None} for v in videos]
    os.makedirs(output_dir, exist_ok=True)
    downloaded = []
    for idx, v in enumerate(videos):
        url = v.get("url")
        ext = os.path.splitext(urllib.parse.urlparse(url).path)[1] or ".mp4"
        file_path = os.path.join(output_dir, "video_%s%s" % (idx, ext))
        urllib.request.urlretrieve(url, file_path)
        downloaded.append({"url": url, "duration": v.get("duration"), "file": file_path})
    return downloaded


def poll_task(task_id, key, output_dir):
    """Poll the task status until it succeeds, fails, or the safe limit is reached."""
    deadline = time.time() + SAFE_LIMIT_S
    while time.time() < deadline:
        time.sleep(POLL_INTERVAL_S)
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
    print(json.dumps({"status": "processing", "task_id": task_id}, ensure_ascii=False))


def main():
    """Entry point: poll the image-to-video task and print the result JSON."""
    args = parse_args()
    key = api_key()
    try:
        poll_task(args.task_id, key, args.output_dir)
    except Exception as e:
        fail(str(e))


if __name__ == "__main__":
    main()
