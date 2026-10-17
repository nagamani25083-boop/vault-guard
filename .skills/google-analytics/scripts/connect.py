#!/usr/bin/env python3
"""Managed Google Analytics entrypoint."""

import os
import re
import sys

from connect_contract import boolean, command, fields, reject, text
from connect_transport import (
    ConnectFailure,
    execute,
    managed_credentials,
    mark_untrusted,
    read_command,
    write_result,
)


CONNECTION_ENV = "MEDO_CONNECT_GOOGLE_ANALYTICS"
ROUTES = {
    "list_properties": "https://app-f58c4fdcbbpd-api-connect-google-analytics-list-properties.gateway.appmedo.com/",
    "get_property": "https://app-f58c4fdcbbpd-api-connect-google-analytics-get-property.gateway.appmedo.com/",
    "list_data_streams": "https://app-f58c4fdcbbpd-api-connect-google-analytics-list-streams.gateway.appmedo.com/",
    "get_metadata": "https://app-f58c4fdcbbpd-api-connect-google-analytics-get-metadata.gateway.appmedo.com/",
    "run_report": "https://app-f58c4fdcbbpd-api-connect-google-analytics-run-report.gateway.appmedo.com/",
    "run_realtime_report": "https://app-f58c4fdcbbpd-api-connect-google-analytics-realtime.gateway.appmedo.com/",
}
_PROPERTY = re.compile(r"^properties/\d{1,20}$")
# GA4 field names, including custom definitions such as customEvent:plan_name.
_FIELD_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,59}(?::[A-Za-z0-9_]{1,80})?$")
_DATE = re.compile(r"^(?:\d{4}-\d{2}-\d{2}|today|yesterday|\d{1,4}daysAgo)$")
_RANGE_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,39}$")
_CURRENCY = re.compile(r"^[A-Z]{3}$")
_INT64 = re.compile(r"^-?\d{1,18}$")
# The projection returns totals only; MAXIMUM / MINIMUM would land in fields the gateway drops.
_AGGREGATIONS = ("TOTAL",)
_MATCH_TYPES = ("EXACT", "BEGINS_WITH", "ENDS_WITH", "CONTAINS", "FULL_REGEXP", "PARTIAL_REGEXP")
_NUMERIC_OPERATIONS = ("EQUAL", "LESS_THAN", "LESS_THAN_OR_EQUAL", "GREATER_THAN", "GREATER_THAN_OR_EQUAL")
_ORDER_TYPES = ("ALPHANUMERIC", "CASE_INSENSITIVE_ALPHANUMERIC", "NUMERIC")
_FILTER_DEPTH = 3


def _property(arguments):
    value = text(arguments, "property", required=True, max_length=40)
    if not _PROPERTY.fullmatch(value):
        reject("property must look like properties/123456789; copy it from list_properties")
    return value


def _field_name(value):
    if not isinstance(value, str) or not _FIELD_NAME.fullmatch(value):
        reject("Dimension and metric names must be GA4 API names; check get_metadata")
    return value


def _named_list(arguments, name, maximum, minimum=0):
    if name not in arguments:
        if minimum:
            reject(f"{name} is required")
        return
    items = arguments[name]
    if not isinstance(items, list) or not 1 <= len(items) <= maximum:
        reject(f"{name} must be a list of 1 to {maximum} items")
    seen = set()
    for item in items:
        if not isinstance(item, dict) or set(item) != {"name"}:
            reject(f'{name} items look like {{"name": "sessions"}}')
        if _field_name(item["name"]) in seen:
            reject(f"{name} must not repeat a name")
        seen.add(item["name"])


def _numeric_value(value):
    if not isinstance(value, dict) or len(value) != 1:
        reject("Numeric values are {\"int64Value\": \"10\"} or {\"doubleValue\": 1.5}")
    (kind, number), = value.items()
    if kind == "int64Value":
        if not isinstance(number, str) or not _INT64.fullmatch(number):
            reject("int64Value is a string of digits")
    elif kind == "doubleValue":
        if isinstance(number, bool) or not isinstance(number, (int, float)):
            reject("doubleValue is a number")
    else:
        reject("Numeric values are int64Value or doubleValue")


