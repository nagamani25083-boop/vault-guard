#!/usr/bin/env python3
"""Managed Google Ads entrypoint."""

import os
import re
import sys
from datetime import datetime

from connect_contract import command, enum, fields, integer, paired, reject, text
from connect_transport import (
    ConnectFailure,
    execute,
    managed_credentials,
    mark_untrusted,
    read_command,
    write_result,
)


CONNECTION_ENV = "MEDO_CONNECT_GOOGLE_ADS"
ROUTES = {
    "list_accessible_customers": "https://app-f58c4fdcbbpd-api-connect-google-ads-list-customers.gateway.appmedo.com/",
    "list_sub_accounts": "https://app-f58c4fdcbbpd-api-connect-google-ads-list-sub-accounts.gateway.appmedo.com/",
    "get_account_report": "https://app-f58c4fdcbbpd-api-connect-google-ads-get-account-report.gateway.appmedo.com/",
    "get_campaign_report": "https://app-f58c4fdcbbpd-api-connect-google-ads-get-campaign-report.gateway.appmedo.com/",
    "get_ad_report": "https://app-f58c4fdcbbpd-api-connect-google-ads-get-ad-report.gateway.appmedo.com/",
    "get_keyword_report": "https://app-f58c4fdcbbpd-api-connect-google-ads-get-keyword-report.gateway.appmedo.com/",
    "get_campaign": "https://app-f58c4fdcbbpd-api-connect-google-ads-get-campaign.gateway.appmedo.com/",
    "get_campaign_by_name": "https://app-f58c4fdcbbpd-api-connect-google-ads-find-campaign.gateway.appmedo.com/",
    "get_conversion_tag": "https://app-f58c4fdcbbpd-api-connect-google-ads-get-conversion-tag.gateway.appmedo.com/",
    "create_conversion_action": "https://app-f58c4fdcbbpd-api-connect-google-ads-create-conversion.gateway.appmedo.com/",
    "create_campaign_budget": "https://app-f58c4fdcbbpd-api-connect-google-ads-create-budget.gateway.appmedo.com/",
    "create_search_campaign": "https://app-f58c4fdcbbpd-api-connect-google-ads-create-search-campaign.gateway.appmedo.com/",
    "update_campaign_status": "https://app-f58c4fdcbbpd-api-connect-google-ads-update-campaign-status.gateway.appmedo.com/",
    "update_campaign_budget": "https://app-f58c4fdcbbpd-api-connect-google-ads-update-campaign-budget.gateway.appmedo.com/",
    "create_ad_group": "https://app-f58c4fdcbbpd-api-connect-google-ads-create-ad-group.gateway.appmedo.com/",
    "create_responsive_search_ad": "https://app-f58c4fdcbbpd-api-connect-google-ads-create-search-ad.gateway.appmedo.com/",
    "add_campaign_location": "https://app-f58c4fdcbbpd-api-connect-google-ads-add-campaign-location.gateway.appmedo.com/",
    "create_callout_asset": "https://app-f58c4fdcbbpd-api-connect-google-ads-create-callout.gateway.appmedo.com/",
}
_WRITE_ACTIONS = {
    "create_conversion_action",
    "create_campaign_budget",
    "create_search_campaign",
    "update_campaign_status",
    "update_campaign_budget",
    "create_ad_group",
    "create_responsive_search_ad",
    "add_campaign_location",
    "create_callout_asset",
}
_REPORTS = {
    "get_account_report",
    "get_campaign_report",
    "get_ad_report",
    "get_keyword_report",
}
_CUSTOMER = re.compile(r"^\d{3}-?\d{3}-?\d{4}$")
_NUMERIC = re.compile(r"^\d{1,20}$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_CAMPAIGN_RN = re.compile(r"^customers/\d{10}/campaigns/\d{1,20}$")
_BUDGET_RN = re.compile(r"^customers/\d{10}/campaignBudgets/\d{1,20}$")
_AD_GROUP_RN = re.compile(r"^customers/\d{10}/adGroups/\d{1,20}$")
_GEO = re.compile(r"^geoTargetConstants/\d{1,10}$")
_HTTPS = re.compile(r"^https://[A-Za-z0-9.-]+(?::\d{1,5})?(?:/[^\s]*)?$")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


def _customer_id(arguments, required=True):
    value = text(arguments, "customerId", required=required, max_length=12)
    if value is None:
        return None
    if not _CUSTOMER.fullmatch(value):
        reject("customerId must be a 10-digit Google Ads customer ID")
    return value


def _ymd(arguments, name):
    value = text(arguments, name, required=True, max_length=10)
    if not _DATE.fullmatch(value):
        reject("Dates must use YYYY-MM-DD")
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        reject("Dates must use YYYY-MM-DD")


def _report_window(arguments):
    paired(arguments, "startDate", "endDate")
    if "startDate" not in arguments:
        return
    start = _ymd(arguments, "startDate")
    end = _ymd(arguments, "endDate")
    if end < start or (end - start).days > 90:
        reject("Report windows must be positive and no longer than 90 days")


def _report_arguments(arguments):
    fields(arguments, ("customerId", "startDate", "endDate", "maxRows"), ("customerId",))
    _customer_id(arguments, required=True)
    _report_window(arguments)
    integer(arguments, "maxRows", minimum=1, maximum=100)


def _confirm(arguments):
    if arguments.get("confirm") is not True:
        reject("Explicit confirmation is required")


def _resource(arguments, name, pattern, label):
    value = text(arguments, name, required=True, max_length=96)
    if not pattern.fullmatch(value):
        reject(f"{name} must be a {label} resource name")
    return value


def _amount_micros(arguments):
    value = integer(arguments, "amountMicros", minimum=10_000, maximum=10_000_000_000_000)
    if value is None:
        reject("Required arguments are missing")
    return value


def _https_urls(values, minimum, maximum):
    if not isinstance(values, list) or not minimum <= len(values) <= maximum:
        reject()
    for value in values:
        if not isinstance(value, str) or not _HTTPS.fullmatch(value) or _CONTROL.search(value):
            reject("final_urls must be https URLs")
        if "@" in value.split("://", 1)[-1].split("/", 1)[0]:
            reject("final_urls must be https URLs")


def _text_parts(values, minimum, maximum, max_length):
    if not isinstance(values, list) or not minimum <= len(values) <= maximum:
        reject()
    texts = []
    for item in values:
        if not isinstance(item, dict) or set(item) != {"text"}:
            reject()
        value = item["text"]
        if (
            not isinstance(value, str)
            or not value.strip()
            or len(value) > max_length
            or _CONTROL.search(value)
        ):
            reject()
        texts.append(value)
    if len(texts) != len(set(texts)):
        reject()


def _responsive_search_ad(arguments):
    ad = arguments.get("ad")
    if not isinstance(ad, dict) or set(ad) != {"final_urls", "responsive_search_ad"}:
        reject()
    rsa = ad.get("responsive_search_ad")
    if not isinstance(rsa, dict) or set(rsa) != {"headlines", "descriptions"}:
        reject()
    _https_urls(ad.get("final_urls"), 1, 3)
    _text_parts(rsa.get("headlines"), 3, 15, 30)
    _text_parts(rsa.get("descriptions"), 2, 4, 90)


def _location(arguments):
    location = arguments.get("location")
    if not isinstance(location, dict) or set(location) != {"geo_target_constant"}:
        reject()
    value = location.get("geo_target_constant")
    if not isinstance(value, str) or not _GEO.fullmatch(value):
        reject("location.geo_target_constant must be a geoTargetConstants ID")


def validate(action, arguments):
    """Validate the public arguments for one fixed action."""
    if action == "list_accessible_customers":
        fields(arguments, ())
    elif action == "list_sub_accounts":
        fields(arguments, ("customerId", "pageToken"), ("customerId",))
        _customer_id(arguments, required=True)
        text(arguments, "pageToken")
    elif action in _REPORTS:
        _report_arguments(arguments)
    elif action == "get_campaign":
        fields(arguments, ("customerId", "campaignId"), ("customerId", "campaignId"))
        _customer_id(arguments, required=True)
        campaign_id = text(arguments, "campaignId", required=True, max_length=20)
        if not _NUMERIC.fullmatch(campaign_id):
            reject("campaignId must be a numeric Google Ads campaign ID")
    elif action == "get_campaign_by_name":
        fields(arguments, ("customerId", "name"), ("customerId", "name"))
        _customer_id(arguments, required=True)
        text(arguments, "name", required=True, max_length=255)
    elif action == "get_conversion_tag":
        fields(arguments, ("customerId", "conversionActionId"), ("customerId", "conversionActionId"))
        _customer_id(arguments, required=True)
        conversion_id = text(arguments, "conversionActionId", required=True, max_length=20)
        if not _NUMERIC.fullmatch(conversion_id):
            reject("conversionActionId must be numeric")
    elif action == "create_conversion_action":
        fields(
            arguments,
            ("customerId", "name", "type", "category", "confirm"),
            ("customerId", "name", "type", "category", "confirm"),
        )
        _confirm(arguments)
        _customer_id(arguments, required=True)
        text(arguments, "name", required=True, max_length=255)
        enum(arguments, "type", {"WEBPAGE"})
        enum(arguments, "category", {"DEFAULT"})
    elif action == "create_campaign_budget":
        fields(arguments, ("customerId", "name", "amountMicros", "confirm"),
               ("customerId", "name", "amountMicros", "confirm"))
        _confirm(arguments)
        _customer_id(arguments, required=True)
        text(arguments, "name", required=True, max_length=255)
        _amount_micros(arguments)
    elif action == "create_search_campaign":
        fields(
            arguments,
            ("customerId", "name", "campaignBudget", "confirm"),
            ("customerId", "name", "campaignBudget", "confirm"),
        )
        _confirm(arguments)
        _customer_id(arguments, required=True)
        text(arguments, "name", required=True, max_length=255)
        _resource(arguments, "campaignBudget", _BUDGET_RN, "campaign budget")
    elif action == "update_campaign_status":
        fields(
            arguments,
            ("customerId", "campaignResourceName", "status", "confirm"),
            ("customerId", "campaignResourceName", "status", "confirm"),
        )
        _confirm(arguments)
        _customer_id(arguments, required=True)
        _resource(arguments, "campaignResourceName", _CAMPAIGN_RN, "campaign")
        enum(arguments, "status", {"ENABLED", "PAUSED"})
    elif action == "update_campaign_budget":
        fields(
            arguments,
            ("customerId", "budgetResourceName", "amountMicros", "confirm"),
            ("customerId", "budgetResourceName", "amountMicros", "confirm"),
        )
        _confirm(arguments)
        _customer_id(arguments, required=True)
        _resource(arguments, "budgetResourceName", _BUDGET_RN, "campaign budget")
        _amount_micros(arguments)
    elif action == "create_ad_group":
        fields(
            arguments,
            ("customerId", "name", "campaignResourceName", "confirm"),
            ("customerId", "name", "campaignResourceName", "confirm"),
        )
        _confirm(arguments)
        _customer_id(arguments, required=True)
        text(arguments, "name", required=True, max_length=255)
        _resource(arguments, "campaignResourceName", _CAMPAIGN_RN, "campaign")
    elif action == "create_responsive_search_ad":
        fields(
            arguments,
            ("customerId", "adGroupResourceName", "ad", "confirm"),
            ("customerId", "adGroupResourceName", "ad", "confirm"),
        )
        _confirm(arguments)
        _customer_id(arguments, required=True)
        _resource(arguments, "adGroupResourceName", _AD_GROUP_RN, "ad group")
        _responsive_search_ad(arguments)
    elif action == "add_campaign_location":
        fields(
            arguments,
            ("customerId", "campaignResourceName", "location", "confirm"),
            ("customerId", "campaignResourceName", "location", "confirm"),
        )
        _confirm(arguments)
        _customer_id(arguments, required=True)
        _resource(arguments, "campaignResourceName", _CAMPAIGN_RN, "campaign")
        _location(arguments)
    elif action == "create_callout_asset":
        fields(arguments, ("customerId", "calloutText", "confirm"),
               ("customerId", "calloutText", "confirm"))
        _confirm(arguments)
        _customer_id(arguments, required=True)
        text(arguments, "calloutText", required=True, max_length=25)


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
