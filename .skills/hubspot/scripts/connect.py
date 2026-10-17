#!/usr/bin/env python3
"""Managed HubSpot CRM and automation entrypoint."""

import os
import re
import sys
from datetime import date, datetime

from connect_contract import boolean, command, enum, fields, integer, reject, text
from connect_transport import (
    ConnectFailure,
    execute,
    managed_credentials,
    mark_untrusted,
    read_command,
    write_result,
)

CONNECTION_ENV = "MEDO_CONNECT_HUBSPOT"
ROUTES = {
    "search_contacts": "https://app-f58c4fdcbbpd-api-connect-hubspot-search-contacts.gateway.appmedo.com/",
    "list_contacts": "https://app-f58c4fdcbbpd-api-connect-hubspot-list-contacts.gateway.appmedo.com/",
    "get_contact": "https://app-f58c4fdcbbpd-api-connect-hubspot-get-contact.gateway.appmedo.com/",
    "create_contact": "https://app-f58c4fdcbbpd-api-connect-hubspot-create-contact.gateway.appmedo.com/",
    "update_contact": "https://app-f58c4fdcbbpd-api-connect-hubspot-update-contact.gateway.appmedo.com/",
    "search_companies": "https://app-f58c4fdcbbpd-api-connect-hubspot-search-companies.gateway.appmedo.com/",
    "list_companies": "https://app-f58c4fdcbbpd-api-connect-hubspot-list-companies.gateway.appmedo.com/",
    "get_company": "https://app-f58c4fdcbbpd-api-connect-hubspot-get-company.gateway.appmedo.com/",
    "create_company": "https://app-f58c4fdcbbpd-api-connect-hubspot-create-company.gateway.appmedo.com/",
    "update_company": "https://app-f58c4fdcbbpd-api-connect-hubspot-update-company.gateway.appmedo.com/",
    "search_deals": "https://app-f58c4fdcbbpd-api-connect-hubspot-search-deals.gateway.appmedo.com/",
    "list_deals": "https://app-f58c4fdcbbpd-api-connect-hubspot-list-deals.gateway.appmedo.com/",
    "get_deal": "https://app-f58c4fdcbbpd-api-connect-hubspot-get-deal.gateway.appmedo.com/",
    "create_deal": "https://app-f58c4fdcbbpd-api-connect-hubspot-create-deal.gateway.appmedo.com/",
    "update_deal": "https://app-f58c4fdcbbpd-api-connect-hubspot-update-deal.gateway.appmedo.com/",
    "search_tickets": "https://app-f58c4fdcbbpd-api-connect-hubspot-search-tickets.gateway.appmedo.com/",
    "list_tickets": "https://app-f58c4fdcbbpd-api-connect-hubspot-list-tickets.gateway.appmedo.com/",
    "get_ticket": "https://app-f58c4fdcbbpd-api-connect-hubspot-get-ticket.gateway.appmedo.com/",
    "create_ticket": "https://app-f58c4fdcbbpd-api-connect-hubspot-create-ticket.gateway.appmedo.com/",
    "update_ticket": "https://app-f58c4fdcbbpd-api-connect-hubspot-update-ticket.gateway.appmedo.com/",
    "list_owners": "https://app-f58c4fdcbbpd-api-connect-hubspot-list-owners.gateway.appmedo.com/",
    "list_pipelines": "https://app-f58c4fdcbbpd-api-connect-hubspot-list-pipelines.gateway.appmedo.com/",
    "get_pipeline": "https://app-f58c4fdcbbpd-api-connect-hubspot-get-pipeline.gateway.appmedo.com/",
    "create_pipeline": "https://app-f58c4fdcbbpd-api-connect-hubspot-create-pipeline.gateway.appmedo.com/",
    "update_pipeline": "https://app-f58c4fdcbbpd-api-connect-hubspot-update-pipeline.gateway.appmedo.com/",
    "create_pipeline_stage": "https://app-f58c4fdcbbpd-api-connect-hubspot-create-pipeline-stage.gateway.appmedo.com/",
    "update_pipeline_stage": "https://app-f58c4fdcbbpd-api-connect-hubspot-update-pipeline-stage.gateway.appmedo.com/",
    "list_properties": "https://app-f58c4fdcbbpd-api-connect-hubspot-list-properties.gateway.appmedo.com/",
    "list_associations": "https://app-f58c4fdcbbpd-api-connect-hubspot-list-associations.gateway.appmedo.com/",
    "list_association_types": "https://app-f58c4fdcbbpd-api-connect-hubspot-list-association-types.gateway.appmedo.com/",
    "create_association": "https://app-f58c4fdcbbpd-api-connect-hubspot-create-association.gateway.appmedo.com/",
    "create_note": "https://app-f58c4fdcbbpd-api-connect-hubspot-create-note.gateway.appmedo.com/",
    "get_note": "https://app-f58c4fdcbbpd-api-connect-hubspot-get-note.gateway.appmedo.com/",
    "get_list": "https://app-f58c4fdcbbpd-api-connect-hubspot-get-list.gateway.appmedo.com/",
    "create_list": "https://app-f58c4fdcbbpd-api-connect-hubspot-create-list.gateway.appmedo.com/",
    "list_list_members": "https://app-f58c4fdcbbpd-api-connect-hubspot-list-list-members.gateway.appmedo.com/",
    "list_workflows": "https://app-f58c4fdcbbpd-api-connect-hubspot-list-workflows.gateway.appmedo.com/",
    "get_workflow": "https://app-f58c4fdcbbpd-api-connect-hubspot-get-workflow.gateway.appmedo.com/",
    "create_workflow": "https://app-f58c4fdcbbpd-api-connect-hubspot-create-workflow.gateway.appmedo.com/",
    "update_workflow": "https://app-f58c4fdcbbpd-api-connect-hubspot-update-workflow.gateway.appmedo.com/",
    "enroll_contact": "https://app-f58c4fdcbbpd-api-connect-hubspot-enroll-contact.gateway.appmedo.com/",
    "list_campaigns": "https://app-f58c4fdcbbpd-api-connect-hubspot-list-campaigns.gateway.appmedo.com/",
    "get_campaign": "https://app-f58c4fdcbbpd-api-connect-hubspot-get-campaign.gateway.appmedo.com/",
    "get_campaign_metrics": "https://app-f58c4fdcbbpd-api-connect-hubspot-get-campaign-metrics.gateway.appmedo.com/",
}

