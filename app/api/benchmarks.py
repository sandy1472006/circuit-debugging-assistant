"""
benchmarks.py - API endpoints for executing and visualizing the 28,800 test case
benchmark from Mahajan et al. (2026).
"""

from fastapi import APIRouter, Query
from typing import Dict, Any
from scripts.run_benchmark import evaluate_benchmarks

router = APIRouter(prefix="/api/benchmarks", tags=["benchmarks"])

# Published numbers from the paper for baseline reference
PUBLISHED_TABLE_3 = [
    {"noise_pct": 0, "baseline": 100.00, "proposed": 100.00, "gain": 0.00},
    {"noise_pct": 1, "baseline": 83.49, "proposed": 100.00, "gain": 16.51},
    {"noise_pct": 3, "baseline": 82.19, "proposed": 99.93, "gain": 17.74},
    {"noise_pct": 5, "baseline": 79.89, "proposed": 98.43, "gain": 18.54}
]

PUBLISHED_TABLE_4 = [
    {"circuit": "Voltage Divider", "baseline": 95.75, "proposed": 95.75},
    {"circuit": "RC Low-Pass", "baseline": 50.12, "proposed": 98.50},
    {"circuit": "RL High-Pass", "baseline": 65.44, "proposed": 98.81},
    {"circuit": "RLC Band-Pass", "baseline": 98.79, "proposed": 99.92}
]

@router.get("/reference")
async def get_published_reference():
    """Returns published benchmark statistics directly from the 2026 research paper."""
    return {
        "title": "Published Benchmark Metrics (Mahajan et al., 2026)",
        "total_instances": 28800,
        "trials_per_fault": 200,
        "table_3_noise_progression": PUBLISHED_TABLE_3,
        "table_4_per_circuit_5pct": PUBLISHED_TABLE_4
    }

@router.get("/run")
async def run_live_benchmark(trials: int = Query(20, ge=5, le=200)):
    """
    Executes live verification of the benchmark on the server
    and returns exact replicated accuracy numbers.
    """
    res = evaluate_benchmarks(trials_per_fault=trials)
    return {
        "status": "completed",
        "trials_per_fault": res["trials_per_fault"],
        "total_instances_evaluated": res["total_instances"],
        "execution_time_seconds": res["elapsed_seconds"],
        "replicated_table_3": res["table_3"],
        "replicated_table_4": res["table_4"],
        "published_reference_table_3": PUBLISHED_TABLE_3,
        "published_reference_table_4": PUBLISHED_TABLE_4
    }
