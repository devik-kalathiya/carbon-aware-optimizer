from data.data_loader import get_datacenters_with_carbon_data
from optimizer.scheduler import recommend_region
from calculations.comparison import (
    calculate_co2_savings,
    calculate_co2_savings_percentage
)

# Load real datacenter + grid-zone data
datacenters = get_datacenters_with_carbon_data()

# -----------------------------
# User workload (test input)
# -----------------------------
power_kw = 0.8
duration_hours = 2

# Calculate energy
energy_kwh = power_kw * duration_hours

# -----------------------------
# BASELINE
# -----------------------------
# Baseline = first operational datacenter
baseline = datacenters[0]

baseline_co2 = (
    energy_kwh * baseline["carbon_intensity"]
)

baseline_cost = (
    energy_kwh * baseline["electricity_price"]
)

# -----------------------------
# CARBON-AWARE OPTIMIZATION
# -----------------------------
best = recommend_region(
    regions=datacenters,
    power_kw=power_kw,
    duration_hours=duration_hours,
    weights={
        "carbon": 0.40,
        "cost": 0.20,
        "latency": 0.10,
        "renewable": 0.30,
    }
)

if best is None:
    print("No suitable datacenter found.")
    exit()

# Optimized values
optimized_co2 = best["carbon_emissions"]
optimized_cost = best["electricity_cost"]

# -----------------------------
# COMPARISON
# -----------------------------
co2_saved = calculate_co2_savings(
    baseline_co2,
    optimized_co2
)

co2_savings_percentage = calculate_co2_savings_percentage(
    baseline_co2,
    optimized_co2
)

cost_saved = baseline_cost - optimized_cost

# -----------------------------
# OUTPUT
# -----------------------------
print("=== Real Dataset Stage 1 Test ===")
print(f"Total Datacenters : {len(datacenters)}")

print()
print("=== Workload ===")
print(f"Power               : {power_kw} kW")
print(f"Duration            : {duration_hours} hours")
print(f"Energy              : {energy_kwh:.2f} kWh")

print()
print("=== Baseline ===")
print(f"Datacenter          : {baseline['id']}")
print(f"Provider            : {baseline['provider']}")
print(f"Region              : {baseline['region']}")
print(f"Grid Zone           : {baseline['zoneKey']}")
print(f"Country             : {baseline['country']}")
print(f"Carbon Intensity    : {baseline['carbon_intensity']} gCO2/kWh")
print(f"Electricity Price   : ₹{baseline['electricity_price']}/kWh")
print(f"CO2 Emissions       : {baseline_co2:.2f} gCO2")
print(f"Electricity Cost    : ₹{baseline_cost:.2f}")

print()
print("=== Carbon-Aware Optimization ===")
print(f"ID                  : {best['id']}")
print(f"Provider             : {best['provider']}")
print(f"Region               : {best['region']}")
print(f"Grid Zone            : {best['zoneKey']}")
print(f"Country              : {best['country']}")
print(f"Carbon Intensity     : {best['carbon_intensity']} gCO2/kWh")
print(f"Renewable            : {best['renewable_pct']}%")
print(f"Electricity Price    : ₹{best['electricity_price']}/kWh")
print(f"CO2 Emissions        : {optimized_co2:.2f} gCO2")
print(f"Electricity Cost     : ₹{optimized_cost:.2f}")
print(f"Optimization Score   : {best['score']:.4f}")

print()
print("=== Improvement ===")
print(f"CO2 Saved            : {co2_saved:.2f} gCO2")
print(f"CO2 Reduction        : {co2_savings_percentage:.2f}%")
print(f"Cost Saved           : ₹{cost_saved:.2f}")