# Writable record fields: public name -> HubSpot property (used in search filters and responses).
RECORD_FIELDS = {
    "contact": {
        "firstname": "firstname", "lastname": "lastname", "email": "email", "phone": "phone",
        "company": "company", "jobtitle": "jobtitle", "lifecyclestage": "lifecyclestage",
        "leadStatus": "hs_lead_status", "ownerId": "hubspot_owner_id",
    },
    "company": {
        "name": "name", "domain": "domain", "industry": "industry", "city": "city", "state": "state",
        "country": "country", "numberofemployees": "numberofemployees", "annualrevenue": "annualrevenue",
        "phone": "phone", "description": "description", "ownerId": "hubspot_owner_id",
    },
    "deal": {
        "dealname": "dealname", "amount": "amount", "dealstage": "dealstage", "pipeline": "pipeline",
        "closedate": "closedate", "ownerId": "hubspot_owner_id", "description": "description",
        "dealtype": "dealtype",
    },
    "ticket": {
        "subject": "subject", "content": "content", "pipeline": "hs_pipeline",
        "pipelineStage": "hs_pipeline_stage", "priority": "hs_ticket_priority",
        "ownerId": "hubspot_owner_id", "sourceType": "source_type",
    },
}
CREATE_REQUIRED = {
    "contact": ("email",),
    "company": ("name",),
    "deal": ("dealname", "pipeline", "dealstage"),
    "ticket": ("subject", "pipeline", "pipelineStage"),
}
# Properties the gateway returns for each record type; search filters and sorts stay inside them.
SEARCH_PROPERTIES = {
    "contact": ("hs_object_id", "firstname", "lastname", "email", "phone", "company", "lifecyclestage",
                "createdate", "lastmodifieddate", "jobtitle", "hs_lead_status", "hubspot_owner_id"),
    "company": ("hs_object_id", "name", "domain", "industry", "city", "state", "country",
                "numberofemployees", "annualrevenue", "hs_lastmodifieddate", "phone", "description",
                "hubspot_owner_id"),
    "deal": ("hs_object_id", "dealname", "amount", "dealstage", "pipeline", "closedate", "createdate",
             "hs_lastmodifieddate", "hubspot_owner_id", "description", "dealtype"),
    "ticket": ("hs_object_id", "subject", "content", "hs_pipeline", "hs_pipeline_stage",
               "hs_ticket_priority", "hubspot_owner_id", "createdate", "hs_lastmodifieddate", "source_type"),
}
RECORD_ACTIONS = {
    f"{verb}_{name}": kind
    for kind, plural in (("contact", "contacts"), ("company", "companies"), ("deal", "deals"), ("ticket", "tickets"))
    for verb, name in (("search", plural), ("list", plural), ("get", kind), ("create", kind), ("update", kind))
}
ID_FIELD = {"contact": "contactId", "company": "companyId", "deal": "dealId", "ticket": "ticketId"}
CRM_OBJECTS = ("contacts", "companies", "deals", "tickets")
ASSOCIATION_OBJECTS = CRM_OBJECTS + ("notes",)
PIPELINE_OBJECTS = ("deals", "tickets")
FILTER_OPERATORS = (
    "EQ", "NEQ", "LT", "LTE", "GT", "GTE", "HAS_PROPERTY", "NOT_HAS_PROPERTY",
    "CONTAINS_TOKEN", "NOT_CONTAINS_TOKEN", "IN", "NOT_IN", "BETWEEN",
)
LIST_FILTER_PROPERTIES = ("email", "firstname", "lastname", "company", "city")
PROBABILITIES = tuple(f"{step / 10:.1f}" for step in range(11))
# update_workflow sends these keys; the gateway pins type, schedules, blocked dates, custom settings and Salesforce.
WORKFLOW_KEYS = (
    "name", "description", "actions", "isEnabled", "revisionId", "startActionId", "enrollmentCriteria",
    "suppressionListIds",
)
WORKFLOW_REQUIRED = tuple(key for key in WORKFLOW_KEYS if key != "description")
# A read is written back only with these values; the gateway always sends them this way.
WORKFLOW_PINNED = {"type": "CONTACT_FLOW", "timeWindows": [], "blockedDates": [], "customProperties": {},
                   "canEnrollFromSalesforce": False}
