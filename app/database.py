from supabase_client import supabase


def save_optimization_run(result):

    workload = result["workload"]

    run_data = {
        "workload_type": workload.workload_type,
        "power_kw": workload.power_kw,
        "duration_hours": workload.duration_hours,
        "energy_kwh": result["energy"],
        "latency_max_ms": workload.latency_max_ms,
        "budget": workload.budget,
        "workload_demand": workload.workload_demand,
        "baseline_carbon": result["baseline_carbon"],
        "optimized_carbon": result["optimized_carbon"],
        "carbon_reduction_percent": result["carbon_reduction"],
        "baseline_cost": result["baseline_cost"],
        "optimized_cost": result["optimized_cost"],
        "cost_change_percent": result["cost_change"]
    }

    response = (
        supabase
        .table("optimization_runs")
        .insert(run_data)
        .execute()
    )

    run_id = response.data[0]["id"]


    # ---------------------------------------------------------
    # STAGE 1
    # ---------------------------------------------------------

    stage1 = result["best_region"]

    scheduler_data = {
        "optimization_run_id": run_id,
        "datacenter": stage1["id"],
        "region": stage1["region"],
        "grid_zone": stage1["zoneKey"],
        "carbon_emissions": stage1["carbon_emissions"],
        "electricity_cost": stage1["electricity_cost"],
        "optimization_score": stage1["score"]
    }

    supabase \
        .table("scheduler_results") \
        .insert(scheduler_data) \
        .execute()


    # ---------------------------------------------------------
    # MMFG
    # ---------------------------------------------------------

    mmfg = result["mmfg_result"]

    selected_dc = mmfg["selected_datacenter"]

    selected_zone = mmfg["best_zone"]

    mmfg_data = {
        "optimization_run_id": run_id,
        "datacenter": selected_dc["id"],
        "region": selected_dc["region"],
        "grid_zone": selected_zone,
        "attractiveness": mmfg["attractiveness"].get(
            selected_zone,
            0
        ),
        "population": mmfg["population"].get(
            selected_zone,
            0
        ),
        "iterations": mmfg["iterations"],
        "converged": mmfg["converged"]
    }

    supabase \
        .table("mmfg_results") \
        .insert(mmfg_data) \
        .execute()


    # ---------------------------------------------------------
    # ROBUST OPTIMIZATION
    # ---------------------------------------------------------

    robust = result["robust_result"]

    if robust is not None:

        robust_data = {
            "optimization_run_id": run_id,
            "datacenter": robust["datacenter_id"],
            "worst_case_scenario":
                robust["worst_case_scenario"],
            "worst_case_co2":
                robust["worst_case_co2"],
            "worst_case_cost":
                robust["worst_case_cost"],
            "worst_case_score":
                robust["worst_case_score"],
            "stable":
                robust["stable"]
        }

        supabase \
            .table("robust_results") \
            .insert(robust_data) \
            .execute()


    # ---------------------------------------------------------
    # CANDIDATE DATACENTERS
    # ---------------------------------------------------------

    candidate_datacenters = result[
        "candidate_datacenters"
    ]

    candidate_rows = []

    for dc in candidate_datacenters:

        candidate_rows.append({

            "optimization_run_id":
                run_id,

            "datacenter":
                dc["id"],

            "region":
                dc["region"],

            "grid_zone":
                dc["zoneKey"],

            "carbon_intensity":
                dc["carbon_intensity"],

            "electricity_price":
                dc["electricity_price"]
        })

    if candidate_rows:

        supabase \
            .table("candidate_datacenters") \
            .insert(candidate_rows) \
            .execute()


    # ---------------------------------------------------------
    # TOP 10 CARBON DATACENTERS
    # ---------------------------------------------------------

    top_10 = result[
        "top_10_datacenters"
    ]

    top_10_rows = []

    for rank, dc in enumerate(
        top_10,
        1
    ):

        top_10_rows.append({

            "optimization_run_id":
                run_id,

            "rank":
                rank,

            "datacenter":
                dc["datacenter"],

            "region":
                dc["region"],

            "carbon_intensity":
                dc["carbon_intensity"],

            "carbon_emissions":
                dc["carbon_emissions"]
        })

    if top_10_rows:

        supabase \
            .table("top_carbon_datacenters") \
            .insert(top_10_rows) \
            .execute()


    return run_id
def get_optimization_history():

    response = (
        supabase
        .table("optimization_runs")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )

    return response.data


def get_top_carbon_datacenters(run_id):

    response = (
        supabase
        .table("top_carbon_datacenters")
        .select("*")
        .eq("optimization_run_id", run_id)
        .order("rank")
        .execute()
    )

    return response.data