def _filter(spec):
    if not isinstance(spec, dict) or "fieldName" not in spec or len(spec) != 2:
        reject("A filter has fieldName and exactly one condition")
    _field_name(spec["fieldName"])
    (kind, condition), = ((key, value) for key, value in spec.items() if key != "fieldName")
    if not isinstance(condition, dict):
        reject("Filter conditions are objects")
    if kind == "stringFilter":
        if not set(condition).issubset({"matchType", "value", "caseSensitive"}) or "value" not in condition:
            reject("stringFilter takes value, matchType, and caseSensitive")
        if not isinstance(condition["value"], str) or len(condition["value"]) > 1_000:
            reject("stringFilter.value is text up to 1000 characters")
        if condition.get("matchType", "EXACT") not in _MATCH_TYPES:
            reject("Unsupported stringFilter.matchType")
        if not isinstance(condition.get("caseSensitive", False), bool):
            reject("caseSensitive is true or false")
    elif kind == "inListFilter":
        if not set(condition).issubset({"values", "caseSensitive"}):
            reject("inListFilter takes values and caseSensitive")
        values = condition.get("values")
        if (
            not isinstance(values, list)
            or not 1 <= len(values) <= 100
            or not all(isinstance(item, str) and len(item) <= 1_000 for item in values)
        ):
            reject("inListFilter.values is a list of 1 to 100 strings")
        if not isinstance(condition.get("caseSensitive", False), bool):
            reject("caseSensitive is true or false")
    elif kind == "numericFilter":
        if set(condition) != {"operation", "value"} or condition["operation"] not in _NUMERIC_OPERATIONS:
            reject("numericFilter takes operation and value")
        _numeric_value(condition["value"])
    elif kind == "betweenFilter":
        if set(condition) != {"fromValue", "toValue"}:
            reject("betweenFilter takes fromValue and toValue")
        _numeric_value(condition["fromValue"])
        _numeric_value(condition["toValue"])
    elif kind == "emptyFilter":
        if condition:
            reject("emptyFilter is an empty object")
    else:
        reject("Unsupported filter condition")


def _filter_expression(value, depth=0):
    if depth > _FILTER_DEPTH or not isinstance(value, dict) or len(value) != 1:
        reject(f"Filter expressions have one key and nest at most {_FILTER_DEPTH} levels")
    (kind, inner), = value.items()
    if kind in ("andGroup", "orGroup"):
        expressions = inner.get("expressions") if isinstance(inner, dict) and set(inner) == {"expressions"} else None
        if not isinstance(expressions, list) or not 1 <= len(expressions) <= 10:
            reject(f"{kind}.expressions is a list of 1 to 10 expressions")
        for expression in expressions:
            _filter_expression(expression, depth + 1)
    elif kind == "notExpression":
        _filter_expression(inner, depth + 1)
    elif kind == "filter":
        _filter(inner)
    else:
        reject("Filter expressions are andGroup, orGroup, notExpression, or filter")


def _filters(arguments):
    for name in ("dimensionFilter", "metricFilter"):
        if name in arguments:
            _filter_expression(arguments[name])


def _order_bys(arguments):
    if "orderBys" not in arguments:
        return
    orders = arguments["orderBys"]
    if not isinstance(orders, list) or not 1 <= len(orders) <= 5:
        reject("orderBys is a list of 1 to 5 orders")
    for order in orders:
        if not isinstance(order, dict) or not set(order).issubset({"desc", "metric", "dimension"}):
            reject("An order has desc and one of metric or dimension")
        if ("metric" in order) == ("dimension" in order):
            reject("An order sorts by one metric or one dimension")
        if not isinstance(order.get("desc", False), bool):
            reject("desc is true or false")
        if "metric" in order:
            metric = order["metric"]
            if not isinstance(metric, dict) or set(metric) != {"metricName"}:
                reject('Metric orders look like {"metric": {"metricName": "sessions"}}')
            _field_name(metric["metricName"])
        else:
            dimension = order["dimension"]
            if not isinstance(dimension, dict) or not set(dimension).issubset({"dimensionName", "orderType"}):
                reject('Dimension orders look like {"dimension": {"dimensionName": "date"}}')
            _field_name(dimension.get("dimensionName"))
            if dimension.get("orderType", "ALPHANUMERIC") not in _ORDER_TYPES:
                reject("Unsupported dimension orderType")


def _aggregations(arguments):
    if "metricAggregations" not in arguments:
        return
    values = arguments["metricAggregations"]
    if (
        not isinstance(values, list)
        or not 1 <= len(values) <= len(_AGGREGATIONS)
        or len(set(values)) != len(values)
        or any(value not in _AGGREGATIONS for value in values)
    ):
        reject('metricAggregations is ["TOTAL"]')


