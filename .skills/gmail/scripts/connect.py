#!/usr/bin/env python3
"""Managed Gmail entrypoint. Input is one JSON object on stdin."""

import os
import sys

from connect_contract import command, enum, fields, reject, text, text_list
from connect_transport import (
    ConnectFailure,
    execute,
    managed_credentials,
    mark_untrusted,
    read_command,
    write_result,
)


CONNECTION_ENV = "MEDO_CONNECT_GMAIL"
ROUTES = {
    "search_messages": "https://app-f58c4fdcbbpd-api-connect-gmail-search-messages.gateway.appmedo.com/",
    "get_message": "https://app-f58c4fdcbbpd-api-connect-gmail-get-message.gateway.appmedo.com/",
    "get_thread": "https://app-f58c4fdcbbpd-api-connect-gmail-get-thread.gateway.appmedo.com/",
    "send_email": "https://app-f58c4fdcbbpd-api-connect-gmail-send-email.gateway.appmedo.com/",
    "modify_message_labels": "https://app-f58c4fdcbbpd-api-connect-gmail-modify-message-labels.gateway.appmedo.com/",
}


def _email(value):
    """Reject malformed recipient addresses without attempting full RFC parsing."""
    return isinstance(value, str) and value.count("@") == 1 and not value.startswith("@") and not value.endswith("@")


def validate(action, arguments):
    """Validate the public arguments for one fixed action."""
    if action == "search_messages":
        fields(arguments, ("query", "labelIds", "pageToken"))
        text(arguments, "query", max_length=2_048)
        text_list(arguments, "labelIds", maximum=50, item_max_length=128)
        text(arguments, "pageToken")
    elif action == "get_message":
        fields(arguments, ("messageId", "format"), ("messageId",))
        text(arguments, "messageId", required=True, max_length=256)
        enum(arguments, "format", ("metadata", "full"))
    elif action == "get_thread":
        fields(arguments, ("threadId",), ("threadId",))
        text(arguments, "threadId", required=True, max_length=256)
    elif action == "send_email":
        fields(arguments, ("to", "subject", "body", "cc", "bcc"), ("to", "subject", "body"))
        recipient = text(arguments, "to", required=True, max_length=320)
        text(arguments, "subject", required=True, max_length=998)
        text(arguments, "body", required=True, max_length=32_000)
        cc = text_list(arguments, "cc", maximum=50, item_max_length=320) or []
        bcc = text_list(arguments, "bcc", maximum=50, item_max_length=320) or []
        if not _email(recipient) or any(not _email(address) for address in cc + bcc):
            reject("Recipient addresses are invalid")
    elif action == "modify_message_labels":
        fields(arguments, ("messageId", "addLabelIds", "removeLabelIds"), ("messageId",))
        text(arguments, "messageId", required=True, max_length=256)
        add_labels = text_list(arguments, "addLabelIds", maximum=20, item_max_length=128) or []
        remove_labels = text_list(arguments, "removeLabelIds", maximum=20, item_max_length=128) or []
        if not add_labels and not remove_labels:
            reject("At least one label change is required")
        if set(add_labels).intersection(remove_labels):
            reject("A label cannot be added and removed together")


def handle(value, environ=os.environ, sender=execute):
    """Validate and execute one managed Connect command."""
    action, arguments = command(value, ROUTES)
    validate(action, arguments)
    gateway_jwt, connection = managed_credentials(environ, CONNECTION_ENV)
    return mark_untrusted(sender(ROUTES[action], gateway_jwt, connection, arguments))


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
