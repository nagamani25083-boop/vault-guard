#!/usr/bin/env python3
"""Managed Monday.com boards, items and item updates entrypoint."""

import json
import os
import re
import sys

from connect_contract import command, enum, fields, integer, reject, text, text_list
from connect_transport import (
    ConnectFailure,
    execute,
    managed_credentials,
    mark_untrusted,
    read_command,
    write_result,
)


CONNECTION_ENV = "MEDO_CONNECT_MONDAY"
ROUTES = {
    "list_workspaces": "https://app-f58c4fdcbbpd-api-connect-monday-list-workspaces.gateway.appmedo.com/",
    "list_boards": "https://app-f58c4fdcbbpd-api-connect-monday-list-boards.gateway.appmedo.com/",
    "get_board_columns": "https://app-f58c4fdcbbpd-api-connect-monday-get-columns.gateway.appmedo.com/",
    "list_groups": "https://app-f58c4fdcbbpd-api-connect-monday-list-groups.gateway.appmedo.com/",
    "list_items": "https://app-f58c4fdcbbpd-api-connect-monday-list-items.gateway.appmedo.com/",
    "search_items": "https://app-f58c4fdcbbpd-api-connect-monday-search-items.gateway.appmedo.com/",
    "get_items": "https://app-f58c4fdcbbpd-api-connect-monday-get-items.gateway.appmedo.com/",
    "list_users": "https://app-f58c4fdcbbpd-api-connect-monday-list-users.gateway.appmedo.com/",
    "create_item": "https://app-f58c4fdcbbpd-api-connect-monday-create-item.gateway.appmedo.com/",
    "update_column_value": "https://app-f58c4fdcbbpd-api-connect-monday-update-column.gateway.appmedo.com/",
    "move_item_to_group": "https://app-f58c4fdcbbpd-api-connect-monday-move-item.gateway.appmedo.com/",
    "list_item_updates": "https://app-f58c4fdcbbpd-api-connect-monday-list-updates.gateway.appmedo.com/",
    "create_item_update": "https://app-f58c4fdcbbpd-api-connect-monday-create-update.gateway.appmedo.com/",
    "archive_item": "https://app-f58c4fdcbbpd-api-connect-monday-archive-item.gateway.appmedo.com/",
    "delete_item": "https://app-f58c4fdcbbpd-api-connect-monday-delete-item.gateway.appmedo.com/",
    "list_subitems": "https://app-f58c4fdcbbpd-api-connect-monday-list-subitems.gateway.appmedo.com/",
}
READ_ACTIONS = (
    "list_workspaces", "list_boards", "get_board_columns", "list_groups", "list_items", "search_items",
    "get_items", "list_users", "list_item_updates", "list_subitems",
)
WRITE_ACTIONS = (
    "create_item", "update_column_value", "move_item_to_group", "create_item_update", "archive_item",
    "delete_item",
)
# The local `confirm: true` marker is checked here and never sent to the gateway.
CONFIRMED_ACTIONS = ("delete_item",)
# Successful data must carry these receipts; anything else is an unknown result.
BOARD_RECEIPTS = ("get_board_columns", "list_groups")
UPDATE_RECEIPTS = ("create_item_update",)
MAX_IDS = 50
MAX_NAME_LENGTH = 256
MAX_BODY_LENGTH = 20_000
MAX_COLUMN_VALUE_BYTES = 16 * 1024
MAX_COLUMN_VALUES = 50
MAX_ORDER_BY = 5
MAX_COLUMN_FILTERS = 10
MAX_FILTER_VALUES = 20
MAX_PAGE = 10_000
DIRECTIONS = ("asc", "desc")
_NUMERIC_ID = re.compile(r"[0-9]{1,20}")
_KEY = re.compile(r"[A-Za-z0-9_-]{1,128}")
# Multi-line text keeps tabs and line breaks; every other control character is rejected.
_UNSAFE_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_MAX_SAFE_INTEGER = 9_007_199_254_740_991


def _numeric_id(arguments, name, required=True):
    """Validate one Monday numeric ID passed as a string."""
    value = text(arguments, name, required=required, max_length=20)
    if value is not None and not _NUMERIC_ID.fullmatch(value):
        reject(f"{name} must be a Monday ID string of digits")
    return value


def _key(arguments, name, required=True):
    """Validate one group or column ID copied from a Monday response."""
    value = text(arguments, name, required=required, max_length=128)
    if value is not None and not _KEY.fullmatch(value):
        reject(f"{name} must be an ID returned by Monday")
    return value


def _id_list(arguments, name, required=False):
    """Validate a non-empty list of at most fifty unique Monday ID strings."""
    if required and name not in arguments:
        reject("Required arguments are missing")
    values = text_list(arguments, name, maximum=MAX_IDS, item_max_length=20)
    if values is None:
        return None
    if not values:
        reject(f"{name} cannot be empty")
    if any(not _NUMERIC_ID.fullmatch(value) for value in values):
        reject(f"{name} must contain Monday ID strings of digits")
    return values


