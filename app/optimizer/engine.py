from app.calculations.energy import calculate_energy
from app.data.data_loader import get_datacenters_with_carbon_data
from app.data.grid_zone_loader import load_grid_zones
from app.models.workload import create_workload
from app.optimizer.scheduler import recommend_region
from app.mmfg.integration import run_mmfg_routing
from app.uncertainty.robust import (
    evaluate_robust_scenarios,
    get_robust_recommendation
)
from app.simulation.multi_idc import simulate_multi_idc


def get_dc_id(dc):
    if isinstance(dc, dict):
        return dc.get("id")
    return dc


def run_optimization(
    workload_type,
    power_kw,
    duration_hours,
    latency_max_ms=None,
    budget=None,
    workload_demand=None
):
    weights = {
        "carbon": 0.40,
        "cost": 0.20,
        "latency": 0.10,
        "renewable": 0.30
    }

    energy = calculate_energy(
        power_kw,
        duration_hours
    )

    datacenters = get_datacenters_with_carbon_data()
    grid_zones = load_grid_zones()

    workload = create_workload(
        power_kw,
        duration_hours,
        latency_max_ms=latency_max_ms,
        budget=budget,
        workload_demand=workload_demand
    )

    # Stage 1: Carbon-aware scheduler
    best_region = recommend_region(
        regions=datacenters,
        power_kw=workload.power_kw,
        duration_hours=workload.duration_hours,
        weights=weights,
        latency_max_ms=workload.latency_max_ms,
        budget=workload.budget,
        workload_demand=workload.workload_demand
    )

    if best_region is None:
        return {
            "status": "failed",
            "message": "No suitable datacenter found."
        }

    # Stage 2: MMFG routing
    mmfg_result = run_mmfg_routing(
        datacenters=datacenters,
        grid_zones=grid_zones,
        workload_type=workload_type,
        interaction_strength=0.5,
        learning_rate=0.5
    )

    mmfg_dc = mmfg_result["selected_datacenter"]

    # Stage 3: Robust optimization
    robust_results = evaluate_robust_scenarios(
        datacenters=datacenters,
        power_kw=workload.power_kw,
        duration_hours=workload.duration_hours,
        weights=weights,
        latency_max_ms=workload.latency_max_ms,
        budget=workload.budget,
        workload_demand=workload.workload_demand
    )

    robust_result = get_robust_recommendation(
        robust_results
    )

    # Convert recommendations to datacenter IDs
    best_region_id = get_dc_id(best_region)
    mmfg_dc_id = get_dc_id(mmfg_dc)

    if isinstance(robust_result, dict):
        robust_dc = robust_result.get("datacenter")
        robust_dc_id = get_dc_id(robust_dc)

        if robust_dc_id is None:
            robust_dc_id = robust_result.get("id")
    else:
        robust_dc_id = get_dc_id(robust_result)

    # Build candidate datacenters using original dictionaries
    candidate_datacenters = []

    for dc_id in [
        best_region_id,
        mmfg_dc_id,
        robust_dc_id
    ]:
        if dc_id:
            for dc in datacenters:
                if dc["id"] == dc_id:
                    if dc not in candidate_datacenters:
                        candidate_datacenters.append(dc)
                    break

    if not candidate_datacenters:
        return {
            "status": "failed",
            "message": "No candidate datacenters available."
        }

    # Baseline simulation
    baseline_simulation = simulate_multi_idc(
        datacenters=candidate_datacenters,
        total_power_kw=workload.power_kw,
        duration_hours=workload.duration_hours
    )

    # Select optimized datacenter
    optimized_id = mmfg_dc_id

    if isinstance(robust_result, dict):
        if robust_result.get("stable", False):
            if robust_dc_id:
                optimized_id = robust_dc_id
    elif robust_dc_id:
        optimized_id = robust_dc_id

    # Make sure optimized ID exists
    candidate_ids = [
        dc["id"] for dc in candidate_datacenters
    ]

    if optimized_id not in candidate_ids:
        optimized_id = candidate_ids[0]

    # Optimized simulation
    optimized_simulation = simulate_multi_idc(
        datacenters=candidate_datacenters,
        total_power_kw=workload.power_kw,
        duration_hours=workload.duration_hours,
        allocations={
            optimized_id: 1.0
        }
    )

    # Read simulation totals
    baseline_totals = baseline_simulation["totals"]
    optimized_totals = optimized_simulation["totals"]

    baseline_carbon = baseline_totals["total_carbon_emissions"]
    optimized_carbon = optimized_totals["total_carbon_emissions"]

    baseline_cost = baseline_totals["total_electricity_cost"]
    optimized_cost = optimized_totals["total_electricity_cost"]

    # Carbon reduction
    carbon_reduction = 0

    if baseline_carbon > 0:
        carbon_reduction = (
            (baseline_carbon - optimized_carbon)
            / baseline_carbon
        ) * 100

    # Cost change
    cost_change = 0

    if baseline_cost > 0:
        cost_change = (
            (optimized_cost - baseline_cost)
            / baseline_cost
        ) * 100

    return {
        "status": "success",

        "workload": {
            "type": workload_type,
            "power_kw": power_kw,
            "duration_hours": duration_hours,
            "energy_kwh": energy,
            "latency_max_ms": latency_max_ms,
            "budget": budget,
            "workload_demand": workload_demand
        },

        "stage1": {
            "recommended_datacenter": best_region_id
        },

        "stage2": {
            "selected_datacenter": mmfg_dc_id,
            "best_zone": mmfg_result.get("best_zone")
        },

        "stage3": {
            "recommendation": robust_dc_id,
            "stable": (
                robust_result.get("stable", False)
                if isinstance(robust_result, dict)
                else False
            )
        },

        "final_recommendation": optimized_id,

        "metrics": {
            "baseline_carbon": baseline_carbon,
            "optimized_carbon": optimized_carbon,
            "carbon_reduction_percent": carbon_reduction,
            "baseline_cost": baseline_cost,
            "optimized_cost": optimized_cost,
            "cost_change_percent": cost_change
        }
    }