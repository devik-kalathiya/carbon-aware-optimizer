from app.optimizer.scheduler import recommend_region


def generate_scenarios(
    carbon_uncertainty=0.10,
    price_uncertainty=0.10,
    workload_uncertainty=0.10
):
    """
    Generate uncertainty scenarios for robust optimization.
    """

    scenarios = [
        {
            "name": "optimistic",
            "carbon_factor": 1 - carbon_uncertainty,
            "price_factor": 1 - price_uncertainty,
            "workload_factor": 1 - workload_uncertainty,
        },
        {
            "name": "nominal",
            "carbon_factor": 1.0,
            "price_factor": 1.0,
            "workload_factor": 1.0,
        },
        {
            "name": "pessimistic",
            "carbon_factor": 1 + carbon_uncertainty,
            "price_factor": 1 + price_uncertainty,
            "workload_factor": 1 + workload_uncertainty,
        },
    ]

    return scenarios


def evaluate_robust_scenarios(
    datacenters,
    power_kw,
    duration_hours,
    weights=None,
    latency_max_ms=None,
    budget=None,
    workload_demand=None,
    carbon_uncertainty=0.10,
    price_uncertainty=0.10,
    workload_uncertainty=0.10
):
    """
    Run the carbon-aware scheduler under multiple
    uncertainty scenarios.
    """

    scenarios = generate_scenarios(
        carbon_uncertainty=carbon_uncertainty,
        price_uncertainty=price_uncertainty,
        workload_uncertainty=workload_uncertainty
    )

    results = []

    for scenario in scenarios:

        # Apply workload uncertainty
        scenario_power = (
            power_kw * scenario["workload_factor"]
        )

        # Run scheduler for this scenario
        best = recommend_region(
            regions=datacenters,
            power_kw=scenario_power,
            duration_hours=duration_hours,
            weights=weights,
            latency_max_ms=latency_max_ms,
            budget=budget,
            workload_demand=workload_demand,
            carbon_uncertainty_pct=(
            scenario["carbon_factor"] - 1
    ),
    cost_uncertainty_pct=(
        scenario["price_factor"] - 1
    )
        )

        if best is None:
            continue

        results.append({
            "scenario": scenario["name"],
            "datacenter_id": best["id"],
            "provider": best["provider"],
            "region": best["region"],
            "zoneKey": best["zoneKey"],
            "country": best["country"],
            "carbon_intensity": best["carbon_intensity"],
            "electricity_price": best["electricity_price"],
            "renewable_pct": best["renewable_pct"],
            "energy_kwh": best["energy_kwh"],
            "carbon_emissions": best["carbon_emissions"],
            "electricity_cost": best["electricity_cost"],
            "score": best["score"]
        })

    return results


def get_robust_recommendation(results):
    """
    Select the robust recommendation based on
    worst-case scenario performance.
    """

    if not results:
        return None

    # Find the scenario with the highest CO2 emissions
    worst_case = max(
        results,
        key=lambda x: x["carbon_emissions"]
    )

    # Check whether the same datacenter was selected
    # in every scenario
    datacenter_ids = {
        result["datacenter_id"]
        for result in results
    }

    stable = len(datacenter_ids) == 1

    return {
        "datacenter_id": worst_case["datacenter_id"],
        "provider": worst_case["provider"],
        "region": worst_case["region"],
        "zoneKey": worst_case["zoneKey"],
        "country": worst_case["country"],
        "worst_case_scenario": worst_case["scenario"],
        "worst_case_co2": worst_case["carbon_emissions"],
        "worst_case_cost": worst_case["electricity_cost"],
        "worst_case_score": worst_case["score"],
        "stable": stable
    }