# ============================================================
# MMFG - Grid Zone Dataset Adapter
# ============================================================

import json
from pathlib import Path


def load_grid_zones(file_path):
    """
    Load grid-zone information from grid_zones.json.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Grid zone file not found: {path}"
        )

    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            "grid_zones.json must contain a JSON object."
        )

    return data


def get_carbon_intensity(grid_zones):
    """
    Extract carbon intensity for each grid zone.

    Returns:
        {
            "AE": 450,
            "AU-NSW": 610,
            ...
        }
    """

    carbon_intensity = {}

    for zone, data in grid_zones.items():

        value = data.get("carbon_intensity")

        if value is None:
            continue

        carbon_intensity[zone] = float(value)

    return carbon_intensity


def get_electricity_price(grid_zones):
    """
    Extract electricity price for each grid zone.
    """

    electricity_price = {}

    for zone, data in grid_zones.items():

        value = data.get("electricity_price")

        if value is None:
            continue

        electricity_price[zone] = float(value)

    return electricity_price


def get_renewable_percentage(grid_zones):
    """
    Extract renewable-energy percentage for each grid zone.
    """

    renewable_percentage = {}

    for zone, data in grid_zones.items():

        value = data.get("renewable_pct")

        if value is None:
            continue

        renewable_percentage[zone] = float(value)

    return renewable_percentage


def calculate_carbon_score(grid_zones):
    """
    Convert carbon intensity into a normalized carbon score.

    Lower carbon intensity = higher score.

    Formula:

        carbon_score =
            (max_carbon - carbon) /
            (max_carbon - min_carbon)

    Therefore:

        lowest carbon -> 1.0
        highest carbon -> 0.0
    """

    carbon = get_carbon_intensity(grid_zones)

    if not carbon:
        raise ValueError(
            "No carbon intensity data available."
        )

    min_carbon = min(carbon.values())
    max_carbon = max(carbon.values())

    if min_carbon == max_carbon:
        return {
            zone: 1.0
            for zone in carbon
        }

    scores = {}

    for zone, value in carbon.items():

        scores[zone] = (
            (max_carbon - value)
            / (max_carbon - min_carbon)
        )

    return scores