import os
import matplotlib.pyplot as plt


def create_carbon_comparison(
    baseline_carbon,
    optimized_carbon,
    output_path="results/carbon_comparison.png"
):
    os.makedirs(
        os.path.dirname(output_path) or ".",
        exist_ok=True
    )

    labels = [
        "Baseline",
        "Optimized"
    ]

    values = [
        baseline_carbon,
        optimized_carbon
    ]

    plt.figure()

    plt.bar(
        labels,
        values
    )

    plt.title(
        "Carbon Emissions Comparison"
    )

    plt.ylabel(
        "CO2 Emissions (gCO2)"
    )

    plt.tight_layout()

    plt.savefig(
        output_path
    )

    plt.close()

    return output_path


def create_cost_comparison(
    baseline_cost,
    optimized_cost,
    output_path="results/cost_comparison.png"
):
    os.makedirs(
        os.path.dirname(output_path) or ".",
        exist_ok=True
    )

    labels = [
        "Baseline",
        "Optimized"
    ]

    values = [
        baseline_cost,
        optimized_cost
    ]

    plt.figure()

    plt.bar(
        labels,
        values
    )

    plt.title(
        "Electricity Cost Comparison"
    )

    plt.ylabel(
        "Electricity Cost (₹)"
    )

    plt.tight_layout()

    plt.savefig(
        output_path
    )

    plt.close()

    return output_path


def create_multi_idc_carbon_chart(
    results,
    output_path="results/multi_idc_carbon.png"
):
    os.makedirs(
        os.path.dirname(output_path) or ".",
        exist_ok=True
    )

    labels = [
        result["datacenter"]
        for result in results
    ]

    values = [
        result["carbon_emissions"]
        for result in results
    ]

    plt.figure(figsize=(10, 6))

    plt.bar(
        labels,
        values
    )

    plt.title(
        "Top 10 Lowest-Carbon Datacenters"
    )

    plt.ylabel(
        "CO2 Emissions (gCO2)"
    )

    plt.xlabel(
        "Datacenter"
    )

    plt.xticks(
        rotation=45,
        ha="right"
    )

    plt.tight_layout()

    plt.savefig(
        output_path
    )

    plt.close()

    return output_path


def create_workload_allocation_chart(
    results,
    output_path="results/workload_allocation.png"
):
    os.makedirs(
        os.path.dirname(output_path) or ".",
        exist_ok=True
    )

    labels = [
        result["datacenter"]
        for result in results
    ]

    values = [
        result["allocation"] * 100
        for result in results
    ]

    plt.figure()

    plt.pie(
        values,
        labels=labels,
        autopct="%1.1f%%"
    )

    plt.title(
        "Workload Allocation"
    )

    plt.tight_layout()

    plt.savefig(
        output_path
    )

    plt.close()

    return output_path