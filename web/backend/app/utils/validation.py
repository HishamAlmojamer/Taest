"""Shared request-payload validation helpers.

Routers that accept a raw ``dict`` body (``data: dict``) get no automatic
validation from FastAPI/Pydantic, so a missing or blank field used to travel
all the way into the INSERT and surface as a database error (HTTP 500):
``KeyError``, ``NotNullViolationError`` or ``ForeignKeyViolationError``.

These helpers fail fast with a 422 naming the offending fields, which is what
a client actually needs in order to correct the request.

They also carry response-side hardening: several tables inherited from an older
stack store timestamps in ``text`` columns, so a value like
``'2026-08-24 13:48:11.325934+03'`` reaches Pydantic as a string and used to
abort the whole endpoint with a 500. :func:`coerce_datetime` keeps a single
malformed row from taking down a listing.
"""

from typing import Any, Iterable, Optional

from fastapi import HTTPException


def coerce_datetime(value: Any) -> Optional[Any]:
    """Best-effort conversion of a stored timestamp into ``datetime``.

    Returns ``None`` instead of raising when the value cannot be understood, so
    response models stay usable in the presence of legacy/bad rows. Never call
    this on values the user supplied directly -- use :func:`parse_date_value`.
    """
    from datetime import date as _date, datetime as _datetime

    if value is None or isinstance(value, _datetime):
        return value
    if isinstance(value, _date):
        return _datetime(value.year, value.month, value.day)

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        seconds = value / 1000 if abs(value) > 1e11 else value
        try:
            return _datetime.utcfromtimestamp(seconds)
        except (OverflowError, OSError, ValueError):
            return None

    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
        # A trailing '+HH' / '-HH' offset is valid ISO-8601 shorthand for
        # '+HH:00'; Postgres emits it when it prints a 2-digit zone.
        if normalized[-3:-2] in "+-" and normalized[-2:].isdigit():
            normalized = normalized + ":00"
        try:
            return _datetime.fromisoformat(normalized)
        except ValueError:
            pass
        for fmt in ("%Y-%m-%d %H:%M:%S.%f%z", "%Y-%m-%d %H:%M:%S%z",
                    "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return _datetime.strptime(normalized, fmt)
            except ValueError:
                continue
    return None


def require_fields(data: Any, fields: Iterable[str]) -> None:
    """Raise 422 unless every name in ``fields`` is present and non-blank."""
    if not isinstance(data, dict):
        raise HTTPException(status_code=422, detail="Request body must be a JSON object")

    missing = [
        name
        for name in fields
        if data.get(name) is None
        or (isinstance(data.get(name), str) and not data[name].strip())
    ]
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Missing required field(s): {', '.join(missing)}",
        )


def require_one_of(data: Any, fields: Iterable[str], label: Optional[str] = None) -> str:
    """Require at least one of ``fields`` and return the first one supplied."""
    if not isinstance(data, dict):
        raise HTTPException(status_code=422, detail="Request body must be a JSON object")

    supplied = [
        name
        for name in fields
        if data.get(name) is not None
        and not (isinstance(data.get(name), str) and not data[name].strip())
    ]
    if not supplied:
        raise HTTPException(
            status_code=422,
            detail=f"Missing required field(s): {' or '.join(fields)}"
            + (f" ({label})" if label else ""),
        )
    return supplied[0]


def parse_date_value(value: Any, field: str = "date") -> Optional[Any]:
    """Coerce a date/datetime/ISO-string into ``datetime.date``.

    Accepts ``date``, ``datetime``, ISO-8601 text (``YYYY-MM-DD`` with or
    without a time part) and epoch milliseconds/seconds. Returns ``None`` for
    an empty value so callers can treat the field as optional. Raises 422 for
    anything else, instead of letting ``date.fromisoformat`` raise ValueError
    and turn into a 500.
    """
    from datetime import date as _date, datetime as _datetime

    if value is None or value == "":
        return None

    if isinstance(value, _datetime):
        return value.date()

    if isinstance(value, _date):
        return value

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        # Epoch seconds vs milliseconds, decided by magnitude.
        seconds = value / 1000 if abs(value) > 1e11 else value
        try:
            return _datetime.utcfromtimestamp(seconds).date()
        except (OverflowError, OSError, ValueError):
            raise HTTPException(status_code=422, detail=f"Invalid {field}: {value!r}")

    if isinstance(value, str):
        raw = value.strip()
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        try:
            return _datetime.fromisoformat(raw).date()
        except ValueError:
            pass
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y", "%Y%m%d"):
            try:
                return _datetime.strptime(raw, fmt).date()
            except ValueError:
                continue
        raise HTTPException(status_code=422, detail=f"Invalid {field}: {value!r}")

    raise HTTPException(status_code=422, detail=f"Invalid {field}: {value!r}")


def parse_optional_date(data: Any, field: str, default: Any = None) -> Any:
    """Read ``data[field]`` and parse it with :func:`parse_date_value`."""
    if not isinstance(data, dict):
        raise HTTPException(status_code=422, detail="Request body must be a JSON object")
    parsed = parse_date_value(data.get(field), field)
    return parsed if parsed is not None else default
