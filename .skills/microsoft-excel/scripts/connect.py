#!/usr/bin/env python3
"""Managed Microsoft Excel entrypoint."""

import math
import os
import re
import sys

from connect_contract import (
    boolean,
    bounded_a1,
    command,
    fields,
    integer,
    reject,
    text,
    text_list,
)
from connect_transport import (
    ConnectFailure,
    execute,
    managed_credentials,
    mark_untrusted,
    read_command,
    write_result,
)


CONNECTION_ENV = "MEDO_CONNECT_MICROSOFT_EXCEL"
ROUTES = {
    "search_workbooks": "https://app-f58c4fdcbbpd-api-connect-microsoft-excel-search-workbooks.gateway.appmedo.com/",
    "list_files": "https://app-f58c4fdcbbpd-api-connect-microsoft-excel-list-files.gateway.appmedo.com/",
    "create_workbook": "https://app-f58c4fdcbbpd-api-connect-microsoft-excel-create-workbook.gateway.appmedo.com/",
    "list_worksheets": "https://app-f58c4fdcbbpd-api-connect-microsoft-excel-list-worksheets.gateway.appmedo.com/",
    "add_worksheet": "https://app-f58c4fdcbbpd-api-connect-microsoft-excel-add-worksheet.gateway.appmedo.com/",
    "update_worksheet": "https://app-f58c4fdcbbpd-api-connect-microsoft-excel-update-worksheet.gateway.appmedo.com/",
    "delete_worksheet": "https://app-f58c4fdcbbpd-api-connect-microsoft-excel-delete-worksheet.gateway.appmedo.com/",
    "get_range": "https://app-f58c4fdcbbpd-api-connect-microsoft-excel-get-range.gateway.appmedo.com/",
    "get_used_range": "https://app-f58c4fdcbbpd-api-connect-microsoft-excel-get-used-range.gateway.appmedo.com/",
    "update_range": "https://app-f58c4fdcbbpd-api-connect-microsoft-excel-update-range.gateway.appmedo.com/",
    "clear_range": "https://app-f58c4fdcbbpd-api-connect-microsoft-excel-clear-range.gateway.appmedo.com/",
    "list_tables": "https://app-f58c4fdcbbpd-api-connect-microsoft-excel-list-tables.gateway.appmedo.com/",
    "create_table": "https://app-f58c4fdcbbpd-api-connect-microsoft-excel-create-table.gateway.appmedo.com/",
    "list_table_columns": "https://app-f58c4fdcbbpd-api-connect-microsoft-excel-list-table-columns.gateway.appmedo.com/",
    "list_table_rows": "https://app-f58c4fdcbbpd-api-connect-microsoft-excel-list-table-rows.gateway.appmedo.com/",
    "add_table_rows": "https://app-f58c4fdcbbpd-api-connect-microsoft-excel-add-table-rows.gateway.appmedo.com/",
}

# One call carries at most this many cells: the gateway caps a request body at 64 KiB and a
# provider response at 1 MiB, and Excel returns every cell several times (values, text, formulas).
MAX_CELLS = 2_000
MAX_CELL_TEXT = 32_767
MAX_WORKSHEETS = 20
MAX_ROW = 1_048_576
_ITEM_ID = re.compile(r"^[A-Za-z0-9!_.-]{1,256}$")
_SHEET_NAME_FORBIDDEN = re.compile(r"[\\/?*\[\]:\x00-\x1f\x7f]")
_REFERENCE_FORBIDDEN = re.compile(r"[/?#\\]")
_PATH_SEGMENT_FORBIDDEN = re.compile(r'[\\:*?"<>|#%]')
_ROW_NUMBER = re.compile(r"\d+")
_TOO_MANY_CELLS = "address cannot cover more than 2,000 cells; read or write a large area in several ranges"


def _workbook_id(arguments):
    """Validate the drive item ID of the workbook."""
    value = text(arguments, "workbookId", required=True, max_length=256)
    if not _ITEM_ID.fullmatch(value):
        reject("workbookId must be the drive item ID returned by a file action")


def _reference(arguments, name):
    """Validate a worksheet or table reference: its name or its ID."""
    value = text(arguments, name, required=True, max_length=128)
    if _REFERENCE_FORBIDDEN.search(value):
        reject(f"{name} is the name or id returned by a list action")


