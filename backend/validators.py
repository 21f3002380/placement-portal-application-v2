import re
from datetime import datetime

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def valid_email(email):
    email = (email or "").strip().lower()
    if not EMAIL_RE.match(email):
        return None, "Please enter a valid email address."
    return email, None


def valid_float(raw, field, lo=None, hi=None, required=False):
    raw = (raw or "").strip() if isinstance(raw, str) else raw
    if raw in (None, ""):
        if required:
            return None, f"{field} is required."
        return None, None
    try:
        val = float(raw)
    except (TypeError, ValueError):
        return None, f"{field} must be a number."
    if lo is not None and val < lo:
        return None, f"{field} must be at least {lo}."
    if hi is not None and val > hi:
        return None, f"{field} must be at most {hi}."
    return val, None


def valid_int(raw, field, lo=None, hi=None, required=False):
    raw = (raw or "").strip() if isinstance(raw, str) else raw
    if raw in (None, ""):
        if required:
            return None, f"{field} is required."
        return None, None
    try:
        val = int(raw)
    except (TypeError, ValueError):
        return None, f"{field} must be a whole number."
    if lo is not None and val < lo:
        return None, f"{field} must be at least {lo}."
    if hi is not None and val > hi:
        return None, f"{field} must be at most {hi}."
    return val, None


def valid_date_eod(raw, field, required=False):
    raw = (raw or "").strip()
    if not raw:
        if required:
            return None, f"{field} is required."
        return None, None
    try:
        d = datetime.strptime(raw, "%Y-%m-%d")
    except ValueError:
        return None, f"{field} must be a valid date (YYYY-MM-DD)."
    return d.replace(hour=23, minute=59, second=59), None


def valid_datetime(raw, field, required=False):
    raw = (raw or "").strip()
    if not raw:
        if required:
            return None, f"{field} is required."
        return None, None
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(raw, fmt), None
        except ValueError:
            continue
    return None, f"{field} must be a valid date/time."


def require_fields(data, fields):
    for f in fields:
        if not (data.get(f) or "").strip():
            return f"{f} is required."
    return None
