# ============================================================
# MMFG - Scheduler Router
# ============================================================

from mmfg.mean_field import calculate_equilibrium


def calculate_mmfg_routing(
    initial_population,
    attractiveness,
    interaction_strength=0.5,
    learning_rate=0.5
):
    """
    Run MMFG equilibrium and return the workload distribution.
    """

    result = calculate_equilibrium(
        attractiveness=attractiveness,
        initial_population=initial_population,
        interaction_strength=interaction_strength,
        learning_rate=learning_rate
    )

    return result


def select_best_zone(equilibrium_population):
    """
    Select the grid zone with the highest final MMFG population.
    """

    if not equilibrium_population:
        raise ValueError(
            "Equilibrium population cannot be empty."
        )

    return max(
        equilibrium_population.items(),
        key=lambda x: x[1]
    )


def rank_zones(equilibrium_population):
    """
    Rank grid zones according to their final MMFG population.
    """

    return sorted(
        equilibrium_population.items(),
        key=lambda x: x[1],
        reverse=True
    )


def route_workload(
    initial_population,
    attractiveness,
    interaction_strength=0.5,
    learning_rate=0.5
):
    """
    Complete MMFG workload-routing process.

    Returns:
        {
            "best_zone": ...,
            "best_population": ...,
            "ranked_zones": ...,
            "iterations": ...,
            "converged": ...
        }
    """

    result = calculate_mmfg_routing(
        initial_population,
        attractiveness,
        interaction_strength,
        learning_rate
    )

    best_zone, best_population = select_best_zone(
        result["population"]
    )

    ranked_zones = rank_zones(
        result["population"]
    )

    return {
        "best_zone": best_zone,
        "best_population": best_population,
        "ranked_zones": ranked_zones,
        "iterations": result["iterations"],
        "converged": result["converged"]
    }