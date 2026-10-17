#!/usr/bin/env python3
"""Managed Google Sheets entrypoint."""

import os
import sys

from connect_contract import (
    a1_format_list,
    boolean,
    bounded_a1,
    command,
    fields,
    integer,
    paired,
    reject,
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


CONNECTION_ENV = "MEDO_CONNECT_GOOGLE_SHEETS"
ROUTES = {
    "lookup_row": "https://app-f58c4fdcbbpd-api-connect-google-sheets-lookup-row.gateway.appmedo.com/",
    "get_spreadsheet": "https://app-f58c4fdcbbpd-api-connect-google-sheets-get-spreadsheet.gateway.appmedo.com/",
    "get_values": "https://app-f58c4fdcbbpd-api-connect-google-sheets-get-values.gateway.appmedo.com/",
    "create_spreadsheet": "https://app-f58c4fdcbbpd-api-connect-google-sheets-create-spreadsheet.gateway.appmedo.com/",
    "update_values": "https://app-f58c4fdcbbpd-api-connect-google-sheets-update-values.gateway.appmedo.com/",
    "append_values": "https://app-f58c4fdcbbpd-api-connect-google-sheets-append-values.gateway.appmedo.com/",
    "clear_values": "https://app-f58c4fdcbbpd-api-connect-google-sheets-clear-values.gateway.appmedo.com/",
}


def _values_matrix(arguments, cells_in_range, columns):
    values = arguments.get("values")
    if not isinstance(values, list) or not values or len(values) > 10_000:
        reject("Values must be a non-empty rectangular matrix")
    width = None
    cells = 0
    for row in values:
        if not isinstance(row, list) or not row:
            reject("Values must be a non-empty rectangular matrix")
        if width is None:
            width = len(row)
        if len(row) != width or width > columns:
            reject("Values must fit the requested range")
        for value in row:
            if value is not None and type(value) not in (str, int, float, bool):
                reject("Cell values must be JSON scalars")
            if isinstance(value, str) and (len(value) > 4_096 or "\x00" in value):
                reject("Cell text is invalid")
        cells += len(row)
    if len(values) > cells_in_range // columns:
        reject("Values must fit the requested range")
    if cells > 10_000:
        reject("Values cannot exceed 10,000 cells")


def validate(action, arguments):
    """Validate the public arguments for one fixed action."""
    if action == "lookup_row":
        fields(arguments, ("spreadsheetId", "query", "range"), ("spreadsheetId", "query", "range"))
        text(arguments, "spreadsheetId", required=True, max_length=256)
        text(arguments, "query", required=True, max_length=2_048)
        bounded_a1(arguments, "range", required=True)
    elif action == "get_spreadsheet":
        fields(arguments, ("spreadsheetId", "ranges"), ("spreadsheetId",))
        text(arguments, "spreadsheetId", required=True, max_length=256)
        a1_format_list(arguments, "ranges", maximum=20)
    elif action == "get_values":
        fields(
            arguments,
            ("spreadsheetId", "range", "startRow", "endRow"),
            ("spreadsheetId", "range"),
        )
        text(arguments, "spreadsheetId", required=True, max_length=256)
        _, column_count = bounded_a1(arguments, "range", required=True)
        paired(arguments, "startRow", "endRow")
        start = integer(arguments, "startRow")
        end = integer(arguments, "endRow")
        if start is not None and (end < start or (end - start + 1) * column_count > 10_000):
            reject("A range cannot exceed 10,000 cells")
    elif action == "create_spreadsheet":
        fields(arguments, ("title",), ("title",))
        text(arguments, "title", required=True, max_length=256)
    elif action in ("update_values", "append_values"):
        fields(arguments, ("spreadsheetId", "range", "values"), ("spreadsheetId", "range", "values"))
        text(arguments, "spreadsheetId", required=True, max_length=256)
        cells_in_range, columns = bounded_a1(arguments, "range", required=True)
        _values_matrix(arguments, cells_in_range, columns)
    elif action == "clear_values":
        fields(arguments, ("spreadsheetId", "range", "confirm"), ("spreadsheetId", "range", "confirm"))
        text(arguments, "spreadsheetId", required=True, max_length=256)
        bounded_a1(arguments, "range", required=True)
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
