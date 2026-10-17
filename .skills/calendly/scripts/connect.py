#!/usr/bin/env python3
"""Managed Calendly entrypoint."""

import os
import re
import sys
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

from connect_contract import boolean, command, enum, fields, paired, reject, text
from connect_transport import (
    ConnectFailure,
    execute,
    managed_credentials,
    mark_untrusted,
    read_command,
    write_result,
)


CONNECTION_ENV = "MEDO_CONNECT_CALENDLY"
ROUTES = {
    "get_current_user": "https://app-f58c4fdcbbpd-api-connect-calendly-get-current-user.gateway.appmedo.com/",
    "list_event_types": "https://app-f58c4fdcbbpd-api-connect-calendly-list-event-types.gateway.appmedo.com/",
    "list_available_times": "https://app-f58c4fdcbbpd-api-connect-calendly-list-available-times.gateway.appmedo.com/",
    "list_scheduled_events": "https://app-f58c4fdcbbpd-api-connect-calendly-list-scheduled-events.gateway.appmedo.com/",
    "list_event_invitees": "https://app-f58c4fdcbbpd-api-connect-calendly-list-event-invitees.gateway.appmedo.com/",
    "create_scheduling_link": "https://app-f58c4fdcbbpd-api-connect-calendly-create-scheduling-link.gateway.appmedo.com/",
    "cancel_scheduled_event": "https://app-f58c4fdcbbpd-api-connect-calendly-cancel-scheduled-event.gateway.appmedo.com/",
}
_UTC_RFC3339 = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?Z$")


def _calendly_uri(arguments, name, resource):
    value = text(arguments, name, required=True, max_length=2_048)
    try:
        parsed = urlsplit(value)
    except ValueError:
        reject(f"{name} must be a Calendly {resource.replace('_', ' ')} URI")
    prefix = f"/{resource}/"
    identifier = parsed.path[len(prefix):] if parsed.path.startswith(prefix) else ""
    if (
        parsed.scheme != "https"
        or parsed.netloc != "api.calendly.com"
        or not identifier
        or "/" in identifier
        or parsed.query
        or parsed.fragment
    ):
        reject(f"{name} must be a Calendly {resource.replace('_', ' ')} URI")
    return value


def _utc_time(arguments, name):
    value = text(arguments, name, required=True, max_length=64)
    if not _UTC_RFC3339.fullmatch(value):
        reject("Calendly times must use UTC RFC 3339 ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        reject("Calendly times must use UTC RFC 3339 ending in Z")
    if parsed.utcoffset() != timedelta(0):
        reject("Calendly times must use UTC RFC 3339 ending in Z")
    return parsed


def _window(arguments, first, second, maximum_days, future=False):
    paired(arguments, first, second)
    if first not in arguments:
        return
    start = _utc_time(arguments, first)
    end = _utc_time(arguments, second)
    if end <= start or end - start > timedelta(days=maximum_days):
        reject(f"Calendly time windows must be positive and no longer than {maximum_days} days")
    if future and start <= datetime.now(timezone.utc):
        reject("Calendly availability windows must start in the future")


def _email(arguments):
    value = text(arguments, "email", max_length=320)
    if value is not None and (
        value != value.strip()
        or value.count("@") != 1
        or value.startswith("@")
        or value.endswith("@")
    ):
        reject("Email address is invalid")


def validate(action, arguments):
    """Validate the public arguments for one fixed action."""
    if action == "get_current_user":
        fields(arguments, ())
    elif action == "list_event_types":
        fields(arguments, ("userUri", "active", "pageToken"), ("userUri",))
        _calendly_uri(arguments, "userUri", "users")
        boolean(arguments, "active")
        text(arguments, "pageToken", max_length=2_048)
    elif action == "list_available_times":
        fields(
            arguments,
            ("eventTypeUri", "startTime", "endTime"),
            ("eventTypeUri", "startTime", "endTime"),
        )
        _calendly_uri(arguments, "eventTypeUri", "event_types")
        _window(arguments, "startTime", "endTime", 7, future=True)
    elif action == "list_scheduled_events":
        fields(
            arguments,
            ("userUri", "status", "minStartTime", "maxStartTime", "pageToken"),
            ("userUri",),
        )
        _calendly_uri(arguments, "userUri", "users")
        enum(arguments, "status", ("active", "canceled"))
        text(arguments, "pageToken", max_length=2_048)
        _window(arguments, "minStartTime", "maxStartTime", 31)
    elif action == "list_event_invitees":
        fields(arguments, ("eventId", "email", "status", "pageToken"), ("eventId",))
        text(arguments, "eventId", required=True, max_length=256)
        _email(arguments)
        enum(arguments, "status", ("active", "canceled"))
        text(arguments, "pageToken", max_length=2_048)
    elif action == "create_scheduling_link":
        fields(arguments, ("eventTypeUri",), ("eventTypeUri",))
        _calendly_uri(arguments, "eventTypeUri", "event_types")
    elif action == "cancel_scheduled_event":
        fields(arguments, ("eventId", "reason", "confirm"), ("eventId", "confirm"))
        text(arguments, "eventId", required=True, max_length=256)
        text(arguments, "reason", max_length=1_024)
        boolean(arguments, "confirm")
        if arguments.get("confirm") is not True:
            reject("Explicit confirmation is required")


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
