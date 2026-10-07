""" from mmfg.mean_field import (
    get_workload_classes,
    get_default_population,
    validate_population
)


workloads = get_workload_classes()
population = get_default_population()

validate_population(population)


print("=== MMFG Workload Population ===")

for key, workload in workloads.items():

    percentage = population[key] * 100

    print(
        f"{workload['name']:<30} : "
        f"{percentage:5.1f}%"
    )

print()
print(
    f"Total Population             : "
    f"{sum(population.values()) * 100:.1f}%"
)

print("Population Valid             : YES") """

""" from mmfg.mean_field import apply_mean_field


# Initial region attractiveness
attractiveness = {
    "India": 0.90,
    "Singapore": 0.80,
    "Japan": 0.70
}


# Current workload population
region_population = {
    "India": 0.60,
    "Singapore": 0.25,
    "Japan": 0.15
}


adjusted = apply_mean_field(
    attractiveness,
    region_population,
    interaction_strength=0.5
)


print("Original Attractiveness:")
for region, score in attractiveness.items():
    print(f"{region:12} : {score:.3f}")


print("\nAdjusted Attractiveness:")
for region, score in adjusted.items():
    print(f"{region:12} : {score:.3f}") """
"""
from mmfg.mean_field import calculate_equilibrium


# ------------------------------------------------------------
# Test data
# ------------------------------------------------------------

attractiveness = {
    "India": 0.90,
    "Singapore": 0.80,
    "Japan": 0.70
}


initial_population = {
    "India": 0.60,
    "Singapore": 0.25,
    "Japan": 0.15
}


# ------------------------------------------------------------
# Calculate equilibrium
# ------------------------------------------------------------

result = calculate_equilibrium(
    attractiveness,
    initial_population,
    interaction_strength=0.5,
    learning_rate=0.5
)


# ------------------------------------------------------------
# Display result
# ------------------------------------------------------------

print("=== MMFG Iterative Equilibrium ===")

print("\nInitial Population:")

for region, population in initial_population.items():
    print(f"{region:12} : {population:.4f}")


print("\nEquilibrium Population:")

for region, population in result["population"].items():
    print(f"{region:12} : {population:.4f}")


print("\nIterations  :", result["iterations"])
print("Converged   :", result["converged"])


print(
    "\nPopulation Sum:",
    f"{sum(result['population'].values()):.6f}"
)
"""
"""
# ============================================================
# Stage 3.5 - Test MMFG with Datacenter Dataset
# ============================================================

from mmfg.datacenter_adapter import (
    load_datacenters,
    get_operational_datacenters,
    group_datacenters_by_zone,
    create_region_population
)

from mmfg.mean_field import (
    calculate_equilibrium
)


# ------------------------------------------------------------
# Load dataset
# ------------------------------------------------------------

datacenters = load_datacenters("data/datacenters.json")


print("=== MMFG Datacenter Integration Test ===")


# ------------------------------------------------------------
# Count datacenters
# ------------------------------------------------------------

print("\nTotal datacenters:", len(datacenters))


# ------------------------------------------------------------
# Keep operational datacenters
# ------------------------------------------------------------

operational = get_operational_datacenters(datacenters)

print(
    "Operational datacenters:",
    len(operational)
)


# ------------------------------------------------------------
# Group datacenters by grid zone
# ------------------------------------------------------------

zones = group_datacenters_by_zone(operational)

print(
    "Unique grid zones:",
    len(zones)
)


# ------------------------------------------------------------
# Initial population
# ------------------------------------------------------------

population = create_region_population(operational)


print("\nInitial Population Distribution:")

for zone, value in sorted(
    population.items(),
    key=lambda x: x[1],
    reverse=True
):
    print(
        f"{zone:15} : "
        f"{value:.4f}"
    )


# ------------------------------------------------------------
# Create initial attractiveness
# ------------------------------------------------------------
#
# For this integration test, every zone starts with
# equal base attractiveness.
#
# Real carbon/grid attractiveness will be introduced
# when grid.json is connected.
# ------------------------------------------------------------

attractiveness = {
    zone: 1.0
    for zone in population
}


# ------------------------------------------------------------
# Calculate MMFG equilibrium
# ------------------------------------------------------------

result = calculate_equilibrium(
    attractiveness=attractiveness,
    initial_population=population,
    interaction_strength=0.5,
    learning_rate=0.5
)


# ------------------------------------------------------------
# Results
# ------------------------------------------------------------

print("\n=== Equilibrium Result ===")

print(
    "Iterations:",
    result["iterations"]
)

print(
    "Converged :",
    result["converged"]
)

print("\nFinal Population:")

for zone, value in sorted(
    result["population"].items(),
    key=lambda x: x[1],
    reverse=True
):
    print(
        f"{zone:15} : "
        f"{value:.4f}"
    )


print(
    "\nPopulation Sum:",
    f"{sum(result['population'].values()):.6f}"
)
"""
"""
from mmfg.grid_adapter import (
    load_grid_zones,
    get_carbon_intensity,
    get_electricity_price,
    get_renewable_percentage,
    calculate_carbon_score
)


grid_zones = load_grid_zones(
    "data/grid_zones.json"
)

print("=== Grid Zone Adapter Test ===")

print("\nTotal grid zones:", len(grid_zones))


carbon = get_carbon_intensity(grid_zones)
price = get_electricity_price(grid_zones)
renewable = get_renewable_percentage(grid_zones)
carbon_score = calculate_carbon_score(grid_zones)


print("Carbon intensity values:", len(carbon))
print("Electricity price values:", len(price))
print("Renewable percentage values:", len(renewable))


print("\nSample Carbon Data:")

for zone in list(carbon.keys())[:10]:
    print(
        f"{zone:15} : "
        f"{carbon[zone]:.2f} gCO2/kWh"
    )


print("\nSample Carbon Scores:")

for zone in list(carbon_score.keys())[:10]:
    print(
        f"{zone:15} : "
        f"{carbon_score[zone]:.4f}"
    )"""
