#!/usr/bin/env python3
"""Managed OneDrive entrypoint."""

import os
import re
import sys
import urllib.parse

from connect_contract import boolean, command, enum, fields, reject, text, text_list
from connect_transport import (
    ConnectFailure,
    execute,
    managed_credentials,
    mark_untrusted,
    read_command,
    write_result,
)


CONNECTION_ENV = "MEDO_CONNECT_ONEDRIVE"
ROUTES = {
    "list_items": "https://app-f58c4fdcbbpd-api-connect-onedrive-list-items.gateway.appmedo.com/",
    "search_items": "https://app-f58c4fdcbbpd-api-connect-onedrive-search-items.gateway.appmedo.com/",
    "get_item": "https://app-f58c4fdcbbpd-api-connect-onedrive-get-item.gateway.appmedo.com/",
    "create_folder": "https://app-f58c4fdcbbpd-api-connect-onedrive-create-folder.gateway.appmedo.com/",
    "create_text_file": "https://app-f58c4fdcbbpd-api-connect-onedrive-create-text.gateway.appmedo.com/",
    "upload_from_url": "https://app-f58c4fdcbbpd-api-connect-onedrive-upload-url.gateway.appmedo.com/",
    "download_file": "https://app-f58c4fdcbbpd-api-connect-onedrive-download-file.gateway.appmedo.com/",
    "move_item": "https://app-f58c4fdcbbpd-api-connect-onedrive-move-item.gateway.appmedo.com/",
    "copy_item": "https://app-f58c4fdcbbpd-api-connect-onedrive-copy-item.gateway.appmedo.com/",
    "delete_item": "https://app-f58c4fdcbbpd-api-connect-onedrive-delete-item.gateway.appmedo.com/",
    "create_share_link": "https://app-f58c4fdcbbpd-api-connect-onedrive-create-link.gateway.appmedo.com/",
    "share_with_people": "https://app-f58c4fdcbbpd-api-connect-onedrive-share-people.gateway.appmedo.com/",
    "list_permissions": "https://app-f58c4fdcbbpd-api-connect-onedrive-list-permissions.gateway.appmedo.com/",
    "update_permission": "https://app-f58c4fdcbbpd-api-connect-onedrive-update-permission.gateway.appmedo.com/",
    "remove_permission": "https://app-f58c4fdcbbpd-api-connect-onedrive-remove-permission.gateway.appmedo.com/",
}
# Personal drives use IDs such as "A1B2C3D4E5F60718!s0123..."; business drives use "01ABC...".
_ITEM_ID = re.compile(r"^[A-Za-z0-9!_.-]{8,256}$")
_NAME_FORBIDDEN = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
_PATH_FORBIDDEN = re.compile(r'[\\:*?"<>|\x00-\x1f]')
_CONFLICT = {"fail", "replace", "rename"}
_PERMISSION_ID = re.compile(r"^[A-Za-z0-9_-]{1,256}$")
_EMAIL = re.compile(
    r"^[^@\s<>,;]{1,64}@[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?\.[A-Za-z]{2,24}$"
)
_UTC_TIME = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_ROLES = {"read", "write"}
# Folder arguments take an ID of one of these two shapes or a path. A bare name such as
# "Documents" is rejected: OneDrive would resolve it as a folder name under the root.
_FOLDER_ID = re.compile(r"^(?:[A-Za-z0-9]+![A-Za-z0-9_.-]+|01[A-Z0-9]{32})$")
_CONTENT_FORBIDDEN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _item_id(arguments, name, required=False):
    value = text(arguments, name, required=required, max_length=256)
    if value is None:
        return None
    if not _ITEM_ID.fullmatch(value):
        reject(f"{name} must be a OneDrive item ID")
    return value


def _item_name(arguments, name, required=False):
    value = text(arguments, name, required=required, max_length=255)
    if value is None:
        return None
    if _NAME_FORBIDDEN.search(value) or value in {".", ".."} or value != value.strip():
        reject(f"{name} must be a OneDrive item name without path characters")
    return value


def _folder_path(arguments, name, required=False):
    value = text(arguments, name, required=required, max_length=400)
    if value is None:
        return None
    segments = value.split("/")[1:]
    if (
        not value.startswith("/")
        or _PATH_FORBIDDEN.search(value)
        or (value != "/" and any(segment in {"", ".", ".."} for segment in segments))
    ):
        reject(f"{name} must be a folder path that starts with / and does not end with /")
    return value


def _folder(arguments, name):
    """Accept a folder item ID or a path from the drive root."""
    value = text(arguments, name, max_length=400)
    if value is None:
        return None
    if value.startswith("/"):
        return _folder_path(arguments, name)
    if not _FOLDER_ID.fullmatch(value):
        reject(f"{name} must be a folder item ID or a path starting with /")
    return _item_id(arguments, name)


def _content(arguments, name, required=True, max_length=65_536):
    """Accept multi-line text: line breaks and tabs are content, other control characters are not."""
    if name not in arguments and not required:
        return None
    value = arguments.get(name)
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > max_length
        or _CONTENT_FORBIDDEN.search(value)
    ):
        reject(f"{name} must be non-empty text of at most {max_length} characters")
    return value


def _permission_id(arguments):
    value = text(arguments, "permissionId", required=True, max_length=256)
    if not _PERMISSION_ID.fullmatch(value):
        reject("permissionId must be a permission ID returned by OneDrive")
    return value


def _roles(arguments):
    value = text_list(arguments, "roles", maximum=1, item_max_length=16)
    if value is None or len(value) != 1 or value[0] not in _ROLES:
        reject('roles must be ["read"] or ["write"]')
    return value


