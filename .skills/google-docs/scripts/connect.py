#!/usr/bin/env python3
"""Managed Google Docs entrypoint."""

import os
import sys

from connect_contract import (
    boolean,
    command,
    fields,
    markdown,
    reject,
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


CONNECTION_ENV = "MEDO_CONNECT_GOOGLE_DOCS"
ROUTES = {
    "search_documents": "https://app-f58c4fdcbbpd-api-connect-google-docs-search-docs.gateway.appmedo.com/",
    "get_document": "https://app-f58c4fdcbbpd-api-connect-google-docs-get-doc.gateway.appmedo.com/",
    "get_plaintext": "https://app-f58c4fdcbbpd-api-connect-google-docs-get-text.gateway.appmedo.com/",
    "create_document": "https://app-f58c4fdcbbpd-api-connect-google-docs-create-doc.gateway.appmedo.com/",
    "copy_document": "https://app-f58c4fdcbbpd-api-connect-google-docs-copy-doc.gateway.appmedo.com/",
    "append_markdown": "https://app-f58c4fdcbbpd-api-connect-google-docs-append-md.gateway.appmedo.com/",
    "replace_all_text": "https://app-f58c4fdcbbpd-api-connect-google-docs-replace-text.gateway.appmedo.com/",
    "replace_document": "https://app-f58c4fdcbbpd-api-connect-google-docs-replace-doc.gateway.appmedo.com/",
}
_CONFIRM_ACTIONS = {"replace_document"}


def validate(action, arguments):
    """Validate the public arguments for one fixed action."""
    if action == "search_documents":
        fields(arguments, ("query", "pageToken"), ("query",))
        text(arguments, "query", required=True, max_length=2_048)
        text(arguments, "pageToken")
    elif action == "get_document":
        fields(arguments, ("documentId",), ("documentId",))
        text(arguments, "documentId", required=True, max_length=256)
    elif action == "get_plaintext":
        fields(arguments, ("documentId",), ("documentId",))
        text(arguments, "documentId", required=True, max_length=256)
    elif action == "create_document":
        fields(arguments, ("title", "markdown"), ("title", "markdown"))
        text(arguments, "title", required=True, max_length=256)
        markdown(arguments, "markdown", required=True)
    elif action == "copy_document":
        fields(arguments, ("documentId", "title"), ("documentId", "title"))
        text(arguments, "documentId", required=True, max_length=256)
        text(arguments, "title", required=True, max_length=256)
    elif action == "append_markdown":
        fields(arguments, ("documentId", "markdown"), ("documentId", "markdown"))
        text(arguments, "documentId", required=True, max_length=256)
        markdown(arguments, "markdown", required=True)
    elif action == "replace_all_text":
        fields(
            arguments,
            ("documentId", "findText", "replaceText"),
            ("documentId", "findText", "replaceText"),
        )
        text(arguments, "documentId", required=True, max_length=256)
        text(arguments, "findText", required=True, max_length=8_192)
        replacement_text(arguments, "replaceText", required=True)
    elif action == "replace_document":
        fields(arguments, ("documentId", "markdown", "confirm"), ("documentId", "markdown", "confirm"))
        text(arguments, "documentId", required=True, max_length=256)
        markdown(arguments, "markdown", required=True)
        boolean(arguments, "confirm")
        if arguments.get("confirm") is not True:
            reject("Explicit confirmation is required")


def handle(value, environ=os.environ, sender=execute):
    """Validate and execute one managed Connect command."""
    action, arguments = command(value, ROUTES)
    validate(action, arguments)
    safe_arguments = dict(arguments)
    if action in _CONFIRM_ACTIONS:
        safe_arguments.pop("confirm")
    gateway_jwt, connection = managed_credentials(environ, CONNECTION_ENV)
    return mark_untrusted(sender(ROUTES[action], gateway_jwt, connection, safe_arguments))


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
