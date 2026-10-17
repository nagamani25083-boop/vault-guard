#!/usr/bin/env python3
"""Managed Figma entrypoint: read files, tokens, components, styles, images and interactions."""

import json
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


CONNECTION_ENV = "MEDO_CONNECT_FIGMA"
ROUTES = {
    "get_current_user": "https://app-f58c4fdcbbpd-api-connect-figma-get-current-user.gateway.appmedo.com/",
    "discover_resources": "https://app-f58c4fdcbbpd-api-connect-figma-discover-resources.gateway.appmedo.com/",
    "list_team_projects": "https://app-f58c4fdcbbpd-api-connect-figma-list-team-projects.gateway.appmedo.com/",
    "list_project_files": "https://app-f58c4fdcbbpd-api-connect-figma-list-project-files.gateway.appmedo.com/",
    "get_file_metadata": "https://app-f58c4fdcbbpd-api-connect-figma-get-file-metadata.gateway.appmedo.com/",
    "get_file_content": "https://app-f58c4fdcbbpd-api-connect-figma-get-file-content.gateway.appmedo.com/",
    "get_file_nodes": "https://app-f58c4fdcbbpd-api-connect-figma-get-file-nodes.gateway.appmedo.com/",
    "render_node_images": "https://app-f58c4fdcbbpd-api-connect-figma-render-node-images.gateway.appmedo.com/",
    "get_image_fills": "https://app-f58c4fdcbbpd-api-connect-figma-get-image-fills.gateway.appmedo.com/",
    "extract_design_tokens": "https://app-f58c4fdcbbpd-api-connect-figma-extract-design-tokens.gateway.appmedo.com/",
    "tokens_to_tailwind": "https://app-f58c4fdcbbpd-api-connect-figma-tokens-to-tailwind.gateway.appmedo.com/",
    "list_file_styles": "https://app-f58c4fdcbbpd-api-connect-figma-list-file-styles.gateway.appmedo.com/",
    "list_file_components": "https://app-f58c4fdcbbpd-api-connect-figma-list-file-components.gateway.appmedo.com/",
    "list_file_component_sets": "https://app-f58c4fdcbbpd-api-connect-figma-list-file-component-sets.gateway.appmedo.com/",
    "get_component_detail": "https://app-f58c4fdcbbpd-api-connect-figma-get-component-detail.gateway.appmedo.com/",
    "get_component_set": "https://app-f58c4fdcbbpd-api-connect-figma-get-component-set.gateway.appmedo.com/",
    "get_style": "https://app-f58c4fdcbbpd-api-connect-figma-get-style.gateway.appmedo.com/",
    "list_team_components": "https://app-f58c4fdcbbpd-api-connect-figma-list-team-components.gateway.appmedo.com/",
    "list_team_component_sets": "https://app-f58c4fdcbbpd-api-connect-figma-list-team-component-sets.gateway.appmedo.com/",
    "list_team_styles": "https://app-f58c4fdcbbpd-api-connect-figma-list-team-styles.gateway.appmedo.com/",
    "list_prototype_interactions": "https://app-f58c4fdcbbpd-api-connect-figma-list-prototype-interactions.gateway.appmedo.com/",
}
# The launch scope is read-only: comments, webhooks, dev resources, variables and writes stay out.
READ_ACTIONS = tuple(ROUTES)
MAX_NODE_IDS = 50
MAX_DEPTH = 64
MAX_PAGE_SIZE = 100
MAX_TOKENS_BYTES = 256 * 1024
_FILE_KEY = re.compile(r"[A-Za-z0-9]{8,64}")
_ASSET_KEY = re.compile(r"[0-9a-f]{10,64}")
_NUMERIC_ID = re.compile(r"[0-9]{1,20}")
_NODE_ID = re.compile(r"[0-9A-Za-z;]+:[0-9A-Za-z:;_-]+")
_IMAGE_FORMATS = ("png", "jpg", "svg", "pdf")
_CONFIG_FORMATS = ("js", "ts", "mjs", "cjs")


def _file_key(arguments, name="fileKey", required=True):
    """Validate one Figma file key copied from a URL or an API response."""
    value = text(arguments, name, required=required, max_length=64)
    if value is not None and not _FILE_KEY.fullmatch(value):
        reject(f"{name} must be the file key from a Figma URL")
    return value


def _asset_key(arguments, name):
    """Validate one published component, component set or style key."""
    value = text(arguments, name, required=True, max_length=64)
    if not _ASSET_KEY.fullmatch(value):
        reject(f"{name} must be the key of a published library item")
    return value


def _team_id(arguments):
    """Validate the numeric Figma team ID passed as a string."""
    value = text(arguments, "teamId", required=True, max_length=20)
    if not _NUMERIC_ID.fullmatch(value):
        reject("teamId must be the numeric team ID string")
    return value


def _node_ids(arguments, required):
    """Validate 1–50 Figma node IDs and send them upstream comma-joined."""
    if "nodeIds" not in arguments:
        if required:
            reject("Required arguments are missing")
        return None
    values = text_list(arguments, "nodeIds", maximum=MAX_NODE_IDS, item_max_length=64)
    if not values:
        reject("nodeIds cannot be empty")
    if any(not _NODE_ID.fullmatch(value) for value in values):
        reject("nodeIds must contain node IDs such as \"1:2\"")
    return ",".join(values)


def _geometry(arguments):
    """Validate the optional geometry selector."""
    enum(arguments, "geometry", ("paths",))


