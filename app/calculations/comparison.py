def calculate_reduction(baseline_value, optimized_value):
    if baseline_value < 0 or optimized_value < 0:
        raise ValueError("Values cannot be negative.")

    reduction = baseline_value - optimized_value

    if baseline_value == 0:
        percentage = 0.0
    else:
        percentage = (reduction / baseline_value) * 100

    return {
        "reduction": reduction,
        "percentage": percentage
    }


def compare_datacenters(
    baseline,
    optimized,
    energy_kwh
):
    baseline_carbon = (
        energy_kwh * baseline["carbon_intensity"]
    )

    optimized_carbon = (
        energy_kwh * optimized["carbon_intensity"]
    )

    baseline_cost = (
        energy_kwh * baseline["electricity_price"]
    )

    optimized_cost = (
        energy_kwh * optimized["electricity_price"]
    )

    carbon_result = calculate_reduction(
        baseline_carbon,
        optimized_carbon
    )

    cost_result = calculate_reduction(
        baseline_cost,
        optimized_cost
    )

    return {
        "baseline": {
            "datacenter": baseline["id"],
            "region": baseline["region"],
            "carbon_emissions": baseline_carbon,
            "electricity_cost": baseline_cost
        },
        "optimized": {
            "datacenter": optimized["id"],
            "region": optimized["region"],
            "carbon_emissions": optimized_carbon,
            "electricity_cost": optimized_cost
        },
        "carbon_reduction": carbon_result["reduction"],
        "carbon_reduction_percentage": carbon_result["percentage"],
        "cost_reduction": cost_result["reduction"],
        "cost_reduction_percentage": cost_result["percentage"]
    }