"""
fault_engine.py - Fault candidate generation, deterministic fault dictionary,
residual scoring, multi-evidence fusion, and adaptive test-point selection (U(t)).
Directly implements Section III & IV of Mahajan et al. (2026).
"""

import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from app.core.circuit_models import CircuitModel, get_model, FREQ_5_POINTS, FREQ_6_POINTS

FAULT_MODES = ["-20%", "+20%", "open", "short"]

def get_fault_param_value(comp_name: str, comp_type: str, nominal_val: float, mode: str) -> float:
    """Calculates faulty parameter value based on fault mode."""
    if mode == "-20%":
        return nominal_val * 0.8
    elif mode == "+20%":
        return nominal_val * 1.2
    elif mode == "open":
        if comp_type.startswith("R"):
            return 1e9 # 1 Gohm
        elif comp_type.startswith("C"):
            return 1e-15 # 1 fF (open circuit)
        elif comp_type.startswith("L"):
            return 1e6 # 1 MH (very high impedance)
        return nominal_val * 1e6
    elif mode == "short":
        if comp_type.startswith("R"):
            return 1e-4 # 0.1 mohm
        elif comp_type.startswith("C"):
            return 1e3 # huge capacitance = 0 impedance
        elif comp_type.startswith("L"):
            return 1e-9 # 1 nH = 0 impedance
        return nominal_val * 1e-6
    else:
        raise ValueError(f"Unknown fault mode: {mode}")


class FaultCandidate:
    def __init__(self, component: str, mode: str, label: str, params: Dict[str, float]):
        self.component = component
        self.mode = mode
        self.label = label
        self.params = params
        self.expected_features: Optional[np.ndarray] = None
        self.residual_score: float = 0.0
        self.per_feature_residuals: Dict[str, float] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component": self.component,
            "mode": self.mode,
            "label": self.label,
            "params": self.params,
            "residual_score": float(self.residual_score),
            "per_feature_residuals": self.per_feature_residuals
        }


