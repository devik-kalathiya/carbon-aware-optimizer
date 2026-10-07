from database import supabase

data = {
    "workload_type": "test",
    "power_kw": 1.0,
    "duration_hours": 1.0,
    "energy_kwh": 1.0,
    "baseline_carbon": 100.0,
    "optimized_carbon": 80.0,
    "carbon_reduction_percent": 20.0,
    "baseline_cost": 10.0,
    "optimized_cost": 8.0,
    "cost_change_percent": -20.0
}

response = (
    supabase
    .table("optimization_runs")
    .insert(data)
    .execute()
)

print(response.data)