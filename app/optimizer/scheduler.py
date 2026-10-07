"""
scheduler.py
Carbon-Aware Region Optimizer

This is a simplified deterministic optimization model inspired by
the first-stage workload-allocation idea discussed in the research paper.

It is NOT a reproduction of the paper's exact CCG equations.

Decision:
    Select exactly one eligible datacenter.

Objective:
    Maximize a weighted normalized score based on:
        - Carbon
        - Electricity cost
        - Latency
        - Renewable energy

Additional constraints:
    - Maximum latency
    - Maximum budget
    - Minimum required capacity

Uncertainty:
    Carbon intensity and electricity price can be pessimistically
    increased by a configurable percentage.
"""

from typing import List, Dict, Optional


# ============================================================
# Default Weights
# ============================================================

DEFAULT_WEIGHTS = {
    "carbon": 0.40,
    "cost": 0.20,
    "latency": 0.10,
    "renewable": 0.30,
}


# ============================================================
# Helper: Get Datacenter ID
# ============================================================

def _get_id(region: Dict) -> str:
    """
    Supports both:
        datacenter_id
    and
        id

    Our current datacenters.json uses 'id'.
    """

    return region.get(
        "datacenter_id",
        region.get("id", "unknown")
    )


# ============================================================
# Normalize Values
# ============================================================

def _normalize(
    values: Dict[str, float],
    lower_is_better: bool
) -> Dict[str, float]:

    if not values:
        return {}

    vmin = min(values.values())
    vmax = max(values.values())

    # If all values are identical, there is no difference
    # between regions for this metric.
    if vmax == vmin:
        return {
            key: 1.0
            for key in values
        }

    scores = {}

    for key, value in values.items():

        if lower_is_better:
            # Lower value = better score
            scores[key] = (
                (vmax - value) /
                (vmax - vmin)
            )

        else:
            # Higher value = better score
            scores[key] = (
                (value - vmin) /
                (vmax - vmin)
            )

    return scores


# ============================================================
# Apply Uncertainty
# ============================================================

def apply_uncertainty(
    regions: List[Dict],
    carbon_uncertainty_pct: float = 0.0,
    cost_uncertainty_pct: float = 0.0
) -> List[Dict]:

    adjusted = []

    for region in regions:

        region_copy = dict(region)

        # Worst-case carbon
        if region_copy.get("carbon_intensity") is not None:

            region_copy["carbon_intensity"] = (
                region_copy["carbon_intensity"]
                * (1 + carbon_uncertainty_pct)
            )

        # Worst-case electricity price
        if region_copy.get("electricity_price") is not None:

            region_copy["electricity_price"] = (
                region_copy["electricity_price"]
                * (1 + cost_uncertainty_pct)
            )

        adjusted.append(region_copy)

    return adjusted


# ============================================================
# Calculate Energy
# ============================================================

def calculate_energy(
    power_kw: float,
    duration_hours: float
) -> float:

    return power_kw * duration_hours


# ============================================================
# Score Regions
# ============================================================

