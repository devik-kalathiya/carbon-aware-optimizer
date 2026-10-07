import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATACENTERS_FILE = os.path.join(BASE_DIR, "datacenters.json")
GRID_ZONES_FILE = os.path.join(BASE_DIR, "grid_zones.json")

URL = "https://openrouter.ai/api/v1/chat/completions"


def load_zone_keys():
    """Get unique zoneKeys from datacenters.json."""

    with open(DATACENTERS_FILE, "r", encoding="utf-8") as file:
        datacenters = json.load(file)

    zones = set()

    for datacenter in datacenters.values():
        zone_key = datacenter.get("zoneKey")

        if zone_key:
            zones.add(zone_key)

    return sorted(zones)


def fetch_zone_data(zone_key):
    """Ask OpenRouter Web Search for information about one grid zone."""

    prompt = f"""
Research the electricity grid zone: {zone_key}

Find information from the internet about this grid zone.

Return ONLY valid JSON:

{{
    "zoneKey": "{zone_key}",
    "country": null,
    "carbon_intensity": null,
    "electricity_price": null,
    "renewable_pct": null,
    "source": null,
    "source_url": null,
    "last_updated": null
}}

Requirements:

- carbon_intensity must be in gCO2/kWh.
- electricity_price should preferably be in INR/kWh.
- renewable_pct must be a percentage.
- Search the web.
- Prefer government sources, electricity-grid operators,
  recognized energy organizations, or reliable research sources.
- Do not invent values.
- If reliable information cannot be found, use null.
- Include source names and URLs.
- Keep the response JSON only.
"""

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openrouter/free:online",
        "plugins": [
            {
                "id": "web",
                "max_results": 5
            }
        ],
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    try:
        response = requests.post(
            URL,
            headers=headers,
            json=payload,
            timeout=120
        )

        print("HTTP Status:", response.status_code)

        if not response.ok:
            print("ERROR:", response.text)
            return None

        result = response.json()

        content = result["choices"][0]["message"]["content"]

        content = content.strip()

        # Remove markdown code fences
        if content.startswith("```"):
            content = content.replace("```json", "")
            content = content.replace("```", "")
            content = content.strip()

        try:
            data = json.loads(content)

            # Make sure the correct zone is stored
            data["zoneKey"] = zone_key

            return data

        except json.JSONDecodeError:
            print("ERROR: Invalid JSON returned by model.")
            print(content)
            return None

    except Exception as error:
        print("REQUEST ERROR:", error)
        return None


def main():

    if not API_KEY:
        print("ERROR: OPENROUTER_API_KEY not found.")
        return

    zones = load_zone_keys()

    print("===================================")
    print(" OpenRouter Grid Data Collection")
    print("===================================")

    print(f"Total unique grid zones: {len(zones)}")

    grid_data = {}

    # Existing data is loaded so the script does not
    # unnecessarily overwrite previously collected zones.
    if os.path.exists(GRID_ZONES_FILE):

        try:
            with open(GRID_ZONES_FILE, "r", encoding="utf-8") as file:
                grid_data = json.load(file)

        except json.JSONDecodeError:
            print("Existing grid_zones.json is invalid.")
            grid_data = {}

    for index, zone_key in enumerate(zones, start=1):

        print()
        print("-----------------------------------")
        print(f"Zone {index}/{len(zones)}: {zone_key}")
        print("-----------------------------------")

        # Skip zones already containing actual data
        existing = grid_data.get(zone_key)

        if (
            existing
            and any(
                existing.get(field) is not None
                for field in [
                    "carbon_intensity",
                    "electricity_price",
                    "renewable_pct"
                ]
            )
        ):
            print("Already has data. Skipping.")
            continue

        data = fetch_zone_data(zone_key)

        if data:

            grid_data[zone_key] = data

            print("Saved:")
            print(json.dumps(data, indent=4))

        else:

            print("No valid data returned.")
            grid_data[zone_key] = {
                "zoneKey": zone_key,
                "country": None,
                "carbon_intensity": None,
                "electricity_price": None,
                "renewable_pct": None,
                "source": None,
                "source_url": None,
                "last_updated": None
            }

        # Small delay between requests
        time.sleep(2)

        # Save after every zone
        with open(
            GRID_ZONES_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                grid_data,
                file,
                indent=4,
                ensure_ascii=False
            )

    print()
    print("===================================")
    print(" Collection completed")
    print("===================================")
    print(f"Grid zones saved: {GRID_ZONES_FILE}")


if __name__ == "__main__":
    main()