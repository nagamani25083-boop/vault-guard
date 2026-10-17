#!/usr/bin/env python3
"""Managed Jira issues, projects and agile boards entrypoint."""

import json
import os
import re
import sys

from connect_contract import command, boolean, enum, fields, integer, reject, text, text_list
from connect_transport import (
    ConnectFailure,
    execute,
    managed_credentials,
    mark_untrusted,
    read_command,
    write_result,
)


CONNECTION_ENV = "MEDO_CONNECT_JIRA"
ROUTES = {
    "who_am_i": "https://app-f58c4fdcbbpd-api-connect-jira-who-am-i.gateway.appmedo.com/",
    "get_current_user": "https://app-f58c4fdcbbpd-api-connect-jira-get-current-user.gateway.appmedo.com/",
    "list_projects": "https://app-f58c4fdcbbpd-api-connect-jira-list-projects.gateway.appmedo.com/",
    "get_project": "https://app-f58c4fdcbbpd-api-connect-jira-get-project.gateway.appmedo.com/",
    "search_issues": "https://app-f58c4fdcbbpd-api-connect-jira-search-issues.gateway.appmedo.com/",
    "get_issue": "https://app-f58c4fdcbbpd-api-connect-jira-get-issue.gateway.appmedo.com/",
    "list_issue_comments": "https://app-f58c4fdcbbpd-api-connect-jira-list-issue-comments.gateway.appmedo.com/",
    "list_boards": "https://app-f58c4fdcbbpd-api-connect-jira-list-boards.gateway.appmedo.com/",
    "list_sprints": "https://app-f58c4fdcbbpd-api-connect-jira-list-sprints.gateway.appmedo.com/",
    "list_issue_types": "https://app-f58c4fdcbbpd-api-connect-jira-list-issue-types.gateway.appmedo.com/",
    "list_statuses": "https://app-f58c4fdcbbpd-api-connect-jira-list-statuses.gateway.appmedo.com/",
    "list_transitions": "https://app-f58c4fdcbbpd-api-connect-jira-list-transitions.gateway.appmedo.com/",
    "find_users": "https://app-f58c4fdcbbpd-api-connect-jira-find-users.gateway.appmedo.com/",
    "list_users": "https://app-f58c4fdcbbpd-api-connect-jira-list-users.gateway.appmedo.com/",
    "get_create_issue_meta": "https://app-f58c4fdcbbpd-api-connect-jira-get-create-meta.gateway.appmedo.com/",
    "get_issue_edit_meta": "https://app-f58c4fdcbbpd-api-connect-jira-get-edit-meta.gateway.appmedo.com/",
    "create_issue": "https://app-f58c4fdcbbpd-api-connect-jira-create-issue.gateway.appmedo.com/",
    "edit_issue": "https://app-f58c4fdcbbpd-api-connect-jira-edit-issue.gateway.appmedo.com/",
    "transition_issue": "https://app-f58c4fdcbbpd-api-connect-jira-transition-issue.gateway.appmedo.com/",
    "assign_issue": "https://app-f58c4fdcbbpd-api-connect-jira-assign-issue.gateway.appmedo.com/",
    "add_comment": "https://app-f58c4fdcbbpd-api-connect-jira-add-comment.gateway.appmedo.com/",
    "link_issues": "https://app-f58c4fdcbbpd-api-connect-jira-link-issues.gateway.appmedo.com/",
    "list_issue_link_types": "https://app-f58c4fdcbbpd-api-connect-jira-list-link-types.gateway.appmedo.com/",
}
READ_ACTIONS = (
    "who_am_i", "get_current_user", "list_projects", "get_project", "search_issues", "get_issue",
    "list_issue_comments", "list_boards", "list_sprints", "list_issue_types", "list_statuses",
    "list_transitions", "find_users", "list_users", "get_create_issue_meta", "get_issue_edit_meta",
    "list_issue_link_types",
)
WRITE_ACTIONS = (
    "create_issue", "edit_issue", "transition_issue", "assign_issue", "add_comment", "link_issues",
)
# No Jira action is destructive, so the local `confirm` marker is never used.
CONFIRMED_ACTIONS = ()
LIST_RECEIPTS = (
    "list_projects", "search_issues", "list_issue_comments", "list_boards", "list_sprints",
    "list_issue_types", "list_statuses", "list_transitions", "find_users", "list_users",
    "get_create_issue_meta", "list_issue_link_types",
)
MAX_START_AT = 100_000
MAX_SUMMARY_LENGTH = 255
MAX_TEXT_LENGTH = 32_768
MAX_JQL_LENGTH = 8_192
MAX_LIST_ITEMS = 100
_ISSUE_KEY = re.compile(r"(?:[A-Z][A-Z0-9_]{0,63}-\d{1,10}|\d{1,20})")
_PROJECT_KEY = re.compile(r"[A-Za-z0-9][A-Za-z0-9_]{0,63}")
_ACCOUNT_ID = re.compile(r"[A-Za-z0-9:_-]{1,128}")
_ID_OR_NAME = re.compile(r"(?:\d{1,20}|[^\x00-\x1f\x7f]{1,256})")
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_DATE_OR_DATETIME = re.compile(r"\d{4}-\d{2}-\d{2}([T ][0-9:.]+(Z|[+-][0-9:]+)?)?")
_UNSAFE_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
SPRINT_STATES = ("future", "active", "closed")
VISIBILITY_TYPES = ("group", "role")


