"""Small, dependency-free validators shared by the managed Connect Skills."""

import re
from datetime import datetime, timedelta

from connect_transport import ConnectFailure


_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_A1 = re.compile(
    r"^(?:(?:'(?:[^']|'')+'|[A-Za-z0-9_.-]+)!)?"
    r"\$?([A-Za-z]{1,3})\$?([1-9][0-9]*)"
    r"(?::\$?([A-Za-z]{1,3})\$?([1-9][0-9]*))?$"
)


def reject(message="The requested action or arguments are not allowed"):
    """Raise a stable validation failure."""
    raise ConnectFailure("ACTION_NOT_ALLOWED", message)


def command(value, routes):
    """Validate the command envelope and select a fixed action."""
    if not isinstance(value, dict) or set(value) != {"action", "arguments"}:
        reject()
    action = value.get("action")
    arguments = value.get("arguments")
    if not isinstance(action, str) or action not in routes or not isinstance(arguments, dict):
        reject()
    return action, arguments


def fields(arguments, allowed, required=()):
    """Validate allowed and required argument names."""
    if not isinstance(arguments, dict) or not set(arguments).issubset(set(allowed)):
        reject()
    missing = [name for name in required if name not in arguments]
    if missing:
        reject("Required arguments are missing")


def text(arguments, name, required=False, max_length=4096):
    """Validate and return one text argument."""
    if name not in arguments:
        if required:
            reject("Required arguments are missing")
        return None
    value = arguments[name]
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > max_length
        or _CONTROL.search(value)
    ):
        reject()
    return value


_MARKDOWN_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def markdown(arguments, name, required=False, max_length=50_000):
    """Validate markdown that may contain newlines and tabs."""
    if name not in arguments:
        if required:
            reject("Required arguments are missing")
        return None
    value = arguments[name]
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > max_length
        or _MARKDOWN_CONTROL.search(value)
    ):
        reject()
    return value


def replacement_text(arguments, name, required=False, max_length=8_192):
    """Validate replacement text that may be empty but never contains controls."""
    if name not in arguments:
        if required:
            reject("Required arguments are missing")
        return None
    value = arguments[name]
    if not isinstance(value, str) or len(value) > max_length or _CONTROL.search(value):
        reject()
    return value


def boolean(arguments, name):
    """Validate an optional boolean argument."""
    if name in arguments and type(arguments[name]) is not bool:
        reject()


def integer(arguments, name, minimum=1, maximum=10_000_000):
    """Validate and return one bounded integer argument."""
    if name not in arguments:
        return None
    value = arguments[name]
    if type(value) is not int or value < minimum or value > maximum:
        reject()
    return value


def enum(arguments, name, values):
    """Validate an optional argument against fixed values."""
    if name in arguments and arguments[name] not in values:
        reject()


def text_list(arguments, name, maximum, item_max_length=1024, unique=True):
    """Validate and return a bounded list of safe strings."""
    if name not in arguments:
        return None
    values = arguments[name]
    if not isinstance(values, list) or len(values) > maximum:
        reject()
    for value in values:
        if (
            not isinstance(value, str)
            or not value.strip()
            or len(value) > item_max_length
            or _CONTROL.search(value)
        ):
            reject()
    if unique and len(values) != len(set(values)):
        reject()
    return values


def paired(arguments, first, second):
    """Require two optional arguments to appear together."""
    if (first in arguments) != (second in arguments):
        reject("Paired arguments must be supplied together")


def calendar_window(arguments, first="timeMin", second="timeMax", required=False):
    """Validate a positive RFC 3339 window of at most 31 days."""
    if required:
        fields(arguments, arguments.keys(), (first, second))
    paired(arguments, first, second)
    if first not in arguments:
        return
    start = _rfc3339(text(arguments, first, required=True, max_length=64))
    end = _rfc3339(text(arguments, second, required=True, max_length=64))
    if end <= start or end - start > timedelta(days=31):
        reject("Calendar time windows must be positive and no longer than 31 days")


def _rfc3339(value):
    try:
        normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        reject("Calendar times must use RFC 3339")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        reject("Calendar times must include a timezone")
    return parsed


def a1_cell_count(value):
    """Validate a bounded A1 range and calculate its dimensions."""
    start_column, start_row, end_column, end_row = _a1_bounds(value)
    cells = (end_column - start_column + 1) * (end_row - start_row + 1)
    if cells > 10_000:
        reject("A range cannot exceed 10,000 cells")
    return cells, end_column - start_column + 1


def a1_format_list(arguments, name, maximum=20):
    """Validate a bounded list of A1 ranges without reading grid data."""
    values = text_list(arguments, name, maximum=maximum, item_max_length=512)
    if values is not None:
        for value in values:
            _a1_bounds(value)
    return values


def _a1_bounds(value):
    if not isinstance(value, str) or len(value) > 512:
        reject("A bounded A1 range is required")
    match = _A1.fullmatch(value)
    if not match:
        reject("A bounded A1 range is required")
    first_col, first_row, last_col, last_row = match.groups()
    last_col = last_col or first_col
    last_row = last_row or first_row
    start_column = _column_number(first_col)
    end_column = _column_number(last_col)
    start_row = int(first_row)
    end_row = int(last_row)
    if start_column > 16_384 or end_column > 16_384 or end_column < start_column or end_row < start_row:
        reject("A bounded A1 range is required")
    return start_column, start_row, end_column, end_row


def bounded_a1(arguments, name, required=False):
    """Validate one bounded A1 argument and return its dimensions."""
    value = text(arguments, name, required=required, max_length=512)
    return a1_cell_count(value) if value is not None else None


def _column_number(value):
    result = 0
    for character in value.upper():
        result = result * 26 + ord(character) - ord("A") + 1
    return result
