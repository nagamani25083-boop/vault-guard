#!/usr/bin/env python3
"""Managed Intercom entrypoint."""

import json
import os
import re
import sys

from connect_contract import boolean, command, enum, fields, integer, reject, text
from connect_transport import (
    ConnectFailure,
    execute,
    managed_credentials,
    mark_untrusted,
    read_command,
    write_result,
)


CONNECTION_ENV = "MEDO_CONNECT_INTERCOM"
ROUTES = {
    "list_conversations": "https://app-f58c4fdcbbpd-api-connect-intercom-list-conversations.gateway.appmedo.com/",
    "search_conversations": "https://app-f58c4fdcbbpd-api-connect-intercom-search-conversations.gateway.appmedo.com/",
    "get_conversation": "https://app-f58c4fdcbbpd-api-connect-intercom-get-conversation.gateway.appmedo.com/",
    "create_conversation": "https://app-f58c4fdcbbpd-api-connect-intercom-create-conversation.gateway.appmedo.com/",
    "reply_conversation": "https://app-f58c4fdcbbpd-api-connect-intercom-reply-conversation.gateway.appmedo.com/",
    "close_conversation": "https://app-f58c4fdcbbpd-api-connect-intercom-close-conversation.gateway.appmedo.com/",
    "reopen_conversation": "https://app-f58c4fdcbbpd-api-connect-intercom-reopen-conversation.gateway.appmedo.com/",
    "tag_conversation": "https://app-f58c4fdcbbpd-api-connect-intercom-tag-conversation.gateway.appmedo.com/",
    "list_contacts": "https://app-f58c4fdcbbpd-api-connect-intercom-list-contacts.gateway.appmedo.com/",
    "search_contacts": "https://app-f58c4fdcbbpd-api-connect-intercom-search-contacts.gateway.appmedo.com/",
    "get_contact": "https://app-f58c4fdcbbpd-api-connect-intercom-get-contact.gateway.appmedo.com/",
    "get_contact_by_external_id": "https://app-f58c4fdcbbpd-api-connect-intercom-get-contact-ext-id.gateway.appmedo.com/",
    "create_contact": "https://app-f58c4fdcbbpd-api-connect-intercom-create-contact.gateway.appmedo.com/",
    "update_contact": "https://app-f58c4fdcbbpd-api-connect-intercom-update-contact.gateway.appmedo.com/",
    "tag_contact": "https://app-f58c4fdcbbpd-api-connect-intercom-tag-contact.gateway.appmedo.com/",
    "list_companies": "https://app-f58c4fdcbbpd-api-connect-intercom-list-companies.gateway.appmedo.com/",
    "get_company": "https://app-f58c4fdcbbpd-api-connect-intercom-get-company.gateway.appmedo.com/",
    "create_or_update_company": "https://app-f58c4fdcbbpd-api-connect-intercom-upsert-company.gateway.appmedo.com/",
    "search_tickets": "https://app-f58c4fdcbbpd-api-connect-intercom-search-tickets.gateway.appmedo.com/",
    "get_ticket": "https://app-f58c4fdcbbpd-api-connect-intercom-get-ticket.gateway.appmedo.com/",
    "create_ticket": "https://app-f58c4fdcbbpd-api-connect-intercom-create-ticket.gateway.appmedo.com/",
    "update_ticket": "https://app-f58c4fdcbbpd-api-connect-intercom-update-ticket.gateway.appmedo.com/",
    "reply_ticket": "https://app-f58c4fdcbbpd-api-connect-intercom-reply-ticket.gateway.appmedo.com/",
    "list_ticket_types": "https://app-f58c4fdcbbpd-api-connect-intercom-list-ticket-types.gateway.appmedo.com/",
    "list_ticket_states": "https://app-f58c4fdcbbpd-api-connect-intercom-list-ticket-states.gateway.appmedo.com/",
    "list_articles": "https://app-f58c4fdcbbpd-api-connect-intercom-list-articles.gateway.appmedo.com/",
    "search_articles": "https://app-f58c4fdcbbpd-api-connect-intercom-search-articles.gateway.appmedo.com/",
    "get_article": "https://app-f58c4fdcbbpd-api-connect-intercom-get-article.gateway.appmedo.com/",
    "list_help_centers": "https://app-f58c4fdcbbpd-api-connect-intercom-list-help-centers.gateway.appmedo.com/",
    "list_admins": "https://app-f58c4fdcbbpd-api-connect-intercom-list-admins.gateway.appmedo.com/",
    "list_tags": "https://app-f58c4fdcbbpd-api-connect-intercom-list-tags.gateway.appmedo.com/",
    "get_counts": "https://app-f58c4fdcbbpd-api-connect-intercom-get-counts.gateway.appmedo.com/",
    "list_data_events": "https://app-f58c4fdcbbpd-api-connect-intercom-list-data-events.gateway.appmedo.com/",
    "create_data_event": "https://app-f58c4fdcbbpd-api-connect-intercom-create-data-event.gateway.appmedo.com/",
}
_WRITE_ACTIONS = {
    "create_conversation", "reply_conversation", "close_conversation",
    "reopen_conversation", "tag_conversation", "create_contact", "update_contact", "tag_contact",
    "create_or_update_company", "create_ticket", "update_ticket", "reply_ticket",
    "create_data_event",
}
_ID = re.compile(r"[A-Za-z0-9_-]{1,128}")
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_CONTACT_SEARCH = ("email", "name", "role", "contactId")
_CONVERSATION_SEARCH = ("conversationId", "state")
_TICKET_SEARCH_FIELDS = (
    "ticket_type_id", "admin_assignee_id", "team_assignee_id", "created_at",
)


