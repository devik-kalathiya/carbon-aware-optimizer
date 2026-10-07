import json
from pathlib import Path

def load_datacenters():
    file_path = Path(__file__).parent / "datacenters.json"

    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data


def get_datacenter_list():
    data = load_datacenters()

    datacenters = []

    for datacenter_id, details in data.items():
        record = {
            "id": datacenter_id,
            **details
        }

        datacenters.append(record)

    return datacenters
def get_operational_datacenters():
    datacenters = get_datacenter_list()

    return [
        datacenter
        for datacenter in datacenters
        if datacenter["status"] == "operational"
    ]
def get_datacenters_with_carbon_data():
    from data.grid_zone_loader import load_grid_zones

    datacenters = get_operational_datacenters()
    grid_zones = load_grid_zones()

    result = []

    for datacenter in datacenters:
        zone_key = datacenter.get("zoneKey")

        if zone_key not in grid_zones:
            continue

        zone_data = grid_zones[zone_key]

        record = {
            **datacenter,
            "country": zone_data.get("country"),
            "carbon_intensity": zone_data.get("carbon_intensity"),
            "electricity_price": zone_data.get("electricity_price"),
            "renewable_pct": zone_data.get("renewable_pct")
        }

        result.append(record)

    return result
if __name__ == "__main__":
    datacenters = get_datacenters_with_carbon_data()

    print("Datacenters with carbon data:", len(datacenters))

    for datacenter in datacenters:
        print(
            datacenter["id"],
            "|",
            datacenter["region"],
            "| Carbon:",
            datacenter["carbon_intensity"],
            "gCO2/kWh",
            "| Price: ₹",
            datacenter["electricity_price"],
            "/kWh"
        )