WORKFLOW_EMPTY = ("uuid", "enrollmentSchedule", "unEnrollmentSetting", "eventAnchor", "goalFilterBranch",
                  "suppressionFilterBranch", "dataSources")
_NUMERIC_ID = re.compile(r"[0-9]{1,32}")
_KEY = re.compile(r"[A-Za-z0-9_-]{1,128}")
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_MAX_SAFE_INTEGER = 9_007_199_254_740_991


def _numeric_id(arguments, name, required=True):
    """Validate a HubSpot numeric ID sent as a string."""
    value = text(arguments, name, required=required, max_length=32)
    if value is not None and not _NUMERIC_ID.fullmatch(value):
        reject(f"{name} must be a HubSpot numeric ID string")
    return value


def _key(arguments, name, required=True):
    """Validate an ID that may be a slug, such as a pipeline or stage ID."""
    value = text(arguments, name, required=required, max_length=128)
    if value is not None and not _KEY.fullmatch(value):
        reject(f"{name} must be a HubSpot ID")
    return value


def _email(arguments, name="email", required=False):
    """Validate an email address argument."""
    value = text(arguments, name, required=required, max_length=320)
    if value is not None and not _EMAIL.fullmatch(value):
        reject("email must be a real address")
    return value


def _value(value, max_length=2_048, allow_empty=False):
    """Validate one bounded string value."""
    if not isinstance(value, str) or len(value) > max_length or (not allow_empty and not value.strip()):
        reject()
    return value


def _record_fields(arguments, kind, allow_empty):
    """Validate the writable record fields of one record type."""
    for name in RECORD_FIELDS[kind]:
        if name in arguments:
            _value(arguments[name], max_length=65_536 if name in ("content", "description") else 2_000,
                   allow_empty=allow_empty)
    if "email" in arguments and arguments["email"]:
        _email(arguments)
    for name in ("ownerId",):
        if name in arguments and arguments[name]:
            _numeric_id(arguments, name)


def _filter_groups(groups, properties):
    """Validate CRM search filter groups."""
    if not isinstance(groups, list) or not 1 <= len(groups) <= 3:
        reject("filterGroups must contain one to three groups")
    for group in groups:
        if not isinstance(group, dict) or set(group) != {"filters"}:
            reject()
        filters = group["filters"]
        if not isinstance(filters, list) or not 1 <= len(filters) <= 6:
            reject("Each filter group must contain one to six filters")
        for item in filters:
            _filter(item, properties)