def _issue_key(arguments, name="issueKey", required=True):
    """Validate one Jira issue key or numeric issue ID."""
    value = text(arguments, name, required=required, max_length=128)
    if value is not None and not _ISSUE_KEY.fullmatch(value):
        reject(f"{name} must be a Jira issue key like PROJ-123 or a numeric issue ID")
    return value


def _project_key(arguments, name, required=True):
    """Validate one Jira project key or numeric project ID."""
    value = text(arguments, name, required=required, max_length=64)
    if value is not None and not _PROJECT_KEY.fullmatch(value):
        reject(f"{name} must be a Jira project key like PROJ or a numeric project ID")
    return value


def _id_or_name(arguments, name, required=False):
    """Validate one entity reference that may be a numeric ID or a display name."""
    value = text(arguments, name, required=required, max_length=256)
    if value is not None and not _ID_OR_NAME.fullmatch(value):
        reject(f"{name} must be a numeric ID or a name from a list Action")
    return value


def _account_id(arguments, name, required=False):
    """Validate one Atlassian accountId such as 712020:..."""
    value = text(arguments, name, required=required, max_length=128)
    if value is not None and not _ACCOUNT_ID.fullmatch(value):
        reject(f"{name} must be an accountId from find_users or list_users")
    return value


def _start_at(arguments):
    """Validate the optional zero-based paging offset."""
    return integer(arguments, "startAt", minimum=0, maximum=MAX_START_AT)


def _page_token(arguments):
    """Validate an opaque cursor returned as nextPageToken."""
    return text(arguments, "pageToken", max_length=4_096)


def _date(arguments, name):
    """Validate one YYYY-MM-DD date argument."""
    value = text(arguments, name, max_length=32)
    if value is not None and not _DATE.fullmatch(value):
        reject(f"{name} must be a YYYY-MM-DD date")
    return value


def _date_or_datetime(arguments, name):
    """Validate a date or ISO datetime range filter."""
    value = text(arguments, name, max_length=64)
    if value is not None and not _DATE_OR_DATETIME.fullmatch(value):
        reject(f"{name} must be a YYYY-MM-DD date or ISO datetime")
    return value


def _multiline(arguments, name, required, max_length=MAX_TEXT_LENGTH):
    """Validate text that may contain line breaks, such as a comment body."""
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


def _text_or_adf(arguments, name):
    """Validate a description given as plain text or an Atlassian Document object."""
    if name not in arguments:
        return None
    value = arguments[name]
    if isinstance(value, str):
        if not value.strip() or len(value) > MAX_TEXT_LENGTH or _UNSAFE_CONTROL.search(value):
            reject(f"{name} must be non-empty text or a document object")
        return value
    if not isinstance(value, dict):
        reject(f"{name} must be text or an Atlassian Document object")
    try:
        encoded = json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError):
        reject(f"{name} must be valid JSON")
    if len(encoded) > MAX_TEXT_LENGTH:
        reject(f"{name} is too large")
    return value


def _name_list(arguments, name):
    """Validate a bounded list of entity names, labels or version names."""
    return text_list(arguments, name, maximum=MAX_LIST_ITEMS, item_max_length=256)


