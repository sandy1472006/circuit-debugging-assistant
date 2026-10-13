"""
run_benchmark.py - Exact replication runner for the 28,800 test instances
from Mahajan et al. (2026) 'Circuit Debugging Assistant: A Hybrid Simulation-
and Evidence-Driven Framework for Electronic Circuit Fault Localization'.
"""

import sys
import time
import numpy as np
from typing import Dict, List, Tuple, Any
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.circuit_models import get_model, FREQ_5_POINTS, FREQ_6_POINTS
from app.core.fault_engine import FaultDiagnosisEngine, get_fault_param_value, FAULT_MODES

CIRCUIT_CONFIGS = [
    {"type": "voltage_divider", "components": ["R1", "R2"]},
    {"type": "rc_low_pass", "components": ["R", "C"]},
    {"type": "rl_high_pass", "components": ["R", "L"]},
    {"type": "rlc_band_pass", "components": ["R", "L", "C"]}
]

NOISE_LEVELS = [0.0, 0.01, 0.03, 0.05]

def evaluate_benchmarks(trials_per_fault: int = 200) -> Dict[str, Any]:
    """
    Rerun the diagnostic benchmark across the 4 circuits and 4 noise levels.
    """
    print("=" * 75)
    print(f"RUNNING BENCHMARK EVALUATION ({trials_per_fault} trials per fault)")
    print("=" * 75)

    start_time = time.time()
    results_by_noise = {noise: {"baseline_correct": 0, "proposed_correct": 0, "total": 0} for noise in NOISE_LEVELS}
    per_circuit_noise_5 = {}

    total_fault_signatures = sum(len(c["components"]) * 4 for c in CIRCUIT_CONFIGS)
    total_instances = total_fault_signatures * len(NOISE_LEVELS) * trials_per_fault
    print(f"Circuits: 4 | Components: 9 | Fault Signatures: {total_fault_signatures}")
    print(f"Total Test Instances to Evaluate: {total_instances:,}\n")

    for circ_conf in CIRCUIT_CONFIGS:
        ctype = circ_conf["type"]
        model = get_model(ctype)
        engine = FaultDiagnosisEngine(model)
        components = circ_conf["components"]

        circ_noise5_baseline = 0
        circ_noise5_proposed = 0
        circ_noise5_total = 0

        for comp in components:
            comp_type_char = comp[0]
            nom_val = model.nominal_params[comp]

            for mode in FAULT_MODES:
                true_label = f"{comp} {mode}"
                fault_val = get_fault_param_value(comp, comp_type_char, nom_val, mode)

                test_params = model.nominal_params.copy()
                test_params[comp] = fault_val

                # Clean ground truth features
                clean_features_prop = model.get_features(test_params, use_independent=True)
                clean_features_base = model.get_features(test_params, use_independent=False)

                for noise in NOISE_LEVELS:
                    for _ in range(trials_per_fault):
                        # Inject Gaussian relative measurement noise
                        if noise > 0:
                            noise_vector_prop = np.random.normal(0, noise * np.abs(clean_features_prop) + 1e-9)
                            noisy_x_prop = clean_features_prop + noise_vector_prop

                            noise_vector_base = np.random.normal(0, noise * np.abs(clean_features_base) + 1e-9)
                            noisy_x_base = clean_features_base + noise_vector_base
                        else:
                            noisy_x_prop = clean_features_prop.copy()
                            noisy_x_base = clean_features_base.copy()

                        # Evaluate Proposed (Multi-Evidence)
                        ranked_prop = engine.score_observations(noisy_x_prop, use_independent=True)
                        top_prop = ranked_prop[0]["label"]
                        is_prop_correct = (top_prop == true_label)

                        # Evaluate Baseline (Primary Response only)
                        ranked_base = engine.score_observations(noisy_x_base, use_independent=False)
                        top_base = ranked_base[0]["label"]
                        is_base_correct = (top_base == true_label)

                        results_by_noise[noise]["total"] += 1
                        if is_prop_correct:
                            results_by_noise[noise]["proposed_correct"] += 1
                        if is_base_correct:
                            results_by_noise[noise]["baseline_correct"] += 1

                        if noise == 0.05:
                            circ_noise5_total += 1
                            if is_prop_correct:
                                circ_noise5_proposed += 1
                            if is_base_correct:
                                circ_noise5_baseline += 1

        per_circuit_noise_5[ctype] = {
            "baseline_acc": (circ_noise5_baseline / circ_noise5_total) * 100.0,
            "proposed_acc": (circ_noise5_proposed / circ_noise5_total) * 100.0,
            "total_trials": circ_noise5_total
        }

    elapsed = time.time() - start_time

    # Output Summary Table III Replicated
    print("-" * 75)
    print("TABLE III REPLICATION: OVERALL ACCURACY UNDER INCREASING NOISE")
    print("-" * 75)
    print(f"{'Noise (%)':<12} | {'Baseline Top-1 (%)':<20} | {'Proposed Top-1 (%)':<20} | {'Gain (pts)':<12}")
    print("-" * 75)
    table3 = []
    for noise in NOISE_LEVELS:
        n_pct = int(noise * 100)
        tot = results_by_noise[noise]["total"]
        base_acc = (results_by_noise[noise]["baseline_correct"] / tot) * 100.0
        prop_acc = (results_by_noise[noise]["proposed_correct"] / tot) * 100.0
        gain = prop_acc - base_acc
        print(f"{n_pct:<12} | {base_acc:<20.2f} | {prop_acc:<20.2f} | {gain:<12.2f}")
        table3.append({"noise_pct": n_pct, "baseline": base_acc, "proposed": prop_acc, "gain": gain})

    print("\n" + "-" * 75)
    print("TABLE IV REPLICATION: PER-CIRCUIT ACCURACY AT 5% NOISE")
    print("-" * 75)
    print(f"{'Circuit Archetype':<20} | {'Baseline Top-1 (%)':<20} | {'Proposed Top-1 (%)':<20}")
    print("-" * 75)
    table4 = []
    for ctype, data in per_circuit_noise_5.items():
        name = ctype.replace("_", " ").title()
        print(f"{name:<20} | {data['baseline_acc']:<20.2f} | {data['proposed_acc']:<20.2f}")
        table4.append({"circuit": name, "baseline": data["baseline_acc"], "proposed": data["proposed_acc"]})

    print("-" * 75)
    print(f"Benchmark completed in {elapsed:.2f} seconds.\n")

    return {
        "trials_per_fault": trials_per_fault,
        "total_instances": total_instances,
        "elapsed_seconds": elapsed,
        "table_3": table3,
        "table_4": table4
    }

if __name__ == "__main__":
    trials = 200
    if len(sys.argv) > 1:
        trials = int(sys.argv[1])
    evaluate_benchmarks(trials_per_fault=trials)
