# ============================================================
# MMFG - Datacenter Dataset Adapter
# ============================================================

import json
from pathlib import Path


def load_datacenters(file_path):
    """
    Load datacenter information from datacenter.json.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Datacenter file not found: {path}"
        )

    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            "datacenter.json must contain a JSON object."
        )

    return data


def get_operational_datacenters(datacenters):
    """
    Keep only operational datacenters.
    """

    return {
        datacenter_id: data
        for datacenter_id, data in datacenters.items()
        if data.get("status") == "operational"
    }


def group_datacenters_by_zone(datacenters):
    """
    Group datacenters using their zoneKey.

    Example:

        US-MIDA-PJM
            ├── AWS
            ├── Azure
            └── GCP

    Returns:
        {
            "US-MIDA-PJM": [...],
            "IN-WE": [...],
            ...
        }
    """

    zones = {}

    for datacenter_id, data in datacenters.items():

        zone = data.get("zoneKey")

        if not zone:
            continue

        if zone not in zones:
            zones[zone] = []

        zones[zone].append(datacenter_id)

    return zones


def create_region_population(datacenters):
    """
    Create an initial population distribution across
    datacenter zones.

    Initially, population is proportional to the number
    of datacenters in each zone.
    """

    zones = group_datacenters_by_zone(datacenters)

    total_datacenters = sum(
        len(datacenters_in_zone)
        for datacenters_in_zone in zones.values()
    )

    if total_datacenters == 0:
        raise ValueError(
            "No datacenters available."
        )

    population = {
        zone: len(datacenters_in_zone) / total_datacenters
        for zone, datacenters_in_zone in zones.items()
    }

    return population