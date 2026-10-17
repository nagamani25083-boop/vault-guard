#!/usr/bin/env python3
"""Managed Zoho CRM entrypoint. Input is one JSON object on stdin."""

import math
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


CONNECTION_ENV = "MEDO_CONNECT_ZOHO_CRM"
ROUTES = {
    "list_modules": "https://app-f58c4fdcbbpd-api-connect-zoho-crm-list-modules.gateway.appmedo.com/",
    "get_module_fields": "https://app-f58c4fdcbbpd-api-connect-zoho-crm-get-module-fields.gateway.appmedo.com/",
    "list_records": "https://app-f58c4fdcbbpd-api-connect-zoho-crm-list-records.gateway.appmedo.com/",
    "search_records": "https://app-f58c4fdcbbpd-api-connect-zoho-crm-search-records.gateway.appmedo.com/",
    "create_records": "https://app-f58c4fdcbbpd-api-connect-zoho-crm-create-records.gateway.appmedo.com/",
    "update_records": "https://app-f58c4fdcbbpd-api-connect-zoho-crm-update-records.gateway.appmedo.com/",
    "list_related_lists": "https://app-f58c4fdcbbpd-api-connect-zoho-crm-list-related-lists.gateway.appmedo.com/",
    "list_related_records": "https://app-f58c4fdcbbpd-api-connect-zoho-crm-list-related-records.gateway.appmedo.com/",
}
MAX_FIELDS = 50
MAX_RECORDS = 100
# Zoho serves at most 2,000 records per list without a page token; pages hold 100 records.
MAX_PAGE = 20
_API_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,99}")
_RECORD_ID = re.compile(r"[0-9]{5,25}")
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _api_name(arguments, name, required=True):
    """Validate one module or field API name."""
    value = text(arguments, name, required=required, max_length=100)
    if value is not None and not _API_NAME.fullmatch(value):
        reject(f"{name} must be a Zoho CRM API name")
    return value


def _record_id(arguments, name):
    """Validate one numeric Zoho CRM record ID."""
    value = text(arguments, name, required=True, max_length=25)
    if not _RECORD_ID.fullmatch(value):
        reject(f"{name} must be a Zoho CRM record ID")
    return value


def _field_names(arguments, required):
    """Validate the unique field API names a read returns."""
    values = text_list(arguments, "fieldNames", maximum=MAX_FIELDS, item_max_length=100)
    if values is None:
        if required:
            reject("fieldNames is required")
        return
    if not values or any(not _API_NAME.fullmatch(value) for value in values):
        reject("fieldNames must contain one to fifty Zoho CRM field API names")


def _record_ids(arguments):
    """Validate the optional list of record IDs to fetch."""
    values = text_list(arguments, "recordIds", maximum=MAX_RECORDS, item_max_length=25)
    if values is not None and (not values or any(not _RECORD_ID.fullmatch(value) for value in values)):
        reject("recordIds must contain one to one hundred Zoho CRM record IDs")


def _scalar(value):
    """Return whether a field value is a bounded JSON scalar."""
    if value is None or type(value) is bool:
        return True
    if type(value) is int:
        return abs(value) <= 9_007_199_254_740_991
    if type(value) is float:
        return math.isfinite(value)
    if isinstance(value, str):
        return len(value) <= 32_000 and not _CONTROL.search(value)
    return False


def _lookup(value):
    """A lookup, owner, or parent reference: {"id": "<record id>"} with an optional module name."""
    if not isinstance(value, dict) or "id" not in value or not set(value) <= {"id", "module"}:
        return False
    if not isinstance(value["id"], str) or not _RECORD_ID.fullmatch(value["id"]):
        return False
    return "module" not in value or (
        isinstance(value["module"], str) and _API_NAME.fullmatch(value["module"]) is not None)


def _field_value(value):
    """Validate one field value of a record write."""
    if _scalar(value) or _lookup(value):
        return
    if isinstance(value, list) and len(value) <= 100 and all(
            (isinstance(item, str) and _scalar(item)) or _lookup(item) for item in value):
        return
    reject("Field values must be text, numbers, booleans, null, lookups, or bounded lists of them")


