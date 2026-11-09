"""Read plain-text and gzip-compressed authentication logs."""

import gzip
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def ingest(path: str | Path) -> list[tuple[str, str]]:
    """Return (line, stable source identifier) pairs from files inside *path*."""
    data_dir = Path(path)
    lines: list[tuple[str, str]] = []
    try:
        files = sorted(item for item in data_dir.iterdir() if item.is_file() and item.name != "read.py")
    except OSError:
        logger.exception("Could not read log directory %s", data_dir)
        return lines

    for file_path in files:
        try:
            with file_path.open("rb") as probe:
                is_gzip = file_path.suffix == ".gz" or probe.read(2) == b"\x1f\x8b"
        except OSError as error:
            logger.error("Could not inspect %s: %s", file_path, error)
            continue

        opener = gzip.open if is_gzip else open
        try:
            with opener(file_path, mode="rt", encoding="utf-8", errors="replace") as stream:
                for line_number, line in enumerate(stream, start=1):
                    lines.append((line, f"{file_path.name}:{line_number}"))
        except (OSError, EOFError) as error:
            logger.error("Could not read %s: %s", file_path, error)
    return lines