def _page(arguments):
    """Validate the optional page number, counted from 1."""
    integer(arguments, "page", minimum=1, maximum=MAX_PAGE)


def _cursor(arguments):
    """Validate an opaque cursor returned as nextCursor."""
    return text(arguments, "cursor", max_length=4_096)


def _multiline(arguments, name, required, max_length):
    """Validate text that may contain line breaks, such as an item update body."""
    if name not in arguments:
        if required:
            reject("Required arguments are missing")
        return None
    value = arguments[name]
    if not isinstance(value, str) or not value.strip() or len(value) > max_length:
        reject(f"{name} must be non-empty text of at most {max_length} characters")
    if _UNSAFE_CONTROL.search(value):
        reject(f"{name} contains control characters")
    return value


def _is_json_object_text(value):
    """Return whether a string is an encoded JSON object, which Monday.com rejects as a column value."""
    if not value.lstrip().startswith("{"):
        return False
    try:
        return isinstance(json.loads(value), dict)
    except ValueError:
        return False


def _column_value(value, name):
    """Validate one column value: a string, or a JSON object such as {"label": "Done"}."""
    if isinstance(value, str):
        if _UNSAFE_CONTROL.search(value):
            reject(f"{name} contains control characters")
        if _is_json_object_text(value):
            reject(f"{name} must be the JSON object itself, not a JSON string; Monday.com rejects encoded values")
    elif not isinstance(value, dict):
        reject(f"{name} must be a string or a JSON object")
    try:
        encoded = json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError):
        reject(f"{name} must be valid JSON")
    if len(encoded) > MAX_COLUMN_VALUE_BYTES:
        reject(f"{name} is too large")


def _column_values(arguments):
    """Validate create_item columnValues: {columnId: value} as an object or its JSON string."""
    if "columnValues" not in arguments:
        return
    values = arguments["columnValues"]
    if isinstance(values, str):
        try:
            values = json.loads(values)
        except ValueError:
            reject("columnValues must be a JSON object keyed by column ID")
    if not isinstance(values, dict) or not 1 <= len(values) <= MAX_COLUMN_VALUES:
        reject("columnValues must map one to fifty column IDs to values")
    for column_id, value in values.items():
        if not isinstance(column_id, str) or not _KEY.fullmatch(column_id):
            reject("columnValues keys must be column IDs from get_board_columns")
        _column_value(value, f"columnValues.{column_id}")
    _column_value(values, "columnValues")


def _order_by(arguments):
    """Validate list_items orderBy: [{column_id, direction: asc|desc}]."""
    if "orderBy" not in arguments:
        return
    rules = arguments["orderBy"]
    if not isinstance(rules, list) or not 1 <= len(rules) <= MAX_ORDER_BY:
        reject("orderBy must contain one to five sort rules")
    seen = set()
    for rule in rules:
        if not isinstance(rule, dict):
            reject("orderBy entries must be objects")
        fields(rule, ("column_id", "direction"), ("column_id",))
        seen.add(_key(rule, "column_id"))
        enum(rule, "direction", DIRECTIONS)
    if len(seen) != len(rules):
        reject("orderBy cannot repeat a column")


def _column_filters(arguments, required):
    """Validate search_items columnFilters: [{column_id, column_values: [label]}]."""
    if "columnFilters" not in arguments:
        if required:
            reject("columnFilters is required on the first page")
        return
    filters = arguments["columnFilters"]
    if not isinstance(filters, list) or not 1 <= len(filters) <= MAX_COLUMN_FILTERS:
        reject("columnFilters must contain one to ten column filters")
    seen = set()
    for column_filter in filters:
        if not isinstance(column_filter, dict):
            reject("columnFilters entries must be objects")
        fields(column_filter, ("column_id", "column_values"), ("column_id", "column_values"))
        seen.add(_key(column_filter, "column_id"))
        labels = text_list(column_filter, "column_values", maximum=MAX_FILTER_VALUES, item_max_length=256)
        if not labels:
            reject("column_values must list one to twenty labels")
    if len(seen) != len(filters):
        reject("Combine the labels for one column in a single filter")