def _filter(item, properties):
    """Validate one search filter against its operator."""
    if not isinstance(item, dict) or item.get("propertyName") not in properties:
        reject("Filters use a returned property of this record type")
    operator = item.get("operator")
    if operator not in FILTER_OPERATORS:
        reject()
    if operator in ("HAS_PROPERTY", "NOT_HAS_PROPERTY"):
        expected = set()
    elif operator in ("IN", "NOT_IN"):
        expected = {"values"}
    elif operator == "BETWEEN":
        expected = {"value", "highValue"}
    else:
        expected = {"value"}
    if set(item) != {"propertyName", "operator"} | expected:
        reject("Filter values do not match the operator")
    for name in expected & {"value", "highValue"}:
        _value(item[name], allow_empty=True)
    if "values" in expected:
        values = item["values"]
        if not isinstance(values, list) or not 1 <= len(values) <= 100:
            reject()
        for value in values:
            _value(value, max_length=256, allow_empty=True)


def _search(arguments, kind, sortable):
    """Validate a CRM search request."""
    allowed = ("query", "after", "filterGroups") + (("sort",) if sortable else ())
    fields(arguments, allowed)
    if not {"query", "filterGroups", "sort"} & set(arguments):
        reject("Search requires query, filterGroups or sort")
    text(arguments, "query", max_length=2_048)
    text(arguments, "after", max_length=2_048)
    if "filterGroups" in arguments:
        _filter_groups(arguments["filterGroups"], SEARCH_PROPERTIES[kind])
    if "sort" in arguments:
        sort = arguments["sort"]
        if (
            not isinstance(sort, list)
            or len(sort) != 1
            or not isinstance(sort[0], dict)
            or set(sort[0]) != {"propertyName", "direction"}
            or sort[0]["propertyName"] not in SEARCH_PROPERTIES[kind]
            or sort[0]["direction"] not in ("ASCENDING", "DESCENDING")
        ):
            reject("sort is one {propertyName, direction} object")


def _stage_metadata(metadata, object_type, required):
    """Validate pipeline stage metadata for deals or tickets."""
    if metadata is None:
        if required:
            reject("Stage metadata is required")
        return
    if not isinstance(metadata, dict) or not metadata:
        reject()
    if object_type == "deals":
        if set(metadata) - {"probability", "isClosed"} or metadata.get("probability") not in PROBABILITIES:
            reject("Deal stages require probability from 0.0 to 1.0")
    else:
        if set(metadata) - {"ticketState", "isClosed"} or metadata.get("ticketState") not in ("OPEN", "CLOSED"):
            reject("Ticket stages require ticketState OPEN or CLOSED")
    if "isClosed" in metadata and metadata["isClosed"] not in ("true", "false"):
        reject()


def _display_order(arguments, required):
    """Validate a pipeline or stage display order."""
    if required and "displayOrder" not in arguments:
        reject("Required arguments are missing")
    integer(arguments, "displayOrder", minimum=0, maximum=10_000)


def _filter_branch(branch):
    """Contact list grammar: OR of up to three AND branches of text PROPERTY filters."""
    if (
        not isinstance(branch, dict)
        or set(branch) - {"filterBranchType", "filterBranchOperator"} != {"filters", "filterBranches"}
        or branch.get("filterBranchType") != "OR"
        or branch.get("filterBranchOperator", "OR") != "OR"
        or branch["filters"] != []
        or not isinstance(branch["filterBranches"], list)
        or not 1 <= len(branch["filterBranches"]) <= 3
    ):
        reject("filterBranch is an OR branch of one to three AND branches")
    for child in branch["filterBranches"]:
        if (
            not isinstance(child, dict)
            or set(child) - {"filterBranchType", "filterBranchOperator"} != {"filters", "filterBranches"}
            or child.get("filterBranchType") != "AND"
            or child.get("filterBranchOperator", "AND") != "AND"
            or child["filterBranches"] != []
            or not isinstance(child["filters"], list)
            or not 1 <= len(child["filters"]) <= 6
        ):
            reject("Each AND branch holds one to six filters")
        for item in child["filters"]:
            operation = item.get("operation") if isinstance(item, dict) else None
            if (
                not isinstance(operation, dict)
                or set(item) != {"filterType", "property", "operation"}
                or item["filterType"] != "PROPERTY"
                or item["property"] not in LIST_FILTER_PROPERTIES
                or set(operation) - {"includeObjectsWithNoValueSet"} != {"operationType", "operator", "values"}
                or operation["operationType"] != "MULTISTRING"
                or operation["operator"] not in ("IS_EQUAL_TO", "IS_NOT_EQUAL_TO")
                or type(operation.get("includeObjectsWithNoValueSet", False)) is not bool
                or not isinstance(operation["values"], list)
                or not 1 <= len(operation["values"]) <= 20
            ):
                reject("List filters are text PROPERTY filters with MULTISTRING equality")
            for value in operation["values"]:
                _value(value, max_length=256)


