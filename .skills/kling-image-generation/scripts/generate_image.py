#!/usr/bin/env python3
"""
Submit a Kling image generation task and poll until done.

Exit codes:
    0 - success, prints JSON:
        {"status":"succeed","task_id":"...","images":[{"url":"...","file":"/path"}]}
        or, if not finished within the safe time limit:
        {"status":"processing","task_id":"..."}
    1 - API, argument, or download error
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


SUBMIT_URL = "https://app-f58c4fdcbbpd-api-DY8MnRlwkXKa.gateway.appmedo.com/v1/images/generations"
QUERY_URL_BASE = "https://app-f58c4fdcbbpd-api-M9v0wzOkZXGY.gateway.appmedo.com/v1/images/generations"
POLL_INTERVAL_S = 7
SAFE_LIMIT_S = 550


def fail(message):
    """Print an error message to stderr and exit non-zero."""
    print(message, file=sys.stderr)
    sys.exit(1)


def parse_args():
    """Parse command line arguments."""
    p = argparse.ArgumentParser(description="Submit a Kling image generation task and poll for the result.")
    p.add_argument("--prompt", required=True, help="positive prompt")
    p.add_argument("--negative-prompt", dest="negative_prompt", help="negative prompt")
    group = p.add_mutually_exclusive_group()
    group.add_argument("--image", help="local path of the reference image")
    group.add_argument("--image-url", dest="image_url", help="URL of the reference image")
    p.add_argument("--model", default="kling-v2", help="model name (default: kling-v2)")
    p.add_argument("--aspect-ratio", dest="aspect_ratio", help="aspect ratio, e.g. 16:9, 1:1")
    p.add_argument("--image-fidelity", dest="image_fidelity", type=float, help="image fidelity")
    p.add_argument("-n", "--num", type=int, default=1, help="number of images to generate [1, 9]")
    p.add_argument("--callback-url", dest="callback_url", help="optional callback URL")
    p.add_argument("--output-dir", dest="output_dir", help="output directory for result images")
    return p.parse_args()


def api_key():
    """Read the API key from the environment; exit if unset."""
    key = os.environ.get("INTEGRATIONS_API_KEY")
    if not key:
        fail("INTEGRATIONS_API_KEY is required")
    return key


def file_to_base64(path):
    """Read a local file and encode it as a Base64 string."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def post_json(url, key, payload):
    """Send a POST JSON request and return the parsed response."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "X-Gateway-Authorization": "Bearer " + key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError("HTTP %s: %s" % (e.code, body))


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


def submit_task(args, key):
    """Submit the image generation task and return the task id."""
    payload = {
        "prompt": args.prompt,
        "model_name": args.model,
        "n": args.num,
    }
    if args.negative_prompt:
        payload["negative_prompt"] = args.negative_prompt
    if args.image_url:
        payload["image"] = args.image_url
    elif args.image:
        payload["image"] = file_to_base64(args.image)
    if args.aspect_ratio:
        payload["aspect_ratio"] = args.aspect_ratio
    if args.image_fidelity is not None:
        payload["image_fidelity"] = args.image_fidelity
    if args.callback_url:
        payload["callback_url"] = args.callback_url
    data = unwrap(post_json(SUBMIT_URL, key, payload))
    task_id = data.get("task_id") or data.get("taskId")
    if not task_id:
        raise RuntimeError("submit response missing task_id: %s" % json.dumps(data, ensure_ascii=False))
    return task_id


def extract_images(data):
    """Extract the generated image list from the task result."""
    result = data.get("task_result") or data.get("taskResult") or {}
    return result.get("images") or []


def download_images(images, output_dir):
    """Download result images into the output dir; return URLs only when no dir is given."""
    if not output_dir:
        return [{"url": img.get("url"), "file": None} for img in images]
    os.makedirs(output_dir, exist_ok=True)
    downloaded = []
    for img in images:
        url = img.get("url")
        idx = img.get("index", len(downloaded))
        ext = os.path.splitext(urllib.parse.urlparse(url).path)[1] or ".png"
        file_path = os.path.join(output_dir, "image_%s%s" % (idx, ext))
        urllib.request.urlretrieve(url, file_path)
        downloaded.append({"url": url, "file": file_path})
    return downloaded


def poll_task(task_id, key, output_dir):
    """Poll the task status until it succeeds, fails, or the safe limit is reached."""
    deadline = time.time() + SAFE_LIMIT_S
    while time.time() < deadline:
        time.sleep(POLL_INTERVAL_S)
        data = unwrap(get_json(QUERY_URL_BASE + "/" + urllib.parse.quote(task_id), key))
        status = data.get("task_status") or data.get("status")
        if status == "succeed":
            images = extract_images(data)
            if not images:
                raise RuntimeError("succeed response missing images: %s" % json.dumps(data, ensure_ascii=False))
            print(json.dumps(
                {"status": "succeed", "task_id": task_id, "images": download_images(images, output_dir)},
                ensure_ascii=False,
            ))
            return
        if status in ("failed", "failure"):
            msg = data.get("task_status_msg") or data.get("message") or "unknown error"
            raise RuntimeError("Task %s failed: %s" % (task_id, msg))
    print(json.dumps({"status": "processing", "task_id": task_id}, ensure_ascii=False))


def main():
    """Entry point: submit and poll the image generation task, then print the result JSON."""
    args = parse_args()
    key = api_key()
    try:
        task_id = submit_task(args, key)
        poll_task(task_id, key, args.output_dir)
    except Exception as e:
        fail(str(e))


if __name__ == "__main__":
    main()
