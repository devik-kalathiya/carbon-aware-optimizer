# ============================================================
# MMFG - Workload Classes and Population Distribution
# ============================================================


# ------------------------------------------------------------
# Workload Classes
# ------------------------------------------------------------

WORKLOAD_CLASSES = {

    "ai_training": {
        "name": "AI Training",
        "carbon_sensitivity": 0.90,
        "cost_sensitivity": 0.40,
        "latency_sensitivity": 0.20,
    },

    "ai_inference": {
        "name": "AI Inference",
        "carbon_sensitivity": 0.70,
        "cost_sensitivity": 0.50,
        "latency_sensitivity": 0.80,
    },

    "web_application": {
        "name": "Web Application",
        "carbon_sensitivity": 0.40,
        "cost_sensitivity": 0.50,
        "latency_sensitivity": 0.90,
    },

    "video_processing": {
        "name": "Video Processing",
        "carbon_sensitivity": 0.70,
        "cost_sensitivity": 0.60,
        "latency_sensitivity": 0.30,
    },

    "batch_processing": {
        "name": "Batch Processing",
        "carbon_sensitivity": 0.60,
        "cost_sensitivity": 0.90,
        "latency_sensitivity": 0.10,
    },

    "data_analytics": {
        "name": "Data Analytics",
        "carbon_sensitivity": 0.70,
        "cost_sensitivity": 0.70,
        "latency_sensitivity": 0.40,
    },

    "database": {
        "name": "Database",
        "carbon_sensitivity": 0.50,
        "cost_sensitivity": 0.60,
        "latency_sensitivity": 0.90,
    },

    "scientific_computing": {
        "name": "Scientific Computing",
        "carbon_sensitivity": 0.85,
        "cost_sensitivity": 0.50,
        "latency_sensitivity": 0.20,
    },

    "rendering": {
        "name": "3D Rendering",
        "carbon_sensitivity": 0.75,
        "cost_sensitivity": 0.70,
        "latency_sensitivity": 0.20,
    },

    "backup_storage": {
        "name": "Backup and Storage",
        "carbon_sensitivity": 0.65,
        "cost_sensitivity": 0.85,
        "latency_sensitivity": 0.10,
    },

    "iot_processing": {
        "name": "IoT Data Processing",
        "carbon_sensitivity": 0.60,
        "cost_sensitivity": 0.50,
        "latency_sensitivity": 0.85,
    },

    "high_performance_computing": {
        "name": "High Performance Computing",
        "carbon_sensitivity": 0.90,
        "cost_sensitivity": 0.60,
        "latency_sensitivity": 0.30,
    },

    "machine_learning_inference": {
        "name": "Machine Learning Inference",
        "carbon_sensitivity": 0.65,
        "cost_sensitivity": 0.55,
        "latency_sensitivity": 0.90,
    },

    "distributed_training": {
        "name": "Distributed ML Training",
        "carbon_sensitivity": 0.95,
        "cost_sensitivity": 0.55,
        "latency_sensitivity": 0.25,
    },

    "scientific_simulation": {
        "name": "Scientific Simulation",
        "carbon_sensitivity": 0.90,
        "cost_sensitivity": 0.60,
        "latency_sensitivity": 0.15,
    },

    "financial_computing": {
        "name": "Financial Computing",
        "carbon_sensitivity": 0.45,
        "cost_sensitivity": 0.65,
        "latency_sensitivity": 0.95,
    },

    "real_time_analytics": {
        "name": "Real-Time Analytics",
        "carbon_sensitivity": 0.50,
        "cost_sensitivity": 0.55,
        "latency_sensitivity": 0.95,
    },

    "content_delivery": {
        "name": "Content Delivery",
        "carbon_sensitivity": 0.45,
        "cost_sensitivity": 0.60,
        "latency_sensitivity": 0.95,
    },

    "software_build": {
        "name": "Software Build and CI",
        "carbon_sensitivity": 0.65,
        "cost_sensitivity": 0.75,
        "latency_sensitivity": 0.45,
    },

    "email_messaging": {
        "name": "Email and Messaging",
        "carbon_sensitivity": 0.40,
        "cost_sensitivity": 0.65,
        "latency_sensitivity": 0.85,
    },
}


# ------------------------------------------------------------
# Workload Population Distribution
# ------------------------------------------------------------

DEFAULT_POPULATION = {

    "ai_training": 0.07,
    "ai_inference": 0.07,
    "web_application": 0.09,
    "video_processing": 0.05,
    "batch_processing": 0.07,
    "data_analytics": 0.07,
    "database": 0.06,
    "scientific_computing": 0.04,
    "rendering": 0.04,
    "backup_storage": 0.05,
    "iot_processing": 0.04,
    "high_performance_computing": 0.04,
    "machine_learning_inference": 0.05,
    "distributed_training": 0.04,
    "scientific_simulation": 0.04,
    "financial_computing": 0.04,
    "real_time_analytics": 0.04,
    "content_delivery": 0.03,
    "software_build": 0.03,
    "email_messaging": 0.04,
}


# ------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------

