import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import os
import json
from io import BytesIO
from datetime import datetime

import streamlit as st

from optimizer.scheduler import recommend_region

from data.data_loader import get_datacenters_with_carbon_data
from data.grid_zone_loader import load_grid_zones
from database import (
    save_optimization_run,
    get_optimization_history,
    get_top_carbon_datacenters
)

from calculations.energy import calculate_energy

from models.workload import create_workload, get_workload_classes

from mmfg.integration import run_mmfg_routing
from ai.constraint_analyzer import analyze_constraint_failure

from uncertainty.robust import (
    evaluate_robust_scenarios,
    get_robust_recommendation
)

from simulation.multi_idc import simulate_multi_idc

from visualization.charts import (
    create_carbon_comparison,
    create_cost_comparison,
    create_multi_idc_carbon_chart,
    create_workload_allocation_chart
)


st.set_page_config(
    page_title="Carbon-Aware Workload Scheduler",
    page_icon="🌱",
    layout="wide"
)
st.markdown(
    """
    <style>

    .section-title {
        font-size: 24px;
        font-weight: 700;
        margin-top: 25px;
        margin-bottom: 15px;
    }

    .card {
        padding: 20px;
        border-radius: 14px;
        border: 1px solid rgba(128, 128, 128, 0.25);
        background-color: rgba(128, 128, 128, 0.06);
        margin-bottom: 15px;
    }

    .card-title {
        font-size: 14px;
        font-weight: 600;
        opacity: 0.7;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .card-value {
        font-size: 24px;
        font-weight: 700;
        margin-top: 5px;
    }

    .card-subtitle {
        font-size: 13px;
        opacity: 0.65;
        margin-top: 3px;
    }

    .hero-card {
        padding: 25px;
        border-radius: 16px;
        border: 1px solid rgba(128, 128, 128, 0.25);
        background-color: rgba(128, 128, 128, 0.06);
        margin-bottom: 20px;
    }

    .hero-title {
        font-size: 28px;
        font-weight: 750;
    }

    .hero-subtitle {
        font-size: 15px;
        opacity: 0.7;
    }

    </style>
    """,
    unsafe_allow_html=True
)

st.title("🌱 Carbon-Aware Workload Scheduler")
st.caption(
    "Carbon-aware workload scheduling, MMFG routing "
    "and robust optimization"
)


# ============================================================
# SIDEBAR - WORKLOAD INPUT
# ============================================================

st.sidebar.header("Workload Configuration")

workload_classes = get_workload_classes()
workload_names = list(workload_classes.keys())

workload_type = st.sidebar.selectbox(
    "Workload Type",
    workload_names
)

power = st.sidebar.number_input(
    "Power (kW)",
    min_value=0.01,
    value=10.0,
    step=0.5
)

duration = st.sidebar.number_input(
    "Duration (hours)",
    min_value=0.01,
    value=6.0,
    step=0.5
)

latency_enabled = st.sidebar.checkbox(
    "Set maximum latency"
)

latency_max_ms = None

if latency_enabled:
    latency_max_ms = st.sidebar.number_input(
        "Maximum Latency (ms)",
        min_value=0.1,
        value=100.0,
        step=1.0
    )


budget_enabled = st.sidebar.checkbox(
    "Set budget"
)

budget = None

if budget_enabled:
    budget = st.sidebar.number_input(
        "Budget (₹)",
        min_value=0.01,
        value=500.0,
        step=10.0
    )


demand_enabled = st.sidebar.checkbox(
    "Set workload demand"
)

workload_demand = None

if demand_enabled:
    workload_demand = st.sidebar.number_input(
        "Workload Demand",
        min_value=0.01,
        value=10.0,
        step=1.0
    )


run_button = st.sidebar.button(
    "Run Optimization",
    type="primary",
    use_container_width=True
)


# ============================================================
# SESSION STATE
# ============================================================

if "optimization_result" not in st.session_state:
    st.session_state.optimization_result = None


# ============================================================
# RUN OPTIMIZATION
# ============================================================

