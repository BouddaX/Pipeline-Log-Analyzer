"""Extract SSH authentication attempts from system log lines."""

import logging
import re

logger = logging.getLogger(__name__)

_HEADER = re.compile(
    r"^(?P<month>\w{3})\s+(?P<day>\d{1,2})\s+"
    r"(?P<time>\d{2}:\d{2}:\d{2})\s+.*?:\s*(?P<message>.*)$"
)
_ATTEMPT = re.compile(
    r"(?P<status>Failed|Accepted)\s+(?P<method>\S+)\s+for\s+"
    r"(?P<invalid>invalid user\s+)?(?P<user>\S*)\s+from\s+"
    r"(?P<ip>(?:\d{1,3}\.){3}\d{1,3})\b"
)
_REPEATED = re.compile(r"message repeated\s+(?P<count>\d+)\s+times:\s*\[\s*(?P<message>.*)\s*\]")


def extract(row: str) -> dict[str, str | int] | None:
    """Return parsed authentication fields, or None for unrelated log rows."""
    try:
        header = _HEADER.match(row.strip())
        if not header:
            return None

        message = header.group("message")
        count = 1
        repeated = _REPEATED.search(message)
        if repeated:
            count = int(repeated.group("count"))
            message = repeated.group("message")

        attempt = _ATTEMPT.search(message)
        if not attempt:
            return None

        return {
            "month": header.group("month"),
            "day": header.group("day"),
            "time": header.group("time"),
            "message": message,
            "status": attempt.group("status"),
            "method": attempt.group("method"),
            "invalid": "invalid user" if attempt.group("invalid") else "",
            "user": attempt.group("user"),
            "ip": attempt.group("ip"),
            "count": count,
            "event_key": row.strip(),
        }
    except (AttributeError, ValueError, TypeError):
        logger.exception("Could not parse log row: %r", row)
        return None
