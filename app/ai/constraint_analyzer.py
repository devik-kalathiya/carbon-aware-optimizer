import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

def analyze_constraint_failure(
    workload_type,
    power_kw,
    duration_hours,
    latency_max_ms,
    budget,
    workload_demand
):
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("GROQ_API_KEY is not set.")

    client = Groq(api_key=api_key)

    energy_kwh = power_kw * duration_hours

    prompt = f"""
You are a cloud workload scheduling assistant.

A deterministic carbon-aware scheduler could not find
a feasible datacenter.

Workload type: {workload_type}
Power: {power_kw} kW
Duration: {duration_hours} hours
Energy: {energy_kwh} kWh
Maximum latency: {latency_max_ms}
Budget: {budget}
Workload demand: {workload_demand}

Analyze which constraint is most likely causing the
infeasible result.

Suggest ONE reasonable constraint relaxation.

Do not select a datacenter.
Do not invent datacenter resources.

Return ONLY valid JSON in this format:

{{
    "constraint": "budget",
    "suggested_value": 500,
    "reason": "The current budget is too restrictive for the required energy."
}}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    content = response.choices[0].message.content

    return json.loads(content)