"""
# ============================================================
# Stage 3.6 - Carbon-Aware Attractiveness Test
# ============================================================

from mmfg.grid_adapter import load_grid_zones
from mmfg.attractiveness import calculate_attractiveness


grid_zones = load_grid_zones(
    "data/grid_zones.json"
)

attractiveness = calculate_attractiveness(
    grid_zones
)

print("=== Carbon-Aware Attractiveness Test ===")

print(
    "\nTotal zones:",
    len(attractiveness)
)

print("\nTop 10 Most Attractive Zones:")

top_zones = sorted(
    attractiveness.items(),
    key=lambda x: x[1],
    reverse=True
)

for zone, score in top_zones[:10]:

    carbon = grid_zones[zone]["carbon_intensity"]
    renewable = grid_zones[zone]["renewable_pct"]
    cost = grid_zones[zone]["electricity_price"]

    print(
        f"{zone:15} : "
        f"Attractiveness={score:.4f} | "
        f"Carbon={carbon:.1f} | "
        f"Renewable={renewable:.1f}% | "
        f"Price={cost:.2f}"
    )


print("\nBottom 10 Least Attractive Zones:")

for zone, score in top_zones[-10:]:

    carbon = grid_zones[zone]["carbon_intensity"]
    renewable = grid_zones[zone]["renewable_pct"]
    cost = grid_zones[zone]["electricity_price"]

    print(
        f"{zone:15} : "
        f"Attractiveness={score:.4f} | "
        f"Carbon={carbon:.1f} | "
        f"Renewable={renewable:.1f}% | "
        f"Price={cost:.2f}"
    )"""
