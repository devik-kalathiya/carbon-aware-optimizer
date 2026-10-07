import json
from pathlib import Path


def load_regions():
    file_path = Path(__file__).parent / "regions.json"

    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data


if __name__ == "__main__":
    regions = load_regions()

    print("Region data loaded successfully!")
    print("Total regions:", len(regions))

    for region, details in regions.items():
        print(
            region,
            "|",
            details["country"],
            "| Carbon:",
            details["carbon_intensity"],
            "gCO2/kWh",
            "| Price: ₹",
            details["electricity_price"],
            "/kWh"
        )