def _page(arguments):
    """Validate optional list paging: bounded pageSize and integer cursors."""
    integer(arguments, "pageSize", minimum=1, maximum=MAX_PAGE_SIZE)
    integer(arguments, "after", minimum=0, maximum=2**63 - 1)
    integer(arguments, "before", minimum=0, maximum=2**63 - 1)


def _figma_url(arguments):
    """Validate an optional figma.com URL used to discover file, node, team or project IDs."""
    value = text(arguments, "figmaUrl", max_length=2_048)
    if value is None:
        return None
    try:
        parsed = urllib.parse.urlsplit(value)
        port = parsed.port
        host = parsed.hostname or ""
    except ValueError:
        reject("figmaUrl must be an https://www.figma.com/ link")
    if (
        parsed.scheme != "https"
        or parsed.username is not None
        or parsed.password is not None
        or port not in (None, 443)
        or not (host == "figma.com" or host.endswith(".figma.com"))
    ):
        reject("figmaUrl must be an https://www.figma.com/ link")
    return value


def _scale(arguments):
    """Validate the optional render scale inside Figma's 0.01–4 range."""
    if "scale" not in arguments:
        return
    value = arguments["scale"]
    if type(value) not in (int, float) or not 0.01 <= value <= 4:
        reject("scale must be a number between 0.01 and 4")


def _tokens(arguments):
    """Validate the design-token payload for Tailwind conversion."""
    if "tokens" not in arguments:
        reject("Required arguments are missing")
    value = arguments["tokens"]
    if not isinstance(value, dict):
        reject("tokens must be the JSON object returned by extract_design_tokens")
    try:
        encoded = json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError):
        reject("tokens must be valid JSON")
    if len(encoded) > MAX_TOKENS_BYTES:
        reject("tokens is too large")
    return value


def validate(action, arguments):
    """Validate the public arguments for one fixed action."""
    if action == "get_current_user":
        fields(arguments, ())
    elif action == "discover_resources":
        fields(arguments, ("figmaUrl", "fileKey", "nodeDepth", "teamId", "projectId"))
        _figma_url(arguments)
        _file_key(arguments, required=False)
        integer(arguments, "nodeDepth", minimum=1, maximum=MAX_DEPTH)
        if "teamId" in arguments:
            team = text(arguments, "teamId", max_length=20)
            if team is not None and not _NUMERIC_ID.fullmatch(team):
                reject("teamId must be the numeric team ID string")
        if "projectId" in arguments:
            text(arguments, "projectId", max_length=64)
    elif action == "list_team_projects":
        fields(arguments, ("teamId",), ("teamId",))
        _team_id(arguments)
    elif action == "list_project_files":
        fields(arguments, ("projectId",), ("projectId",))
        text(arguments, "projectId", required=True, max_length=64)
    elif action in ("get_file_metadata", "get_image_fills", "list_file_styles",
                    "list_file_components", "list_file_component_sets"):
        fields(arguments, ("fileKey",), ("fileKey",))
        _file_key(arguments)
    elif action in ("get_file_content", "get_file_nodes"):
        fields(arguments, ("fileKey", "nodeIds", "depth", "geometry"), ("fileKey",))
        _file_key(arguments)
        node_ids = _node_ids(arguments, required=(action == "get_file_nodes"))
        if node_ids is not None:
            arguments["nodeIds"] = node_ids
        integer(arguments, "depth", minimum=1, maximum=MAX_DEPTH)
        _geometry(arguments)
    elif action == "render_node_images":
        fields(arguments, ("fileKey", "nodeIds", "format", "scale", "contentsOnly"),
               ("fileKey", "nodeIds"))
        _file_key(arguments)
        node_ids = _node_ids(arguments, required=True)
        arguments["nodeIds"] = node_ids
        enum(arguments, "format", _IMAGE_FORMATS)
        _scale(arguments)
        boolean(arguments, "contentsOnly")
    elif action == "extract_design_tokens":
        fields(arguments, ("fileKey", "extractFromNodes", "includeLocalStyles"), ("fileKey",))
        _file_key(arguments)
        boolean(arguments, "extractFromNodes")
        boolean(arguments, "includeLocalStyles")
    elif action == "tokens_to_tailwind":
        fields(arguments, ("tokens", "prefix", "configFormat", "includeFontImports"), ("tokens",))
        _tokens(arguments)
        text(arguments, "prefix", max_length=128)
        enum(arguments, "configFormat", _CONFIG_FORMATS)
        boolean(arguments, "includeFontImports")
    elif action == "get_component_detail":
        fields(arguments, ("componentKey",), ("componentKey",))
        _asset_key(arguments, "componentKey")
    elif action == "get_component_set":
        fields(arguments, ("componentSetKey",), ("componentSetKey",))
        _asset_key(arguments, "componentSetKey")
    elif action == "get_style":
        fields(arguments, ("styleKey",), ("styleKey",))
        _asset_key(arguments, "styleKey")
    elif action in ("list_team_components", "list_team_component_sets", "list_team_styles"):
        fields(arguments, ("teamId", "after", "before", "pageSize"), ("teamId",))
        _team_id(arguments)
        _page(arguments)
    elif action == "list_prototype_interactions":
        fields(arguments, ("fileKey", "analyzeComponents", "includeAnimations"), ("fileKey",))
        _file_key(arguments)
        boolean(arguments, "analyzeComponents")
        boolean(arguments, "includeAnimations")
    else:
        reject()


def handle(value, environ=os.environ, sender=execute):
    """Validate and execute one managed Connect command."""
    action, arguments = command(value, ROUTES)
    safe_arguments = dict(arguments)
    validate(action, safe_arguments)
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
