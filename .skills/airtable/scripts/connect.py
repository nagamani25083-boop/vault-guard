#!/usr/bin/env python3
"""Managed Airtable entrypoint."""

import math
import os
import re
import sys

from connect_contract import boolean, command, fields, reject, text, text_list
from connect_transport import (
    ConnectFailure,
    execute,
    managed_credentials,
    mark_untrusted,
    read_command,
    write_result,
)


CONNECTION_ENV = "MEDO_CONNECT_AIRTABLE"
ROUTES = {
    "list_bases": "https://app-f58c4fdcbbpd-api-connect-airtable-list-bases.gateway.appmedo.com/",
    "get_base_schema": "https://app-f58c4fdcbbpd-api-connect-airtable-get-base-schema.gateway.appmedo.com/",
    "list_records": "https://app-f58c4fdcbbpd-api-connect-airtable-list-records.gateway.appmedo.com/",
    "get_record": "https://app-f58c4fdcbbpd-api-connect-airtable-get-record.gateway.appmedo.com/",
    "create_records": "https://app-f58c4fdcbbpd-api-connect-airtable-create-records.gateway.appmedo.com/",
    "update_records": "https://app-f58c4fdcbbpd-api-connect-airtable-update-records.gateway.appmedo.com/",
    "delete_records": "https://app-f58c4fdcbbpd-api-connect-airtable-delete-records.gateway.appmedo.com/",
}
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


def _id(arguments, name, prefix):
    value = text(arguments, name, required=True, max_length=67)
    if not re.fullmatch(prefix + r"[A-Za-z0-9]{14,64}", value):
        reject(f"{name} must be an Airtable {prefix} ID")
    return value


def _id_list(arguments, name, prefix, maximum, required=False):
    values = text_list(arguments, name, maximum=maximum, item_max_length=67)
    if values is None:
        if required:
            reject("Required arguments are missing")
        return None
    if not values:
        reject("ID lists cannot be empty")
    for value in values:
        if not re.fullmatch(prefix + r"[A-Za-z0-9]{14,64}", value):
            reject(f"{name} must contain Airtable {prefix} IDs")
    return values


def _sort(arguments):
    if "sort" not in arguments:
        return
    values = arguments["sort"]
    if not isinstance(values, list) or not values or len(values) > 3:
        reject("sort must contain one to three entries")
    seen = set()
    for item in values:
        if not isinstance(item, dict) or set(item) != {"field", "direction"}:
            reject("Each sort entry requires only field and direction")
        field_id = item["field"]
        if (
            not isinstance(field_id, str)
            or not re.fullmatch(r"fld[A-Za-z0-9]{14,64}", field_id)
            or field_id in seen
            or item["direction"] not in ("asc", "desc")
        ):
            reject("Invalid Airtable sort entry")
        seen.add(field_id)


def _field_value(value):
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        if abs(value) > 9_007_199_254_740_991:
            reject("Numeric field values must be JSON-safe")
        return
    if type(value) is float:
        if not math.isfinite(value):
            reject("Numeric field values must be finite")
        return
    if isinstance(value, str):
        if len(value) > 10_000 or _CONTROL.search(value):
            reject("Text field values are invalid")
        return
    if isinstance(value, list):
        if len(value) > 100:
            reject("Text array field values are too large")
        for item in value:
            if not isinstance(item, str) or len(item) > 10_000 or _CONTROL.search(item):
                reject("Only string arrays are accepted as array field values")
        return
    reject("Nested Airtable field values are not accepted")


def _record_fields(value):
    if not isinstance(value, dict) or not value or len(value) > 100:
        reject("Each record requires one to one hundred fields")
    for field_id, field_value in value.items():
        if not isinstance(field_id, str) or not re.fullmatch(r"fld[A-Za-z0-9]{14,64}", field_id):
            reject("Record fields must use Airtable field IDs")
        _field_value(field_value)


def _records(arguments, update):
    records = arguments.get("records")
    if not isinstance(records, list) or not 1 <= len(records) <= 10:
        reject("records must contain one to ten entries")
    record_ids = set()
    for record in records:
        expected = {"id", "fields"} if update else {"fields"}
        if not isinstance(record, dict) or set(record) != expected:
            reject("Record objects do not match the reviewed contract")
        if update:
            record_id = _id(record, "id", "rec")
            if record_id in record_ids:
                reject("Updated record IDs must be unique")
            record_ids.add(record_id)
        _record_fields(record["fields"])


def _target(arguments):
    _id(arguments, "baseId", "app")
    _id(arguments, "tableId", "tbl")


def validate(action, arguments):
    """Validate the public arguments for one fixed action."""
    if action == "list_bases":
        fields(arguments, ("offset",))
        text(arguments, "offset", max_length=2_048)
    elif action == "get_base_schema":
        fields(arguments, ("baseId",), ("baseId",))
        _id(arguments, "baseId", "app")
    elif action == "list_records":
        fields(
            arguments,
            ("baseId", "tableId", "fieldIds", "filterByFormula", "sort", "viewId", "offset"),
            ("baseId", "tableId"),
        )
        _target(arguments)
        _id_list(arguments, "fieldIds", "fld", 100)
        text(arguments, "filterByFormula", max_length=1_000)
        _sort(arguments)
        if "viewId" in arguments:
            _id(arguments, "viewId", "viw")
        text(arguments, "offset", max_length=2_048)
    elif action == "get_record":
        fields(arguments, ("baseId", "tableId", "recordId"), ("baseId", "tableId", "recordId"))
        _target(arguments)
        _id(arguments, "recordId", "rec")
    elif action == "create_records":
        fields(arguments, ("baseId", "tableId", "records"), ("baseId", "tableId", "records"))
        _target(arguments)
        _records(arguments, update=False)
    elif action == "update_records":
        fields(arguments, ("baseId", "tableId", "records"), ("baseId", "tableId", "records"))
        _target(arguments)
        _records(arguments, update=True)
    elif action == "delete_records":
        fields(
            arguments,
            ("baseId", "tableId", "recordIds", "confirm"),
            ("baseId", "tableId", "recordIds", "confirm"),
        )
        _target(arguments)
        _id_list(arguments, "recordIds", "rec", 10, required=True)
        boolean(arguments, "confirm")
        if arguments.get("confirm") is not True:
            reject("Explicit confirmation is required")


def handle(value, environ=os.environ, sender=execute):
    """Validate and execute one managed Connect command."""
    action, arguments = command(value, ROUTES)
    validate(action, arguments)
    safe_arguments = dict(arguments)
    if action == "delete_records":
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
