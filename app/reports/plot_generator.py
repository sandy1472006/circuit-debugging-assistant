"""
plot_generator.py - Generates publication-ready scientific figures and schematic preview images
using Matplotlib for PDF report generation and UI export.
"""

import matplotlib
matplotlib.use("Agg") # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import io
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

# Publication-quality style defaults
plt.rcParams.update({
    "font.size": 8.5,
    "axes.labelsize": 9.5,
    "axes.titlesize": 10.5,
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5,
    "legend.fontsize": 8.5,
    "figure.titlesize": 11,
    "font.family": "sans-serif",
    "axes.edgecolor": "#94A3B8",
    "axes.linewidth": 0.8,
    "grid.color": "#E2E8F0",
    "grid.linestyle": "--",
    "grid.linewidth": 0.6,
})

def generate_bode_plot(
    freqs: np.ndarray,
    mag_nominal_db: np.ndarray,
    phase_nominal_deg: np.ndarray,
    mag_actual_db: Optional[np.ndarray] = None,
    phase_actual_deg: Optional[np.ndarray] = None,
    cutoff_freq: Optional[float] = None,
    title_suffix: str = "",
    output_path: Optional[Path] = None
) -> bytes:
    """Generates 2-panel Bode Plot (Magnitude dB and Phase deg). Sized compactly for A4 2-page report."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6.2, 3.2), sharex=True, dpi=250)
    fig.patch.set_facecolor("white")
    ax1.set_facecolor("#FCFCFD")
    ax2.set_facecolor("#FCFCFD")

    # Magnitude
    ax1.semilogx(freqs, mag_nominal_db, label="Reference Design", color="#1E40AF", lw=1.8)
    if mag_actual_db is not None:
        ax1.semilogx(freqs, mag_actual_db, label="Observed / Extracted", color="#DC2626", lw=1.6, ls="--")
    if cutoff_freq is not None and cutoff_freq > 0:
        ax1.axvline(cutoff_freq, color="#059669", ls=":", lw=1.2, label=f"fc = {cutoff_freq:,.1f} Hz")
    ax1.set_ylabel("Magnitude (dB)")
    ax1.grid(True)
    ax1.legend(loc="best", framealpha=0.9, fontsize=7.5)
    ax1.set_title(f"Bode Frequency Response {title_suffix}", pad=4, fontsize=9.5, weight="bold", color="#0F172A")

    # Phase
    ax2.semilogx(freqs, phase_nominal_deg, label="Reference Phase", color="#1E40AF", lw=1.8)
    if phase_actual_deg is not None:
        ax2.semilogx(freqs, phase_actual_deg, label="Observed Phase", color="#DC2626", lw=1.6, ls="--")
    if cutoff_freq is not None and cutoff_freq > 0:
        ax2.axvline(cutoff_freq, color="#059669", ls=":", lw=1.2)
    ax2.set_xlabel("Frequency (Hz)")
    ax2.set_ylabel("Phase (deg)")
    ax2.grid(True)

    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=250, bbox_inches="tight")
    if output_path:
        fig.savefig(output_path, format="png", dpi=250, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def generate_step_plot(
    time_points: np.ndarray,
    v_nominal: np.ndarray,
    v_actual: Optional[np.ndarray] = None,
    output_path: Optional[Path] = None
) -> bytes:
    """Generates transient step response plot."""
    fig, ax = plt.subplots(figsize=(6.2, 2.6), dpi=250)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#FCFCFD")

    t_disp = time_points * 1e3
    ax.plot(t_disp, v_nominal, label="Reference Target", color="#1E40AF", lw=1.8)
    if v_actual is not None:
        ax.plot(t_disp, v_actual, label="Observed Circuit", color="#DC2626", lw=1.6, ls="--")

    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Output Voltage Vout (V)")
    ax.set_title("Transient Step Response", pad=4, fontsize=9.5, weight="bold", color="#0F172A")
    ax.grid(True)
    ax.legend(loc="best", framealpha=0.9, fontsize=8)

    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=250, bbox_inches="tight")
    if output_path:
        fig.savefig(output_path, format="png", dpi=250, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def generate_schematic_preview_image(
    circuit_type: str,
    params: Dict[str, float],
    output_path: Path
):
    """
    Renders a clean raster PNG schematic of the reference or corrected circuit
    for inclusion in Section 1 of the 1–2 page PDF report.
    """
    fig, ax = plt.subplots(figsize=(5.2, 3.2), dpi=250)
    fig.patch.set_facecolor("#FAFAFA")
    ax.set_facecolor("#FAFAFA")
    ax.axis("off")

    if circuit_type == "voltage_divider":
        r1 = params.get("R1", 10000.0)
        r2 = params.get("R2", 10000.0)
        ax.text(0.5, 0.93, "Reference: Voltage Divider", ha="center", fontsize=11, weight="bold", color="#0F172A")
        # Wires
        ax.plot([0.15, 0.35], [0.65, 0.65], 'k-', lw=1.8)
        ax.plot(0.15, 0.65, 'ko', ms=5)
        ax.text(0.12, 0.65, "Vin", ha="right", va="center", fontsize=9, weight="bold")
        # R1
        ax.plot([0.35, 0.40, 0.43, 0.47, 0.50, 0.53, 0.57, 0.60, 0.65],
                [0.65, 0.65, 0.70, 0.60, 0.70, 0.60, 0.70, 0.65, 0.65], 'b-', lw=2.2)
        ax.text(0.5, 0.74, f"R1: {r1:g}Ω", ha="center", fontsize=9, color="#1E40AF", weight="bold")
        # Vout node
        ax.plot([0.65, 0.85], [0.65, 0.65], 'k-', lw=1.8)
        ax.plot(0.70, 0.65, 'ko', ms=5)
        ax.plot(0.85, 0.65, 'ko', ms=5)
        ax.text(0.88, 0.65, "Vout", ha="left", va="center", fontsize=9, weight="bold")
        # R2
        ax.plot([0.70, 0.70], [0.65, 0.52], 'k-', lw=1.8)
        ax.plot([0.70, 0.70, 0.65, 0.75, 0.65, 0.75, 0.65, 0.70, 0.70],
                [0.52, 0.47, 0.44, 0.40, 0.37, 0.34, 0.30, 0.27, 0.22], 'b-', lw=2.2)
        ax.text(0.77, 0.37, f"R2: {r2:g}Ω", ha="left", fontsize=9, color="#1E40AF", weight="bold")
        # GND
        ax.plot([0.70, 0.70], [0.22, 0.14], 'k-', lw=1.8)
        ax.plot([0.62, 0.78], [0.14, 0.14], 'k-', lw=1.8)
        ax.plot([0.65, 0.75], [0.11, 0.11], 'k-', lw=1.8)
        ax.plot([0.68, 0.72], [0.08, 0.08], 'k-', lw=1.8)
        ax.text(0.70, 0.02, "GND", ha="center", fontsize=8, color="#475569")

    elif circuit_type == "rc_low_pass":
        r = params.get("R", 1000.0)
        c = params.get("C", 100e-9)
        ax.text(0.5, 0.93, "Reference: RC Low-Pass Filter", ha="center", fontsize=11, weight="bold", color="#0F172A")
        # Vin
        ax.plot([0.15, 0.35], [0.65, 0.65], 'k-', lw=1.8)
        ax.plot(0.15, 0.65, 'ko', ms=5)
        ax.text(0.12, 0.65, "Vin", ha="right", va="center", fontsize=9, weight="bold")
        # R
        ax.plot([0.35, 0.40, 0.43, 0.47, 0.50, 0.53, 0.57, 0.60, 0.65],
                [0.65, 0.65, 0.70, 0.60, 0.70, 0.60, 0.70, 0.65, 0.65], 'b-', lw=2.2)
        ax.text(0.5, 0.74, f"R: {r:g}Ω", ha="center", fontsize=9, color="#1E40AF", weight="bold")
        # Vout
        ax.plot([0.65, 0.85], [0.65, 0.65], 'k-', lw=1.8)
        ax.plot(0.70, 0.65, 'ko', ms=5)
        ax.plot(0.85, 0.65, 'ko', ms=5)
        ax.text(0.88, 0.65, "Vout", ha="left", va="center", fontsize=9, weight="bold")
        # C
        ax.plot([0.70, 0.70], [0.65, 0.45], 'k-', lw=1.8)
        ax.plot([0.62, 0.78], [0.45, 0.45], 'b-', lw=2.5)
        ax.plot([0.62, 0.78], [0.38, 0.38], 'b-', lw=2.5)
        ax.text(0.80, 0.41, f"C: {c*1e9:.1f}nF", ha="left", fontsize=9, color="#1E40AF", weight="bold")
        # GND
        ax.plot([0.70, 0.70], [0.38, 0.20], 'k-', lw=1.8)
        ax.plot([0.62, 0.78], [0.20, 0.20], 'k-', lw=1.8)
        ax.plot([0.65, 0.75], [0.17, 0.17], 'k-', lw=1.8)
        ax.plot([0.68, 0.72], [0.14, 0.14], 'k-', lw=1.8)
        ax.text(0.70, 0.08, "GND", ha="center", fontsize=8, color="#475569")

    elif circuit_type == "rl_high_pass":
        r = params.get("R", 1000.0)
        l = params.get("L", 0.1)
        ax.text(0.5, 0.93, "Reference: RL High-Pass Filter", ha="center", fontsize=11, weight="bold", color="#0F172A")
        # Vin
        ax.plot([0.15, 0.35], [0.65, 0.65], 'k-', lw=1.8)
        ax.plot(0.15, 0.65, 'ko', ms=5)
        ax.text(0.12, 0.65, "Vin", ha="right", va="center", fontsize=9, weight="bold")
        # R
        ax.plot([0.35, 0.40, 0.43, 0.47, 0.50, 0.53, 0.57, 0.60, 0.65],
                [0.65, 0.65, 0.70, 0.60, 0.70, 0.60, 0.70, 0.65, 0.65], 'b-', lw=2.2)
        ax.text(0.5, 0.74, f"R: {r:g}Ω", ha="center", fontsize=9, color="#1E40AF", weight="bold")
        # Vout
        ax.plot([0.65, 0.85], [0.65, 0.65], 'k-', lw=1.8)
        ax.plot(0.70, 0.65, 'ko', ms=5)
        ax.plot(0.85, 0.65, 'ko', ms=5)
        ax.text(0.88, 0.65, "Vout", ha="left", va="center", fontsize=9, weight="bold")
        # L
        ax.plot([0.70, 0.70], [0.65, 0.52], 'k-', lw=1.8)
        theta = np.linspace(0, 4*np.pi, 80)
        y_ind = np.linspace(0.52, 0.30, 80)
        x_ind = 0.70 + 0.04 * np.sin(theta)
        ax.plot(x_ind, y_ind, 'b-', lw=2)
        ax.text(0.78, 0.41, f"L: {l*1e3:.1f}mH", ha="left", fontsize=9, color="#1E40AF", weight="bold")
        # GND
        ax.plot([0.70, 0.70], [0.30, 0.18], 'k-', lw=1.8)
        ax.plot([0.62, 0.78], [0.18, 0.18], 'k-', lw=1.8)
        ax.plot([0.65, 0.75], [0.15, 0.15], 'k-', lw=1.8)
        ax.plot([0.68, 0.72], [0.12, 0.12], 'k-', lw=1.8)
        ax.text(0.70, 0.06, "GND", ha="center", fontsize=8, color="#475569")

    else: # RLC Band-Pass
        r = params.get("R", 1000.0)
        l = params.get("L", 0.01)
        c = params.get("C", 25.33e-9)
        ax.text(0.5, 0.93, "Reference: RLC Band-Pass Filter", ha="center", fontsize=11, weight="bold", color="#0F172A")
        # Vin
        ax.plot([0.10, 0.25], [0.65, 0.65], 'k-', lw=1.8)
        ax.plot(0.10, 0.65, 'ko', ms=5)
        ax.text(0.08, 0.65, "Vin", ha="right", va="center", fontsize=8.5, weight="bold")
        # R
        ax.plot([0.25, 0.30, 0.33, 0.37, 0.40, 0.43, 0.47, 0.50, 0.55],
                [0.65, 0.65, 0.70, 0.60, 0.70, 0.60, 0.70, 0.65, 0.65], 'b-', lw=2.2)
        ax.text(0.40, 0.73, f"R: {r:g}Ω", ha="center", fontsize=8.5, color="#1E40AF", weight="bold")
        # Top bus
        ax.plot([0.55, 0.88], [0.65, 0.65], 'k-', lw=1.8)
        ax.plot(0.62, 0.65, 'ko', ms=4)
        ax.plot(0.78, 0.65, 'ko', ms=4)
        ax.plot(0.88, 0.65, 'ko', ms=5)
        ax.text(0.90, 0.65, "Vout", ha="left", va="center", fontsize=8.5, weight="bold")
        # L
        ax.plot([0.62, 0.62], [0.65, 0.52], 'k-', lw=1.8)
        theta = np.linspace(0, 4*np.pi, 80)
        y_ind = np.linspace(0.52, 0.35, 80)
        x_ind = 0.62 + 0.03 * np.sin(theta)
        ax.plot(x_ind, y_ind, 'b-', lw=2)
        ax.plot([0.62, 0.62], [0.35, 0.22], 'k-', lw=1.8)
        ax.text(0.56, 0.43, f"L:{l*1e3:.0f}mH", ha="right", fontsize=8, color="#1E40AF", weight="bold")
        # C
        ax.plot([0.78, 0.78], [0.65, 0.48], 'k-', lw=1.8)
        ax.plot([0.72, 0.84], [0.48, 0.48], 'b-', lw=2.2)
        ax.plot([0.72, 0.84], [0.42, 0.42], 'b-', lw=2.2)
        ax.plot([0.78, 0.78], [0.42, 0.22], 'k-', lw=1.8)
        ax.text(0.86, 0.45, f"C:{c*1e9:.1f}nF", ha="left", fontsize=8, color="#1E40AF", weight="bold")
        # Bottom bus & GND
        ax.plot([0.62, 0.78], [0.22, 0.22], 'k-', lw=1.8)
        ax.plot([0.70, 0.70], [0.22, 0.14], 'k-', lw=1.8)
        ax.plot([0.62, 0.78], [0.14, 0.14], 'k-', lw=1.8)
        ax.plot([0.65, 0.75], [0.11, 0.11], 'k-', lw=1.8)
        ax.plot([0.68, 0.72], [0.08, 0.08], 'k-', lw=1.8)
        ax.text(0.70, 0.03, "GND", ha="center", fontsize=8, color="#475569")

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