if run_button:

    with st.spinner("Running carbon-aware optimization..."):

        energy = calculate_energy(
            power,
            duration
        )

        datacenters = get_datacenters_with_carbon_data()
        grid_zones = load_grid_zones()

        workload = create_workload(
            power_kw=power,
            duration_hours=duration,
            latency_max_ms=latency_max_ms,
            budget=budget,
            workload_type=workload_type,
            workload_demand=workload_demand
        )

        # ====================================================
        # STAGE 1 - CARBON-AWARE SCHEDULER
        # ====================================================

        weights = {
            "carbon": 0.40,
            "cost": 0.20,
            "latency": 0.10,
            "renewable": 0.30
        }

        best_region = recommend_region(
            regions=datacenters,
            power_kw=workload.power_kw,
            duration_hours=workload.duration_hours,
            weights=weights,
            latency_max_ms=workload.latency_max_ms,
            budget=workload.budget,
            workload_demand=workload.workload_demand
        )


        # ====================================================
        # GROQ CONSTRAINT RELAXATION
        # ====================================================

        groq_result = None

        if best_region is None:

            try:

                groq_result = analyze_constraint_failure(
                    workload_type=workload_type,
                    power_kw=workload.power_kw,
                    duration_hours=duration,
                    latency_max_ms=latency_max_ms,
                    budget=budget,
                    workload_demand=workload_demand
                )

                constraint = groq_result.get(
                    "constraint"
                )

                suggested_value = groq_result.get(
                    "suggested_value"
                )

                if constraint == "budget":

                    workload.budget = float(
                        suggested_value
                    )

                elif constraint == "latency":

                    workload.latency_max_ms = float(
                        suggested_value
                    )

                elif constraint == "workload_demand":

                    workload.workload_demand = float(
                        suggested_value
                    )


                best_region = recommend_region(
                    regions=datacenters,
                    power_kw=workload.power_kw,
                    duration_hours=workload.duration_hours,
                    weights=weights,
                    latency_max_ms=workload.latency_max_ms,
                    budget=workload.budget,
                    workload_demand=workload.workload_demand
                )

            except Exception as error:

                st.error(
                    f"Constraint analysis failed: {error}"
                )


        if best_region is None:

            st.error(
                "No suitable datacenter found."
            )

            st.stop()


        # ====================================================
        # STAGE 2 - MMFG ROUTING
        # ====================================================

        mmfg_result = run_mmfg_routing(
            datacenters=datacenters,
            grid_zones=grid_zones,
            workload_type=workload_type,
            interaction_strength=0.5,
            learning_rate=0.5
        )

        best_zone = mmfg_result["best_zone"]

        mmfg_dc = mmfg_result[
            "selected_datacenter"
        ]


        # ====================================================
        # STAGE 3 - ROBUST OPTIMIZATION
        # ====================================================

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


        # ====================================================
        # CANDIDATE DATACENTERS
        # ====================================================

        stage1_id = best_region["id"]
        mmfg_id = mmfg_dc["id"]

        candidate_ids = [
            stage1_id,
            mmfg_id
        ]

        if robust_result is not None:

            stage2_id = robust_result[
                "datacenter_id"
            ]

            candidate_ids.append(
                stage2_id
            )


        candidate_datacenters = []

        for dc in datacenters:

            if dc["id"] in candidate_ids:

                if not any(
                    existing["id"] == dc["id"]
                    for existing in candidate_datacenters
                ):

                    candidate_datacenters.append(
                        dc
                    )


        # ====================================================
        # BASELINE SIMULATION
        # ====================================================

        baseline_simulation = simulate_multi_idc(
            datacenters=candidate_datacenters,
            total_power_kw=workload.power_kw,
            duration_hours=workload.duration_hours
        )


        # ====================================================
        # OPTIMIZED SIMULATION
        # ====================================================

        if (
            robust_result is not None
            and robust_result["stable"]
        ):

            optimized_id = robust_result[
                "datacenter_id"
            ]

        else:

            optimized_id = mmfg_dc["id"]


        optimized_allocations = {
            optimized_id: 1.0
        }

        optimized_simulation = simulate_multi_idc(
            datacenters=candidate_datacenters,
            total_power_kw=workload.power_kw,
            duration_hours=workload.duration_hours,
            allocations=optimized_allocations
        )


        # ====================================================
        # METRICS
        # ====================================================

        baseline_carbon = (
            baseline_simulation[
                "totals"
            ][
                "total_carbon_emissions"
            ]
        )

        optimized_carbon = (
            optimized_simulation[
                "totals"
            ][
                "total_carbon_emissions"
            ]
        )

        baseline_cost = (
            baseline_simulation[
                "totals"
            ][
                "total_electricity_cost"
            ]
        )

        optimized_cost = (
            optimized_simulation[
                "totals"
            ][
                "total_electricity_cost"
            ]
        )


        if baseline_carbon > 0:

            carbon_reduction = (
                (
                    baseline_carbon
                    - optimized_carbon
                )
                / baseline_carbon
            ) * 100

        else:

            carbon_reduction = 0


        if baseline_cost > 0:

            cost_change = (
                (
                    optimized_cost
                    - baseline_cost
                )
                / baseline_cost
            ) * 100

        else:

            cost_change = 0


        # ====================================================
        # TOP 10 LOWEST-CARBON DATACENTERS
        # ====================================================

        energy_kwh = (
            workload.power_kw
            * workload.duration_hours
        )

        carbon_comparison = []

        for dc in datacenters:

            if dc.get("carbon_intensity") is None:
                continue

            carbon_emissions = (
                energy_kwh
                * dc["carbon_intensity"]
            )

            carbon_comparison.append(
                {
                    "datacenter": dc["id"],
                    "region": dc["region"],
                    "carbon_intensity": dc[
                        "carbon_intensity"
                    ],
                    "carbon_emissions": carbon_emissions
                }
            )


        carbon_comparison.sort(
            key=lambda x: x["carbon_emissions"]
        )

        top_10_datacenters = (
            carbon_comparison[:10]
        )


        # ====================================================
        # CHARTS
        # ====================================================

        results_directory = "results"

        os.makedirs(
            results_directory,
            exist_ok=True
        )


        carbon_chart = create_carbon_comparison(
            baseline_carbon,
            optimized_carbon
        )


        cost_chart = create_cost_comparison(
            baseline_cost,
            optimized_cost
        )


        multi_idc_chart = (
            create_multi_idc_carbon_chart(
                results=top_10_datacenters
            )
        )


        optimized_results = (
            optimized_simulation["datacenters"]
        )


        allocation_chart = (
            create_workload_allocation_chart(
                results=optimized_results
            )
        )


        # ====================================================
        # STORE EVERYTHING IN SESSION STATE
        # ====================================================

        st.session_state.optimization_result = {

            "workload": workload,
            "energy": energy,

            "datacenters": datacenters,

            "best_region": best_region,

            "mmfg_result": mmfg_result,

            "robust_result": robust_result,

            "candidate_datacenters":
                candidate_datacenters,

            "baseline_simulation":
                baseline_simulation,

            "optimized_simulation":
                optimized_simulation,

            "baseline_carbon":
                baseline_carbon,

            "optimized_carbon":
                optimized_carbon,

            "baseline_cost":
                baseline_cost,

            "optimized_cost":
                optimized_cost,

            "carbon_reduction":
                carbon_reduction,

            "cost_change":
                cost_change,

            "top_10_datacenters":
                top_10_datacenters,

            "carbon_chart":
                carbon_chart,

            "cost_chart":
                cost_chart,

            "multi_idc_chart":
                multi_idc_chart,

            "allocation_chart":
                allocation_chart,

            "groq_result":
                groq_result,

            "timestamp":
                datetime.now().isoformat()
        }

        save_optimization_run(
            st.session_state.optimization_result
        )


