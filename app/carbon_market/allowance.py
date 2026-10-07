def calculate_allowance_requirement(
    carbon_emissions,
    allowance_coverage=1.0
):
    if carbon_emissions < 0:
        raise ValueError(
            "Carbon emissions cannot be negative."
        )

    if allowance_coverage <= 0 or allowance_coverage > 1:
        raise ValueError(
            "Allowance coverage must be between 0 and 1."
        )

    return carbon_emissions * allowance_coverage


def calculate_allowance_cost(
    allowance_quantity,
    allowance_price
):
    if allowance_quantity < 0:
        raise ValueError(
            "Allowance quantity cannot be negative."
        )

    if allowance_price < 0:
        raise ValueError(
            "Allowance price cannot be negative."
        )

    return allowance_quantity * allowance_price


def procure_carbon_allowances(
    carbon_emissions,
    allowance_price,
    allowance_coverage=1.0
):
    allowance_quantity = calculate_allowance_requirement(
        carbon_emissions,
        allowance_coverage
    )

    procurement_cost = calculate_allowance_cost(
        allowance_quantity,
        allowance_price
    )

    return {
        "carbon_emissions": carbon_emissions,
        "allowance_quantity": allowance_quantity,
        "allowance_price": allowance_price,
        "allowance_coverage": allowance_coverage,
        "procurement_cost": procurement_cost
    }


def calculate_total_cost(
    electricity_cost,
    allowance_cost
):
    if electricity_cost < 0:
        raise ValueError(
            "Electricity cost cannot be negative."
        )

    if allowance_cost < 0:
        raise ValueError(
            "Allowance cost cannot be negative."
        )

    return electricity_cost + allowance_cost