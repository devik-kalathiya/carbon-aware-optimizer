import json
from pathlib import Path


def load_grid_zones():
    file_path = Path(__file__).parent / "grid_zones.json"

    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data