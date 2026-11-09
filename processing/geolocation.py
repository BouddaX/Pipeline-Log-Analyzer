"""Look up country information from the local PostgreSQL mapping table."""

import logging

from storage import country_for_ip

logger = logging.getLogger(__name__)


def geolocation(ip: str) -> str:
    """Return a mapped country or ``Unknown`` if the IP is not in the database."""
    try:
        return country_for_ip(ip)
    except Exception:
        logger.exception("Could not resolve country for IP %s", ip)
        return "Unknown"