def _records(arguments, update):
    """Validate the records of a create or update request."""
    records = arguments.get("records")
    if not isinstance(records, list) or not 1 <= len(records) <= MAX_RECORDS:
        reject("records must contain one to one hundred entries")
    seen = set()
    for record in records:
        if not isinstance(record, dict) or not 1 <= len(record) <= 200:
            reject("Each record must be an object of field API names to values")
        if update:
            record_id = _record_id(record, "id")
            if record_id in seen:
                reject("Updated record IDs must be unique")
            seen.add(record_id)
            if len(record) == 1:
                reject("Each updated record needs at least one field change")
        elif "id" in record:
            reject("New records cannot carry an id")
        for field_name, value in record.items():
            if not isinstance(field_name, str) or not _API_NAME.fullmatch(field_name):
                reject("Record keys must be Zoho CRM field API names")
            if field_name != "id":
                _field_value(value)


def _pagination(arguments, allow_token=True):
    """Validate the page number and optional page token."""
    integer(arguments, "page", minimum=1, maximum=MAX_PAGE)
    if allow_token:
        text(arguments, "pageToken", max_length=2_048)
        if "page" in arguments and "pageToken" in arguments:
            reject("page and pageToken cannot be used together")


def validate(action, arguments):
    """Validate the public arguments for one fixed action."""
    if action == "list_modules":
        fields(arguments, ())
    elif action == "get_module_fields":
        fields(arguments, ("module",), ("module",))
        _api_name(arguments, "module")
    elif action == "list_records":
        fields(
            arguments,
            ("module", "fieldNames", "recordIds", "sortBy", "sortOrder", "page", "pageToken"),
            ("module", "fieldNames"),
        )
        _api_name(arguments, "module")
        _field_names(arguments, required=True)
        _record_ids(arguments)
        enum(arguments, "sortBy", ("id", "Created_Time", "Modified_Time"))
        enum(arguments, "sortOrder", ("asc", "desc"))
        _pagination(arguments)
        if "recordIds" in arguments and "pageToken" in arguments:
            reject("recordIds and pageToken cannot be used together")
    elif action == "search_records":
        conditions = ("criteria", "keyword", "email", "phone")
        fields(arguments, ("module", "fieldNames", "page") + conditions, ("module", "fieldNames"))
        _api_name(arguments, "module")
        _field_names(arguments, required=True)
        text(arguments, "criteria", max_length=2_000)
        text(arguments, "keyword", max_length=255)
        text(arguments, "email", max_length=320)
        text(arguments, "phone", max_length=64)
        if sum(name in arguments for name in conditions) != 1:
            reject("Use exactly one of criteria, keyword, email, or phone")
        if "keyword" in arguments and len(arguments["keyword"].strip()) < 2:
            reject("keyword needs at least two characters")
        _pagination(arguments, allow_token=False)
    elif action in ("create_records", "update_records"):
        fields(arguments, ("module", "records"), ("module", "records"))
        _api_name(arguments, "module")
        _records(arguments, update=action == "update_records")
    elif action == "list_related_lists":
        fields(arguments, ("module",), ("module",))
        _api_name(arguments, "module")
    elif action == "list_related_records":
        fields(
            arguments,
            ("module", "recordId", "relatedList", "fieldNames", "page", "pageToken"),
            ("module", "recordId", "relatedList", "fieldNames"),
        )
        _api_name(arguments, "module")
        _record_id(arguments, "recordId")
        _api_name(arguments, "relatedList")
        _field_names(arguments, required=True)
        _pagination(arguments)


def handle(value, environ=os.environ, sender=execute):
    """Validate and execute one managed Connect command."""
    action, arguments = command(value, ROUTES)
    validate(action, arguments)
    safe_arguments = dict(arguments)
    # The gateway forwards these as Zoho's comma-separated query values.
    for name in ("fieldNames", "recordIds"):
        if name in safe_arguments:
            safe_arguments[name] = ",".join(safe_arguments[name])
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
