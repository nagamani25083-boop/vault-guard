#!/usr/bin/env python3
"""Transcribe audio to text via the LemonFox transcriptions API and print one JSON line."""

import argparse
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid


ENDPOINT = "https://app-f58c4fdcbbpd-api-DY8MNQoqOnMa.gateway.appmedo.com/v1/audio/transcriptions"
TEXT_FORMATS = ("text", "srt", "vtt")


def fail(message):
    """Print an error to stderr and exit non-zero."""
    print(message, file=sys.stderr)
    sys.exit(1)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Transcribe an audio file or URL to text.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--file-url", dest="file_url",
                        help="Public URL of the audio file (up to 1 GB).")
    source.add_argument("--file", help="Local audio file path to upload (up to 100 MB).")
    parser.add_argument("--response-format", dest="response_format", default="json",
                        choices=["json", "text", "srt", "verbose_json", "vtt"],
                        help="Response format. Default: json.")
    parser.add_argument("--language", help="Audio language, e.g. english, chinese. Auto-detected if omitted.")
    parser.add_argument("--speaker-labels", dest="speaker_labels", action="store_true",
                        help="Enable speaker diarization (requires --response-format verbose_json).")
    parser.add_argument("--min-speakers", dest="min_speakers", type=int, help="Minimum number of speakers.")
    parser.add_argument("--max-speakers", dest="max_speakers", type=int, help="Maximum number of speakers.")
    parser.add_argument("--prompt", help="Prompt guiding transcription style or proper nouns.")
    parser.add_argument("--translate", action="store_true", help="Translate the audio content to English.")
    parser.add_argument("--callback-url", dest="callback_url", help="Async callback URL for long audio.")
    parser.add_argument("--word-timestamps", dest="word_timestamps", action="store_true",
                        help="Request word-level timestamps (requires --response-format verbose_json).")
    parser.add_argument("--timeout", type=int, default=600, help="Request timeout in seconds. Default: 600.")
    return parser.parse_args()


def build_fields(args):
    """Build the list of (name, value) form fields shared by both upload modes."""
    fields = [("response_format", args.response_format)]
    if args.language:
        fields.append(("language", args.language))
    if args.speaker_labels:
        fields.append(("speaker_labels", "true"))
    if args.min_speakers is not None:
        fields.append(("min_speakers", str(args.min_speakers)))
    if args.max_speakers is not None:
        fields.append(("max_speakers", str(args.max_speakers)))
    if args.prompt:
        fields.append(("prompt", args.prompt))
    if args.translate:
        fields.append(("translate", "true"))
    if args.callback_url:
        fields.append(("callback_url", args.callback_url))
    if args.word_timestamps:
        fields.append(("timestamp_granularities[]", "word"))
    return fields


def build_url_request(args, api_key):
    """Build a urlencoded request that submits a public audio URL."""
    fields = [("file", args.file_url)] + build_fields(args)
    return urllib.request.Request(
        ENDPOINT,
        data=urllib.parse.urlencode(fields).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Gateway-Authorization": "Bearer " + api_key,
        },
    )


def build_upload_request(args, api_key):
    """Build a multipart/form-data request that uploads a local audio file."""
    try:
        with open(args.file, "rb") as fh:
            content = fh.read()
    except OSError as exc:
        fail("Failed to read audio file %s: %s" % (args.file, exc))
        return None

    boundary = "----DuccBoundary" + uuid.uuid4().hex
    filename = os.path.basename(args.file)
    mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    parts = []
    for name, value in build_fields(args):
        parts.append(('--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n'
                      % (boundary, name, value)).encode("utf-8"))
    parts.append(('--%s\r\nContent-Disposition: form-data; name="file"; filename="%s"\r\n'
                  'Content-Type: %s\r\n\r\n' % (boundary, filename, mime)).encode("utf-8"))
    parts.append(content)
    parts.append(("\r\n--%s--\r\n" % boundary).encode("utf-8"))

    return urllib.request.Request(
        ENDPOINT,
        data=b"".join(parts),
        method="POST",
        headers={
            "Content-Type": "multipart/form-data; boundary=" + boundary,
            "X-Gateway-Authorization": "Bearer " + api_key,
        },
    )


def main():
    """Entry point: submit the audio, then print the transcription as one JSON line."""
    args = parse_args()
    api_key = os.environ.get("INTEGRATIONS_API_KEY")
    if not api_key:
        fail("INTEGRATIONS_API_KEY is required")

    request = build_url_request(args, api_key) if args.file_url else build_upload_request(args, api_key)

    try:
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        fail("HTTP %s: %s" % (exc.code, exc.read().decode("utf-8", errors="replace")[:1000]))
        return
    except urllib.error.URLError as exc:
        fail("Request failed: " + str(exc.reason))
        return
    except TimeoutError:
        fail("Request timed out")
        return

    # text/srt/vtt come back as plain text; json/verbose_json come back as JSON
    if args.response_format in TEXT_FORMATS:
        result = {"text": raw}
    else:
        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            fail("Response is not valid JSON: " + raw[:500])
            return

    print(json.dumps({"status": "succeed", "result": result},
                     ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