def _enrollment(criteria):
    """Validate MANUAL or LIST_BASED workflow enrollment criteria."""
    if not isinstance(criteria, dict) or type(criteria.get("shouldReEnroll")) is not bool:
        reject("enrollmentCriteria needs shouldReEnroll")
    if criteria.get("type") == "MANUAL":
        if set(criteria) != {"type", "shouldReEnroll"}:
            reject()
        return
    expected = {
        "type", "shouldReEnroll", "listFilterBranch", "unEnrollObjectsNotMeetingCriteria",
        "reEnrollmentTriggersFilterBranches",
    }
    if (
        criteria.get("type") != "LIST_BASED"
        or set(criteria) != expected
        or type(criteria["unEnrollObjectsNotMeetingCriteria"]) is not bool
        or criteria["reEnrollmentTriggersFilterBranches"] != []
    ):
        reject("enrollmentCriteria is MANUAL or LIST_BASED")
    _filter_branch(criteria["listFilterBranch"])


def _workflow_actions(actions, start):
    """Only linear contact delay (0-1) and create-task (0-3) nodes are supported."""
    if not isinstance(actions, list) or not 1 <= len(actions) <= 20:
        reject("A workflow has one to twenty actions")
    nodes = {}
    for node in actions:
        if (
            not isinstance(node, dict)
            or set(node) - {"connection"} != {"actionId", "type", "actionTypeVersion", "actionTypeId", "fields"}
            or not isinstance(node["actionId"], str)
            or not _NUMERIC_ID.fullmatch(node["actionId"])
            or node["actionId"] in nodes
            or node["type"] != "SINGLE_CONNECTION"
            or type(node["actionTypeVersion"]) is not int
            or node["actionTypeVersion"] != 0
            or not isinstance(node["fields"], dict)
        ):
            reject("Workflow actions are linear SINGLE_CONNECTION nodes")
        _workflow_fields(node["actionTypeId"], node["fields"])
        if "connection" in node:
            connection = node["connection"]
            if (
                not isinstance(connection, dict)
                or set(connection) != {"edgeType", "nextActionId"}
                or connection["edgeType"] != "STANDARD"
                or not isinstance(connection["nextActionId"], str)
            ):
                reject()
        nodes[node["actionId"]] = node
    seen = []
    current = start
    while current is not None:
        if current not in nodes or current in seen:
            reject("Workflow actions must form one chain from startActionId")
        seen.append(current)
        current = nodes[current].get("connection", {}).get("nextActionId")
    if len(seen) != len(nodes):
        reject("Every workflow action must be reachable from startActionId")
    return nodes