def _sheet_name(value):
    """Validate a new worksheet name against Excel naming rules."""
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > 31
        or _SHEET_NAME_FORBIDDEN.search(value)
        or value.startswith("'")
        or value.endswith("'")
    ):
        reject(
            "A worksheet name has 1-31 characters, none of \\ / ? * [ ] :, "
            "and no apostrophe at either end"
        )


def _unique_sheet_names(names):
    """Reject names that differ only by letter case; Excel treats them as the same sheet."""
    if len({name.casefold() for name in names}) != len(names):
        reject("Worksheet names must be unique, ignoring letter case")


def _address(arguments):
    """Validate a bounded A1 address without a worksheet prefix and return (rows, columns)."""
    value = text(arguments, "address", required=True, max_length=64)
    if "!" in value or "$" in value:
        reject("address is a plain A1 range such as A1:D20; pass the worksheet separately")
    if any(int(row) > MAX_ROW for row in _ROW_NUMBER.findall(value)):
        reject("address is outside the worksheet")
    try:
        cells, columns = bounded_a1(arguments, "address", required=True)
    except ConnectFailure as failure:
        # The shared check reports its own, larger ceiling; this Skill's limit is the one to act on.
        if "cannot exceed" in failure.safe_message:
            reject(_TOO_MANY_CELLS)
        raise
    if cells > MAX_CELLS:
        reject(_TOO_MANY_CELLS)
    return cells // columns, columns


def _matrix(value, rows=None, columns=None):
    """Validate a rectangular matrix of JSON scalars and return (rows, columns)."""
    if not isinstance(value, list) or not value:
        reject("values must be an array of rows, each row an array of cells")
    width = None
    for row in value:
        if not isinstance(row, list) or not row:
            reject("values must be an array of rows, each row an array of cells")
        if width is None:
            width = len(row)
        if len(row) != width:
            reject("Every row in values must have the same number of cells")
        for cell in row:
            if cell is not None and type(cell) not in (str, int, float, bool):
                reject("Cell values must be JSON scalars or null")
            if isinstance(cell, str) and (len(cell) > MAX_CELL_TEXT or "\x00" in cell):
                reject("Cell text is invalid")
            if type(cell) is float and not math.isfinite(cell):
                reject("Cell numbers must be finite")
    if len(value) * width > MAX_CELLS:
        reject("values cannot exceed 2,000 cells; send a large block in several calls")
    if rows is not None and (len(value) != rows or width != columns):
        reject("values must have exactly the rows and columns of address")
    return len(value), width


def _relative_path(value, message):
    """Validate a path below the drive root that cannot escape it."""
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 400
        or value.startswith("/")
        or value.endswith("/")
    ):
        reject(message)
    for segment in value.split("/"):
        if (
            not segment.strip()
            or segment in (".", "..")
            or segment != segment.strip()
            or _PATH_SEGMENT_FORBIDDEN.search(segment)
        ):
            reject(message)


def _create_workbook(arguments):
    """Validate the path, worksheet names and initial cells of a new workbook."""
    fields(arguments, ("path", "worksheetNames", "worksheetData"), ("path",))
    path = text(arguments, "path", required=True, max_length=400)
    _relative_path(path, "path is a folder path and file name under the drive root, without a leading slash")
    if not path.lower().endswith(".xlsx") or path.rsplit("/", 1)[-1].lower() == ".xlsx":
        reject("path must end with a file name and the .xlsx extension")
    names = text_list(arguments, "worksheetNames", maximum=MAX_WORKSHEETS, item_max_length=31)
    if names is not None:
        if not names:
            reject("worksheetNames lists at least one worksheet name")
        for name in names:
            _sheet_name(name)
        _unique_sheet_names(names)
    if "worksheetData" in arguments:
        data = arguments["worksheetData"]
        if not isinstance(data, dict) or not data or len(data) > MAX_WORKSHEETS:
            reject("worksheetData maps a worksheet name to an array of rows")
        _unique_sheet_names(list(data))
        cells = 0
        for name, matrix in data.items():
            _sheet_name(name)
            if names is not None and name not in names:
                reject("Every worksheetData key must also be listed in worksheetNames")
            rows, columns = _matrix(matrix)
            cells += rows * columns
        if cells > MAX_CELLS:
            reject("worksheetData cannot exceed 2,000 cells; write further rows with update_range")


