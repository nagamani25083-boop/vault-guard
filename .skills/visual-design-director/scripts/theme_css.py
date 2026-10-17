#!/usr/bin/env python3
"""Baseline theme css lookup — shared by theme_search.py (Step 1) and
design_system.py (Step 3).

Both paths can hit a named template from data/theme.xlsx. When they do, the
coding agent should start from a palette that already matches the template
instead of inventing one, so we copy the vetted baseline css over the
scaffold's style entry file.

Baselines live in data/css/<stack>/<template>.<ext> and exist for the two stacks
this skill covers: vite (.css) and taro (.scss). Game / Frontend Game / Mobile
App are outside the skill's scope, so they have none by design. All were derived
from production output and checked against the matching scaffold contract — bare
HSL triplets throughout, and per stack: vite keeps @tailwind directives / @layer
base / border-border / body base styles, taro keeps the @use 'tailwindcss/*'
head plus a `page` base rule and avoids what weapp cannot render
(backdrop-filter, background-clip:text, ::-webkit-scrollbar).

Everything here is best-effort: callers must not let the result change their
exit code.
"""

from __future__ import annotations

import sys
from pathlib import Path

CSS_DIR = Path(__file__).resolve().parent.parent / "data" / "css"


def css_key(template_name: str) -> str:
    """Template title → baseline filename stem: the title's UTF-8 bytes as hex.

    Template titles are Chinese and some runtimes can't handle non-ASCII paths,
    so filenames are pure ASCII. hex is chosen over a hash or the xlsx data.id
    because it is reversible (``bytes.fromhex(stem).decode()`` gives the title
    back) and derived from nothing but the title — no lookup table to keep in
    sync with theme.xlsx. data/css/vite/index.json maps stem → title for
    humans; it is not read here.
    """
    return str(template_name or "").strip().encode("utf-8").hex()


# PRD app_type → frontend stack. The stack, not the app_type, decides the style
# entry file. Mirrors _APP_TYPE_TO_XLSX in theme_search.py.
#
# Game / Frontend Game / Mobile App are out of this skill's scope per SKILL.md,
# so they get no baseline: Game isn't listed at all (stack_for → '') and the
# "mobile app" row is kept only to mirror theme_search.py — expo has no entry in
# _STACK_ENTRY, so it resolves to skipped_stack.
_APP_TYPE_TO_STACK = {
    "web": "vite",
    "h5": "vite",
    "tool": "vite",
    "frontend tool": "vite",
    "questionnaire": "vite",
    "others": "vite",
    "mini program": "taro",
    "miniprogram": "taro",
    "mobile app": "expo",
}

# Stack → style entry path relative to the app workspace root.
# Only stacks listed here get a baseline written.
_STACK_ENTRY = {
    "vite": ("src", "index.css"),
    "taro": ("src", "app.scss"),
}

# Stack → baseline file extension. Taro's entry is sass, so the data files are
# .scss; vite's is plain css.
_STACK_EXT = {
    "vite": "css",
    "taro": "scss",
}


def stack_for(app_type: str) -> str:
    """Map PRD app_type to frontend stack name ('' when unknown)."""
    return _APP_TYPE_TO_STACK.get(str(app_type or "").strip().lower(), "")


def app_root_for(output_path) -> Path:
    """Derive the app workspace root from the DESIGN.md path.

    Resolution order, first match wins:
      1. nearest ancestor named ``app-*`` — the workspace root by convention,
         so any --output shape under it lands the css correctly
      2. ``<root>/docs/DESIGN.md`` — the documented layout, root is docs' parent
      3. otherwise treat the file's own directory as the root

    No layout is rejected: callers asked for the css to always be written.
    """
    out = Path(output_path).resolve()
    for parent in out.parents:
        if parent.name.startswith("app-"):
            return parent
    if out.parent.name == "docs":
        return out.parent.parent
    return out.parent


def write_theme_css(template_name: str, app_type: str, output_path, log_prefix: str):
    """Write the baseline theme css for template_name over the scaffold entry.

    The workspace root is derived from output_path (the DESIGN.md path) via
    ``app_root_for``, so no extra CLI argument is needed.

    Returns (state, entry_path, css_text) where state is one of:
      written        — baseline found and written to entry_path
      absent         — this template has no baseline css yet
      skipped_stack  — stack has no baseline support (taro/expo) or unknown app_type
      skipped_no_out — output_path missing, so the workspace root is unknown
      failed         — baseline exists but writing raised (reason on stderr)
    """
    if not output_path:
        return "skipped_no_out", None, None

    stack = stack_for(app_type)
    entry_parts = _STACK_ENTRY.get(stack)
    if entry_parts is None:
        return "skipped_stack", None, None

    src = CSS_DIR / stack / f"{css_key(template_name)}.{_STACK_EXT[stack]}"
    if not src.is_file():
        print(
            f"{log_prefix} no {stack} baseline css yet for template {template_name!r}, skipping",
            file=sys.stderr,
        )
        return "absent", None, None

    entry = app_root_for(output_path).joinpath(*entry_parts)
    try:
        css_text = src.read_text(encoding="utf-8")
        entry.parent.mkdir(parents=True, exist_ok=True)
        entry.write_text(css_text, encoding="utf-8")
    except OSError as e:
        print(f"{log_prefix} failed to write css (DESIGN.md unaffected): {e}", file=sys.stderr)
        return "failed", None, None

    print(f"{log_prefix} theme css written to {entry}", file=sys.stderr)
    return "written", entry, css_text


def format_css_block(state: str, entry_path, css_text) -> list:
    """Stdout lines echoing the written css, so the agent needn't read the file."""
    if state != "written":
        return []
    return [
        "",
        f"--- baseline theme css written to {entry_path} — begin ---",
        css_text,
        f"--- baseline theme css written to {entry_path} — end ---",
    ]