def _recipients(arguments):
    value = arguments.get("recipients")
    if not isinstance(value, list) or not 1 <= len(value) <= 20:
        reject("recipients must list 1 to 20 people")
    seen = set()
    for recipient in value:
        if (
            not isinstance(recipient, dict)
            or set(recipient) != {"email"}
            or not isinstance(recipient["email"], str)
            or not _EMAIL.fullmatch(recipient["email"])
            or recipient["email"].lower() in seen
        ):
            reject('each recipient must be {"email": "<address>"} and appear once')
        seen.add(recipient["email"].lower())
    return value


def _https_url(arguments, name, required=False):
    value = text(arguments, name, required=required, max_length=2_048)
    if value is None:
        return None
    parsed = urllib.parse.urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
    ):
        reject("sourceUrl must be https without credentials")
    return value


def _confirm(arguments):
    boolean(arguments, "confirm")
    if arguments.get("confirm") is not True:
        reject("Explicit confirmation is required")


def validate(action, arguments):
    """Validate the public arguments for one fixed action."""
    if action == "list_items":
        fields(arguments, ("folderId", "folderPath", "pageToken"))
        _item_id(arguments, "folderId")
        _folder_path(arguments, "folderPath")
        if ("folderId" in arguments) == ("folderPath" in arguments):
            reject("list_items requires exactly one of folderId or folderPath")
        text(arguments, "pageToken", max_length=4_096)
    elif action == "search_items":
        fields(arguments, ("query", "pageToken"), ("query",))
        text(arguments, "query", required=True, max_length=1_024)
        text(arguments, "pageToken", max_length=4_096)
    elif action == "get_item":
        fields(arguments, ("itemId",), ("itemId",))
        _item_id(arguments, "itemId", required=True)
    elif action == "create_folder":
        fields(arguments, ("name", "parentFolder"), ("name",))
        _item_name(arguments, "name", required=True)
        _folder(arguments, "parentFolder")
    elif action == "create_text_file":
        fields(
            arguments,
            ("name", "content", "folder", "conflictBehavior"),
            ("name", "content"),
        )
        _item_name(arguments, "name", required=True)
        _content(arguments, "content")
        _folder(arguments, "folder")
        enum(arguments, "conflictBehavior", _CONFLICT)
    elif action == "upload_from_url":
        fields(
            arguments,
            ("sourceUrl", "fileName", "folder", "conflictBehavior"),
            ("sourceUrl", "fileName"),
        )
        _https_url(arguments, "sourceUrl", required=True)
        _item_name(arguments, "fileName", required=True)
        _folder(arguments, "folder")
        enum(arguments, "conflictBehavior", _CONFLICT)
    elif action == "download_file":
        fields(arguments, ("itemId", "fileName"), ("itemId", "fileName"))
        _item_id(arguments, "itemId", required=True)
        _item_name(arguments, "fileName", required=True)
    elif action in {"move_item", "copy_item"}:
        fields(
            arguments,
            ("itemId", "destinationFolderId", "newName"),
            ("itemId", "destinationFolderId"),
        )
        _item_id(arguments, "itemId", required=True)
        _item_id(arguments, "destinationFolderId", required=True)
        _item_name(arguments, "newName")
    elif action == "delete_item":
        fields(arguments, ("itemId", "confirm"), ("itemId", "confirm"))
        _item_id(arguments, "itemId", required=True)
        _confirm(arguments)
    elif action == "create_share_link":
        fields(
            arguments,
            ("itemId", "linkType", "expirationDateTime"),
            ("itemId", "linkType"),
        )
        _item_id(arguments, "itemId", required=True)
        if arguments["linkType"] not in ("view", "edit"):
            reject("linkType must be view or edit")
        expires = text(arguments, "expirationDateTime", max_length=20)
        if expires is not None and not _UTC_TIME.fullmatch(expires):
            reject("expirationDateTime must be UTC like 2027-01-31T23:59:59Z")
    elif action == "share_with_people":
        fields(
            arguments,
            ("itemId", "recipients", "roles", "sendInvitation", "message"),
            ("itemId", "recipients", "roles"),
        )
        _item_id(arguments, "itemId", required=True)
        _recipients(arguments)
        _roles(arguments)
        boolean(arguments, "sendInvitation")
        _content(arguments, "message", required=False, max_length=2_000)
        if "message" in arguments and arguments.get("sendInvitation") is not True:
            reject("message is sent only with sendInvitation: true")
    elif action == "list_permissions":
        fields(arguments, ("itemId", "pageToken"), ("itemId",))
        _item_id(arguments, "itemId", required=True)
        text(arguments, "pageToken", max_length=4_096)
    elif action == "update_permission":
        fields(arguments, ("itemId", "permissionId", "roles"), ("itemId", "permissionId", "roles"))
        _item_id(arguments, "itemId", required=True)
        _permission_id(arguments)
        _roles(arguments)
    elif action == "remove_permission":
        fields(
            arguments,
            ("itemId", "permissionId", "confirm"),
            ("itemId", "permissionId", "confirm"),
        )
        _item_id(arguments, "itemId", required=True)
        _permission_id(arguments)
        _confirm(arguments)


def handle(value, environ=os.environ, sender=execute):
    """Validate and execute one managed Connect command."""
    action, arguments = command(value, ROUTES)
    validate(action, arguments)
    safe_arguments = dict(arguments)
    if action in {"delete_item", "remove_permission"}:
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
