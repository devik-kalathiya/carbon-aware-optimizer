def calculate_carbon(energy_kwh, carbon_intensity):
    """
    Calculate CO2 emissions.

    carbon_intensity = grams of CO2 per kWh
    """
    return energy_kwh * carbon_intensity