# ============================================================
# DISPLAY DASHBOARD
# ============================================================

result = st.session_state.optimization_result


if result is None:

    st.info(
        "Configure the workload from the sidebar "
        "and click Run Optimization."
    )

    st.markdown(
        """
        ### System Workflow

        **Workload Input**
        ↓

        **Carbon-Aware Scheduler**
        ↓

        **MMFG Routing**
        ↓

        **Robust Optimization**
        ↓

        **Multi-IDC Simulation**
        ↓

        **Dashboard + Reports**
        """
    )

    st.stop()


workload = result["workload"]


# ============================================================
# WORKLOAD SUMMARY
# ============================================================

st.markdown(
    '<div class="section-title">⚙️ Workload Summary</div>',
    unsafe_allow_html=True
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">Workload</div>
            <div class="card-value">{workload.workload_type}</div>
            <div class="card-subtitle">Workload Class</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">Power</div>
            <div class="card-value">{workload.power_kw:.2f} kW</div>
            <div class="card-subtitle">Compute Power</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">Duration</div>
            <div class="card-value">{workload.duration_hours:.2f} h</div>
            <div class="card-subtitle">Execution Time</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col4:
    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">Energy</div>
            <div class="card-value">{result['energy']:.2f} kWh</div>
            <div class="card-subtitle">Estimated Energy</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ============================================================
# OPTIMIZATION SUMMARY
# ============================================================

st.header("Optimization Summary")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Baseline Carbon",
    f"{result['baseline_carbon']:.2f} gCO₂"
)