def validate(action, arguments):
    """Validate the public arguments for one fixed action."""
    if action in ("list_workspaces", "list_users"):
        fields(arguments, ("page",))
        _page(arguments)
    elif action == "list_boards":
        fields(arguments, ("workspaceIds", "boardIds", "page"))
        _id_list(arguments, "workspaceIds")
        _id_list(arguments, "boardIds")
        _page(arguments)
    elif action == "get_board_columns":
        fields(arguments, ("boardIds",), ("boardIds",))
        _id_list(arguments, "boardIds", required=True)
    elif action == "list_groups":
        fields(arguments, ("boardId",), ("boardId",))
        _numeric_id(arguments, "boardId")
    elif action == "list_items":
        fields(arguments, ("boardId", "groupId", "cursor", "orderBy"))
        cursor = _cursor(arguments)
        _numeric_id(arguments, "boardId", required=cursor is None)
        if cursor is not None and ("groupId" in arguments or "orderBy" in arguments):
            reject("A cursor already carries the group and order of its first page")
        _key(arguments, "groupId", required=False)
        _order_by(arguments)
    elif action == "search_items":
        fields(arguments, ("boardId", "columnFilters", "cursor"), ("boardId",))
        _numeric_id(arguments, "boardId")
        cursor = _cursor(arguments)
        if cursor is not None and "columnFilters" in arguments:
            reject("A cursor already carries the filters of its first page")
        _column_filters(arguments, required=cursor is None)
    elif action == "get_items":
        fields(arguments, ("itemIds",), ("itemIds",))
        _id_list(arguments, "itemIds", required=True)
    elif action == "create_item":
        fields(arguments, ("boardId", "name", "groupId", "columnValues"), ("boardId", "name"))
        _numeric_id(arguments, "boardId")
        text(arguments, "name", required=True, max_length=MAX_NAME_LENGTH)
        _key(arguments, "groupId", required=False)
        _column_values(arguments)
    elif action == "update_column_value":
        required = ("boardId", "itemId", "columnId", "value")
        fields(arguments, required, required)
        _numeric_id(arguments, "boardId")
        _numeric_id(arguments, "itemId")
        column_id = _key(arguments, "columnId")
        _column_value(arguments["value"], "value")
        if column_id == "name" and not (isinstance(arguments["value"], str) and arguments["value"].strip()):
            reject("Renaming an item needs a non-empty string value")
        if column_id == "name" and len(arguments["value"]) > MAX_NAME_LENGTH:
            reject("Item names are at most 256 characters")
    elif action == "move_item_to_group":
        fields(arguments, ("itemId", "groupId"), ("itemId", "groupId"))
        _numeric_id(arguments, "itemId")
        _key(arguments, "groupId")
    elif action == "list_item_updates":
        fields(arguments, ("itemId", "page"), ("itemId",))
        _numeric_id(arguments, "itemId")
        _page(arguments)
    elif action == "create_item_update":
        fields(arguments, ("itemId", "body", "parentUpdateId"), ("itemId", "body"))
        _numeric_id(arguments, "itemId")
        _multiline(arguments, "body", required=True, max_length=MAX_BODY_LENGTH)
        _numeric_id(arguments, "parentUpdateId", required=False)
    elif action in ("archive_item", "delete_item"):
        fields(arguments, ("itemId",), ("itemId",))
        _numeric_id(arguments, "itemId")
    elif action == "list_subitems":
        fields(arguments, ("parentItemIds",), ("parentItemIds",))
        _id_list(arguments, "parentItemIds", required=True)
    else:
        reject()


def _present_id(value):
    """Return whether a projected mutation ID is a real Monday ID."""
    if isinstance(value, str):
        return bool(_NUMERIC_ID.fullmatch(value))
    return type(value) is int and 0 < value <= _MAX_SAFE_INTEGER


def _receipt_ok(action, data):
    """Check that a successful response carries the expected business receipt."""
    if action in BOARD_RECEIPTS:
        return isinstance(data.get("boards"), list)
    if action in UPDATE_RECEIPTS:
        return _present_id(data.get("updateId"))
    if action in WRITE_ACTIONS:
        return _present_id(data.get("itemId"))
    return isinstance(data.get("items"), list)


def handle(value, environ=os.environ, sender=execute):
    """Validate and execute one managed Connect command."""
    action, arguments = command(value, ROUTES)
    safe_arguments = dict(arguments)
    confirm = safe_arguments.pop("confirm", None)
    validate(action, safe_arguments)
    if action in CONFIRMED_ACTIONS:
        if confirm is not True:
            raise ConnectFailure("ACTION_NOT_ALLOWED", "Explicit confirmation is required")
    elif "confirm" in arguments:
        raise ConnectFailure("ACTION_NOT_ALLOWED", "Confirmation is not used for this action")
    gateway_jwt, connection = managed_credentials(environ, CONNECTION_ENV)
    result = sender(ROUTES[action], gateway_jwt, connection, safe_arguments)
    data = result.get("data") if isinstance(result, dict) else None
    if not (isinstance(data, dict) and result.get("successful") is True and _receipt_ok(action, data)):
        if action in WRITE_ACTIONS:
            raise ConnectFailure(
                "RESULT_UNKNOWN", "The Monday change is unconfirmed; read the item back before any retry"
            )
        raise ConnectFailure("RESULT_UNKNOWN", "The provider returned an unexpected response")
    return mark_untrusted(result)


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