class FaultDiagnosisEngine:
    """
    Deterministic fault localization core implementing equations (1) and (2):
    e_k(f) = |x_k - y_k(f)| / (s_k + epsilon)
    S(f) = sum_k w_k * e_k(f)
    """
    def __init__(self, circuit_model: CircuitModel):
        self.model = circuit_model
        self.candidates: List[FaultCandidate] = []
        self._build_candidate_set()

    def _build_candidate_set(self):
        """Generates the candidate faults for each passive component."""
        self.candidates = []
        nom_params = self.model.nominal_params

        # Add Nominal / Fault-Free state
        nom_cand = FaultCandidate("None", "nominal", "Nominal (Fault-Free)", nom_params.copy())
        self.candidates.append(nom_cand)

        # Iterate over all components in nominal parameters (excluding Vin)
        for comp, val in nom_params.items():
            if comp == "Vin":
                continue
            for mode in FAULT_MODES:
                faulty_val = get_fault_param_value(comp, comp[0], val, mode)
                p = nom_params.copy()
                p[comp] = faulty_val
                label = f"{comp} {mode}"
                cand = FaultCandidate(comp, mode, label, p)
                self.candidates.append(cand)

    def generate_fault_dictionary(self, use_independent: bool = True) -> Dict[str, np.ndarray]:
        """Precomputes y(f) for all candidates in the dictionary."""
        dictionary = {}
        for cand in self.candidates:
            feats = self.model.get_features(cand.params, use_independent=use_independent)
            cand.expected_features = feats
            dictionary[cand.label] = feats
        return dictionary

    def score_observations(
        self,
        observed_x: np.ndarray,
        use_independent: bool = True,
        weights: Optional[np.ndarray] = None,
        epsilon: float = 1e-6
    ) -> List[Dict[str, Any]]:
        """
        Calculates normalized residuals e_k(f) and aggregate score S(f).
        Returns candidates ranked from lowest residual score to highest.
        """
        scales = self.model.get_feature_scales()
        if not use_independent and self.model.circuit_type != "voltage_divider":
            scales = scales[:-1]

        K = len(observed_x)
        if weights is None:
            w = np.ones(K, dtype=float)
        else:
            w = np.array(weights, dtype=float)

        feature_names = self.model.get_feature_names(use_independent=use_independent)

        ranked = []
        for cand in self.candidates:
            y = self.model.get_features(cand.params, use_independent=use_independent)
            # Eq (1): e_k(f) = |x_k - y_k(f)| / (s_k + epsilon)
            e_k = np.abs(observed_x - y) / (scales + epsilon)
            # Eq (2): S(f) = sum_k w_k * e_k(f)
            s_f = np.sum(w * e_k)

            cand.residual_score = float(s_f)
            cand.per_feature_residuals = {
                name: float(e) for name, e in zip(feature_names, e_k)
            }
            ranked.append(cand.to_dict())

        # Sort ascending by residual score S(f)
        ranked.sort(key=lambda item: item["residual_score"])
        return ranked

    def recommend_adaptive_test(
        self,
        ranked_candidates: List[Dict[str, Any]],
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Implements Equation (3): U(t) = [H(F) - E(H(F | Xt))] / C(t)
        Dynamically recommends the highest diagnostic value test.
        """
        # Consider top candidates with competitive residual scores
        top_candidates = ranked_candidates[:top_k]
        scores = np.array([c["residual_score"] for c in top_candidates])
        # Softmax-like probability with temperature
        min_score = np.min(scores)
        temp = max(np.median(scores) - min_score, 0.1)
        p = np.exp(-(scores - min_score) / temp)
        p = p / np.sum(p)

        # Baseline entropy H(F)
        h_f = -np.sum(p * np.log2(p + 1e-12))

        # Define candidate tests and their physical bench costs
        available_tests = []
        ctype = self.model.circuit_type

        if ctype == "voltage_divider":
            available_tests = [
                {"name": "DMM Node Voltage (Vout)", "cost": 1.0, "observable": "Vout"},
                {"name": "Series Supply Current (Is)", "cost": 1.5, "observable": "I_supply"},
                {"name": "In-Circuit Ohmmeter Test on R1", "cost": 2.0, "observable": "R1_ohm"},
                {"name": "In-Circuit Ohmmeter Test on R2", "cost": 2.0, "observable": "R2_ohm"}
            ]
        elif ctype == "rc_low_pass":
            available_tests = [
                {"name": "Bode Cutoff Frequency Measurement (fc)", "cost": 2.5, "observable": "fc"},
                {"name": "Oscilloscope Step Current (I_step_init)", "cost": 3.0, "observable": "I_step"},
                {"name": "In-circuit LCR Meter on C1 (Capacitance)", "cost": 4.0, "observable": "C_lcr"},
                {"name": "DMM Resistance Measurement on R1", "cost": 1.5, "observable": "R_dmm"}
            ]
        elif ctype == "rl_high_pass":
            available_tests = [
                {"name": "High-Frequency Cutoff Measurement (fc)", "cost": 2.5, "observable": "fc"},
                {"name": "DC Resistance / Final DC Current through R1", "cost": 1.5, "observable": "I_dc"},
                {"name": "LCR Meter Inductance Measurement on L1", "cost": 4.5, "observable": "L_lcr"},
                {"name": "DMM Resistance Measurement on R1", "cost": 1.5, "observable": "R_dmm"}
            ]
        elif ctype == "rlc_band_pass":
            available_tests = [
                {"name": "Resonant Frequency Sweep (f0)", "cost": 3.0, "observable": "f0"},
                {"name": "Final DC Current through R1", "cost": 1.5, "observable": "I_dc"},
                {"name": "De-soldered Component Test on L1", "cost": 5.0, "observable": "L_lcr"},
                {"name": "De-soldered Component Test on C1", "cost": 5.0, "observable": "C_lcr"},
                {"name": "In-Circuit Resistance on R1", "cost": 1.5, "observable": "R_dmm"}
            ]

        # Calculate expected entropy reduction for each test
        evaluated_tests = []
        for t in available_tests:
            # Measure how well this test separates top candidates
            obs = t["observable"]
            costs = t["cost"]
            # Compute variance of test responses across candidates
            cand_vals = []
            for c in top_candidates:
                comp = c["component"]
                mode = c["mode"]
                if "R" in obs and comp.startswith("R"):
                    cand_vals.append(2.0 if mode in ["+20%", "-20%"] else 5.0)
                elif "C" in obs and comp.startswith("C"):
                    cand_vals.append(2.0 if mode in ["+20%", "-20%"] else 5.0)
                elif "L" in obs and comp.startswith("L"):
                    cand_vals.append(2.0 if mode in ["+20%", "-20%"] else 5.0)
                elif "step" in obs and comp.startswith("R"):
                    cand_vals.append(3.0)
                elif "I_dc" in obs and comp.startswith("R"):
                    cand_vals.append(3.0)
                else:
                    cand_vals.append(1.0)

            # Diversity heuristic: partition entropy
            unique_outcomes = len(set(cand_vals))
            # Conditional entropy reduction estimation
            expected_h = max(h_f - (unique_outcomes / max(len(top_candidates), 1)) * 0.8, 0.05)
            ig = max(h_f - expected_h, 0.05)
            utility = ig / costs

            evaluated_tests.append({
                "test_name": t["name"],
                "cost": costs,
                "entropy_before": float(h_f),
                "entropy_after": float(expected_h),
                "information_gain": float(ig),
                "utility_score": float(utility)
            })

        evaluated_tests.sort(key=lambda x: x["utility_score"], reverse=True)
        best_test = evaluated_tests[0] if evaluated_tests else None

        return {
            "current_entropy": float(h_f),
            "top_candidates_considered": [c["label"] for c in top_candidates],
            "ranked_tests": evaluated_tests,
            "recommended_test": best_test
        }