"""
# ============================================================
# Stage 3.6 - Carbon-Aware MMFG Integration Test
# ============================================================

from mmfg.datacenter_adapter import (
    load_datacenters,
    get_operational_datacenters,
    group_datacenters_by_zone,
    create_region_population
)

from mmfg.grid_adapter import (
    load_grid_zones
)

from mmfg.attractiveness import (
    calculate_attractiveness
)

from mmfg.mean_field import (
    calculate_equilibrium
)


# ------------------------------------------------------------
# 1. Load Datacenter Dataset
# ------------------------------------------------------------

datacenters = load_datacenters(
    "data/datacenters.json"
)

operational = get_operational_datacenters(
    datacenters
)

zones = group_datacenters_by_zone(
    operational
)

print("=== Carbon-Aware MMFG Integration ===")

print("\nDatacenter Information:")
print("Total datacenters      :", len(datacenters))
print("Operational datacenters:", len(operational))
print("Grid zones             :", len(zones))


# ------------------------------------------------------------
# 2. Create Initial Population
# ------------------------------------------------------------

initial_population = create_region_population(
    operational
)

print(
    "\nInitial Population Sum:",
    f"{sum(initial_population.values()):.6f}"
)


# ------------------------------------------------------------
# 3. Load Grid-Zone Dataset
# ------------------------------------------------------------

grid_zones = load_grid_zones(
    "data/grid_zones.json"
)

print(
    "Grid dataset zones     :",
    len(grid_zones)
)


# ------------------------------------------------------------
# 4. Calculate Carbon-Aware Attractiveness
# ------------------------------------------------------------

attractiveness = calculate_attractiveness(
    grid_zones,
    carbon_weight=0.60,
    renewable_weight=0.25,
    cost_weight=0.15
)


# ------------------------------------------------------------
# 5. Keep Only Zones Available in Both Datasets
# ------------------------------------------------------------

common_zones = (
    set(initial_population.keys())
    & set(attractiveness.keys())
)

if not common_zones:
    raise ValueError(
        "No common grid zones found between "
        "datacenter.json and grid_zones.json."
    )


initial_population = {
    zone: initial_population[zone]
    for zone in common_zones
}


attractiveness = {
    zone: attractiveness[zone]
    for zone in common_zones
}


# Re-normalize population after removing unmatched zones.

population_sum = sum(
    initial_population.values()
)

initial_population = {
    zone: value / population_sum
    for zone, value in initial_population.items()
}


print(
    "Common zones           :",
    len(common_zones)
)

print(
    "Population Sum         :",
    f"{sum(initial_population.values()):.6f}"
)


# ------------------------------------------------------------
# 6. Run MMFG Equilibrium
# ------------------------------------------------------------

result = calculate_equilibrium(
    attractiveness=attractiveness,
    initial_population=initial_population,
    interaction_strength=0.5,
    learning_rate=0.5
)


# ------------------------------------------------------------
# 7. Display Results
# ------------------------------------------------------------

print("\n=== MMFG Equilibrium Result ===")

print(
    "Iterations             :",
    result["iterations"]
)

print(
    "Converged              :",
    result["converged"]
)

print(
    "Final Population Sum   :",
    f"{sum(result['population'].values()):.6f}"
)


# ------------------------------------------------------------
# 8. Display Top Zones
# ------------------------------------------------------------

print("\n=== Top 10 Final Workload Zones ===")

final_population = sorted(
    result["population"].items(),
    key=lambda x: x[1],
    reverse=True
)

for zone, population in final_population[:10]:

    carbon = grid_zones[zone]["carbon_intensity"]
    renewable = grid_zones[zone]["renewable_pct"]
    price = grid_zones[zone]["electricity_price"]
    score = attractiveness[zone]

    print(
        f"{zone:15} : "
        f"Population={population:.4f} | "
        f"Attractiveness={score:.4f} | "
        f"Carbon={carbon:.1f} | "
        f"Renewable={renewable:.1f}% | "
        f"Price={price:.2f}"
    )


# ------------------------------------------------------------
# 9. Display Bottom Zones
# ------------------------------------------------------------

print("\n=== Bottom 10 Final Workload Zones ===")

for zone, population in final_population[-10:]:

    carbon = grid_zones[zone]["carbon_intensity"]
    renewable = grid_zones[zone]["renewable_pct"]
    price = grid_zones[zone]["electricity_price"]
    score = attractiveness[zone]

    print(
        f"{zone:15} : "
        f"Population={population:.4f} | "
        f"Attractiveness={score:.4f} | "
        f"Carbon={carbon:.1f} | "
        f"Renewable={renewable:.1f}% | "
        f"Price={price:.2f}"
    )"""