def validate(action, arguments):
    """Validate the public arguments for one fixed action."""
    if action in (
            "who_am_i", "get_current_user", "list_issue_types", "list_statuses",
            "list_issue_link_types"):
        fields(arguments, ())
    elif action == "list_projects":
        fields(arguments, ("query", "orderBy", "startAt"))
        text(arguments, "query", max_length=256)
        text(arguments, "orderBy", max_length=64)
        _start_at(arguments)
    elif action == "get_project":
        fields(arguments, ("projectIdOrKey",), ("projectIdOrKey",))
        _project_key(arguments, "projectIdOrKey")
    elif action == "search_issues":
        fields(arguments, (
            "jql", "projectKey", "statusIdOrName", "issueTypeIdOrName", "priorityIdOrName",
            "assignee", "labels", "textSearch", "createdAfter", "createdBefore", "updatedAfter",
            "updatedBefore", "sprintIdOrName", "pageToken"))
        text(arguments, "jql", max_length=MAX_JQL_LENGTH)
        _project_key(arguments, "projectKey", required=False)
        _id_or_name(arguments, "statusIdOrName")
        _id_or_name(arguments, "issueTypeIdOrName")
        _id_or_name(arguments, "priorityIdOrName")
        _id_or_name(arguments, "sprintIdOrName")
        _account_id(arguments, "assignee")
        _name_list(arguments, "labels")
        text(arguments, "textSearch", max_length=1024)
        _date_or_datetime(arguments, "createdAfter")
        _date_or_datetime(arguments, "createdBefore")
        _date_or_datetime(arguments, "updatedAfter")
        _date_or_datetime(arguments, "updatedBefore")
        _page_token(arguments)
    elif action == "get_issue":
        fields(arguments, ("issueKey",), ("issueKey",))
        _issue_key(arguments)
    elif action == "list_issue_comments":
        fields(arguments, ("issueKey", "startAt"), ("issueKey",))
        _issue_key(arguments)
        _start_at(arguments)
    elif action == "list_boards":
        fields(arguments, ("name", "type", "projectKeyOrId", "startAt"))
        text(arguments, "name", max_length=256)
        text(arguments, "type", max_length=64)
        _project_key(arguments, "projectKeyOrId", required=False)
        _start_at(arguments)
    elif action == "list_sprints":
        fields(arguments, ("boardId", "state", "startAt"), ("boardId",))
        integer(arguments, "boardId", minimum=1, maximum=2_147_483_647)
        enum(arguments, "state", SPRINT_STATES)
        _start_at(arguments)
    elif action == "list_transitions":
        fields(arguments, ("issueKey",), ("issueKey",))
        _issue_key(arguments)
    elif action == "find_users":
        fields(arguments, ("query", "accountId", "startAt"))
        query = text(arguments, "query", max_length=1024)
        account_id = _account_id(arguments, "accountId")
        if query is None and account_id is None:
            reject("find_users needs query or accountId")
        _start_at(arguments)
    elif action == "list_users":
        fields(arguments, ("startAt",))
        _start_at(arguments)
    elif action == "get_create_issue_meta":
        fields(arguments, ("projectIdOrKey", "issueTypeId", "startAt"),
               ("projectIdOrKey", "issueTypeId"))
        _project_key(arguments, "projectIdOrKey")
        _issue_key(arguments, "issueTypeId")
        _start_at(arguments)
    elif action == "get_issue_edit_meta":
        fields(arguments, ("issueKey",), ("issueKey",))
        _issue_key(arguments)
    elif action == "create_issue":
        fields(arguments, (
            "projectKey", "issueType", "summary", "description", "assignee", "assigneeName",
            "reporter", "priority", "labels", "dueDate", "parent", "sprintId", "components",
            "versions", "fixVersions"), ("projectKey", "issueType", "summary"))
        _project_key(arguments, "projectKey")
        _id_or_name(arguments, "issueType", required=True)
        text(arguments, "summary", required=True, max_length=MAX_SUMMARY_LENGTH)
        _text_or_adf(arguments, "description")
        _account_id(arguments, "assignee")
        text(arguments, "assigneeName", max_length=256)
        _account_id(arguments, "reporter")
        _id_or_name(arguments, "priority")
        _name_list(arguments, "labels")
        _date(arguments, "dueDate")
        _issue_key(arguments, "parent", required=False)
        integer(arguments, "sprintId", minimum=1, maximum=2_147_483_647)
        _name_list(arguments, "components")
        _name_list(arguments, "versions")
        _name_list(arguments, "fixVersions")
    elif action == "edit_issue":
        fields(arguments, (
            "issueKey", "summary", "description", "labels", "assignee", "dueDate",
            "priorityIdOrName", "sprintIdOrName", "notifyUsers", "returnIssue"), ("issueKey",))
        _issue_key(arguments)
        text(arguments, "summary", max_length=MAX_SUMMARY_LENGTH)
        _text_or_adf(arguments, "description")
        _name_list(arguments, "labels")
        _account_id(arguments, "assignee")
        _date(arguments, "dueDate")
        _id_or_name(arguments, "priorityIdOrName")
        _id_or_name(arguments, "sprintIdOrName")
        boolean(arguments, "notifyUsers")
        boolean(arguments, "returnIssue")
        if not any(name in arguments for name in (
                "summary", "description", "labels", "assignee", "dueDate",
                "priorityIdOrName", "sprintIdOrName")):
            reject("edit_issue needs at least one field to change")
    elif action == "transition_issue":
        fields(arguments, (
            "issueKey", "transitionIdOrName", "resolution", "comment", "assignee",
            "assigneeName"), ("issueKey", "transitionIdOrName"))
        _issue_key(arguments)
        _id_or_name(arguments, "transitionIdOrName", required=True)
        _id_or_name(arguments, "resolution")
        _multiline(arguments, "comment", required=False)
        _account_id(arguments, "assignee")
        text(arguments, "assigneeName", max_length=256)
    elif action == "assign_issue":
        fields(arguments, ("issueKey", "accountId", "assigneeName"), ("issueKey",))
        _issue_key(arguments)
        if _account_id(arguments, "accountId") is None \
                and text(arguments, "assigneeName", max_length=256) is None:
            reject("assign_issue needs accountId or assigneeName")
    elif action == "add_comment":
        fields(arguments, ("issueKey", "comment", "visibilityType", "visibilityValue"),
               ("issueKey", "comment"))
        _issue_key(arguments)
        _multiline(arguments, "comment", required=True)
        enum(arguments, "visibilityType", VISIBILITY_TYPES)
        text(arguments, "visibilityValue", max_length=256)
        if ("visibilityType" in arguments) != ("visibilityValue" in arguments):
            reject("visibilityType and visibilityValue must be supplied together")
    elif action == "link_issues":
        fields(arguments, (
            "inwardIssueKey", "outwardIssueKey", "linkType", "linkTypeId", "comment"),
            ("inwardIssueKey", "outwardIssueKey"))
        _issue_key(arguments, "inwardIssueKey")
        _issue_key(arguments, "outwardIssueKey")
        link_type = _id_or_name(arguments, "linkType")
        link_type_id = text(arguments, "linkTypeId", max_length=20)
        if link_type_id is not None and not link_type_id.isdigit():
            reject("linkTypeId must be a numeric link type ID from list_issue_link_types")
        if (link_type is None) == (link_type_id is None):
            reject("link_issues needs exactly one of linkType or linkTypeId")
        _multiline(arguments, "comment", required=False)
    else:
        reject()


def _receipt_ok(action, data):
    """Check that a successful response carries the expected business receipt."""
    if action in LIST_RECEIPTS:
        return isinstance(data.get("items"), list)
    if action == "who_am_i":
        return isinstance(data.get("sites"), list)
    if action == "get_current_user":
        return isinstance(data.get("accountId"), str)
    if action in ("get_project", "get_issue"):
        return isinstance(data.get("key"), str)
    if action == "get_issue_edit_meta":
        return isinstance(data.get("fields"), dict)
    if action == "create_issue":
        return isinstance(data.get("key"), str) and isinstance(data.get("id"), str)
    if action == "edit_issue":
        return data.get("success") is True and isinstance(data.get("issueKey"), str)
    if action in ("transition_issue", "link_issues"):
        return data.get("success") is True
    if action == "add_comment":
        return isinstance(data.get("id"), str)
    # assign_issue returns an empty body on success; the HTTP success already proved the write.
    return isinstance(data, dict)


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
                "RESULT_UNKNOWN", "The Jira change is unconfirmed; read the issue back before any retry"
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
