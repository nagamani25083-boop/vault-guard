#!/usr/bin/env python3
"""Managed Notion fixed Action entrypoint; runtime credentials remain server-side."""

import os
import re
import sys
from connect_contract import command, fields, text, markdown, enum, reject
from connect_transport import (
    ConnectFailure,
    execute,
    managed_credentials,
    mark_untrusted,
    read_command,
    write_result,
)

CONNECTION_ENV = "MEDO_CONNECT_NOTION"
ROUTES = {
    "search": "https://app-f58c4fdcbbpd-api-connect-notion-search.gateway.appmedo.com/",
    "get_page": "https://app-f58c4fdcbbpd-api-connect-notion-get-page.gateway.appmedo.com/",
    "list_block_children": "https://app-f58c4fdcbbpd-api-connect-notion-list-blocks.gateway.appmedo.com/",
    "get_database": "https://app-f58c4fdcbbpd-api-connect-notion-get-db.gateway.appmedo.com/",
    "query_database": "https://app-f58c4fdcbbpd-api-connect-notion-query-db.gateway.appmedo.com/",
    "create_page": "https://app-f58c4fdcbbpd-api-connect-notion-create-page.gateway.appmedo.com/",
    "add_database_row": "https://app-f58c4fdcbbpd-api-connect-notion-add-row.gateway.appmedo.com/",
    "append_blocks": "https://app-f58c4fdcbbpd-api-connect-notion-append-blocks.gateway.appmedo.com/",
    "update_page_properties": "https://app-f58c4fdcbbpd-api-connect-notion-update-page.gateway.appmedo.com/",
    "get_page_property": "https://app-f58c4fdcbbpd-api-connect-notion-get-property.gateway.appmedo.com/",
}
ARGUMENTS = {
    "search": (("query", "objectType", "cursor"), ()),
    "get_page": (("pageId",), ("pageId",)),
    "list_block_children": (("blockId", "cursor"), ("blockId",)),
    "get_database": (("databaseId",), ("databaseId",)),
    "query_database": (
        ("databaseId", "filter", "sorts", "cursor"),
        ("databaseId",),
    ),
    "create_page": (("parentId", "title", "markdown"), ("parentId", "title")),
    "add_database_row": (("databaseId", "properties"), ("databaseId", "properties")),
    "append_blocks": (("blockId", "blocks", "after"), ("blockId", "blocks")),
    "update_page_properties": (("pageId", "properties"), ("pageId", "properties")),
    "get_page_property": (("pageId", "propertyId", "cursor"), ("pageId", "propertyId")),
}
ROW_PROPERTY_TYPES = (
    "title",
    "rich_text",
    "number",
    "select",
    "multi_select",
    "status",
    "date",
    "people",
    "files",
    "checkbox",
    "url",
    "email",
    "phone_number",
    "relation",
)
BLOCK_PROPERTIES = (
    "paragraph",
    "heading_1",
    "heading_2",
    "heading_3",
    "callout",
    "to_do",
    "toggle",
    "quote",
    "bulleted_list_item",
    "numbered_list_item",
    "divider",
)

_UUID = re.compile(
    r"(?:[0-9a-fA-F]{32}|[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12})\Z"
)


def _row_properties(values):
    """Validate add_database_row values: a list of name/type/value strings."""
    if not isinstance(values, list) or not 1 <= len(values) <= 100:
        reject("Supply between one and 100 row properties")
    for item in values:
        if (
            not isinstance(item, dict)
            or set(item) != {"name", "type", "value"}
            or not isinstance(item["name"], str)
            or not item["name"].strip()
            or len(item["name"]) > 256
            or item["type"] not in ROW_PROPERTY_TYPES
            or not isinstance(item["value"], str)
            or len(item["value"]) > 2000
        ):
            reject("Row properties need an exact schema name, a supported type and a string value")
        if item["type"] == "checkbox" and item["value"] not in ("True", "False"):
            reject("Checkbox values are the strings True or False")


def _blocks(values):
    """Validate append_blocks content: 1-100 simplified or full Notion blocks."""
    if not isinstance(values, list) or not 1 <= len(values) <= 100:
        reject("Supply between one and 100 blocks")
    for block in values:
        if not isinstance(block, dict):
            reject("Blocks must be objects")
        if "block_property" in block:
            content = block.get("content")
            if (
                not set(block).issubset({"content", "block_property"})
                or block["block_property"] not in BLOCK_PROPERTIES
                or (block["block_property"] != "divider" and not isinstance(content, str))
                or (content is not None and (not isinstance(content, str) or len(content) > 20_000))
            ):
                reject("Use {content, block_property} with a supported block_property")
        elif not isinstance(block.get("type"), str) or not isinstance(block.get(block["type"]), dict):
            reject("A full block needs a type and a matching object")


def validate(action, arguments):
    """Validate fixed action arguments; return None or raise ConnectFailure.

    Args:
        action: Supported action name.
        arguments: User-supplied argument object.
    """
    allowed, required = ARGUMENTS[action]
    fields(arguments, allowed, required)
    for name in ("pageId", "blockId", "databaseId", "parentId", "after"):
        if name in arguments:
            value = text(arguments, name, required=True, max_length=36)
            if not _UUID.fullmatch(value):
                reject("Resource IDs must be Notion UUIDs")
    text(arguments, "query", max_length=2000)
    text(arguments, "cursor", max_length=2048)
    text(arguments, "propertyId", max_length=256)
    text(arguments, "title", max_length=2000)
    markdown(arguments, "markdown")
    enum(arguments, "objectType", ("page", "database"))
    if action == "add_database_row":
        _row_properties(arguments["properties"])
    elif "properties" in arguments:
        props = arguments["properties"]
        if not isinstance(props, dict) or not props or len(props) > 100:
            reject("Use a nonempty typed properties object")
        if any(
            not isinstance(name, str) or not name or not isinstance(value, dict)
            for name, value in props.items()
        ):
            reject("Use properties from the target schema")
    if "filter" in arguments and not isinstance(arguments["filter"], dict):
        reject("Filter must be an object")
    if "sorts" in arguments:
        sorts = arguments["sorts"]
        if (
            not isinstance(sorts, list)
            or len(sorts) > 100
            or any(not isinstance(v, dict) for v in sorts)
        ):
            reject("Sorts must be a bounded array of objects")
    if "blocks" in arguments:
        _blocks(arguments["blocks"])


def handle(value, environ=None, sender=None):
    """Execute a validated command and return an untrusted result envelope.

    Args:
        value: Input command object.
        environ: Optional runtime credential mapping.
        sender: Optional transport callable.

    Raises:
        ConnectFailure: Invalid input, credentials or provider failure.
    """
    environ = os.environ if environ is None else environ
    sender = execute if sender is None else sender
    action, arguments = command(value, ROUTES)
    validate(action, arguments)
    gateway_jwt, connection = managed_credentials(environ, CONNECTION_ENV)
    return mark_untrusted(
        sender(ROUTES[action], gateway_jwt, connection, dict(arguments))
    )


def main():
    """Read stdin, emit one result and return the process exit code.

    Args: None.
    Returns: Zero on success or one on failure.
    """
    try:
        result = handle(read_command(sys.stdin.buffer))
        exit_code = 0
    except ConnectFailure as failure:
        result, exit_code = failure.as_result(), 1
    except Exception:
        result, exit_code = (
            ConnectFailure(
                "RESULT_UNKNOWN", "The provider result is unknown"
            ).as_result(),
            1,
        )
    write_result(sys.stdout, result)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