def _id(arguments, name, required=False):
    value = text(arguments, name, required=required, max_length=128)
    if value is not None and not _ID.fullmatch(value):
        reject(f"{name} must be an Intercom ID")
    return value


def _email(arguments, name, required=False):
    value = text(arguments, name, required=required, max_length=320)
    if value is not None and not _EMAIL.fullmatch(value):
        reject("email must be a real address")
    return value


def _confirm(arguments):
    boolean(arguments, "confirm")
    if arguments.get("confirm") is not True:
        reject("Explicit confirmation is required")


def _require_one(arguments, names):
    if not set(names).intersection(arguments):
        reject("At least one search or identity field is required")


def _json_filter(field, value):
    return json.dumps({"field": field, "operator": "=", "value": value}, separators=(",", ":"))


def _search_contacts(arguments):
    fields(arguments, ("email", "name", "role", "contactId", "startingAfter"), ())
    _require_one(arguments, _CONTACT_SEARCH)
    enum(arguments, "role", ("user", "lead"))
    _email(arguments, "email")
    text(arguments, "name", max_length=256)
    _id(arguments, "contactId")
    text(arguments, "startingAfter", max_length=2_048)
    filters = []
    if "email" in arguments:
        filters.append({"field": "email", "operator": "=", "value": arguments["email"]})
    if "name" in arguments:
        filters.append({"field": "name", "operator": "=", "value": arguments["name"]})
    if "role" in arguments:
        filters.append({"field": "role", "operator": "=", "value": arguments["role"]})
    if "contactId" in arguments:
        filters.append({"field": "id", "operator": "=", "value": arguments["contactId"]})
    query = filters[0] if len(filters) == 1 else {"operator": "AND", "value": filters}
    sent = {"query": json.dumps(query, separators=(",", ":"))}
    if "startingAfter" in arguments:
        sent["startingAfter"] = arguments["startingAfter"]
    return sent


def _search_conversations(arguments):
    fields(
        arguments,
        ("conversationId", "state", "sortField", "sortOrder", "startingAfter"),
        (),
    )
    _require_one(arguments, _CONVERSATION_SEARCH)
    _id(arguments, "conversationId")
    enum(arguments, "state", ("open", "closed", "snoozed"))
    enum(arguments, "sortField", ("created_at", "updated_at", "waiting_since"))
    enum(arguments, "sortOrder", ("ascending", "descending"))
    text(arguments, "startingAfter", max_length=2_048)
    if "conversationId" in arguments:
        query = _json_filter("id", arguments["conversationId"])
    else:
        query = _json_filter("state", arguments["state"])
    sent = {"query": query}
    for name in ("sortField", "sortOrder", "startingAfter"):
        if name in arguments:
            sent[name] = arguments[name]
    return sent


def _create_ticket(arguments):
    allowed = ("ticketTypeId", "contactId", "email", "title", "description", "companyId", "confirm")
    fields(arguments, allowed, ("ticketTypeId", "confirm"))
    _confirm(arguments)
    _id(arguments, "ticketTypeId", required=True)
    contact_id = _id(arguments, "contactId")
    email = _email(arguments, "email")
    if contact_id is None and email is None:
        reject("A contactId or email is required")
    text(arguments, "title", max_length=1_024)
    text(arguments, "description", max_length=8_192)
    _id(arguments, "companyId")
    contact = {"id": contact_id} if contact_id else {"email": email}
    sent = {"ticketTypeId": arguments["ticketTypeId"], "contacts": [contact]}
    attributes = {}
    if "title" in arguments:
        attributes["_default_title_"] = arguments["title"]
    if "description" in arguments:
        attributes["_default_description_"] = arguments["description"]
    if attributes:
        sent["ticketAttributes"] = attributes
    if "companyId" in arguments:
        sent["companyId"] = arguments["companyId"]
    return sent