# ============================================================
# Stage 3.7 - MMFG Scheduler Router Test
# ============================================================

from mmfg.datacenter_adapter import (
    load_datacenters,
    get_operational_datacenters,
    create_region_population
)

from mmfg.grid_adapter import (
    load_grid_zones
)

from mmfg.attractiveness import (
    calculate_attractiveness
)

from mmfg.scheduler_router import (
    route_workload
)


# ------------------------------------------------------------
# Load datasets
# ------------------------------------------------------------

datacenters = load_datacenters(
    "data/datacenters.json"
)

operational = get_operational_datacenters(
    datacenters
)

grid_zones = load_grid_zones(
    "data/grid_zones.json"
)


# ------------------------------------------------------------
# Initial population
# ------------------------------------------------------------

initial_population = create_region_population(
    operational
)


# ------------------------------------------------------------
# Carbon-aware attractiveness
# ------------------------------------------------------------

attractiveness = calculate_attractiveness(
    grid_zones
)


# ------------------------------------------------------------
# Keep common zones
# ------------------------------------------------------------

common_zones = (
    set(initial_population.keys())
    & set(attractiveness.keys())
)

initial_population = {
    zone: initial_population[zone]
    for zone in common_zones
}

attractiveness = {
    zone: attractiveness[zone]
    for zone in common_zones
}


# Re-normalize population

total = sum(
    initial_population.values()
)

initial_population = {
    zone: value / total
    for zone, value in initial_population.items()
}


# ------------------------------------------------------------
# Route workload using MMFG
# ------------------------------------------------------------

routing = route_workload(
    initial_population,
    attractiveness,
    interaction_strength=0.5,
    learning_rate=0.5
)


# ------------------------------------------------------------
# Display result
# ------------------------------------------------------------

print("=== MMFG Scheduler Router ===")

print("\nBest Grid Zone:")
print(
    "Zone        :",
    routing["best_zone"]
)

print(
    "Population  :",
    f"{routing['best_population']:.4f}"
)

print(
    "Attractiveness:",
    f"{attractiveness[routing['best_zone']]:.4f}"
)

best_zone = routing["best_zone"]

print(
    "Carbon      :",
    f"{grid_zones[best_zone]['carbon_intensity']:.1f} gCO2/kWh"
)

print(
    "Renewable   :",
    f"{grid_zones[best_zone]['renewable_pct']:.1f}%"
)

print(
    "Price       :",
    f"₹{grid_zones[best_zone]['electricity_price']:.2f}/kWh"
)


# ------------------------------------------------------------
# Top 10 recommendations
# ------------------------------------------------------------

print("\n=== Top 10 Recommended Zones ===")

for rank, (zone, population) in enumerate(
    routing["ranked_zones"][:10],
    start=1
):

    print(
        f"{rank:2}. "
        f"{zone:15} | "
        f"Population={population:.4f} | "
        f"Attractiveness={attractiveness[zone]:.4f} | "
        f"Carbon={grid_zones[zone]['carbon_intensity']:.1f}"
    )


print("\nMMFG Information:")
print(
    "Iterations:",
    routing["iterations"]
)

print(
    "Converged :",
    routing["converged"]
)