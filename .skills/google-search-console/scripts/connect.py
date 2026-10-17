#!/usr/bin/env python3
"""Managed Google Search Console entrypoint."""

import os
import re
import sys
import urllib.parse
from datetime import datetime

from connect_contract import boolean, command, enum, fields, integer, reject, text, text_list
from connect_transport import (
    ConnectFailure,
    execute,
    managed_credentials,
    mark_untrusted,
    read_command,
    write_result,
)


CONNECTION_ENV = "MEDO_CONNECT_GOOGLE_SEARCH_CONSOLE"
ROUTES = {
    "list_sites": "https://app-f58c4fdcbbpd-api-connect-google-search-console-list-sites.gateway.appmedo.com/",
    "get_site": "https://app-f58c4fdcbbpd-api-connect-google-search-console-get-site.gateway.appmedo.com/",
    "search_analytics_query": "https://app-f58c4fdcbbpd-api-connect-google-search-console-search-query.gateway.appmedo.com/",
    "inspect_url": "https://app-f58c4fdcbbpd-api-connect-google-search-console-inspect-url.gateway.appmedo.com/",
    "list_sitemaps": "https://app-f58c4fdcbbpd-api-connect-google-search-console-list-sitemap.gateway.appmedo.com/",
    "get_sitemap": "https://app-f58c4fdcbbpd-api-connect-google-search-console-get-sitemap.gateway.appmedo.com/",
    "submit_sitemap": "https://app-f58c4fdcbbpd-api-connect-google-search-console-send-sitemap.gateway.appmedo.com/",
    "add_site": "https://app-f58c4fdcbbpd-api-connect-google-search-console-add-site.gateway.appmedo.com/",
}
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DOMAIN_PROPERTY = re.compile(r"^sc-domain:[A-Za-z0-9.-]{1,253}$")
_LANGUAGE = re.compile(r"^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8}){0,3}$")
_DIMENSIONS = ("date", "query", "page", "country", "device", "searchAppearance")
_FILTER_OPERATORS = ("equals", "contains", "notContains", "includingRegex", "excludingRegex")
_WRITE_ACTIONS = {"submit_sitemap", "add_site"}


def _http_url(arguments, name, required=False):
    value = text(arguments, name, required=required, max_length=2_048)
    if value is None:
        return None
    parsed = urllib.parse.urlsplit(value)
    if (
        parsed.scheme not in ("http", "https")
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
    ):
        reject("URLs must be http or https without credentials")
    return value


def _site_url(arguments, required=False):
    value = text(arguments, "siteUrl", required=required, max_length=2_048)
    if value is None:
        return None
    if _DOMAIN_PROPERTY.fullmatch(value):
        return value
    parsed = urllib.parse.urlsplit(value)
    if (
        parsed.scheme not in ("http", "https")
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
    ):
        reject("siteUrl must be a URL-prefix property or sc-domain:host")
    return value


def _ymd(arguments, name):
    value = text(arguments, name, required=True, max_length=10)
    if not _DATE.fullmatch(value):
        reject("Dates must use YYYY-MM-DD")
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        reject("Dates must use YYYY-MM-DD")


def _analytics_window(arguments):
    start = _ymd(arguments, "startDate")
    end = _ymd(arguments, "endDate")
    if end < start or (end - start).days > 500:
        reject("Search analytics windows must be positive and no longer than 500 days")


def _dimension_filter_groups(arguments):
    if "dimensionFilterGroups" not in arguments:
        return
    groups = arguments["dimensionFilterGroups"]
    if not isinstance(groups, list) or len(groups) > 5:
        reject()
    for group in groups:
        if not isinstance(group, dict) or not set(group).issubset({"groupType", "filters"}):
            reject()
        if group.get("groupType") not in (None, "and"):
            reject()
        filters = group.get("filters")
        if not isinstance(filters, list) or not filters or len(filters) > 10:
            reject()
        for item in filters:
            if not isinstance(item, dict) or set(item) != {"dimension", "operator", "expression"}:
                reject()
            if item["dimension"] not in _DIMENSIONS or item["operator"] not in _FILTER_OPERATORS:
                reject()
            expression = item["expression"]
            if (
                not isinstance(expression, str)
                or not expression.strip()
                or len(expression) > 2_048
            ):
                reject()


def validate(action, arguments):
    """Validate the public arguments for one fixed action."""
    if action == "list_sites":
        fields(arguments, ())
    elif action == "get_site":
        fields(arguments, ("siteUrl",), ("siteUrl",))
        _site_url(arguments, required=True)
    elif action == "search_analytics_query":
        fields(
            arguments,
            (
                "siteUrl",
                "startDate",
                "endDate",
                "rowLimit",
                "startRow",
                "dataState",
                "dimensions",
                "searchType",
                "aggregationType",
                "dimensionFilterGroups",
            ),
            ("siteUrl", "startDate", "endDate"),
        )
        _site_url(arguments, required=True)
        _analytics_window(arguments)
        integer(arguments, "rowLimit", minimum=1, maximum=5_000)
        integer(arguments, "startRow", minimum=0, maximum=25_000)
        enum(arguments, "dataState", ("final", "all"))
        enum(arguments, "searchType", ("web", "image", "video", "news", "discover", "googleNews"))
        enum(arguments, "aggregationType", ("auto", "byPage", "byProperty", "byNewsShowcasePanel"))
        dimensions = text_list(arguments, "dimensions", maximum=5, item_max_length=32)
        if dimensions is not None and any(item not in _DIMENSIONS for item in dimensions):
            reject()
        _dimension_filter_groups(arguments)
    elif action == "inspect_url":
        fields(arguments, ("inspectionUrl", "siteUrl", "languageCode"), ("inspectionUrl", "siteUrl"))
        _http_url(arguments, "inspectionUrl", required=True)
        _site_url(arguments, required=True)
        language = text(arguments, "languageCode", max_length=16)
        if language is not None and not _LANGUAGE.fullmatch(language):
            reject()
    elif action == "list_sitemaps":
        fields(arguments, ("siteUrl", "sitemapIndex"), ("siteUrl",))
        _site_url(arguments, required=True)
        if "sitemapIndex" in arguments:
            _http_url(arguments, "sitemapIndex", required=True)
    elif action == "get_sitemap":
        fields(arguments, ("siteUrl", "feedpath"), ("siteUrl", "feedpath"))
        _site_url(arguments, required=True)
        _http_url(arguments, "feedpath", required=True)
    elif action == "submit_sitemap":
        fields(arguments, ("siteUrl", "feedpath", "confirm"), ("siteUrl", "feedpath", "confirm"))
        _site_url(arguments, required=True)
        _http_url(arguments, "feedpath", required=True)
        boolean(arguments, "confirm")
        if arguments.get("confirm") is not True:
            reject("Explicit confirmation is required")
    elif action == "add_site":
        fields(arguments, ("siteUrl", "confirm"), ("siteUrl", "confirm"))
        _site_url(arguments, required=True)
        boolean(arguments, "confirm")
        if arguments.get("confirm") is not True:
            reject("Explicit confirmation is required")


def handle(value, environ=os.environ, sender=execute):
    """Validate and execute one managed Connect command."""
    action, arguments = command(value, ROUTES)
    validate(action, arguments)
    safe_arguments = dict(arguments)
    if action in _WRITE_ACTIONS:
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
