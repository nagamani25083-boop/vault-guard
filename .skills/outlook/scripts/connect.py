#!/usr/bin/env python3
"""Managed Outlook entrypoint. Input is one JSON object on stdin."""

import os
import sys

from connect_contract import boolean, calendar_window, command, fields, reject, text, text_list
from connect_transport import (
    ConnectFailure,
    execute,
    managed_credentials,
    mark_untrusted,
    read_command,
    write_result,
)


CONNECTION_ENV = "MEDO_CONNECT_OUTLOOK"
ROUTES = {
    "search_messages": "https://app-f58c4fdcbbpd-api-connect-outlook-search-messages.gateway.appmedo.com/",
    "get_message": "https://app-f58c4fdcbbpd-api-connect-outlook-get-message.gateway.appmedo.com/",
    "send_email": "https://app-f58c4fdcbbpd-api-connect-outlook-send-email.gateway.appmedo.com/",
    "reply_email": "https://app-f58c4fdcbbpd-api-connect-outlook-reply-email.gateway.appmedo.com/",
    "update_message": "https://app-f58c4fdcbbpd-api-connect-outlook-update-message.gateway.appmedo.com/",
    "list_calendars": "https://app-f58c4fdcbbpd-api-connect-outlook-list-calendars.gateway.appmedo.com/",
    "list_events": "https://app-f58c4fdcbbpd-api-connect-outlook-list-events.gateway.appmedo.com/",
    "find_event": "https://app-f58c4fdcbbpd-api-connect-outlook-find-event.gateway.appmedo.com/",
    "get_schedule": "https://app-f58c4fdcbbpd-api-connect-outlook-get-schedule.gateway.appmedo.com/",
    "create_event": "https://app-f58c4fdcbbpd-api-connect-outlook-create-event.gateway.appmedo.com/",
    "update_event": "https://app-f58c4fdcbbpd-api-connect-outlook-update-event.gateway.appmedo.com/",
    "delete_event": "https://app-f58c4fdcbbpd-api-connect-outlook-delete-event.gateway.appmedo.com/",
}


def _email(value):
    """Reject malformed addresses without attempting full RFC parsing."""
    return isinstance(value, str) and value.count("@") == 1 and not value.startswith("@") and not value.endswith("@")


def _attendees(arguments):
    attendees = text_list(arguments, "attendees", maximum=50, item_max_length=320) or []
    if any(not _email(address) for address in attendees):
        reject("Attendee addresses are invalid")


def _recipients(arguments, required_to=False):
    recipient = text(arguments, "to", required=required_to, max_length=320)
    cc = text_list(arguments, "cc", maximum=50, item_max_length=320) or []
    bcc = text_list(arguments, "bcc", maximum=50, item_max_length=320) or []
    addresses = ([recipient] if recipient else []) + cc + bcc
    if any(not _email(address) for address in addresses):
        reject("Recipient addresses are invalid")


def validate(action, arguments):
    """Validate the public arguments for one fixed action."""
    if action == "search_messages":
        fields(arguments, ("query", "isRead", "folder", "pageToken"))
        text(arguments, "query", max_length=2_048)
        boolean(arguments, "isRead")
        text(arguments, "folder", max_length=256)
        text(arguments, "pageToken")
        if "query" in arguments and "isRead" in arguments:
            reject("query and isRead cannot be used together")
    elif action == "get_message":
        fields(arguments, ("messageId",), ("messageId",))
        text(arguments, "messageId", required=True, max_length=256)
    elif action == "send_email":
        fields(arguments, ("to", "subject", "body", "cc", "bcc"), ("to", "subject", "body"))
        text(arguments, "subject", required=True, max_length=998)
        text(arguments, "body", required=True, max_length=32_000)
        _recipients(arguments, required_to=True)
    elif action == "reply_email":
        fields(arguments, ("messageId", "body", "cc", "bcc"), ("messageId", "body"))
        text(arguments, "messageId", required=True, max_length=256)
        text(arguments, "body", required=True, max_length=32_000)
        _recipients(arguments)
    elif action == "update_message":
        fields(arguments, ("messageId", "isRead", "categories"), ("messageId",))
        text(arguments, "messageId", required=True, max_length=256)
        boolean(arguments, "isRead")
        text_list(arguments, "categories", maximum=20, item_max_length=128)
        if "isRead" not in arguments and "categories" not in arguments:
            reject("At least one message change is required")
    elif action == "list_calendars":
        fields(arguments, ("pageToken",))
        text(arguments, "pageToken")
    elif action == "list_events":
        fields(
            arguments,
            ("startDateTime", "endDateTime", "calendarId", "pageToken"),
            ("startDateTime", "endDateTime"),
        )
        calendar_window(arguments, "startDateTime", "endDateTime", required=True)
        text(arguments, "calendarId", max_length=1_024)
        text(arguments, "pageToken")
    elif action == "find_event":
        fields(arguments, ("calendarId", "pageToken"))
        text(arguments, "calendarId", max_length=1_024)
        text(arguments, "pageToken")
    elif action == "get_schedule":
        fields(
            arguments,
            ("schedules", "timeMin", "timeMax", "timezone", "endTimezone"),
            ("schedules", "timeMin", "timeMax"),
        )
        schedules = text_list(arguments, "schedules", maximum=20, item_max_length=320) or []
        if not schedules or any(not _email(address) for address in schedules):
            reject("Schedule addresses are invalid")
        calendar_window(arguments, required=True)
        text(arguments, "timezone", max_length=128)
        text(arguments, "endTimezone", max_length=128)
    elif action == "create_event":
        fields(
            arguments,
            ("summary", "startDateTime", "endDateTime", "timezone", "calendarId",
             "attendees", "location", "description"),
            ("summary", "startDateTime", "endDateTime"),
        )
        text(arguments, "summary", required=True, max_length=1_024)
        text(arguments, "timezone", max_length=128)
        text(arguments, "calendarId", max_length=1_024)
        text(arguments, "location", max_length=1_024)
        text(arguments, "description", max_length=8_192)
        calendar_window(arguments, "startDateTime", "endDateTime", required=True)
        _attendees(arguments)
    elif action == "update_event":
        mutable = {"summary", "startDateTime", "endDateTime", "location", "attendees"}
        fields(
            arguments,
            ("eventId", "summary", "startDateTime", "endDateTime", "timezone", "location", "attendees"),
            ("eventId",),
        )
        text(arguments, "eventId", required=True, max_length=256)
        text(arguments, "summary", max_length=1_024)
        text(arguments, "location", max_length=1_024)
        if not mutable.intersection(arguments):
            reject("At least one event change is required")
        if "startDateTime" in arguments or "endDateTime" in arguments:
            text(arguments, "timezone", required=True, max_length=128)
            calendar_window(arguments, "startDateTime", "endDateTime", required=True)
        elif "timezone" in arguments:
            reject("Timezone requires a start and end change")
        _attendees(arguments)
    elif action == "delete_event":
        fields(arguments, ("eventId", "confirm"), ("eventId", "confirm"))
        text(arguments, "eventId", required=True, max_length=256)
        boolean(arguments, "confirm")
        if arguments.get("confirm") is not True:
            reject("Explicit confirmation is required")


def handle(value, environ=os.environ, sender=execute):
    """Validate and execute one managed Connect command."""
    action, arguments = command(value, ROUTES)
    validate(action, arguments)
    if action == "get_schedule":
        arguments.setdefault("timezone", "UTC")
        arguments.setdefault("endTimezone", arguments["timezone"])
    if action == "create_event":
        arguments.setdefault("timezone", "UTC")
    if action == "delete_event":
        arguments.pop("confirm", None)
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