def validate(action, arguments):
    """Validate the public arguments for one fixed action."""
    if action == "list_conversations":
        fields(arguments, ("startingAfter",))
        text(arguments, "startingAfter", max_length=2_048)
    elif action == "search_conversations":
        return
    elif action == "get_conversation":
        fields(arguments, ("conversationId", "displayAs"), ("conversationId",))
        _id(arguments, "conversationId", required=True)
        enum(arguments, "displayAs", ("plaintext", "html"))
    elif action == "create_conversation":
        fields(
            arguments,
            ("body", "subject", "fromUserId", "fromContactId", "fromAdminId", "messageType", "confirm"),
            ("body", "confirm"),
        )
        _confirm(arguments)
        text(arguments, "body", required=True, max_length=10_000)
        text(arguments, "subject", max_length=256)
        _id(arguments, "fromUserId")
        _id(arguments, "fromContactId")
        _id(arguments, "fromAdminId")
        enum(arguments, "messageType", ("inapp", "email", "facebook"))
        if "fromUserId" not in arguments and "fromContactId" not in arguments:
            reject("fromUserId or fromContactId is required")
    elif action == "reply_conversation":
        fields(arguments, ("conversationId", "adminId", "text", "replyType", "confirm"),
               ("conversationId", "adminId", "text", "confirm"))
        _confirm(arguments)
        _id(arguments, "conversationId", required=True)
        _id(arguments, "adminId", required=True)
        text(arguments, "text", required=True, max_length=10_000)
        enum(arguments, "replyType", ("comment", "note"))
    elif action in {"close_conversation", "reopen_conversation"}:
        fields(arguments, ("conversationId", "adminId", "body", "confirm"),
               ("conversationId", "adminId", "confirm"))
        _confirm(arguments)
        _id(arguments, "conversationId", required=True)
        _id(arguments, "adminId", required=True)
        text(arguments, "body", max_length=10_000)
    elif action == "tag_conversation":
        fields(arguments, ("conversationId", "tagId", "adminId", "confirm"),
               ("conversationId", "tagId", "adminId", "confirm"))
        _confirm(arguments)
        _id(arguments, "conversationId", required=True)
        _id(arguments, "tagId", required=True)
        _id(arguments, "adminId", required=True)
    elif action == "list_contacts":
        fields(arguments, ("startingAfter",))
        text(arguments, "startingAfter", max_length=2_048)
    elif action == "search_contacts":
        return
    elif action == "get_contact":
        fields(arguments, ("contactId",), ("contactId",))
        _id(arguments, "contactId", required=True)
    elif action == "get_contact_by_external_id":
        fields(arguments, ("externalId",), ("externalId",))
        text(arguments, "externalId", required=True, max_length=256)
    elif action == "create_contact":
        fields(arguments, ("email", "externalId", "name", "role", "phone", "confirm"), ("confirm",))
        _confirm(arguments)
        _email(arguments, "email")
        text(arguments, "externalId", max_length=256)
        text(arguments, "name", max_length=256)
        enum(arguments, "role", ("user", "lead"))
        text(arguments, "phone", max_length=32)
        if not {"email", "externalId", "role"}.intersection(arguments):
            reject("email, externalId, or role is required")
    elif action == "update_contact":
        mutable = ("email", "externalId", "name", "role", "phone")
        fields(arguments, ("contactId", *mutable, "confirm"), ("contactId", "confirm"))
        _confirm(arguments)
        _id(arguments, "contactId", required=True)
        _email(arguments, "email")
        text(arguments, "externalId", max_length=256)
        text(arguments, "name", max_length=256)
        enum(arguments, "role", ("user", "lead"))
        text(arguments, "phone", max_length=32)
        if not set(mutable).intersection(arguments):
            reject("At least one contact change is required")
    elif action == "tag_contact":
        fields(arguments, ("contactId", "tagId", "confirm"), ("contactId", "tagId", "confirm"))
        _confirm(arguments)
        _id(arguments, "contactId", required=True)
        _id(arguments, "tagId", required=True)
    elif action == "list_companies":
        fields(arguments, ("page",))
        integer(arguments, "page", minimum=1, maximum=1_000)
    elif action == "get_company":
        fields(arguments, ("companyId",), ("companyId",))
        _id(arguments, "companyId", required=True)
    elif action == "create_or_update_company":
        fields(
            arguments,
            ("companyId", "name", "website", "industry", "plan", "size", "confirm"),
            ("confirm",),
        )
        _confirm(arguments)
        text(arguments, "companyId", max_length=256)
        text(arguments, "name", max_length=256)
        text(arguments, "website", max_length=2_048)
        text(arguments, "industry", max_length=256)
        text(arguments, "plan", max_length=128)
        integer(arguments, "size", minimum=1, maximum=10_000_000)
        if not {"companyId", "name"}.intersection(arguments):
            reject("companyId or name is required")
    elif action == "search_tickets":
        fields(arguments, ("searchField", "searchValue"), ("searchField", "searchValue"))
        enum(arguments, "searchField", _TICKET_SEARCH_FIELDS)
        text(arguments, "searchValue", required=True, max_length=512)
    elif action == "get_ticket":
        fields(arguments, ("ticketId",), ("ticketId",))
        _id(arguments, "ticketId", required=True)
    elif action == "create_ticket":
        return
    elif action == "update_ticket":
        mutable = ("open", "adminId", "assigneeId", "companyId", "ticketStateId")
        fields(arguments, ("ticketId", *mutable, "confirm"), ("ticketId", "confirm"))
        _confirm(arguments)
        _id(arguments, "ticketId", required=True)
        boolean(arguments, "open")
        integer(arguments, "adminId", minimum=1, maximum=9_007_199_254_740_991)
        _id(arguments, "assigneeId")
        _id(arguments, "companyId")
        _id(arguments, "ticketStateId")
        if not set(mutable).intersection(arguments):
            reject("At least one ticket change is required")
    elif action == "reply_ticket":
        fields(arguments, ("ticketId", "body", "messageType", "adminId", "confirm"),
               ("ticketId", "body", "confirm"))
        _confirm(arguments)
        _id(arguments, "ticketId", required=True)
        text(arguments, "body", required=True, max_length=10_000)
        enum(arguments, "messageType", ("comment", "note"))
        _id(arguments, "adminId")
    elif action in {
        "list_ticket_types", "list_ticket_states", "list_articles", "list_help_centers",
        "list_admins", "list_tags",
    }:
        fields(arguments, ())
    elif action == "search_articles":
        fields(arguments, ("phrase", "state", "helpCenterId"))
        text(arguments, "phrase", max_length=512)
        enum(arguments, "state", ("published", "draft", "all"))
        integer(arguments, "helpCenterId", minimum=1, maximum=9_007_199_254_740_991)
        if not {"phrase", "state", "helpCenterId"}.intersection(arguments):
            reject("At least one article search field is required")
    elif action == "get_article":
        fields(arguments, ("articleId",), ("articleId",))
        integer(arguments, "articleId", minimum=1, maximum=9_007_199_254_740_991)
    elif action == "get_counts":
        fields(arguments, ("countType",))
        enum(
            arguments,
            "countType",
            ("conversation", "user", "company", "lead", "tag", "segment", "contact"),
        )
    elif action == "list_data_events":
        fields(arguments, ("email", "intercomUserId"))
        _email(arguments, "email")
        _id(arguments, "intercomUserId")
        if "email" not in arguments and "intercomUserId" not in arguments:
            reject("email or intercomUserId is required")
    elif action == "create_data_event":
        fields(
            arguments,
            ("eventName", "createdAt", "email", "contactId", "confirm"),
            ("eventName", "createdAt", "confirm"),
        )
        _confirm(arguments)
        text(arguments, "eventName", required=True, max_length=256)
        integer(arguments, "createdAt", minimum=1, maximum=9_007_199_254_740_991)
        _email(arguments, "email")
        _id(arguments, "contactId")
        if "email" not in arguments and "contactId" not in arguments:
            reject("email or contactId is required")


def _gateway_arguments(action, arguments):
    if action == "search_contacts":
        return _search_contacts(arguments)
    if action == "search_conversations":
        return _search_conversations(arguments)
    if action == "create_ticket":
        return _create_ticket(arguments)
    sent = dict(arguments)
    if action in _WRITE_ACTIONS:
        sent.pop("confirm", None)
    return sent


def handle(value, environ=os.environ, sender=execute):
    """Validate and execute one managed Connect command."""
    action, arguments = command(value, ROUTES)
    if action == "search_contacts":
        sent = _search_contacts(arguments)
    elif action == "search_conversations":
        sent = _search_conversations(arguments)
    elif action == "create_ticket":
        sent = _create_ticket(arguments)
    else:
        validate(action, arguments)
        sent = _gateway_arguments(action, arguments)
    gateway_jwt, connection = managed_credentials(environ, CONNECTION_ENV)
    return mark_untrusted(sender(ROUTES[action], gateway_jwt, connection, sent))


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
