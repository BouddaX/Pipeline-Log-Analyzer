"""Run the SSH authentication log analysis pipeline."""

import hashlib
import logging
from pathlib import Path

from dashboard import create_dashboard
from ingestion.read import ingest
from processing.extract_transform import extract
from storage import dashboard_data, initialize_database, save_attempts

logger = logging.getLogger(__name__)


def main() -> None:
    project_dir = Path(__file__).resolve().parent
    logging.basicConfig(
        filename=project_dir / "app.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        encoding="utf-8",
    )
    try:
        initialize_database()
        rows = ingest(project_dir / "data")
        attempts = []
        for row, source_id in rows:
            try:
                attempt = extract(row)
                if attempt is not None:
                    identity = f"{source_id}\0{row.strip()}"
                    attempt["event_key"] = hashlib.sha256(identity.encode("utf-8")).hexdigest()
                    attempts.append(attempt)
            except (ValueError, TypeError, AttributeError):
                logger.exception("Could not extract a log row: %r", row)

        saved = save_attempts(attempts)
        failed_by_country, successful_by_user, invalid_failures = dashboard_data()
        dashboard_path = create_dashboard(
            failed_by_country,
            successful_by_user,
            invalid_failures,
            project_dir / "reports",
        )

        print(f"Log lines read: {len(rows):,}")
        print(f"Authentication log rows recognized: {len(attempts):,}")
        print(f"Rows inserted or refreshed in PostgreSQL: {saved:,}")
        print("Failed attempts by country:")
        for country, count in failed_by_country:
            print(f"  {country}: {count:,}")
        print("Successful attempts by user:")
        for username, count in successful_by_user:
            print(f"  {username}: {count:,}")
        print(f"Failed attempts for invalid users: {invalid_failures:,}")
        print(f"Dashboard created: {dashboard_path}")
    except Exception:
        logger.exception("Pipeline failed")
        raise


if __name__ == "__main__":
    main()
