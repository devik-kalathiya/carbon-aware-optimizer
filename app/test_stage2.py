from data.data_loader import get_datacenters_with_carbon_data

from uncertainty.robust import (
    evaluate_robust_scenarios,
    get_robust_recommendation
)


# --------------------------------------------------
# Load real datacenter + grid-zone data
# --------------------------------------------------

datacenters = get_datacenters_with_carbon_data()


# --------------------------------------------------
# Example workload
# --------------------------------------------------

power_kw = 0.8
duration_hours = 2


# --------------------------------------------------
# Same weights used in Stage 1
# --------------------------------------------------

weights = {
    "carbon": 0.40,
    "cost": 0.20,
    "latency": 0.10,
    "renewable": 0.30,
}


# --------------------------------------------------
# Run robust optimization
# --------------------------------------------------

results = evaluate_robust_scenarios(
    datacenters=datacenters,
    power_kw=power_kw,
    duration_hours=duration_hours,
    weights=weights,
    carbon_uncertainty=0.10,
    price_uncertainty=0.10,
    workload_uncertainty=0.10
)


# --------------------------------------------------
# Print basic information
# --------------------------------------------------

print("=== Stage 2 Robust Optimization ===")

print(f"Total Datacenters : {len(datacenters)}")

print()
print("Uncertainty:")
print("Carbon            : ±10%")
print("Electricity Price : ±10%")
print("Workload          : ±10%")


# --------------------------------------------------
# Print scenario results
# --------------------------------------------------

print()
print("=== Scenario Results ===")

for result in results:

    print()

    print(f"Scenario            : {result['scenario']}")
    print(f"Datacenter          : {result['datacenter_id']}")
    print(f"Provider             : {result['provider']}")
    print(f"Region               : {result['region']}")
    print(f"Grid Zone            : {result['zoneKey']}")
    print(f"Country              : {result['country']}")

    print(
        f"Carbon Intensity    : "
        f"{result['carbon_intensity']:.2f} gCO2/kWh"
    )

    print(
        f"Renewable           : "
        f"{result['renewable_pct']}%"
    )

    print(
        f"Electricity Price   : "
        f"₹{result['electricity_price']:.2f}/kWh"
    )

    print(
        f"Energy              : "
        f"{result['energy_kwh']:.2f} kWh"
    )

    print(
        f"CO2 Emissions       : "
        f"{result['carbon_emissions']:.2f} gCO2"
    )

    print(
        f"Electricity Cost    : "
        f"₹{result['electricity_cost']:.2f}"
    )

    print(
        f"Score               : "
        f"{result['score']:.4f}"
    )


# --------------------------------------------------
# Get robust recommendation
# IMPORTANT: This is outside the loop
# --------------------------------------------------

robust = get_robust_recommendation(results)


# --------------------------------------------------
# Print robust recommendation
# --------------------------------------------------

print()
print("=== Robust Recommendation ===")

if robust is None:

    print("No feasible robust recommendation found.")

else:

    print(
        f"Datacenter          : "
        f"{robust['datacenter_id']}"
    )

    print(
        f"Provider             : "
        f"{robust['provider']}"
    )

    print(
        f"Region               : "
        f"{robust['region']}"
    )

    print(
        f"Grid Zone            : "
        f"{robust['zoneKey']}"
    )

    print(
        f"Country              : "
        f"{robust['country']}"
    )

    print()

    print(
        f"Worst-Case Scenario : "
        f"{robust['worst_case_scenario']}"
    )

    print(
        f"Worst-Case CO2      : "
        f"{robust['worst_case_co2']:.2f} gCO2"
    )

    print(
        f"Worst-Case Cost     : "
        f"₹{robust['worst_case_cost']:.2f}"
    )

    print(
        f"Worst-Case Score    : "
        f"{robust['worst_case_score']:.4f}"
    )

    print()

    print(
        f"Decision Stable     : "
        f"{'YES' if robust['stable'] else 'NO'}"
    )