def _date_ranges(arguments):
    ranges = arguments.get("dateRanges")
    if not isinstance(ranges, list) or not 1 <= len(ranges) <= 4:
        reject("dateRanges is a list of 1 to 4 ranges")
    for item in ranges:
        if not isinstance(item, dict) or not {"startDate", "endDate"}.issubset(item):
            reject("Each date range has startDate and endDate")
        if not set(item).issubset({"startDate", "endDate", "name"}):
            reject("Date ranges take startDate, endDate, and name")
        for key in ("startDate", "endDate"):
            if not isinstance(item[key], str) or not _DATE.fullmatch(item[key]):
                reject("Dates are YYYY-MM-DD, today, yesterday, or NdaysAgo")
        if "name" in item and (not isinstance(item["name"], str) or not _RANGE_NAME.fullmatch(item["name"])):
            reject("Date range names are letters, digits, and underscores")


def _minute_ranges(arguments):
    if "minuteRanges" not in arguments:
        return
    ranges = arguments["minuteRanges"]
    if not isinstance(ranges, list) or not 1 <= len(ranges) <= 2:
        reject("minuteRanges is a list of 1 or 2 ranges")
    for item in ranges:
        if not isinstance(item, dict) or not set(item).issubset({"startMinutesAgo", "endMinutesAgo", "name"}):
            reject("Minute ranges take startMinutesAgo, endMinutesAgo, and name")
        for key in ("startMinutesAgo", "endMinutesAgo"):
            if key in item and (
                isinstance(item[key], bool) or not isinstance(item[key], int) or not 0 <= item[key] <= 59
            ):
                reject("Minute offsets are whole minutes from 0 to 59")
        if "name" in item and (not isinstance(item["name"], str) or not _RANGE_NAME.fullmatch(item["name"])):
            reject("Minute range names are letters, digits, and underscores")


def _report_fields(arguments):
    if "dimensions" not in arguments and "metrics" not in arguments:
        reject("A report needs at least one dimension or metric")
    _named_list(arguments, "dimensions", 9)
    _named_list(arguments, "metrics", 10)
    _filters(arguments)
    _order_bys(arguments)
    _aggregations(arguments)


def validate(action, arguments):
    """Validate the public arguments for one fixed action."""
    if action == "list_properties":
        fields(arguments, ("pageToken",))
        text(arguments, "pageToken", max_length=2_048)
    elif action in ("get_property", "get_metadata"):
        fields(arguments, ("property",), ("property",))
        _property(arguments)
    elif action == "list_data_streams":
        fields(arguments, ("property", "pageToken"), ("property",))
        _property(arguments)
        text(arguments, "pageToken", max_length=2_048)
    elif action == "run_report":
        fields(
            arguments,
            (
                "property", "dateRanges", "dimensions", "metrics", "dimensionFilter", "metricFilter",
                "orderBys", "rowOffset", "keepEmptyRows", "metricAggregations", "currencyCode",
            ),
            ("property", "dateRanges"),
        )
        _property(arguments)
        _date_ranges(arguments)
        _report_fields(arguments)
        offset = arguments.get("rowOffset", 0)
        if type(offset) is not int or not 0 <= offset <= 100_000:
            reject("rowOffset is an integer from 0 to 100000")
        boolean(arguments, "keepEmptyRows")
        currency = text(arguments, "currencyCode", max_length=3)
        if currency is not None and not _CURRENCY.fullmatch(currency):
            reject("currencyCode is an ISO 4217 code such as USD")
    elif action == "run_realtime_report":
        fields(
            arguments,
            (
                "property", "dimensions", "metrics", "dimensionFilter", "metricFilter", "orderBys",
                "minuteRanges", "metricAggregations",
            ),
            ("property",),
        )
        _property(arguments)
        _report_fields(arguments)
        _minute_ranges(arguments)


def handle(value, environ=os.environ, sender=execute):
    """Validate and execute one managed Connect command."""
    action, arguments = command(value, ROUTES)
    validate(action, arguments)
    safe_arguments = dict(arguments)
    if action == "get_metadata":
        # The metadata Tool names the resource properties/<id>/metadata.
        safe_arguments = {"metadataName": f"{safe_arguments.pop('property')}/metadata"}
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