col2.metric(
    "Optimized Carbon",
    f"{result['optimized_carbon']:.2f} gCO₂"
)

col3.metric(
    "Carbon Reduction",
    f"{result['carbon_reduction']:.2f}%"
)

if result["cost_change"] > 0:

    cost_label = "Cost Increase"
    cost_value = (
        f"{result['cost_change']:.2f}%"
    )

elif result["cost_change"] < 0:

    cost_label = "Cost Reduction"
    cost_value = (
        f"{abs(result['cost_change']):.2f}%"
    )

else:

    cost_label = "Cost Change"
    cost_value = "0.00%"


col4.metric(
    cost_label,
    cost_value
)
# ============================================================
# STAGE 1
# ============================================================

st.header("Stage 1 — Carbon-Aware Scheduler")

stage1 = result["best_region"]

col1, col2, col3 = st.columns(3)

col1.metric(
    "Datacenter",
    stage1["id"]
)

col2.metric(
    "Region",
    stage1["region"]
)

col3.metric(
    "Grid Zone",
    stage1["zoneKey"]
)


st.write(
    f"**CO₂ Emissions:** "
    f"{stage1['carbon_emissions']:.2f} gCO₂"
)

st.write(
    f"**Electricity Cost:** "
    f"₹{stage1['electricity_cost']:.2f}"
)

st.write(
    f"**Optimization Score:** "
    f"{stage1['score']:.4f}"
)


# ============================================================
# MMFG
# ============================================================

st.header("Stage 2 — MMFG Routing")

mmfg = result["mmfg_result"]

col1, col2, col3 = st.columns(3)

col1.metric(
    "Recommended Datacenter",
    mmfg["selected_datacenter"]["id"]
)

col2.metric(
    "Grid Zone",
    mmfg["best_zone"]
)

col3.metric(
    "Converged",
    str(mmfg["converged"])
)


st.write(
    f"**Iterations:** {mmfg['iterations']}"
)


mmfg_rows = []

for rank, (zone, population) in enumerate(
    mmfg["top_zones"],
    1
):

    mmfg_rows.append(
        {
            "Rank": rank,
            "Grid Zone": zone,
            "Population": population,
            "Attractiveness":
                mmfg["attractiveness"].get(
                    zone,
                    0
                )
        }
    )


st.dataframe(
    mmfg_rows,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# ROBUST OPTIMIZATION
# ============================================================

st.header("Stage 3 — Robust Optimization")

robust = result["robust_result"]

if robust is not None:

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Datacenter",
        robust["datacenter_id"]
    )

    col2.metric(
        "Worst Case",
        robust["worst_case_scenario"]
    )

    col3.metric(
        "Stable",
        str(robust["stable"])
    )

    st.write(
    f"**Worst Case CO₂:** "
    f"{robust['worst_case_co2']:.2f} gCO₂"
)

    st.write(
        f"**Worst Case Cost:** "
        f"₹{robust['worst_case_cost']:.2f}"
    )

else:

    st.warning(
        "Robust optimization did not return a result."
    )


# ============================================================
# BASELINE VS OPTIMIZED
# ============================================================

st.header("Baseline vs Optimized")

comparison_data = [

    {
        "Metric": "Energy (kWh)",
        "Baseline":
            result["baseline_simulation"]
            ["totals"]["total_energy_kwh"],
        "Optimized":
            result["optimized_simulation"]
            ["totals"]["total_energy_kwh"]
    },

    {
        "Metric": "Carbon (gCO₂)",
        "Baseline":
            result["baseline_carbon"],
        "Optimized":
            result["optimized_carbon"]
    },

    {
        "Metric": "Electricity Cost (₹)",
        "Baseline":
            result["baseline_cost"],
        "Optimized":
            result["optimized_cost"]
    }
]


