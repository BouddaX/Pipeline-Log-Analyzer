"""PostgreSQL storage and dashboard queries for authentication attempts."""

import logging
import os
from contextlib import contextmanager
from pathlib import Path

import psycopg2

logger = logging.getLogger(__name__)


@contextmanager
def _managed_connection():
    connection = connect()
    try:
        with connection:
            yield connection
    finally:
        connection.close()

_INSERT_ATTEMPT = """
    INSERT INTO authentication_attempts
        (event_key, event_month, event_day, event_time, username, ip_address,
         country, status, method, invalid_user, attempt_count)
    VALUES (
        %s, %s, %s, %s, %s, %s,
        COALESCE((SELECT country FROM ip_country_map WHERE ip_address = %s::inet), 'Unknown'),
        %s, %s, %s, %s
    ) ON CONFLICT (event_key) DO UPDATE SET country = COALESCE(
        (SELECT country FROM ip_country_map WHERE ip_address = EXCLUDED.ip_address),
        authentication_attempts.country
    )
"""


def connect():
    """Connect using LOG_DATABASE_URL or the standard PostgreSQL environment."""
    dsn = os.environ.get("LOG_DATABASE_URL")
    try:
        if dsn:
            return psycopg2.connect(dsn)
        return psycopg2.connect(
            host=os.environ.get("PGHOST", "localhost"),
            port=os.environ.get("PGPORT", "5432"),
            dbname=os.environ.get("PGDATABASE", "log_analysis"),
            user=os.environ.get("PGUSER", "boudda"),
            password=os.environ.get("PGPASSWORD", ""),
        )
    except psycopg2.Error:
        logger.exception("Could not connect to PostgreSQL")
        raise


def initialize_database() -> None:
    """Create the tables and indexes from schema.sql if they do not exist."""
    schema_path = Path(__file__).resolve().parent / "schema.sql"
    try:
        schema = schema_path.read_text(encoding="utf-8")
        with _managed_connection() as connection:
            with connection.cursor() as cursor:
                for statement in schema.split(";"):
                    if statement.strip():
                        cursor.execute(statement)
        logger.info("PostgreSQL schema initialized")
    except (OSError, psycopg2.Error):
        logger.exception("Could not initialize PostgreSQL schema")
        raise


def save_attempts(attempts: list[dict[str, object]]) -> int:
    """Insert parsed attempts and return the number of newly inserted rows."""
    if not attempts:
        return 0
    values = [
        (
            row["event_key"], row["month"], row["day"], row["time"],
            row["user"], row["ip"], row["ip"], row["status"], row["method"],
            bool(row["invalid"]), row["count"],
        )
        for row in attempts
    ]
    try:
        with _managed_connection() as connection:
            with connection.cursor() as cursor:
                cursor.executemany(_INSERT_ATTEMPT, values)
                saved = cursor.rowcount
        logger.info("Inserted or refreshed %d authentication attempts", saved)
        return saved
    except psycopg2.Error:
        logger.exception("Could not save authentication attempts")
        raise


def dashboard_data():
    """Return failed-by-country, successful-by-user and invalid-user totals."""
    try:
        with _managed_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT country, SUM(attempt_count) FROM authentication_attempts "
                    "WHERE status = 'Failed' GROUP BY country ORDER BY SUM(attempt_count) DESC"
                )
                failed_by_country = cursor.fetchall()
                cursor.execute(
                    "SELECT username, SUM(attempt_count) FROM authentication_attempts "
                    "WHERE status = 'Accepted' GROUP BY username ORDER BY SUM(attempt_count) DESC"
                )
                successful_by_user = cursor.fetchall()
                cursor.execute(
                    "SELECT COALESCE(SUM(attempt_count), 0) FROM authentication_attempts "
                    "WHERE status = 'Failed' AND invalid_user = TRUE"
                )
                invalid_failures = cursor.fetchone()[0]
        return failed_by_country, successful_by_user, invalid_failures
    except psycopg2.Error:
        logger.exception("Could not query PostgreSQL dashboard data")
        raise


def update_country(ip: str, country: str) -> None:
    """Add or update an IP-to-country mapping in PostgreSQL."""
    try:
        with _managed_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO ip_country_map (ip_address, country) VALUES (%s::inet, %s) "
                    "ON CONFLICT (ip_address) DO UPDATE SET country = EXCLUDED.country",
                    (ip, country),
                )
    except psycopg2.Error:
        logger.exception("Could not store country mapping for %s", ip)
        raise


def country_for_ip(ip: str) -> str:
    """Return the mapped country name for one address, if it exists."""
    try:
        with _managed_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT country FROM ip_country_map WHERE ip_address = %s::inet", (ip,)
                )
                result = cursor.fetchone()
        return result[0] if result else "Unknown"
    except psycopg2.Error:
        logger.exception("Could not look up country for IP %s", ip)
        raise
