"""Render the aggregated PostgreSQL results as a local dashboard."""

import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


def create_dashboard(failed_by_country, successful_by_user, invalid_user_failures, output_dir):
    """Create dashboard.png and dashboard.html from SQL query results."""
    output = Path(output_dir)
    try:
        output.mkdir(parents=True, exist_ok=True)
        figure, axes = plt.subplots(1, 3, figsize=(16, 5))
        charts = (
            (axes[0], failed_by_country, "Tentatives échouées par pays", "Pays"),
            (axes[1], successful_by_user, "Tentatives réussies par utilisateur", "Utilisateur"),
        )
        for axis, rows, title, label in charts:
            labels = [str(row[0]) for row in rows]
            values = [int(row[1]) for row in rows]
            axis.bar(labels, values, color="#3973ac")
            axis.set_title(title)
            axis.set_ylabel("Nombre de tentatives")
            axis.set_xlabel(label)
            axis.tick_params(axis="x", labelrotation=60)
        axes[2].bar(["Utilisateur invalide"], [invalid_user_failures], color="#d65f5f")
        axes[2].set_title("Échecs avec utilisateur invalide")
        axes[2].set_ylabel("Nombre de tentatives")
        figure.tight_layout()
        figure.savefig(output / "dashboard.png", dpi=140)
        plt.close(figure)
        page = output / "dashboard.html"
        page.write_text(
            "<!doctype html><html lang='fr'><meta charset='utf-8'>"
            "<title>Pipeline Log Analyzer</title><body>"
            "<h1>Dashboard Pipeline Log Analyzer</h1>"
            f"<p>Tentatives échouées avec utilisateur invalide : {invalid_user_failures}</p>"
            "<img src='dashboard.png' alt='Graphiques des tentatives SSH'>"
            "</body></html>",
            encoding="utf-8",
        )
        logger.info("Dashboard written to %s", page)
        return page
    except (OSError, ValueError, RuntimeError):
        logger.exception("Could not create dashboard in %s", output)
        raise