def score_regions(
    regions: List[Dict],
    energy_kwh: float,
    weights: Optional[Dict[str, float]] = None,
    latency_max_ms: Optional[float] = None,
    budget: Optional[float] = None,
    workload_demand: Optional[float] = None,
) -> List[Dict]:

    if weights is None:
        weights = DEFAULT_WEIGHTS

    # --------------------------------------------------------
    # Step 1: Operational filter
    # --------------------------------------------------------

    eligible = [
        region
        for region in regions
        if region.get("status", "operational") == "operational"
    ]

    # --------------------------------------------------------
    # Step 2: Latency constraint
    # --------------------------------------------------------

    if latency_max_ms is not None:

        eligible = [
            region
            for region in eligible
            if (
                region.get("latency_ms") is None
                or region["latency_ms"] <= latency_max_ms
            )
        ]

    # --------------------------------------------------------
    # Step 3: Calculate cost and carbon
    # --------------------------------------------------------

    prepared = []

    for region in eligible:

        region_copy = dict(region)

        carbon_intensity = region_copy.get(
            "carbon_intensity"
        )

        electricity_price = region_copy.get(
            "electricity_price"
        )

        # Skip region if essential data is missing
        if carbon_intensity is None:
            continue

        if electricity_price is None:
            continue

        carbon = energy_kwh * carbon_intensity

        cost = energy_kwh * electricity_price

        region_copy["energy_kwh"] = energy_kwh
        region_copy["carbon_emissions"] = carbon
        region_copy["electricity_cost"] = cost

        # ----------------------------------------------------
        # Capacity constraint
        # ----------------------------------------------------

        if workload_demand is not None:

            capacity = region_copy.get("capacity")

            if capacity is not None:
                if capacity < workload_demand:
                    continue

        # ----------------------------------------------------
        # Budget constraint
        # ----------------------------------------------------

        if budget is not None:

            if cost > budget:
                continue

        prepared.append(region_copy)

    eligible = prepared

    if not eligible:
        return []

    # --------------------------------------------------------
    # Step 4: Prepare metrics
    # --------------------------------------------------------

    metric_specs = {
        "carbon": (
            "carbon_emissions",
            True
        ),

        "cost": (
            "electricity_cost",
            True
        ),

        "latency": (
            "latency_ms",
            True
        ),

        "renewable": (
            "renewable_pct",
            False
        ),
    }

    available_metrics = {}

    for metric_name, (field, lower_is_better) in metric_specs.items():

        values = {
            _get_id(region): region[field]
            for region in eligible
            if region.get(field) is not None
        }

        if values:

            available_metrics[metric_name] = _normalize(
                values,
                lower_is_better
            )

    # --------------------------------------------------------
    # Step 5: Re-normalize weights
    # --------------------------------------------------------

    active_metrics = [
        metric
        for metric in available_metrics
        if metric in weights
        and weights[metric] > 0
    ]

    if not active_metrics:
        return []

    active_weight_sum = sum(
        weights[metric]
        for metric in active_metrics
    )

    active_weights = {
        metric:
        weights[metric] / active_weight_sum
        for metric in active_metrics
    }

    # --------------------------------------------------------
    # Step 6: Calculate final score
    # --------------------------------------------------------

    results = []

    for region in eligible:

        region_id = _get_id(region)

        total_score = 0.0

        breakdown = {}

        for metric in active_metrics:

            normalized_score = (
                available_metrics[metric]
                .get(region_id, 0.0)
            )

            weight = active_weights[metric]

            contribution = (
                normalized_score * weight
            )

            total_score += contribution

            breakdown[metric] = {
                "normalized_score": round(
                    normalized_score,
                    4
                ),

                "weight": round(
                    weight,
                    4
                ),

                "contribution": round(
                    contribution,
                    4
                )
            }

        result = dict(region)

        result["score"] = round(
            total_score,
            4
        )

        result["score_breakdown"] = breakdown

        results.append(result)

    # Highest score = best region
    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return results


# ============================================================
# Recommend Best Region
# ============================================================

def recommend_region(
    regions: List[Dict],
    power_kw: float,
    duration_hours: float,
    weights: Optional[Dict[str, float]] = None,
    latency_max_ms: Optional[float] = None,
    budget: Optional[float] = None,
    workload_demand: Optional[float] = None,
    carbon_uncertainty_pct: float = 0.0,
    cost_uncertainty_pct: float = 0.0,
) -> Optional[Dict]:

    # --------------------------------------------------------
    # Calculate workload energy
    # --------------------------------------------------------

    energy_kwh = calculate_energy(
        power_kw,
        duration_hours
    )

    # --------------------------------------------------------
    # Apply uncertainty
    # --------------------------------------------------------

    adjusted_regions = apply_uncertainty(
        regions,
        carbon_uncertainty_pct,
        cost_uncertainty_pct
    )

    # --------------------------------------------------------
    # Score regions
    # --------------------------------------------------------

    scored = score_regions(
        adjusted_regions,
        energy_kwh=energy_kwh,
        weights=weights,
        latency_max_ms=latency_max_ms,
        budget=budget,
        workload_demand=workload_demand
    )

    # --------------------------------------------------------
    # Return best
    # --------------------------------------------------------

    if not scored:
        return None

    return scored[0]