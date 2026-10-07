def allocate_workload(
    datacenters,
    total_power_kw,
    duration_hours,
    allocations=None
):
    if not datacenters:
        raise ValueError("No datacenters available.")

    if total_power_kw <= 0:
        raise ValueError("Power must be greater than 0.")

    if duration_hours <= 0:
        raise ValueError("Duration must be greater than 0.")

    if allocations is None:
        share = 1 / len(datacenters)
        allocations = {
            dc["id"]: share
            for dc in datacenters
        }

    total_allocation = sum(allocations.values())

    if total_allocation <= 0:
        raise ValueError("Total allocation must be greater than 0.")

    allocations = {
        dc_id: value / total_allocation
        for dc_id, value in allocations.items()
    }

    results = []

    for dc in datacenters:

        dc_id = dc["id"]

        if dc_id not in allocations:
            continue

        allocation = allocations[dc_id]

        power = total_power_kw * allocation
        energy = power * duration_hours

        carbon = (
            energy *
            dc["carbon_intensity"]
        )

        cost = (
            energy *
            dc["electricity_price"]
        )

        results.append({
            "datacenter": dc_id,
            "region": dc["region"],
            "zoneKey": dc["zoneKey"],
            "allocation": allocation,
            "power_kw": power,
            "energy_kwh": energy,
            "carbon_emissions": carbon,
            "electricity_cost": cost
        })

    return results


def calculate_multi_idc_totals(results):

    total_energy = sum(
        result["energy_kwh"]
        for result in results
    )

    total_carbon = sum(
        result["carbon_emissions"]
        for result in results
    )

    total_cost = sum(
        result["electricity_cost"]
        for result in results
    )

    return {
        "total_energy_kwh": total_energy,
        "total_carbon_emissions": total_carbon,
        "total_electricity_cost": total_cost
    }


def simulate_multi_idc(
    datacenters,
    total_power_kw,
    duration_hours,
    allocations=None
):

    results = allocate_workload(
        datacenters=datacenters,
        total_power_kw=total_power_kw,
        duration_hours=duration_hours,
        allocations=allocations
    )

    totals = calculate_multi_idc_totals(
        results
    )

    return {
        "datacenters": results,
        "totals": totals
    }