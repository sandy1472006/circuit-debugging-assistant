"""
circuit_models.py - Deterministic analytical and simulation models for the 4 benchmark circuits:
1. Voltage Divider
2. RC Low-pass Filter
3. RL High-pass Filter
4. RLC Band-pass Filter
"""

import numpy as np
from typing import Dict, List, Tuple, Any, Optional

# Standard frequency evaluation grids from research paper
# RC and RL use 5 log-spaced points between 100 Hz and 100 kHz
FREQ_5_POINTS = np.logspace(2, 5, 5) # [100, 1000, 10000, 31622.78, 100000] Hz
# RLC uses 6 points between 100 Hz and ~316 kHz
FREQ_6_POINTS = np.logspace(2, 5.5, 6) # [100, 501.19, 2511.89, 12589.25, 63095.73, 316227.77] Hz

# Fine sweep for plotting
FREQ_SWEEP_FINE = np.logspace(1, 6, 200)

class CircuitModel:
    """Base class for analytical circuit models."""
    def __init__(self, name: str, circuit_type: str):
        self.name = name
        self.circuit_type = circuit_type
        self.nominal_params: Dict[str, float] = {}

    def get_features(self, params: Dict[str, float], use_independent: bool = True) -> np.ndarray:
        raise NotImplementedError

    def get_feature_names(self, use_independent: bool = True) -> List[str]:
        raise NotImplementedError

    def get_feature_scales(self) -> np.ndarray:
        raise NotImplementedError

    def get_frequency_response(self, params: Dict[str, float], freqs: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        raise NotImplementedError

    def get_step_response(self, params: Dict[str, float], time_points: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def generate_spice_netlist(self, params: Dict[str, float]) -> str:
        raise NotImplementedError


class VoltageDividerModel(CircuitModel):
    """
    Voltage Divider:
    Vin -> R1 -> Vout -> R2 -> GND
    Primary observables: Vout, I_supply
    """
    def __init__(self, r1: float = 10000.0, r2: float = 10000.0, vin: float = 10.0):
        super().__init__("Voltage Divider", "voltage_divider")
        self.nominal_params = {"R1": float(r1), "R2": float(r2), "Vin": float(vin)}

    def compute_dc(self, params: Dict[str, float]) -> Tuple[float, float]:
        r1 = max(params.get("R1", 10000.0), 1e-6)
        r2 = max(params.get("R2", 10000.0), 1e-6)
        vin = params.get("Vin", 10.0)

        r_total = r1 + r2
        i_supply = vin / r_total
        v_out = vin * (r2 / r_total)
        return v_out, i_supply

    def get_features(self, params: Dict[str, float], use_independent: bool = True) -> np.ndarray:
        v_out, i_supply = self.compute_dc(params)
        return np.array([v_out, i_supply], dtype=float)

    def get_feature_names(self, use_independent: bool = True) -> List[str]:
        return ["Vout (V)", "I_supply (A)"]

    def get_feature_scales(self) -> np.ndarray:
        # Scale by nominal values
        v_nom, i_nom = self.compute_dc(self.nominal_params)
        return np.array([max(abs(v_nom), 1.0), max(abs(i_nom), 1e-4)], dtype=float)

    def get_frequency_response(self, params: Dict[str, float], freqs: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        v_out, _ = self.compute_dc(params)
        vin = params.get("Vin", 10.0)
        gain = v_out / max(vin, 1e-6)
        gain_db = 20 * np.log10(max(gain, 1e-6))
        # Flat across all frequencies
        mag_db = np.full_like(freqs, gain_db, dtype=float)
        phase_deg = np.zeros_like(freqs, dtype=float)
        return mag_db, phase_deg

    def get_step_response(self, params: Dict[str, float], time_points: np.ndarray) -> np.ndarray:
        v_out, _ = self.compute_dc(params)
        # Instantaneous step for pure resistive divider
        return np.full_like(time_points, v_out, dtype=float)

    def generate_spice_netlist(self, params: Dict[str, float]) -> str:
        vin = params.get("Vin", 10.0)
        r1 = params.get("R1", 10000.0)
        r2 = params.get("R2", 10000.0)
        netlist = (
            f"* SPICE Netlist: Voltage Divider\n"
            f"VIN in 0 DC {vin}\n"
            f"R1 in out {r1}\n"
            f"R2 out 0 {r2}\n"
            f".op\n"
            f".end\n"
        )
        return netlist


class RCLowPassModel(CircuitModel):
    """
    RC Low-Pass Filter:
    Vin -> R -> Vout -> C -> GND
    Cutoff fc = 1 / (2*pi*R*C)
    Primary features: |H(f)| and Phase(H(f)) at 5 frequencies
    Independent feature: Initial step current I_step(0+) = Vin / R
    """
    def __init__(self, r: float = 1000.0, c: float = 100e-9, vin: float = 1.0):
        super().__init__("RC Low-Pass Filter", "rc_low_pass")
        self.nominal_params = {"R": float(r), "C": float(c), "Vin": float(vin)}

    def cutoff_frequency(self, params: Dict[str, float]) -> float:
        r = max(params.get("R", 1000.0), 1e-6)
        c = max(params.get("C", 100e-9), 1e-15)
        return 1.0 / (2.0 * np.pi * r * c)

    def transfer_function(self, params: Dict[str, float], freqs: np.ndarray) -> np.ndarray:
        r = max(params.get("R", 1000.0), 1e-6)
        c = max(params.get("C", 100e-9), 1e-15)
        omega = 2.0 * np.pi * freqs
        h = 1.0 / (1.0 + 1j * omega * r * c)
        return h

    def get_features(self, params: Dict[str, float], use_independent: bool = True) -> np.ndarray:
        h = self.transfer_function(params, FREQ_5_POINTS)
        mag = np.abs(h)
        phase = np.angle(h) # radians

        if use_independent:
            # Step current at t=0+: I_step(0+) = Vin / R
            r = max(params.get("R", 1000.0), 1e-6)
            vin = params.get("Vin", 1.0)
            i_step = vin / r
            return np.concatenate([mag, phase, [i_step]])
        else:
            return np.concatenate([mag, phase])

    def get_feature_names(self, use_independent: bool = True) -> List[str]:
        names = [f"|H({int(f)}Hz)|" for f in FREQ_5_POINTS] + [f"Phase({int(f)}Hz)" for f in FREQ_5_POINTS]
        if use_independent:
            names.append("I_step_init (A)")
        return names

    def get_feature_scales(self) -> np.ndarray:
        nom_feat = self.get_features(self.nominal_params, use_independent=True)
        scales = []
        for val in nom_feat:
            s = abs(val)
            scales.append(s if s > 1e-4 else 1.0)
        return np.array(scales, dtype=float)

    def get_frequency_response(self, params: Dict[str, float], freqs: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        h = self.transfer_function(params, freqs)
        mag_db = 20.0 * np.log10(np.maximum(np.abs(h), 1e-12))
        phase_deg = np.angle(h, deg=True)
        return mag_db, phase_deg

    def get_step_response(self, params: Dict[str, float], time_points: np.ndarray) -> np.ndarray:
        r = max(params.get("R", 1000.0), 1e-6)
        c = max(params.get("C", 100e-9), 1e-15)
        vin = params.get("Vin", 1.0)
        tau = r * c
        v_out = vin * (1.0 - np.exp(-time_points / max(tau, 1e-12)))
        return v_out

    def generate_spice_netlist(self, params: Dict[str, float]) -> str:
        vin = params.get("Vin", 1.0)
        r = params.get("R", 1000.0)
        c = params.get("C", 100e-9)
        netlist = (
            f"* SPICE Netlist: RC Low-Pass Filter\n"
            f"VIN in 0 AC {vin} PULSE(0 {vin} 0 1n 1n 1m 2m)\n"
            f"R1 in out {r}\n"
            f"C1 out 0 {c}\n"
            f".ac dec 20 100 100k\n"
            f".tran 1u 5m\n"
            f".end\n"
        )
        return netlist


class RLHighPassModel(CircuitModel):
    """
    RL High-Pass Filter:
    Vin -> R -> Vout -> L -> GND
    Cutoff fc = R / (2*pi*L)
    Primary features: |H(f)| and Phase(H(f)) at 5 frequencies
    Independent feature: Final DC current through R: I_DC = Vin / R (since L is short at DC)
    """
    def __init__(self, r: float = 1000.0, l: float = 0.1, vin: float = 1.0):
        super().__init__("RL High-Pass Filter", "rl_high_pass")
        self.nominal_params = {"R": float(r), "L": float(l), "Vin": float(vin)}

    def cutoff_frequency(self, params: Dict[str, float]) -> float:
        r = max(params.get("R", 1000.0), 1e-6)
        l = max(params.get("L", 0.1), 1e-9)
        return r / (2.0 * np.pi * l)

    def transfer_function(self, params: Dict[str, float], freqs: np.ndarray) -> np.ndarray:
        r = max(params.get("R", 1000.0), 1e-6)
        l = max(params.get("L", 0.1), 1e-9)
        omega = 2.0 * np.pi * freqs
        zl = 1j * omega * l
        h = zl / (r + zl)
        return h

    def get_features(self, params: Dict[str, float], use_independent: bool = True) -> np.ndarray:
        h = self.transfer_function(params, FREQ_5_POINTS)
        mag = np.abs(h)
        phase = np.angle(h)

        if use_independent:
            # Final DC current through R: I_DC = Vin / R
            r = max(params.get("R", 1000.0), 1e-6)
            vin = params.get("Vin", 1.0)
            i_dc = vin / r
            return np.concatenate([mag, phase, [i_dc]])
        else:
            return np.concatenate([mag, phase])

    def get_feature_names(self, use_independent: bool = True) -> List[str]:
        names = [f"|H({int(f)}Hz)|" for f in FREQ_5_POINTS] + [f"Phase({int(f)}Hz)" for f in FREQ_5_POINTS]
        if use_independent:
            names.append("I_dc_final (A)")
        return names

    def get_feature_scales(self) -> np.ndarray:
        nom_feat = self.get_features(self.nominal_params, use_independent=True)
        scales = []
        for val in nom_feat:
            s = abs(val)
            scales.append(s if s > 1e-4 else 1.0)
        return np.array(scales, dtype=float)

    def get_frequency_response(self, params: Dict[str, float], freqs: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        h = self.transfer_function(params, freqs)
        mag_db = 20.0 * np.log10(np.maximum(np.abs(h), 1e-12))
        phase_deg = np.angle(h, deg=True)
        return mag_db, phase_deg

    def get_step_response(self, params: Dict[str, float], time_points: np.ndarray) -> np.ndarray:
        r = max(params.get("R", 1000.0), 1e-6)
        l = max(params.get("L", 0.1), 1e-9)
        vin = params.get("Vin", 1.0)
        tau = l / r
        # High pass step response: v_out(t) = Vin * exp(-t / tau)
        v_out = vin * np.exp(-time_points / max(tau, 1e-12))
        return v_out

    def generate_spice_netlist(self, params: Dict[str, float]) -> str:
        vin = params.get("Vin", 1.0)
        r = params.get("R", 1000.0)
        l = params.get("L", 0.1)
        netlist = (
            f"* SPICE Netlist: RL High-Pass Filter\n"
            f"VIN in 0 AC {vin} PULSE(0 {vin} 0 1n 1n 1m 2m)\n"
            f"R1 in out {r}\n"
            f"L1 out 0 {l}\n"
            f".ac dec 20 100 100k\n"
            f".tran 1u 5m\n"
            f".end\n"
        )
        return netlist


class RLCBandPassModel(CircuitModel):
    """
    RLC Band-Pass Filter (Series R, shunt parallel L||C to GND):
    Vin -> R -> Vout -> (L || C) -> GND
    Resonant freq f0 = 1 / (2*pi*sqrt(L*C))
    Quality factor Q = R * sqrt(C / L)
    Bandwidth BW = f0 / Q = 1 / (2*pi*R*C)
    Primary features: |H(f)| and Phase(H(f)) at 6 frequencies
    Independent feature: Final DC current through R: I_DC = Vin / R (since L is short at DC)
    """
    def __init__(self, r: float = 1000.0, l: float = 0.01, c: float = 25.33e-9, vin: float = 1.0):
        super().__init__("RLC Band-Pass Filter", "rlc_band_pass")
        self.nominal_params = {"R": float(r), "L": float(l), "C": float(c), "Vin": float(vin)}

    def resonance_parameters(self, params: Dict[str, float]) -> Tuple[float, float, float]:
        r = max(params.get("R", 1000.0), 1e-6)
        l = max(params.get("L", 0.01), 1e-9)
        c = max(params.get("C", 25.33e-9), 1e-15)

        f0 = 1.0 / (2.0 * np.pi * np.sqrt(l * c))
        q = r * np.sqrt(c / l)
        bw = f0 / max(q, 1e-6)
        return f0, q, bw

    def transfer_function(self, params: Dict[str, float], freqs: np.ndarray) -> np.ndarray:
        r = max(params.get("R", 1000.0), 1e-6)
        l = max(params.get("L", 0.01), 1e-9)
        c = max(params.get("C", 25.33e-9), 1e-15)
        omega = 2.0 * np.pi * freqs

        # Parallel impedance Zp = (j*w*L) / (1 - w^2*L*C)
        # H = Zp / (R + Zp) = 1 / (1 + R/Zp) = 1 / (1 + j*R*(w*C - 1/(w*L)))
        # To avoid division by zero at w=0:
        with np.errstate(divide='ignore', invalid='ignore'):
            w_c = omega * c
            inv_w_l = 1.0 / np.maximum(omega * l, 1e-15)
            denom = 1.0 + 1j * r * (w_c - inv_w_l)
            h = 1.0 / denom
        return h

    def get_features(self, params: Dict[str, float], use_independent: bool = True) -> np.ndarray:
        h = self.transfer_function(params, FREQ_6_POINTS)
        mag = np.abs(h)
        phase = np.angle(h)

        if use_independent:
            r = max(params.get("R", 1000.0), 1e-6)
            vin = params.get("Vin", 1.0)
            i_dc = vin / r
            return np.concatenate([mag, phase, [i_dc]])
        else:
            return np.concatenate([mag, phase])

    def get_feature_names(self, use_independent: bool = True) -> List[str]:
        names = [f"|H({int(f)}Hz)|" for f in FREQ_6_POINTS] + [f"Phase({int(f)}Hz)" for f in FREQ_6_POINTS]
        if use_independent:
            names.append("I_dc_final (A)")
        return names

    def get_feature_scales(self) -> np.ndarray:
        nom_feat = self.get_features(self.nominal_params, use_independent=True)
        scales = []
        for val in nom_feat:
            s = abs(val)
            scales.append(s if s > 1e-4 else 1.0)
        return np.array(scales, dtype=float)

    def get_frequency_response(self, params: Dict[str, float], freqs: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        h = self.transfer_function(params, freqs)
        mag_db = 20.0 * np.log10(np.maximum(np.abs(h), 1e-12))
        phase_deg = np.angle(h, deg=True)
        return mag_db, phase_deg

    def get_step_response(self, params: Dict[str, float], time_points: np.ndarray) -> np.ndarray:
        # Second order RLC step response across parallel LC:
        # At t=0, inductor is open, capacitor uncharged (short), so v_out(0) = 0
        # At t->inf, inductor is short, so v_out(inf) = 0
        # Transient pulse:
        r = max(params.get("R", 1000.0), 1e-6)
        l = max(params.get("L", 0.01), 1e-9)
        c = max(params.get("C", 25.33e-9), 1e-15)
        vin = params.get("Vin", 1.0)

        omega0 = 1.0 / np.sqrt(l * c)
        alpha = 1.0 / (2.0 * r * c) # parallel damping
        if alpha < omega0:
            # Underdamped
            wd = np.sqrt(omega0**2 - alpha**2)
            v_out = vin * (omega0 / wd) * np.exp(-alpha * time_points) * np.sin(wd * time_points)
        else:
            # Overdamped / critically damped
            s1 = -alpha + np.sqrt(max(alpha**2 - omega0**2, 0.0))
            s2 = -alpha - np.sqrt(max(alpha**2 - omega0**2, 0.0))
            v_out = vin * (np.exp(s1 * time_points) - np.exp(s2 * time_points)) * 0.5
        return v_out

    def generate_spice_netlist(self, params: Dict[str, float]) -> str:
        vin = params.get("Vin", 1.0)
        r = params.get("R", 1000.0)
        l = params.get("L", 0.01)
        c = params.get("C", 25.33e-9)
        netlist = (
            f"* SPICE Netlist: RLC Band-Pass Filter\n"
            f"VIN in 0 AC {vin} PULSE(0 {vin} 0 1n 1n 1m 2m)\n"
            f"R1 in out {r}\n"
            f"L1 out 0 {l}\n"
            f"C1 out 0 {c}\n"
            f".ac dec 20 100 500k\n"
            f".tran 0.1u 2m\n"
            f".end\n"
        )
        return netlist


def get_model(circuit_type: str, custom_params: Optional[Dict[str, float]] = None) -> CircuitModel:
    """Factory function for circuit models."""
    if circuit_type == "voltage_divider":
        params = custom_params or {}
        return VoltageDividerModel(
            r1=params.get("R1", 10000.0),
            r2=params.get("R2", 10000.0),
            vin=params.get("Vin", 10.0)
        )
    elif circuit_type == "rc_low_pass":
        params = custom_params or {}
        return RCLowPassModel(
            r=params.get("R", 1000.0),
            c=params.get("C", 100e-9),
            vin=params.get("Vin", 1.0)
        )
    elif circuit_type == "rl_high_pass":
        params = custom_params or {}
        return RLHighPassModel(
            r=params.get("R", 1000.0),
            l=params.get("L", 0.1),
            vin=params.get("Vin", 1.0)
        )
    elif circuit_type == "rlc_band_pass":
        params = custom_params or {}
        return RLCBandPassModel(
            r=params.get("R", 1000.0),
            l=params.get("L", 0.01),
            c=params.get("C", 25.33e-9),
            vin=params.get("Vin", 1.0)
        )
    else:
        raise ValueError(f"Unknown circuit type: {circuit_type}")
