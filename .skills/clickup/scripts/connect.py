#!/usr/bin/env python3
"""Managed ClickUp entrypoint."""

import os
import re
import sys

from connect_contract import boolean, command, fields, integer, reject, text, text_list
from connect_transport import (
    ConnectFailure,
    execute,
    managed_credentials,
    mark_untrusted,
    read_command,
    write_result,
)


CONNECTION_ENV = "MEDO_CONNECT_CLICKUP"
ROUTES = {
    "list_workspaces": "https://app-f58c4fdcbbpd-api-connect-clickup-list-workspaces.gateway.appmedo.com/",
    "list_spaces": "https://app-f58c4fdcbbpd-api-connect-clickup-list-spaces.gateway.appmedo.com/",
    "list_folders": "https://app-f58c4fdcbbpd-api-connect-clickup-list-folders.gateway.appmedo.com/",
    "list_lists": "https://app-f58c4fdcbbpd-api-connect-clickup-list-lists.gateway.appmedo.com/",
    "list_folderless_lists": "https://app-f58c4fdcbbpd-api-connect-clickup-list-folderless-lists.gateway.appmedo.com/",
    "list_tasks": "https://app-f58c4fdcbbpd-api-connect-clickup-list-tasks.gateway.appmedo.com/",
    "create_task": "https://app-f58c4fdcbbpd-api-connect-clickup-create-task.gateway.appmedo.com/",
    "update_task": "https://app-f58c4fdcbbpd-api-connect-clickup-update-task.gateway.appmedo.com/",
}
_ID = re.compile(r"[A-Za-z0-9_-]{1,128}")
_MAX_SAFE_INTEGER = 9_007_199_254_740_991


def _id(arguments, name):
    value = text(arguments, name, required=True, max_length=128)
    if not _ID.fullmatch(value):
        reject(f"{name} must be a ClickUp ID")
    return value


def _strings(arguments, name, maximum=20, item_max_length=100):
    values = text_list(
        arguments,
        name,
        maximum=maximum,
        item_max_length=item_max_length,
    )
    if values is not None and not values:
        reject(f"{name} cannot be empty")
    return values


def _assignee_ids(arguments, name):
    if name not in arguments:
        return None
    values = arguments[name]
    if not isinstance(values, list) or not 1 <= len(values) <= 20:
        reject(f"{name} must contain one to twenty IDs")
    if any(type(value) is not int or not 1 <= value <= _MAX_SAFE_INTEGER for value in values):
        reject(f"{name} must contain positive numeric ClickUp user IDs")
    if len(values) != len(set(values)):
        reject(f"{name} must contain unique IDs")
    return values


def _task_filters(arguments):
    integer(arguments, "page", minimum=0, maximum=10_000)
    boolean(arguments, "includeClosed")
    boolean(arguments, "subtasks")
    values = _strings(arguments, "assigneeIds", item_max_length=32)
    if values is not None and any(not re.fullmatch(r"[0-9]{1,20}", value) for value in values):
        reject("assigneeIds must contain ClickUp user IDs")
    _strings(arguments, "statuses")
    _strings(arguments, "tags")


def _task_write(arguments, updating):
    text(arguments, "name", required=not updating, max_length=1_000)
    text(arguments, "description", max_length=10_000)
    _strings(arguments, "tags")
    text(arguments, "status", max_length=100)
    integer(arguments, "priority", minimum=1, maximum=4)
    integer(arguments, "startDate", minimum=0, maximum=_MAX_SAFE_INTEGER)
    boolean(arguments, "startDateTime")
    integer(arguments, "dueDate", minimum=0, maximum=_MAX_SAFE_INTEGER)
    boolean(arguments, "dueDateTime")
    integer(arguments, "timeEstimate", minimum=0, maximum=_MAX_SAFE_INTEGER)
    if "startDateTime" in arguments and "startDate" not in arguments:
        reject("startDateTime requires startDate")
    if "dueDateTime" in arguments and "dueDate" not in arguments:
        reject("dueDateTime requires dueDate")
    if updating:
        added = _assignee_ids(arguments, "assigneeIdsToAdd") or []
        removed = _assignee_ids(arguments, "assigneeIdsToRemove") or []
        if set(added) & set(removed):
            reject("The same assignee cannot be added and removed")
    else:
        _assignee_ids(arguments, "assigneeIds")
        if "parentTaskId" in arguments:
            _id(arguments, "parentTaskId")


def validate(action, arguments):
    """Validate the public arguments for one fixed action."""
    if action == "list_workspaces":
        fields(arguments, ())
    elif action == "list_spaces":
        fields(arguments, ("workspaceId",), ("workspaceId",))
        _id(arguments, "workspaceId")
    elif action == "list_folders":
        fields(arguments, ("spaceId",), ("spaceId",))
        _id(arguments, "spaceId")
    elif action == "list_lists":
        fields(arguments, ("folderId",), ("folderId",))
        _id(arguments, "folderId")
    elif action == "list_folderless_lists":
        fields(arguments, ("spaceId",), ("spaceId",))
        _id(arguments, "spaceId")
    elif action == "list_tasks":
        allowed = (
            "listId", "page", "includeClosed", "subtasks", "assigneeIds", "statuses", "tags",
        )
        fields(arguments, allowed, ("listId",))
        _id(arguments, "listId")
        _task_filters(arguments)
    elif action == "create_task":
        allowed = (
            "listId", "name", "description", "assigneeIds", "tags", "status", "priority",
            "startDate", "startDateTime", "dueDate", "dueDateTime", "timeEstimate", "parentTaskId",
        )
        fields(arguments, allowed, ("listId", "name"))
        _id(arguments, "listId")
        _task_write(arguments, updating=False)
    elif action == "update_task":
        allowed = (
            "taskId", "name", "description", "assigneeIdsToAdd", "assigneeIdsToRemove", "status",
            "priority", "startDate", "startDateTime", "dueDate", "dueDateTime", "timeEstimate",
        )
        fields(arguments, allowed, ("taskId",))
        _id(arguments, "taskId")
        if len(arguments) == 1:
            reject("At least one task change is required")
        _task_write(arguments, updating=True)


def handle(value, environ=os.environ, sender=execute):
    """Validate and execute one managed Connect command."""
    action, arguments = command(value, ROUTES)
    validate(action, arguments)
    gateway_jwt, connection = managed_credentials(environ, CONNECTION_ENV)
    return mark_untrusted(sender(ROUTES[action], gateway_jwt, connection, dict(arguments)))


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
