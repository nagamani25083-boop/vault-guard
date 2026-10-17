#!/usr/bin/env python3
"""Managed Google Slides entrypoint."""

import os
import sys

from connect_contract import (
    command,
    fields,
    markdown,
    replacement_text,
    text,
)
from connect_transport import (
    ConnectFailure,
    execute,
    managed_credentials,
    mark_untrusted,
    read_command,
    write_result,
)


CONNECTION_ENV = "MEDO_CONNECT_GOOGLE_SLIDES"
ROUTES = {
    "find_presentation": "https://app-f58c4fdcbbpd-api-connect-google-slides-find-deck.gateway.appmedo.com/",
    "get_presentation": "https://app-f58c4fdcbbpd-api-connect-google-slides-get-deck.gateway.appmedo.com/",
    "get_slide_thumbnail": "https://app-f58c4fdcbbpd-api-connect-google-slides-get-thumbnail.gateway.appmedo.com/",
    "create_presentation": "https://app-f58c4fdcbbpd-api-connect-google-slides-create-deck.gateway.appmedo.com/",
    "append_slides": "https://app-f58c4fdcbbpd-api-connect-google-slides-append-slides.gateway.appmedo.com/",
    "copy_presentation": "https://app-f58c4fdcbbpd-api-connect-google-slides-copy-deck.gateway.appmedo.com/",
    "replace_text": "https://app-f58c4fdcbbpd-api-connect-google-slides-replace-text.gateway.appmedo.com/",
}


def validate(action, arguments):
    """Validate the public arguments for one fixed action. Every argument is one string."""
    if action == "find_presentation":
        fields(arguments, ("title",), ("title",))
        text(arguments, "title", required=True, max_length=256)
    elif action == "get_presentation":
        fields(arguments, ("presentationId",), ("presentationId",))
        text(arguments, "presentationId", required=True, max_length=256)
    elif action == "get_slide_thumbnail":
        fields(arguments, ("presentationId", "slideId"), ("presentationId", "slideId"))
        text(arguments, "presentationId", required=True, max_length=256)
        text(arguments, "slideId", required=True, max_length=256)
    elif action == "create_presentation":
        fields(arguments, ("title", "markdown"), ("title", "markdown"))
        text(arguments, "title", required=True, max_length=256)
        markdown(arguments, "markdown", required=True)
    elif action == "append_slides":
        fields(arguments, ("presentationId", "markdown"), ("presentationId", "markdown"))
        text(arguments, "presentationId", required=True, max_length=256)
        markdown(arguments, "markdown", required=True)
    elif action == "copy_presentation":
        fields(arguments, ("presentationId", "title"), ("presentationId", "title"))
        text(arguments, "presentationId", required=True, max_length=256)
        text(arguments, "title", required=True, max_length=256)
    elif action == "replace_text":
        fields(
            arguments,
            ("presentationId", "findText", "replaceText"),
            ("presentationId", "findText", "replaceText"),
        )
        text(arguments, "presentationId", required=True, max_length=256)
        text(arguments, "findText", required=True, max_length=8_192)
        replacement_text(arguments, "replaceText", required=True)


def handle(value, environ=os.environ, sender=execute):
    """Validate and execute one managed Connect command."""
    action, arguments = command(value, ROUTES)
    validate(action, arguments)
    gateway_jwt, connection = managed_credentials(environ, CONNECTION_ENV)
    return mark_untrusted(sender(ROUTES[action], gateway_jwt, connection, dict(arguments)))


def main():
    """Run the stdin-to-stdout command entrypoint."""
    try:
        result = handle(read_command(sys.stdin.buffer))
        exit_code = 0
    except ConnectFailure as failure:
        result = failure.as_result()
        exit_code = 1
    except Exception:
        result = ConnectFailure("RESULT_UNKNOWN", "The provider result is unknown").as_result()
        exit_code = 1
    write_result(sys.stdout, result)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