st.dataframe(
    comparison_data,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# CHARTS
# ============================================================

st.header("Dashboard Visualizations")


chart_col1, chart_col2 = st.columns(2)


with chart_col1:

    st.subheader(
        "Carbon Emissions Comparison"
    )

    st.image(
        result["carbon_chart"],
        use_container_width=True
    )


with chart_col2:

    st.subheader(
        "Electricity Cost Comparison"
    )

    st.image(
        result["cost_chart"],
        use_container_width=True
    )


chart_col1, chart_col2 = st.columns(2)


with chart_col1:

    st.subheader(
        "Top 10 Lowest-Carbon Datacenters"
    )

    st.image(
        result["multi_idc_chart"],
        use_container_width=True
    )


with chart_col2:

    st.subheader(
        "Workload Allocation"
    )

    st.image(
        result["allocation_chart"],
        use_container_width=True
    )


# ============================================================
# TOP 10 TABLE
# ============================================================

st.header(
    "Top 10 Lowest-Carbon Datacenters"
)

top10_rows = []

for rank, dc in enumerate(
    result["top_10_datacenters"],
    1
):

    top10_rows.append(
        {
            "Rank": rank,
            "Datacenter": dc["datacenter"],
            "Region": dc["region"],
            "Carbon Intensity":
                f"{dc['carbon_intensity']:.2f} gCO₂/kWh",
            "CO₂ Emissions":
                f"{dc['carbon_emissions']:.2f} gCO₂"
        }
    )


st.dataframe(
    top10_rows,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# CANDIDATE DATACENTERS
# ============================================================

st.header(
    "Candidate Datacenters"
)

candidate_rows = []

for dc in result["candidate_datacenters"]:

    candidate_rows.append(
        {
            "Datacenter": dc["id"],
            "Region": dc["region"],
            "Grid Zone": dc["zoneKey"],
            "Carbon Intensity":
                f"{dc['carbon_intensity']:.2f} gCO₂/kWh",
            "Electricity Price":
                f"₹{dc['electricity_price']:.2f}/kWh"
        }
    )


st.dataframe(
    candidate_rows,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# REPORT GENERATION
# ============================================================

st.header("Reports")


def make_json_report(result):

    workload = result["workload"]

    robust = result["robust_result"]

    report = {

        "generated_at":
            result["timestamp"],

        "workload": {
            "type":
                workload.workload_type,

            "power_kw":
                workload.power_kw,

            "duration_hours":
                workload.duration_hours,

            "energy_kwh":
                result["energy"],

            "latency_max_ms":
                workload.latency_max_ms,

            "budget":
                workload.budget,

            "workload_demand":
                workload.workload_demand
        },

        "stage1": {
            "datacenter":
                result["best_region"]["id"],

            "region":
                result["best_region"]["region"],

            "grid_zone":
                result["best_region"]["zoneKey"],

            "carbon_emissions":
                result["best_region"]["carbon_emissions"],

            "electricity_cost":
                result["best_region"]["electricity_cost"],

            "optimization_score":
                result["best_region"]["score"]
        },

        "mmfg": {
            "datacenter":
                result["mmfg_result"]
                ["selected_datacenter"]["id"],

            "region":
                result["mmfg_result"]
                ["selected_datacenter"]["region"],

            "grid_zone":
                result["mmfg_result"]
                ["best_zone"],

            "iterations":
                result["mmfg_result"]
                ["iterations"],

            "converged":
                result["mmfg_result"]
                ["converged"]
        },

        "robust_optimization": None,

        "optimization": {

            "baseline_carbon":
                result["baseline_carbon"],

            "optimized_carbon":
                result["optimized_carbon"],

            "carbon_reduction_percent":
                result["carbon_reduction"],

            "baseline_cost":
                result["baseline_cost"],

            "optimized_cost":
                result["optimized_cost"],

            "cost_change_percent":
                result["cost_change"]
        },

        "top_10_lowest_carbon_datacenters":
            result["top_10_datacenters"],

        "baseline_simulation":
            result["baseline_simulation"],

        "optimized_simulation":
            result["optimized_simulation"]
    }


    if robust is not None:

        report[
            "robust_optimization"
        ] = {

            "datacenter":
                robust["datacenter_id"],

            "worst_case_scenario":
                robust["worst_case_scenario"],
            "worst_case_co2":
                robust["worst_case_co2"],
            "worst_case_cost":
                robust["worst_case_cost"],
            "stable":
                robust["stable"]
        }
    return report


json_report = make_json_report(
    result
)


json_bytes = json.dumps(
    json_report,
    indent=4,
    default=str
).encode("utf-8")


# ============================================================
# PDF REPORT
# ============================================================

def make_pdf_report(result):

    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle
    )
    from reportlab.lib import colors
    from reportlab.lib.styles import (
        getSampleStyleSheet
    )

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    story = []

    story.append(
        Paragraph(
            "Carbon-Aware Workload Scheduler",
            styles["Title"]
        )
    )

    story.append(
        Paragraph(
            "Optimization Report",
            styles["Heading2"]
        )
    )

    story.append(
        Spacer(1, 15)
    )


    # Workload

    story.append(
        Paragraph(
            "1. Workload Details",
            styles["Heading2"]
        )
    )

    workload = result["workload"]

    workload_data = [

        ["Workload Type",
         workload.workload_type],

        ["Power",
         f"{workload.power_kw:.2f} kW"],

        ["Duration",
         f"{workload.duration_hours:.2f} hours"],

        ["Energy",
         f"{result['energy']:.2f} kWh"]
    ]

    table = Table(
        workload_data,
        colWidths=[180, 300]
    )

    table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.lightgrey
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "PADDING",
                (0, 0),
                (-1, -1),
                6
            )
        ])
    )

    story.append(table)

    story.append(
        Spacer(1, 15)
    )


    # Stage 1

    story.append(
        Paragraph(
            "2. Stage 1 — Carbon-Aware Scheduler",
            styles["Heading2"]
        )
    )

    stage1 = result["best_region"]

    stage1_data = [

        ["Datacenter",
         stage1["id"]],

        ["Region",
         stage1["region"]],

        ["Grid Zone",
         stage1["zoneKey"]],

        ["CO₂ Emissions",
         f"{stage1['carbon_emissions']:.2f} gCO₂"],

        ["Electricity Cost",
         f"₹{stage1['electricity_cost']:.2f}"],

        ["Optimization Score",
         f"{stage1['score']:.4f}"]
    ]

    table = Table(
        stage1_data,
        colWidths=[180, 300]
    )

    table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.lightgrey
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "PADDING",
                (0, 0),
                (-1, -1),
                6
            )
        ])
    )

    story.append(table)

    story.append(
        Spacer(1, 15)
    )


    # MMFG

    story.append(
        Paragraph(
            "3. MMFG Routing",
            styles["Heading2"]
        )
    )

    mmfg = result["mmfg_result"]

    mmfg_data = [

        ["Datacenter",
         mmfg["selected_datacenter"]["id"]],

        ["Grid Zone",
         mmfg["best_zone"]],

        ["Iterations",
         str(mmfg["iterations"])],

        ["Converged",
         str(mmfg["converged"])]
    ]

    table = Table(
        mmfg_data,
        colWidths=[180, 300]
    )

    table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.lightgrey
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "PADDING",
                (0, 0),
                (-1, -1),
                6
            )
        ])
    )

    story.append(table)

    story.append(
        Spacer(1, 15)
    )


    # Robust

    story.append(
        Paragraph(
            "4. Robust Optimization",
            styles["Heading2"]
        )
    )

    robust = result["robust_result"]

    if robust is not None:

        robust_data = [

        ["Datacenter",
        robust["datacenter_id"]],

        ["Worst Case",
        robust["worst_case_scenario"]],

        ["Worst Case CO₂",
        f"{robust['worst_case_co2']:.2f} gCO₂"],

        ["Worst Case Cost",
        f"₹{robust['worst_case_cost']:.2f}"],

        ["Worst Case Score",
        f"{robust['worst_case_score']:.4f}"],

        ["Stable",
         str(robust["stable"])]
    ]

        table = Table(
            robust_data,
            colWidths=[180, 300]
        )

        table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.lightgrey
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    6
                )
            ])
        )

        story.append(table)

    else:

        story.append(
            Paragraph(
                "No robust optimization result.",
                styles["Normal"]
            )
        )


    story.append(
        Spacer(1, 15)
    )


    # Comparison

    story.append(
        Paragraph(
            "5. Optimization Comparison",
            styles["Heading2"]
        )
    )

    comparison_data = [

        [
            "Metric",
            "Baseline",
            "Optimized"
        ],

        [
            "Energy",
            f"{result['baseline_simulation']['totals']['total_energy_kwh']:.2f} kWh",
            f"{result['optimized_simulation']['totals']['total_energy_kwh']:.2f} kWh"
        ],

        [
            "Carbon",
            f"{result['baseline_carbon']:.2f} gCO₂",
            f"{result['optimized_carbon']:.2f} gCO₂"
        ],

        [
            "Electricity Cost",
            f"₹{result['baseline_cost']:.2f}",
            f"₹{result['optimized_cost']:.2f}"
        ]
    ]

    table = Table(
        comparison_data,
        colWidths=[160, 160, 160]
    )

    table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "PADDING",
                (0, 0),
                (-1, -1),
                6
            )
        ])
    )

    story.append(table)

    story.append(
        Spacer(1, 15)
    )

    story.append(
        Paragraph(
            f"Carbon Reduction: "
            f"{result['carbon_reduction']:.2f}%",
            styles["Normal"]
        )
    )

    if result["cost_change"] > 0:

        cost_text = (
            f"Cost Increase: "
            f"{result['cost_change']:.2f}%"
        )

    elif result["cost_change"] < 0:

        cost_text = (
            f"Cost Reduction: "
            f"{abs(result['cost_change']):.2f}%"
        )

    else:

        cost_text = (
            "Cost Change: 0.00%"
        )

    story.append(
        Paragraph(
            cost_text,
            styles["Normal"]
        )
    )


    # Top 10

    story.append(
        Spacer(1, 15)
    )

    story.append(
        Paragraph(
            "6. Top 10 Lowest-Carbon Datacenters",
            styles["Heading2"]
        )
    )

    top10_data = [

        [
            "Rank",
            "Datacenter",
            "Region",
            "CO₂"
        ]
    ]

    for rank, dc in enumerate(
        result["top_10_datacenters"],
        1
    ):

        top10_data.append(
            [
                str(rank),
                dc["datacenter"],
                dc["region"],
                f"{dc['carbon_emissions']:.2f} gCO₂"
            ]
        )


    table = Table(
        top10_data,
        colWidths=[
            40,
            170,
            150,
            100
        ]
    )

    table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "PADDING",
                (0, 0),
                (-1, -1),
                5
            )
        ])
    )

    story.append(table)


    document.build(story)

    buffer.seek(0)

    return buffer.getvalue()


