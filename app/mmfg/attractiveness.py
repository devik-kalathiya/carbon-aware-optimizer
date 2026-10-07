# ============================================================
# MMFG - Carbon-Aware Attractiveness
# ============================================================

from mmfg.mean_field import WORKLOAD_CLASSES


def normalize_min_max(values):
    """
    Normalize values between 0 and 1.

    Lower value gets a lower score and higher value gets
    a higher score.
    """

    if not values:
        raise ValueError("Values cannot be empty.")

    minimum = min(values.values())
    maximum = max(values.values())

    if minimum == maximum:
        return {
            key: 1.0
            for key in values
        }

    return {
        key: (value - minimum) / (maximum - minimum)
        for key, value in values.items()
    }


def calculate_attractiveness(
    grid_zones,
    workload_type=None,
    carbon_weight=0.60,
    renewable_weight=0.25,
    cost_weight=0.15
):
    """
    Calculate carbon-aware attractiveness for every grid zone.

    If workload_type is provided, the carbon and cost weights
    are adjusted according to the workload sensitivities
    defined in mmfg.mean_field.WORKLOAD_CLASSES.

    Latency is not used in MMFG attractiveness.
    Latency is handled later as a scheduler constraint.
    """

    if workload_type is not None:

        if workload_type not in WORKLOAD_CLASSES:
            raise ValueError(
                f"Unknown workload class: {workload_type}"
            )

        workload = WORKLOAD_CLASSES[workload_type]

        carbon_sensitivity = workload["carbon_sensitivity"]
        cost_sensitivity = workload["cost_sensitivity"]

        sensitivity_total = (
            carbon_sensitivity
            + cost_sensitivity
        )

        if sensitivity_total <= 0:
            raise ValueError(
                "Carbon and cost sensitivities must be greater than 0."
            )

        remaining_weight = 1.0 - renewable_weight

        carbon_weight = (
            remaining_weight
            * carbon_sensitivity
            / sensitivity_total
        )

        cost_weight = (
            remaining_weight
            * cost_sensitivity
            / sensitivity_total
        )

    total_weight = (
        carbon_weight
        + renewable_weight
        + cost_weight
    )

    if abs(total_weight - 1.0) > 1e-6:
        raise ValueError(
            "Attractiveness weights must sum to 1.0."
        )

    carbon = {}
    renewable = {}
    cost = {}

    for zone, data in grid_zones.items():

        if data.get("carbon_intensity") is None:
            continue

        if data.get("renewable_pct") is None:
            continue

        if data.get("electricity_price") is None:
            continue

        carbon[zone] = float(
            data["carbon_intensity"]
        )

        renewable[zone] = float(
            data["renewable_pct"]
        )

        cost[zone] = float(
            data["electricity_price"]
        )

    if not carbon:
        raise ValueError(
            "No complete grid-zone data available."
        )

    # --------------------------------------------------------
    # Carbon score
    # Lower carbon intensity = better score
    # --------------------------------------------------------

    max_carbon = max(carbon.values())
    min_carbon = min(carbon.values())

    if max_carbon == min_carbon:
        carbon_score = {
            zone: 1.0
            for zone in carbon
        }
    else:
        carbon_score = {
            zone:
                (max_carbon - value)
                / (max_carbon - min_carbon)
            for zone, value in carbon.items()
        }

    # --------------------------------------------------------
    # Renewable score
    # Higher renewable percentage = better score
    # --------------------------------------------------------

    renewable_score = normalize_min_max(
        renewable
    )

    # --------------------------------------------------------
    # Cost score
    # Lower electricity price = better score
    # --------------------------------------------------------

    max_cost = max(cost.values())
    min_cost = min(cost.values())

    if max_cost == min_cost:
        cost_score = {
            zone: 1.0
            for zone in cost
        }
    else:
        cost_score = {
            zone:
                (max_cost - value)
                / (max_cost - min_cost)
            for zone, value in cost.items()
        }

    # --------------------------------------------------------
    # Final attractiveness
    # --------------------------------------------------------

    attractiveness = {}

    for zone in carbon_score:

        attractiveness[zone] = (
            carbon_weight * carbon_score[zone]
            + renewable_weight * renewable_score[zone]
            + cost_weight * cost_score[zone]
        )

    return attractiveness