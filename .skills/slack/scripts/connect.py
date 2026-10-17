#!/usr/bin/env python3
"""Managed Slack entrypoint."""

import os
import sys

from connect_contract import command, fields, text
from connect_transport import (
    ConnectFailure,
    execute,
    managed_credentials,
    mark_untrusted,
    read_command,
    write_result,
)


CONNECTION_ENV = "MEDO_CONNECT_SLACK"
ROUTES = {
    "find_channels": "https://app-f58c4fdcbbpd-api-connect-slack-find-channels.gateway.appmedo.com/",
    "search_messages": "https://app-f58c4fdcbbpd-api-connect-slack-search-messages.gateway.appmedo.com/",
    "get_channel_history": "https://app-f58c4fdcbbpd-api-connect-slack-get-channel-history.gateway.appmedo.com/",
    "send_message": "https://app-f58c4fdcbbpd-api-connect-slack-send-message.gateway.appmedo.com/",
}


def validate(action, arguments):
    """Validate the public arguments for one fixed action."""
    if action == "find_channels":
        fields(arguments, ("query",), ("query",))
        text(arguments, "query", required=True, max_length=2_048)
    elif action == "search_messages":
        fields(arguments, ("query", "cursor"), ("query",))
        text(arguments, "query", required=True, max_length=2_048)
        text(arguments, "cursor")
    elif action == "get_channel_history":
        fields(arguments, ("channel", "cursor"), ("channel",))
        text(arguments, "channel", required=True, max_length=256)
        text(arguments, "cursor")
    elif action == "send_message":
        fields(arguments, ("channel", "text", "threadTimestamp"), ("channel", "text"))
        text(arguments, "channel", required=True, max_length=256)
        text(arguments, "text", required=True, max_length=12_000)
        text(arguments, "threadTimestamp", max_length=64)


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