def _workflow_fields(action_type, values):
    """Validate the fields of a delay or create-task step."""
    if action_type == "0-1":
        if (
            set(values) != {"delta", "time_unit"}
            or not isinstance(values["delta"], str)
            or not values["delta"].isdigit()
            or int(values["delta"]) < 1
            or values["time_unit"] not in ("MINUTES", "HOURS", "DAYS")
        ):
            reject("Delay steps need a positive string delta and MINUTES/HOURS/DAYS")
        return
    association = [{
        "target": {"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 10},
        "value": {"type": "ENROLLED_OBJECT"},
    }]
    if (
        action_type != "0-3"
        or set(values) != {"task_type", "subject", "body", "associations", "use_explicit_associations", "priority"}
        or values["task_type"] not in ("TODO", "CALL", "EMAIL")
        or values["priority"] not in ("NONE", "LOW", "MEDIUM", "HIGH")
        or values["use_explicit_associations"] != "true"
        or values["associations"] != association
    ):
        reject("Only delay (0-1) and create-task (0-3) steps are supported")
    _value(values["subject"], max_length=512)
    _value(values["body"], max_length=65_536, allow_empty=True)


def _create_workflow(arguments):
    """Validate a new disabled workflow."""
    fields(
        arguments,
        ("name", "description", "actions", "startActionId", "nextAvailableActionId", "enrollmentCriteria"),
        ("name", "actions", "startActionId", "nextAvailableActionId", "enrollmentCriteria"),
    )
    text(arguments, "name", required=True, max_length=256)
    if "description" in arguments:
        _value(arguments["description"], max_length=4_096, allow_empty=True)
    nodes = _workflow_actions(arguments["actions"], _numeric_id(arguments, "startActionId"))
    next_id = _numeric_id(arguments, "nextAvailableActionId")
    if next_id in nodes or int(next_id) <= max(int(node) for node in nodes):
        reject("nextAvailableActionId must be greater than every action ID")
    _enrollment(arguments["enrollmentCriteria"])


def _workflow_definition(workflow):
    """A complete, supported definition; anything else must stay unchanged in HubSpot."""
    if (
        type(workflow.get("isEnabled")) is not bool
        or not isinstance(workflow.get("revisionId"), str)
        or not _NUMERIC_ID.fullmatch(workflow["revisionId"])
        or not isinstance(workflow.get("startActionId"), str)
    ):
        reject("Send the complete workflow definition from updateDefinition")
    _value(workflow["name"], max_length=256)
    if workflow.get("description") is not None:
        _value(workflow["description"], max_length=4_096, allow_empty=True)
    suppression = workflow["suppressionListIds"]
    if (
        not isinstance(suppression, list)
        or len(suppression) > 50
        or any(type(item) is not int or not 0 < item <= _MAX_SAFE_INTEGER for item in suppression)
    ):
        reject()
    _workflow_actions(workflow["actions"], workflow["startActionId"])
    _enrollment(workflow["enrollmentCriteria"])


def editable_workflow(data):
    """Return the update definition for a supported read, or None when HubSpot must edit it."""
    if not isinstance(data, dict):
        return None
    if any(data.get(key) != value for key, value in WORKFLOW_PINNED.items()):
        return None
    if any(data.get(key) not in (None, []) for key in WORKFLOW_EMPTY):
        return None
    workflow = {key: data[key] for key in WORKFLOW_KEYS if data.get(key) is not None}
    if set(workflow) < set(WORKFLOW_REQUIRED):
        return None
    try:
        _workflow_definition(workflow)
    except ConnectFailure:
        return None
    return workflow


def _iso_date(arguments, name):
    """Validate and parse a YYYY-MM-DD date."""
    value = text(arguments, name, required=True, max_length=10)
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        reject(f"{name} must be YYYY-MM-DD")
    if parsed.isoformat() != value:
        reject(f"{name} must be YYYY-MM-DD")
    return parsed


def _timestamp(arguments):
    """Validate a note timestamp."""
    value = arguments.get("timestamp")
    if type(value) is int and 0 < value <= _MAX_SAFE_INTEGER:
        return
    value = text(arguments, "timestamp", required=True, max_length=64)
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError:
        reject("timestamp is ISO-8601 with a timezone or Unix milliseconds")
    if parsed.utcoffset() is None:
        reject("timestamp is ISO-8601 with a timezone or Unix milliseconds")


def validate(action, arguments):
    """Validate the public arguments for one fixed action."""
    kind = RECORD_ACTIONS.get(action)
    if action.startswith("search_") and kind:
        _search(arguments, kind, sortable=kind != "ticket")
    elif action.startswith("list_") and kind:
        fields(arguments, ("after",))
        text(arguments, "after", max_length=2_048)
    elif action.startswith("get_") and kind:
        fields(arguments, (ID_FIELD[kind],), (ID_FIELD[kind],))
        _numeric_id(arguments, ID_FIELD[kind])
    elif action.startswith("create_") and kind:
        fields(arguments, tuple(RECORD_FIELDS[kind]), CREATE_REQUIRED[kind])
        _record_fields(arguments, kind, allow_empty=False)
        if kind == "contact":
            _email(arguments, required=True)
    elif action.startswith("update_") and kind:
        fields(arguments, (ID_FIELD[kind],) + tuple(RECORD_FIELDS[kind]), (ID_FIELD[kind],))
        _numeric_id(arguments, ID_FIELD[kind])
        if len(arguments) < 2:
            reject("At least one field change is required")
        _record_fields(arguments, kind, allow_empty=True)
    elif action == "list_owners":
        fields(arguments, ("after",))
        text(arguments, "after", max_length=2_048)
    elif action == "list_pipelines":
        fields(arguments, ("objectType",), ("objectType",))
        enum(arguments, "objectType", PIPELINE_OBJECTS)
    elif action == "get_pipeline":
        fields(arguments, ("objectType", "pipelineId"), ("objectType", "pipelineId"))
        enum(arguments, "objectType", PIPELINE_OBJECTS)
        _key(arguments, "pipelineId")
    elif action == "create_pipeline":
        fields(arguments, ("objectType", "label", "displayOrder", "stages"),
               ("objectType", "label", "displayOrder", "stages"))
        enum(arguments, "objectType", PIPELINE_OBJECTS)
        text(arguments, "label", required=True, max_length=256)
        _display_order(arguments, required=True)
        stages = arguments["stages"]
        if not isinstance(stages, list) or not 1 <= len(stages) <= 50:
            reject("A pipeline has one to fifty stages")
        for stage in stages:
            if not isinstance(stage, dict) or set(stage) != {"label", "displayOrder", "metadata"}:
                reject()
            text(stage, "label", required=True, max_length=256)
            _display_order(stage, required=True)
            _stage_metadata(stage["metadata"], arguments["objectType"], required=True)
    elif action == "update_pipeline":
        fields(arguments, ("objectType", "pipelineId", "label", "displayOrder"), ("objectType", "pipelineId"))
        enum(arguments, "objectType", PIPELINE_OBJECTS)
        _key(arguments, "pipelineId")
        text(arguments, "label", max_length=256)
        _display_order(arguments, required=False)
        if len(arguments) < 3:
            reject("At least one pipeline change is required")
    elif action in ("create_pipeline_stage", "update_pipeline_stage"):
        creating = action == "create_pipeline_stage"
        base = ("objectType", "pipelineId") + (() if creating else ("stageId",))
        fields(arguments, base + ("label", "displayOrder", "metadata"),
               base + (("label", "displayOrder", "metadata") if creating else ()))
        enum(arguments, "objectType", PIPELINE_OBJECTS)
        _key(arguments, "pipelineId")
        if not creating:
            _key(arguments, "stageId")
            if len(arguments) == len(base):
                reject("At least one stage change is required")
        text(arguments, "label", required=creating, max_length=256)
        _display_order(arguments, required=creating)
        _stage_metadata(arguments.get("metadata"), arguments["objectType"], required=creating)
    elif action == "list_properties":
        fields(arguments, ("objectType",), ("objectType",))
        enum(arguments, "objectType", CRM_OBJECTS)
    elif action == "list_associations":
        fields(arguments, ("objectType", "objectId", "toObjectType", "after"),
               ("objectType", "objectId", "toObjectType"))
        enum(arguments, "objectType", ASSOCIATION_OBJECTS)
        enum(arguments, "toObjectType", ASSOCIATION_OBJECTS)
        _numeric_id(arguments, "objectId")
        text(arguments, "after", max_length=2_048)
    elif action == "list_association_types":
        fields(arguments, ("fromObjectType", "toObjectType"), ("fromObjectType", "toObjectType"))
        enum(arguments, "fromObjectType", ASSOCIATION_OBJECTS)
        enum(arguments, "toObjectType", ASSOCIATION_OBJECTS)
    elif action == "create_association":
        required = ("objectType", "objectId", "toObjectType", "toObjectId", "labels")
        fields(arguments, required, required)
        enum(arguments, "objectType", ASSOCIATION_OBJECTS)
        enum(arguments, "toObjectType", ASSOCIATION_OBJECTS)
        _numeric_id(arguments, "objectId")
        _numeric_id(arguments, "toObjectId")
        labels = arguments["labels"]
        if not isinstance(labels, list) or not 1 <= len(labels) <= 20:
            reject()
        for label in labels:
            if (
                not isinstance(label, dict)
                or set(label) != {"associationCategory", "associationTypeId"}
                or label["associationCategory"] not in ("HUBSPOT_DEFINED", "USER_DEFINED")
                or type(label["associationTypeId"]) is not int
                or not 1 <= label["associationTypeId"] <= 2_147_483_647
            ):
                reject("Build each label from a list_association_types id with associationCategory HUBSPOT_DEFINED")
    elif action == "create_note":
        fields(arguments, ("body", "timestamp", "ownerId"), ("body", "timestamp"))
        text(arguments, "body", required=True, max_length=65_536)
        _timestamp(arguments)
        _numeric_id(arguments, "ownerId", required=False)
    elif action == "get_note":
        fields(arguments, ("noteId",), ("noteId",))
        _numeric_id(arguments, "noteId")
    elif action == "get_list":
        fields(arguments, ("listId",), ("listId",))
        _numeric_id(arguments, "listId")
    elif action == "create_list":
        fields(arguments, ("name", "processingType", "filterBranch"), ("name", "processingType"))
        text(arguments, "name", required=True, max_length=256)
        enum(arguments, "processingType", ("MANUAL", "DYNAMIC"))
        if arguments["processingType"] == "DYNAMIC":
            if "filterBranch" not in arguments:
                reject("DYNAMIC lists require filterBranch")
            _filter_branch(arguments["filterBranch"])
        elif "filterBranch" in arguments:
            reject("MANUAL lists do not take filterBranch")
    elif action == "list_list_members":
        fields(arguments, ("listId", "after"), ("listId",))
        _numeric_id(arguments, "listId")
        text(arguments, "after", max_length=2_048)
    elif action == "list_workflows":
        fields(arguments, ())
    elif action == "get_workflow":
        fields(arguments, ("flowId",), ("flowId",))
        _numeric_id(arguments, "flowId")
    elif action == "create_workflow":
        _create_workflow(arguments)
    elif action == "update_workflow":
        fields(arguments, ("flowId",) + WORKFLOW_KEYS, ("flowId",) + WORKFLOW_REQUIRED)
        _numeric_id(arguments, "flowId")
        _workflow_definition({key: value for key, value in arguments.items() if key != "flowId"})
    elif action == "enroll_contact":
        fields(arguments, ("workflowId", "email"), ("workflowId", "email"))
        _numeric_id(arguments, "workflowId")
        _email(arguments, required=True)
    elif action == "list_campaigns":
        fields(arguments, ("after",))
        text(arguments, "after", max_length=2_048)
    elif action == "get_campaign":
        fields(arguments, ("campaignId",), ("campaignId",))
        _key(arguments, "campaignId")
    elif action == "get_campaign_metrics":
        fields(arguments, ("campaignId", "startDate", "endDate"), ("campaignId", "startDate", "endDate"))
        _key(arguments, "campaignId")
        start = _iso_date(arguments, "startDate")
        end = _iso_date(arguments, "endDate")
        if start > end or (end - start).days > 366:
            reject("Metrics need startDate <= endDate within 366 days")
    else:
        reject()


def _needs_confirmation(action, arguments):
    """Enrollment and enabling a workflow change live automation, so both need explicit confirmation."""
    return action == "enroll_contact" or (
        action == "update_workflow" and arguments["isEnabled"] is True
    )


def _receipt_ok(action, data):
    """Check that a successful response carries the expected business receipt."""
    if action == "enroll_contact":
        return data.get("accepted") is True
    if action in ("create_list", "get_list"):
        return isinstance(data.get("listId"), str) and bool(data["listId"])
    if action == "create_association":
        return all(
            (isinstance(data.get(name), str) and _NUMERIC_ID.fullmatch(data[name]))
            or (type(data.get(name)) is int and 0 < data[name] <= _MAX_SAFE_INTEGER)
            for name in ("fromObjectId", "toObjectId")
        )
    if action == "get_campaign_metrics":
        return all(
            type(data.get(name)) in (int, float)
            for name in ("sessions", "influencedContacts", "newContactsFirstTouch", "newContactsLastTouch")
        )
    if action.startswith(("list_", "search_")):
        return isinstance(data.get("items"), list)
    return isinstance(data.get("id"), (str, int)) and data["id"] not in ("", 0)


def handle(value, environ=os.environ, sender=execute):
    """Validate and execute one managed Connect command."""
    action, arguments = command(value, ROUTES)
    safe_arguments = dict(arguments)
    confirm = safe_arguments.pop("confirm", None)
    validate(action, safe_arguments)
    if _needs_confirmation(action, safe_arguments):
        if confirm is not True:
            raise ConnectFailure("ACTION_NOT_ALLOWED", "Explicit confirmation is required")
    elif "confirm" in arguments:
        raise ConnectFailure("ACTION_NOT_ALLOWED", "Confirmation is not used for this action")
    gateway_jwt, connection = managed_credentials(environ, CONNECTION_ENV)
    result = sender(ROUTES[action], gateway_jwt, connection, safe_arguments)
    data = result.get("data") if isinstance(result, dict) else None
    if not (isinstance(data, dict) and result.get("successful") is True and _receipt_ok(action, data)):
        raise ConnectFailure("RESULT_UNKNOWN", "Read back the HubSpot resource before retrying")
    if action in ("get_workflow", "create_workflow", "update_workflow"):
        editable = editable_workflow(data)
        data["editable"] = editable is not None
        data["updateDefinition"] = editable
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
