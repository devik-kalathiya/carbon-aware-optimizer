from fastapi import FastAPI
from pydantic import BaseModel

from app.optimizer.engine import run_optimization


app = FastAPI(
    title="Carbon-Aware Optimizer API",
    description="API for carbon-aware workload scheduling and region routing",
    version="1.0.0"
)


class OptimizationRequest(BaseModel):
    workload_type: str
    power_kw: float
    duration_hours: float
    latency_max_ms: float | None = None
    budget: float | None = None
    workload_demand: float | None = None


@app.get("/")
def root():
    return {
        "message": "Carbon-Aware Optimizer API is running"
    }


@app.post("/api/optimize")
def optimize(request: OptimizationRequest):

    result = run_optimization(
        workload_type=request.workload_type,
        power_kw=request.power_kw,
        duration_hours=request.duration_hours,
        latency_max_ms=request.latency_max_ms,
        budget=request.budget,
        workload_demand=request.workload_demand
    )

    return result
@app.get("/health")
def health():
    return {"status": "ok"}