def validate(action, arguments):
    """Validate the public arguments for one fixed action."""
    if action == "search_workbooks":
        fields(arguments, ("query", "pageToken"), ("query",))
        text(arguments, "query", required=True, max_length=256)
        text(arguments, "pageToken", max_length=2_048)
    elif action == "list_files":
        fields(arguments, ("folderPath", "pageToken"))
        if "folderPath" in arguments:
            _relative_path(
                text(arguments, "folderPath", required=True, max_length=400),
                "folderPath is a folder path under the drive root, without a leading or trailing slash",
            )
        text(arguments, "pageToken", max_length=2_048)
    elif action == "create_workbook":
        _create_workbook(arguments)
    elif action == "list_worksheets":
        fields(arguments, ("workbookId",), ("workbookId",))
        _workbook_id(arguments)
    elif action == "add_worksheet":
        fields(arguments, ("workbookId", "name"), ("workbookId", "name"))
        _workbook_id(arguments)
        _sheet_name(arguments["name"])
    elif action == "update_worksheet":
        fields(arguments, ("workbookId", "worksheet", "name", "position"), ("workbookId", "worksheet"))
        _workbook_id(arguments)
        _reference(arguments, "worksheet")
        if "name" not in arguments and "position" not in arguments:
            reject("Supply a new name, a new position, or both")
        if "name" in arguments:
            _sheet_name(arguments["name"])
        integer(arguments, "position", minimum=0, maximum=255)
    elif action == "delete_worksheet":
        fields(arguments, ("workbookId", "worksheet", "confirm"), ("workbookId", "worksheet", "confirm"))
        _workbook_id(arguments)
        _reference(arguments, "worksheet")
        _confirmed(arguments)
    elif action == "get_range":
        fields(arguments, ("workbookId", "worksheet", "address"), ("workbookId", "worksheet", "address"))
        _workbook_id(arguments)
        _reference(arguments, "worksheet")
        _address(arguments)
    elif action in ("get_used_range", "list_tables"):
        fields(arguments, ("workbookId", "worksheet"), ("workbookId", "worksheet"))
        _workbook_id(arguments)
        _reference(arguments, "worksheet")
    elif action == "update_range":
        names = ("workbookId", "worksheet", "address", "values")
        fields(arguments, names, names)
        _workbook_id(arguments)
        _reference(arguments, "worksheet")
        rows, columns = _address(arguments)
        _matrix(arguments["values"], rows, columns)
    elif action == "clear_range":
        names = ("workbookId", "worksheet", "address", "confirm")
        fields(arguments, names, names)
        _workbook_id(arguments)
        _reference(arguments, "worksheet")
        _address(arguments)
        _confirmed(arguments)
    elif action == "create_table":
        names = ("workbookId", "worksheet", "address", "hasHeaders")
        fields(arguments, names, names)
        _workbook_id(arguments)
        _reference(arguments, "worksheet")
        _address(arguments)
        boolean(arguments, "hasHeaders")
    elif action == "list_table_columns":
        fields(arguments, ("workbookId", "table"), ("workbookId", "table"))
        _workbook_id(arguments)
        _reference(arguments, "table")
    elif action == "list_table_rows":
        fields(arguments, ("workbookId", "table", "startIndex"), ("workbookId", "table"))
        _workbook_id(arguments)
        _reference(arguments, "table")
        integer(arguments, "startIndex", minimum=0)
    elif action == "add_table_rows":
        fields(arguments, ("workbookId", "table", "values", "insertAt"), ("workbookId", "table", "values"))
        _workbook_id(arguments)
        _reference(arguments, "table")
        _matrix(arguments["values"])
        integer(arguments, "insertAt", minimum=0)


def _confirmed(arguments):
    """Require the local confirmation flag of a destructive action."""
    boolean(arguments, "confirm")
    if arguments.get("confirm") is not True:
        reject("Explicit confirmation is required")


def handle(value, environ=os.environ, sender=execute):
    """Validate and execute one managed Connect command."""
    action, arguments = command(value, ROUTES)
    validate(action, arguments)
    safe_arguments = dict(arguments)
    if action in ("delete_worksheet", "clear_range"):
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
