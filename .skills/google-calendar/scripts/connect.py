#!/usr/bin/env python3
"""Managed Google Calendar entrypoint."""

import os
import sys

from connect_contract import boolean, calendar_window, command, enum, fields, reject, text, text_list
from connect_transport import (
    ConnectFailure,
    execute,
    managed_credentials,
    mark_untrusted,
    read_command,
    write_result,
)


CONNECTION_ENV = "MEDO_CONNECT_GOOGLE_CALENDAR"
ROUTES = {
    "find_event": "https://app-f58c4fdcbbpd-api-connect-google-calendar-find-event.gateway.appmedo.com/",
    "list_calendars": "https://app-f58c4fdcbbpd-api-connect-google-calendar-list-calendars.gateway.appmedo.com/",
    "list_events": "https://app-f58c4fdcbbpd-api-connect-google-calendar-list-events.gateway.appmedo.com/",
    "create_event": "https://app-f58c4fdcbbpd-api-connect-google-calendar-create-event.gateway.appmedo.com/",
    "update_event": "https://app-f58c4fdcbbpd-api-connect-google-calendar-update-event.gateway.appmedo.com/",
    "delete_event": "https://app-f58c4fdcbbpd-api-connect-google-calendar-delete-event.gateway.appmedo.com/",
}


def _attendees(arguments):
    attendees = text_list(arguments, "attendees", maximum=50, item_max_length=320) or []
    if any(address.count("@") != 1 or address.startswith("@") or address.endswith("@") for address in attendees):
        reject("Attendee addresses are invalid")


def validate(action, arguments):
    """Validate the public arguments for one fixed action."""
    if action == "find_event":
        fields(
            arguments,
            ("query", "calendar", "timeMin", "timeMax", "pageToken"),
            ("query",),
        )
        text(arguments, "query", required=True, max_length=2_048)
        text(arguments, "calendar", max_length=1_024)
        text(arguments, "pageToken")
        calendar_window(arguments)
    elif action == "list_calendars":
        fields(arguments, ("pageToken", "showHidden"))
        text(arguments, "pageToken")
        boolean(arguments, "showHidden")
    elif action == "list_events":
        fields(arguments, ("timeMin", "timeMax", "calendarIds"), ("timeMin", "timeMax"))
        calendar_window(arguments, required=True)
        calendar_ids = text_list(arguments, "calendarIds", maximum=20, item_max_length=1_024)
        if calendar_ids is not None and not calendar_ids:
            reject()
    elif action == "create_event":
        fields(
            arguments,
            ("calendar", "summary", "description", "location", "startDateTime", "endDateTime",
             "timezone", "attendees", "sendUpdates"),
            ("summary", "startDateTime", "endDateTime", "timezone"),
        )
        text(arguments, "calendar", max_length=1_024)
        text(arguments, "summary", required=True, max_length=1_024)
        text(arguments, "description", max_length=8_192)
        text(arguments, "location", max_length=1_024)
        text(arguments, "timezone", required=True, max_length=128)
        calendar_window(arguments, "startDateTime", "endDateTime", required=True)
        _attendees(arguments)
        enum(arguments, "sendUpdates", ("all", "externalOnly", "none"))
    elif action == "update_event":
        mutable = {"summary", "description", "location", "startDateTime", "endDateTime", "attendees"}
        fields(
            arguments,
            ("calendar", "eventId", "summary", "description", "location", "startDateTime", "endDateTime",
             "timezone", "attendees", "sendUpdates"),
            ("eventId",),
        )
        text(arguments, "calendar", max_length=1_024)
        text(arguments, "eventId", required=True, max_length=256)
        text(arguments, "summary", max_length=1_024)
        text(arguments, "description", max_length=8_192)
        text(arguments, "location", max_length=1_024)
        if not mutable.intersection(arguments):
            reject("At least one event change is required")
        if "startDateTime" in arguments or "endDateTime" in arguments:
            text(arguments, "timezone", required=True, max_length=128)
            calendar_window(arguments, "startDateTime", "endDateTime", required=True)
        elif "timezone" in arguments:
            reject("Timezone requires a start and end change")
        _attendees(arguments)
        enum(arguments, "sendUpdates", ("all", "externalOnly", "none"))
    elif action == "delete_event":
        fields(arguments, ("calendar", "eventId", "sendUpdates", "confirm"), ("eventId", "confirm"))
        text(arguments, "calendar", max_length=1_024)
        text(arguments, "eventId", required=True, max_length=256)
        boolean(arguments, "confirm")
        if arguments.get("confirm") is not True:
            reject("Explicit confirmation is required")
        enum(arguments, "sendUpdates", ("all", "externalOnly", "none"))


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
