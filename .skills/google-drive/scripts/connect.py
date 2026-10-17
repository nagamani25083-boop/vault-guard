#!/usr/bin/env python3
"""Managed Google Drive entrypoint."""

import os
import re
import sys
import urllib.parse

from connect_contract import boolean, command, enum, fields, integer, reject, text, text_list
from connect_transport import (
    ConnectFailure,
    execute,
    managed_credentials,
    mark_untrusted,
    read_command,
    write_result,
)


CONNECTION_ENV = "MEDO_CONNECT_GOOGLE_DRIVE"
ROUTES = {
    "find_files": "https://app-f58c4fdcbbpd-api-connect-google-drive-find-files.gateway.appmedo.com/",
    "find_folder": "https://app-f58c4fdcbbpd-api-connect-google-drive-find-folder.gateway.appmedo.com/",
    "get_file": "https://app-f58c4fdcbbpd-api-connect-google-drive-get-file.gateway.appmedo.com/",
    "create_folder": "https://app-f58c4fdcbbpd-api-connect-google-drive-create-folder.gateway.appmedo.com/",
    "create_text_file": "https://app-f58c4fdcbbpd-api-connect-google-drive-create-text.gateway.appmedo.com/",
    "upload_from_url": "https://app-f58c4fdcbbpd-api-connect-google-drive-upload-url.gateway.appmedo.com/",
    "download_file": "https://app-f58c4fdcbbpd-api-connect-google-drive-download-file.gateway.appmedo.com/",
    "move_file": "https://app-f58c4fdcbbpd-api-connect-google-drive-move-file.gateway.appmedo.com/",
    "copy_file": "https://app-f58c4fdcbbpd-api-connect-google-drive-copy-file.gateway.appmedo.com/",
    "edit_file": "https://app-f58c4fdcbbpd-api-connect-google-drive-edit-file.gateway.appmedo.com/",
    "trash_file": "https://app-f58c4fdcbbpd-api-connect-google-drive-trash-file.gateway.appmedo.com/",
}
_DRIVE_ID = re.compile(r"^(?:root|[A-Za-z0-9_-]{8,256})$")
_ORDER = re.compile(
    r"^(?:createdTime|modifiedTime|modifiedByMeTime|viewedByMeTime|sharedWithMeTime|"
    r"name|name_natural|folder|quotaBytesUsed|starred|recency)"
    r"(?: desc)?$"
)
_TEXT_MIME = {
    "text/plain",
    "text/html",
    "text/csv",
    "text/markdown",
    "text/xml",
    "application/json",
}


def _drive_id(arguments, name, required=False):
    value = text(arguments, name, required=required, max_length=256)
    if value is None:
        return None
    if not _DRIVE_ID.fullmatch(value):
        reject(f"{name} must be a Google Drive ID or root")
    return value


def _page_size(arguments):
    integer(arguments, "pageSize", minimum=1, maximum=50)


def _order_by(arguments):
    value = text(arguments, "orderBy", max_length=128)
    if value is None:
        return
    parts = [part.strip() for part in value.split(",") if part.strip()]
    if not parts or len(parts) > 5 or any(not _ORDER.fullmatch(part) for part in parts):
        reject("orderBy must use Drive sort keys")


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
    if action == "find_files":
        fields(arguments, ("query", "folderId", "pageSize", "pageToken", "orderBy"))
        text(arguments, "query", max_length=2_048)
        _drive_id(arguments, "folderId")
        _page_size(arguments)
        text(arguments, "pageToken", max_length=2_048)
        _order_by(arguments)
    elif action == "find_folder":
        fields(
            arguments,
            ("nameContains", "nameExact", "parentFolderId", "pageSize", "pageToken"),
        )
        text(arguments, "nameContains", max_length=255)
        text(arguments, "nameExact", max_length=255)
        _drive_id(arguments, "parentFolderId")
        _page_size(arguments)
        text(arguments, "pageToken", max_length=2_048)
    elif action == "get_file":
        fields(arguments, ("fileId",), ("fileId",))
        _drive_id(arguments, "fileId", required=True)
    elif action == "create_folder":
        fields(arguments, ("name", "parentId"), ("name",))
        text(arguments, "name", required=True, max_length=255)
        _drive_id(arguments, "parentId")
    elif action == "create_text_file":
        fields(
            arguments,
            ("fileName", "textContent", "mimeType", "parentId"),
            ("fileName", "textContent"),
        )
        text(arguments, "fileName", required=True, max_length=255)
        text(arguments, "textContent", required=True, max_length=65_536)
        enum(arguments, "mimeType", _TEXT_MIME)
        _drive_id(arguments, "parentId")
    elif action == "upload_from_url":
        fields(
            arguments,
            ("name", "sourceUrl", "mimeType", "parentFolderId"),
            ("name", "sourceUrl"),
        )
        text(arguments, "name", required=True, max_length=255)
        _https_url(arguments, "sourceUrl", required=True)
        text(arguments, "mimeType", max_length=128)
        if "mimeType" in arguments and arguments["mimeType"].startswith("application/vnd.google-apps."):
            reject("mimeType cannot be a Google Workspace type")
        _drive_id(arguments, "parentFolderId")
    elif action == "download_file":
        fields(arguments, ("fileId", "mimeType"), ("fileId",))
        _drive_id(arguments, "fileId", required=True)
        text(arguments, "mimeType", max_length=128)
    elif action == "move_file":
        fields(arguments, ("fileId", "addParents", "removeParents"), ("fileId",))
        _drive_id(arguments, "fileId", required=True)
        _drive_id(arguments, "addParents")
        _drive_id(arguments, "removeParents")
        if "addParents" not in arguments and "removeParents" not in arguments:
            reject("move_file requires addParents or removeParents")
    elif action == "copy_file":
        fields(arguments, ("fileId", "name", "parents"), ("fileId",))
        _drive_id(arguments, "fileId", required=True)
        text(arguments, "name", max_length=255)
        parents = text_list(arguments, "parents", maximum=1, item_max_length=256)
        if parents is not None and (len(parents) != 1 or not _DRIVE_ID.fullmatch(parents[0])):
            reject("parents must be one Google Drive folder ID")
    elif action == "edit_file":
        fields(arguments, ("fileId", "content", "mimeType"), ("fileId", "content"))
        _drive_id(arguments, "fileId", required=True)
        text(arguments, "content", required=True, max_length=65_536)
        text(arguments, "mimeType", max_length=128)
        if "mimeType" in arguments and arguments["mimeType"].startswith("application/vnd.google-apps."):
            reject("mimeType cannot be a Google Workspace type")
    elif action == "trash_file":
        fields(arguments, ("fileId", "confirm"), ("fileId", "confirm"))
        _drive_id(arguments, "fileId", required=True)
        _confirm(arguments)


def handle(value, environ=os.environ, sender=execute):
    """Validate and execute one managed Connect command."""
    action, arguments = command(value, ROUTES)
    validate(action, arguments)
    safe_arguments = dict(arguments)
    if action == "trash_file":
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
