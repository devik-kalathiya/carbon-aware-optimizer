from app.mmfg.mean_field import WORKLOAD_CLASSES


class Workload:

    def __init__(
        self,
        power_kw,
        duration_hours,
        latency_max_ms=None,
        budget=None,
        workload_type=None,
        workload_demand=None,
        constraints=None
    ):
        self.power_kw = power_kw
        self.duration_hours = duration_hours
        self.latency_max_ms = latency_max_ms
        self.budget = budget
        self.workload_type = workload_type
        self.workload_demand = workload_demand
        self.constraints = constraints or {}

    def calculate_energy(self):
        return self.power_kw * self.duration_hours

    def to_dict(self):
        return {
            "workload_type": self.workload_type,
            "power_kw": self.power_kw,
            "duration_hours": self.duration_hours,
            "energy_kwh": self.calculate_energy(),
            "latency_max_ms": self.latency_max_ms,
            "budget": self.budget,
            "workload_demand": self.workload_demand,
            "constraints": self.constraints
        }


def create_workload(
    power_kw,
    duration_hours,
    latency_max_ms=None,
    budget=None,
    workload_type=None,
    workload_demand=None,
    constraints=None
):
    if power_kw <= 0:
        raise ValueError("Power must be greater than 0.")

    if duration_hours <= 0:
        raise ValueError("Duration must be greater than 0.")

    if latency_max_ms is not None and latency_max_ms <= 0:
        raise ValueError(
            "Latency constraint must be greater than 0."
        )

    if budget is not None and budget <= 0:
        raise ValueError(
            "Budget must be greater than 0."
        )

    if workload_demand is not None and workload_demand <= 0:
        raise ValueError(
            "Workload demand must be greater than 0."
        )

    if workload_type is not None:
        if workload_type not in WORKLOAD_CLASSES:
            raise ValueError(
                f"Unknown workload class: {workload_type}"
            )

    return Workload(
        power_kw=power_kw,
        duration_hours=duration_hours,
        latency_max_ms=latency_max_ms,
        budget=budget,
        workload_type=workload_type,
        workload_demand=workload_demand,
        constraints=constraints
    )


def get_workload_classes():
    return WORKLOAD_CLASSES.copy()


def create_all_workloads(
    power_kw,
    duration_hours,
    latency_max_ms=None,
    budget=None,
    workload_demand=None,
    constraints=None
):
    workloads = []

    for workload_type in WORKLOAD_CLASSES:
        workload = create_workload(
            power_kw=power_kw,
            duration_hours=duration_hours,
            latency_max_ms=latency_max_ms,
            budget=budget,
            workload_type=workload_type,
            workload_demand=workload_demand,
            constraints=constraints
        )

        workloads.append(workload)

    return workloads