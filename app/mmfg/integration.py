from app.mmfg.mean_field import calculate_equilibrium
from app.mmfg.attractiveness import calculate_attractiveness


def create_zone_population(datacenters):
    """
    Create initial population from datacenter distribution.
    """

    zone_counts = {}

    for dc in datacenters:
        zone = dc.get("zoneKey")

        if not zone:
            continue

        zone_counts[zone] = zone_counts.get(zone, 0) + 1

    total = sum(zone_counts.values())

    if total == 0:
        raise ValueError("No datacenter zones available.")

    return {
        zone: count / total
        for zone, count in zone_counts.items()
    }


def run_mmfg_routing(
    datacenters,
    grid_zones,
    workload_type=None,
    interaction_strength=0.5,
    learning_rate=0.5
):
    """
    Run MMFG routing for a workload class and select
    a datacenter from the best grid zone.
    """

    # -----------------------------
    # Validate workload type
    # -----------------------------

    if workload_type is None:
        raise ValueError(
            "workload_type is required for MMFG routing."
        )

    # -----------------------------
    # Initial population
    # -----------------------------

    population = create_zone_population(
        datacenters
    )

    # -----------------------------
    # Calculate workload-specific
    # attractiveness
    # -----------------------------

    attractiveness = calculate_attractiveness(
        grid_zones,
        workload_type=workload_type
    )

    # -----------------------------
    # Find common zones
    # -----------------------------

    common_zones = (
        set(population.keys())
        & set(attractiveness.keys())
    )

    if not common_zones:
        raise ValueError(
            "No common zones between datacenters "
            "and grid data."
        )

    population = {
        zone: population[zone]
        for zone in common_zones
    }

    attractiveness = {
        zone: attractiveness[zone]
        for zone in common_zones
    }

    # -----------------------------
    # Renormalize population
    # -----------------------------

    total_population = sum(
        population.values()
    )

    population = {
        zone: value / total_population
        for zone, value in population.items()
    }

    # -----------------------------
    # MMFG equilibrium
    # -----------------------------

    result = calculate_equilibrium(
        attractiveness=attractiveness,
        initial_population=population,
        interaction_strength=interaction_strength,
        learning_rate=learning_rate
    )

    # -----------------------------
    # Best grid zone
    # -----------------------------

    best_zone = max(
        result["population"],
        key=result["population"].get
    )
    top_zones = sorted(
    result["population"].items(),
    key=lambda x: x[1],
    reverse=True
    )[:5]

    # -----------------------------
    # Find datacenters in best zone
    # -----------------------------

    zone_datacenters = [
        dc
        for dc in datacenters
        if dc.get("zoneKey") == best_zone
    ]

    if not zone_datacenters:
        raise ValueError(
            f"No datacenter found in grid zone: {best_zone}"
        )

    # -----------------------------
    # Select datacenter
    # -----------------------------

    selected_datacenter = min(
        zone_datacenters,
        key=lambda dc: (
            dc.get(
                "carbon_intensity",
                float("inf")
            ),
            dc.get(
                "electricity_price",
                float("inf")
            )
        )
    )

    return {
    "workload_type": workload_type,
    "best_zone": best_zone,
    "top_zones": top_zones,
    "selected_datacenter": selected_datacenter,
    "zone_datacenters": zone_datacenters,
    "population": result["population"],
    "attractiveness": attractiveness,
    "iterations": result["iterations"],
    "converged": result["converged"]
    }