try:

    pdf_bytes = make_pdf_report(
        result
    )

except Exception as error:

    pdf_bytes = None

    st.warning(
        f"PDF generation unavailable: {error}"
    )


# ============================================================
# DOWNLOAD REPORTS
# ============================================================

report_col1, report_col2 = st.columns(2)


with report_col1:

    st.download_button(
        label="📄 Download PDF Report",
        data=pdf_bytes,
        file_name=(
            f"carbon_aware_report_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            f".pdf"
        ),
        mime="application/pdf",
        disabled=pdf_bytes is None,
        use_container_width=True
    )


with report_col2:

    st.download_button(
        label="🧾 Download JSON Report",
        data=json_bytes,
        file_name=(
            f"carbon_aware_report_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            f".json"
        ),
        mime="application/json",
        use_container_width=True
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Carbon-Aware Workload Scheduler | "
    "Scheduler + MMFG + Robust Optimization"
)
st.divider()

st.header("Optimization History")

history = get_optimization_history()

if history:

    history_data = []

    for run in history:

        history_data.append({
            "Run ID": run["id"],
            "Date": run["created_at"],
            "Workload": run["workload_type"],
            "Power (kW)": run["power_kw"],
            "Duration (hrs)": run["duration_hours"],
            "Energy (kWh)": run["energy_kwh"],
            "Baseline CO₂": run["baseline_carbon"],
            "Optimized CO₂": run["optimized_carbon"],
            "CO₂ Reduction (%)": run["carbon_reduction_percent"],
            "Baseline Cost": run["baseline_cost"],
            "Optimized Cost": run["optimized_cost"]
        })

    st.dataframe(
        history_data,
        use_container_width=True,
        hide_index=True
    )

    run_ids = [run["id"] for run in history]

    selected_run = st.selectbox(
        "Select an optimization run",
        run_ids
    )

    top_datacenters = get_top_carbon_datacenters(
        selected_run
    )

    if top_datacenters:

        st.subheader(
            f"Top 10 Lowest-Carbon Datacenters — Run {selected_run}"
        )

        top_data = []

        for dc in top_datacenters:

            top_data.append({
                "Rank": dc["rank"],
                "Datacenter": dc["datacenter"],
                "Region": dc["region"],
                "Carbon Intensity": dc["carbon_intensity"],
                "Carbon Emissions": dc["carbon_emissions"]
            })

        st.dataframe(
            top_data,
            use_container_width=True,
            hide_index=True
        )

else:

    st.info("No optimization history available.")