def get_workload_classes():
    """
    Return all predefined workload classes.
    """
    return WORKLOAD_CLASSES


def get_default_population():
    """
    Return the initial workload population distribution.
    """
    return DEFAULT_POPULATION.copy()


def validate_population(population):
    """
    Validate the workload population distribution.

    Every workload class must be known and non-negative.
    The total population must equal 1.0.
    """

    # Check workload class names
    for workload_class, value in population.items():

        if workload_class not in WORKLOAD_CLASSES:
            raise ValueError(
                f"Unknown workload class: {workload_class}"
            )

        # Check for negative values
        if value < 0:
            raise ValueError(
                f"Negative population for: {workload_class}"
            )

    # Check total population
    total = sum(population.values())

    if abs(total - 1.0) > 1e-6:
        raise ValueError(
            f"Population must sum to 1. "
            f"Current sum: {total}"
        )

    return True
# ------------------------------------------------------------
# Mean-Field Interaction
# ------------------------------------------------------------

def calculate_region_congestion(region_population):
    """
    Calculate normalized congestion for each region.

    region_population:
        Dictionary containing workload population assigned
        to each region.

    Example:
        {
            "India": 0.40,
            "Singapore": 0.30,
            "Japan": 0.30
        }
    """

    total_population = sum(region_population.values())

    if total_population <= 0:
        raise ValueError("Region population must be greater than 0.")

    return {
        region: population / total_population
        for region, population in region_population.items()
    }


def apply_mean_field(attractiveness, region_population, interaction_strength=0.5):
    """
    Apply mean-field interaction to region attractiveness.

    More workload population in a region creates congestion,
    which reduces that region's attractiveness.

    Formula:

        adjusted_score =
            attractiveness - interaction_strength * congestion

    Parameters
    ----------
    attractiveness : dict
        Original attractiveness score for each region.

    region_population : dict
        Current workload population in each region.

    interaction_strength : float
        Strength of congestion effect.

    Returns
    -------
    dict
        Adjusted region attractiveness.
    """

    if interaction_strength < 0:
        raise ValueError("Interaction strength cannot be negative.")

    if set(attractiveness.keys()) != set(region_population.keys()):
        raise ValueError(
            "Attractiveness and region population must contain "
            "the same regions."
        )

    congestion = calculate_region_congestion(region_population)

    adjusted_attractiveness = {}

    for region in attractiveness:

        penalty = (
            interaction_strength *
            congestion[region]
        )

        adjusted_attractiveness[region] = (
            attractiveness[region] - penalty
        )

    return adjusted_attractiveness
# ------------------------------------------------------------
# Iterative Mean-Field Equilibrium
# ------------------------------------------------------------

def calculate_equilibrium(
    attractiveness,
    initial_population,
    interaction_strength=0.5,
    learning_rate=0.5,
    max_iterations=100,
    tolerance=1e-6
):
    """
    Iteratively redistribute workload population until
    the system reaches a stable mean-field equilibrium.

    Parameters
    ----------
    attractiveness : dict
        Base attractiveness of each region.

    initial_population : dict
        Initial workload population of each region.

    interaction_strength : float
        Strength of congestion penalty.

    learning_rate : float
        How quickly the population moves toward the
        new distribution during each iteration.

    max_iterations : int
        Maximum number of iterations.

    tolerance : float
        Difference below which the distribution is
        considered stable.

    Returns
    -------
    dict
        Final equilibrium population distribution.
    """

    if not 0 < learning_rate <= 1:
        raise ValueError(
            "Learning rate must be between 0 and 1."
        )

    if max_iterations <= 0:
        raise ValueError(
            "max_iterations must be greater than 0."
        )

    if abs(sum(initial_population.values()) - 1.0) > 1e-6:
        raise ValueError(
            "Initial population must sum to 1."
        )

    if set(attractiveness.keys()) != set(initial_population.keys()):
        raise ValueError(
            "Attractiveness and population must contain "
            "the same regions."
        )

    population = initial_population.copy()

    for iteration in range(max_iterations):

        # Apply mean-field congestion effect
        adjusted = apply_mean_field(
            attractiveness,
            population,
            interaction_strength
        )

        # Convert adjusted attractiveness into
        # a population distribution.
        #
        # Negative attractiveness is treated as zero.
        positive_scores = {
            region: max(score, 0.0)
            for region, score in adjusted.items()
        }

        total_score = sum(positive_scores.values())

        if total_score <= 0:
            raise ValueError(
                "All adjusted attractiveness scores are zero."
            )

        target_population = {
            region: score / total_score
            for region, score in positive_scores.items()
        }

        # Gradually move current population toward
        # the target distribution.
        new_population = {
            region:
                population[region]
                + learning_rate *
                (target_population[region] - population[region])
            for region in population
        }

        # Check convergence
        difference = max(
            abs(new_population[region] - population[region])
            for region in population
        )

        population = new_population

        if difference < tolerance:
            return {
                "population": population,
                "iterations": iteration + 1,
                "converged": True
            }

    return {
        "population": population,
        "iterations": max_iterations,
        "converged": False
    }