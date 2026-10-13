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


def generate_annotated_schematics(
    circuit_type: str,
    params: Dict[str, float],
    findings: List[Dict[str, Any]],
    is_faulty: bool,
    out_uploaded_path: Path,
    out_expected_path: Path
):
    """
    Renders high-quality side-by-side schematics matching the exact style of the reference report:
    - out_uploaded_path: Uploaded Circuit (Input) with fault highlighted (e.g. red dashed circle).
    - out_expected_path: Expected/Correct Circuit with clean reference topology.
    """
    out_uploaded_path.parent.mkdir(parents=True, exist_ok=True)
    out_expected_path.parent.mkdir(parents=True, exist_ok=True)

    def draw_single(out_path: Path, faulty: bool):
        fig, ax = plt.subplots(figsize=(3.6, 2.3), dpi=260)
        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")
        ax.axis("off")
        ax.set_xlim(-0.25, 3.85)
        ax.set_ylim(-0.4, 2.25)

        if circuit_type == "rc_low_pass":
            r_val = params.get("R", 10000.0)
            c_val = params.get("C", 100e-9)

            # 1. AC Source Vin at x=0.5, y=0.9
            src_circle = plt.Circle((0.5, 0.9), 0.33, color="white", ec="black", lw=1.6)
            ax.add_patch(src_circle)
            sine_x = np.linspace(0.27, 0.73, 40)
            sine_y = 0.9 + 0.14 * np.sin(2 * np.pi * (sine_x - 0.27) / 0.46)
            ax.plot(sine_x, sine_y, "k-", lw=1.3)
            ax.text(0.5, 1.34, "+", ha="center", va="center", fontsize=9, weight="bold")
            ax.text(0.5, 0.44, "-", ha="center", va="center", fontsize=10, weight="bold")
            ax.text(0.04, 0.9, "Vin\n5 V (peak)\n1 kHz", ha="right", va="center", fontsize=7.5, weight="bold", color="#0F172A")

            # Ground under Vin
            ax.plot([0.5, 0.5], [0.57, 0.25], "k-", lw=1.5)
            ax.plot([0.3, 0.7], [0.25, 0.25], "k-", lw=1.6)
            ax.plot([0.38, 0.62], [0.18, 0.18], "k-", lw=1.6)
            ax.plot([0.44, 0.56], [0.11, 0.11], "k-", lw=1.6)

            # Top wire from Vin to R1
            ax.plot([0.5, 0.5, 1.1], [1.23, 1.68, 1.68], "k-", lw=1.5)

            # Resistor R1
            r_x = [1.1, 1.2, 1.28, 1.44, 1.6, 1.76, 1.92, 2.0, 2.1]
            r_y = [1.68, 1.68, 1.83, 1.53, 1.83, 1.53, 1.83, 1.68, 1.68]
            ax.plot(r_x, r_y, "k-", lw=1.6)
            ax.text(1.6, 1.95, f"R1\n{r_val/1000:g} kΩ" if r_val>=1000 else f"R1\n{r_val:g} Ω", ha="center", va="bottom", fontsize=8, weight="bold", color="#0F172A")

            # Wire to Vout and C1
            ax.plot([2.1, 2.7, 3.2], [1.68, 1.68, 1.68], "k-", lw=1.5)
            ax.plot([2.7], [1.68], "ko", ms=4)
            ax.plot([3.2], [1.68], "ro", ms=4)
            ax.text(3.3, 1.68, "Vout", ha="left", va="center", fontsize=8.5, weight="bold", color="#DC2626")

            # Wire down to Capacitor C1
            ax.plot([2.7, 2.7], [1.68, 1.2], "k-", lw=1.5)
            ax.plot([2.35, 3.05], [1.2, 1.2], "k-", lw=2.2)
            ax.plot([2.35, 3.05], [1.05, 1.05], "k-", lw=2.2)
            ax.text(3.15, 1.12, f"C1\n{c_val*1e9:.0f} nF", ha="left", va="center", fontsize=8, weight="bold", color="#0F172A")

            if not faulty:
                # Connected ground
                ax.plot([2.7, 2.7], [1.05, 0.6], "k-", lw=1.5)
                ax.plot([2.5, 2.9], [0.6, 0.6], "k-", lw=1.6)
                ax.plot([2.57, 2.83], [0.53, 0.53], "k-", lw=1.6)
                ax.plot([2.63, 2.77], [0.46, 0.46], "k-", lw=1.6)
            else:
                # Disconnected ground with red dashed circle
                fault_circle = plt.Circle((2.7, 0.8), 0.26, color="none", ec="#DC2626", lw=1.6, ls="--")
                ax.add_patch(fault_circle)
                ax.text(2.7, 0.38, "Capacitor not\nconnected to ground", ha="center", va="top", fontsize=7.2, color="#DC2626", weight="bold")

        elif circuit_type == "voltage_divider":
            r1_val = params.get("R1", 10000.0)
            r2_val = params.get("R2", 5000.0)
            vin_val = params.get("Vin", 10.0)

            # DC Source
            src_circle = plt.Circle((0.5, 0.9), 0.33, color="white", ec="black", lw=1.6)
            ax.add_patch(src_circle)
            ax.text(0.5, 1.05, "+", ha="center", va="center", fontsize=9, weight="bold")
            ax.text(0.5, 0.75, "-", ha="center", va="center", fontsize=10, weight="bold")
            ax.text(0.04, 0.9, f"Vin\n{vin_val:g} V DC", ha="right", va="center", fontsize=7.5, weight="bold")

            # Ground under Vin
            ax.plot([0.5, 0.5], [0.57, 0.25], "k-", lw=1.5)
            ax.plot([0.3, 0.7], [0.25, 0.25], "k-", lw=1.6)
            ax.plot([0.38, 0.62], [0.18, 0.18], "k-", lw=1.6)
            ax.plot([0.44, 0.56], [0.11, 0.11], "k-", lw=1.6)

            # Top wire to R1
            ax.plot([0.5, 0.5, 1.1], [1.23, 1.68, 1.68], "k-", lw=1.5)
            r_x = [1.1, 1.2, 1.28, 1.44, 1.6, 1.76, 1.92, 2.0, 2.1]
            r_y = [1.68, 1.68, 1.83, 1.53, 1.83, 1.53, 1.83, 1.68, 1.68]
            ax.plot(r_x, r_y, "k-", lw=1.6)
            ax.text(1.6, 1.95, f"R1\n{r1_val/1000:g} kΩ", ha="center", va="bottom", fontsize=8, weight="bold")

            # Node to Vout
            ax.plot([2.1, 2.7, 3.2], [1.68, 1.68, 1.68], "k-", lw=1.5)
            ax.plot([2.7], [1.68], "ko", ms=4)
            ax.plot([3.2], [1.68], "ro", ms=4)
            ax.text(3.3, 1.68, "Vout", ha="left", va="center", fontsize=8.5, weight="bold", color="#DC2626")

            # R2 shunt
            ax.plot([2.7, 2.7], [1.68, 1.4], "k-", lw=1.5)
            r2_y = [1.4, 1.34, 1.26, 1.18, 1.10, 1.02, 0.94, 0.86, 0.80]
            r2_x = [2.7, 2.7, 2.55, 2.85, 2.55, 2.85, 2.55, 2.7, 2.7]
            ax.plot(r2_x, r2_y, "k-", lw=1.6)
            ax.text(3.05, 1.1, f"R2\n{r2_val/1000:g} kΩ", ha="left", va="center", fontsize=8, weight="bold")

            if not faulty:
                ax.plot([2.7, 2.7], [0.80, 0.55], "k-", lw=1.5)
                ax.plot([2.5, 2.9], [0.55, 0.55], "k-", lw=1.6)
                ax.plot([2.57, 2.83], [0.48, 0.48], "k-", lw=1.6)
                ax.plot([2.63, 2.77], [0.41, 0.41], "k-", lw=1.6)
            else:
                fault_circle = plt.Circle((2.7, 0.70), 0.26, color="none", ec="#DC2626", lw=1.6, ls="--")
                ax.add_patch(fault_circle)
                ax.text(2.7, 0.32, "Attenuation Drift /\nImproper Ratio", ha="center", va="top", fontsize=7.2, color="#DC2626", weight="bold")

        elif circuit_type == "rl_high_pass":
            r_val = params.get("R", 1000.0)
            l_val = params.get("L", 0.01)

            # AC Source
            src_circle = plt.Circle((0.5, 0.9), 0.33, color="white", ec="black", lw=1.6)
            ax.add_patch(src_circle)
            sine_x = np.linspace(0.27, 0.73, 40)
            sine_y = 0.9 + 0.14 * np.sin(2 * np.pi * (sine_x - 0.27) / 0.46)
            ax.plot(sine_x, sine_y, "k-", lw=1.3)
            ax.text(0.5, 1.34, "+", ha="center", va="center", fontsize=9, weight="bold")
            ax.text(0.5, 0.44, "-", ha="center", va="center", fontsize=10, weight="bold")
            ax.text(0.04, 0.9, "Vin\n5 V (peak)\n1 kHz", ha="right", va="center", fontsize=7.5, weight="bold")

            # Ground under Vin
            ax.plot([0.5, 0.5], [0.57, 0.25], "k-", lw=1.5)
            ax.plot([0.3, 0.7], [0.25, 0.25], "k-", lw=1.6)
            ax.plot([0.38, 0.62], [0.18, 0.18], "k-", lw=1.6)
            ax.plot([0.44, 0.56], [0.11, 0.11], "k-", lw=1.6)

            # Series R1
            ax.plot([0.5, 0.5, 1.1], [1.23, 1.68, 1.68], "k-", lw=1.5)
            r_x = [1.1, 1.2, 1.28, 1.44, 1.6, 1.76, 1.92, 2.0, 2.1]
            r_y = [1.68, 1.68, 1.83, 1.53, 1.83, 1.53, 1.83, 1.68, 1.68]
            ax.plot(r_x, r_y, "k-", lw=1.6)
            ax.text(1.6, 1.95, f"R1\n{r_val:g} Ω", ha="center", va="bottom", fontsize=8, weight="bold")

            # Vout node
            ax.plot([2.1, 2.7, 3.2], [1.68, 1.68, 1.68], "k-", lw=1.5)
            ax.plot([2.7], [1.68], "ko", ms=4)
            ax.plot([3.2], [1.68], "ro", ms=4)
            ax.text(3.3, 1.68, "Vout", ha="left", va="center", fontsize=8.5, weight="bold", color="#DC2626")

            # Shunt Inductor L1
            ax.plot([2.7, 2.7], [1.68, 1.35], "k-", lw=1.5)
            theta = np.linspace(0, 3.5 * np.pi, 60)
            ind_y = np.linspace(1.35, 0.85, 60)
            ind_x = 2.7 + 0.12 * np.sin(theta)
            ax.plot(ind_x, ind_y, "k-", lw=1.8)
            ax.text(3.05, 1.1, f"L1\n{l_val*1000:g} mH", ha="left", va="center", fontsize=8, weight="bold")

            if not faulty:
                ax.plot([2.7, 2.7], [0.85, 0.55], "k-", lw=1.5)
                ax.plot([2.5, 2.9], [0.55, 0.55], "k-", lw=1.6)
                ax.plot([2.57, 2.83], [0.48, 0.48], "k-", lw=1.6)
                ax.plot([2.63, 2.77], [0.41, 0.41], "k-", lw=1.6)
            else:
                fault_circle = plt.Circle((2.7, 0.75), 0.26, color="none", ec="#DC2626", lw=1.6, ls="--")
                ax.add_patch(fault_circle)
                ax.text(2.7, 0.35, "Inductor Shorted /\nDisconnected", ha="center", va="top", fontsize=7.2, color="#DC2626", weight="bold")

        else: # rlc_band_pass
            r_val = params.get("R", 1000.0)
            l_val = params.get("L", 0.01)
            c_val = params.get("C", 100e-9)

            # AC Source
            src_circle = plt.Circle((0.5, 0.9), 0.33, color="white", ec="black", lw=1.6)
            ax.add_patch(src_circle)
            sine_x = np.linspace(0.27, 0.73, 40)
            sine_y = 0.9 + 0.14 * np.sin(2 * np.pi * (sine_x - 0.27) / 0.46)
            ax.plot(sine_x, sine_y, "k-", lw=1.3)
            ax.text(0.5, 1.34, "+", ha="center", va="center", fontsize=9, weight="bold")
            ax.text(0.5, 0.44, "-", ha="center", va="center", fontsize=10, weight="bold")
            ax.text(0.04, 0.9, "Vin\n1 V (peak)\n1 kHz", ha="right", va="center", fontsize=7.5, weight="bold")

            # Ground under Vin
            ax.plot([0.5, 0.5], [0.57, 0.25], "k-", lw=1.5)
            ax.plot([0.3, 0.7], [0.25, 0.25], "k-", lw=1.6)
            ax.plot([0.38, 0.62], [0.18, 0.18], "k-", lw=1.6)
            ax.plot([0.44, 0.56], [0.11, 0.11], "k-", lw=1.6)

            # Series R1
            ax.plot([0.5, 0.5, 1.1], [1.23, 1.68, 1.68], "k-", lw=1.5)
            r_x = [1.1, 1.2, 1.28, 1.44, 1.6, 1.76, 1.92, 2.0, 2.1]
            r_y = [1.68, 1.68, 1.83, 1.53, 1.83, 1.53, 1.83, 1.68, 1.68]
            ax.plot(r_x, r_y, "k-", lw=1.6)
            ax.text(1.6, 1.95, f"R1\n{r_val:g} Ω", ha="center", va="bottom", fontsize=8, weight="bold")

            # Node to Vout
            ax.plot([2.1, 2.9, 3.3], [1.68, 1.68, 1.68], "k-", lw=1.5)
            ax.plot([2.5], [1.68], "ko", ms=3.5)
            ax.plot([2.9], [1.68], "ko", ms=3.5)
            ax.plot([3.3], [1.68], "ro", ms=4)
            ax.text(3.4, 1.68, "Vout", ha="left", va="center", fontsize=8.5, weight="bold", color="#DC2626")

            # Tank: L branch
            ax.plot([2.5, 2.5], [1.68, 1.35], "k-", lw=1.5)
            theta = np.linspace(0, 3 * np.pi, 50)
            ind_y = np.linspace(1.35, 0.95, 50)
            ind_x = 2.5 + 0.10 * np.sin(theta)
            ax.plot(ind_x, ind_y, "k-", lw=1.8)
            ax.plot([2.5, 2.5], [0.95, 0.70], "k-", lw=1.5)
            ax.text(2.35, 1.15, f"L1\n{l_val*1000:g}mH", ha="right", va="center", fontsize=7.5, weight="bold")

            # Tank: C branch
            ax.plot([2.9, 2.9], [1.68, 1.25], "k-", lw=1.5)
            ax.plot([2.7, 3.1], [1.25, 1.25], "k-", lw=2.2)
            ax.plot([2.7, 3.1], [1.10, 1.10], "k-", lw=2.2)
            ax.plot([2.9, 2.9], [1.10, 0.70], "k-", lw=1.5)
            ax.text(3.2, 1.18, f"C1\n{c_val*1e9:.0f}nF", ha="left", va="center", fontsize=7.5, weight="bold")

            # Bottom tank bus
            ax.plot([2.5, 2.9], [0.70, 0.70], "k-", lw=1.5)
            ax.plot([2.7, 2.7], [0.70, 0.50], "k-", lw=1.5)

            if not faulty:
                ax.plot([2.5, 2.9], [0.50, 0.50], "k-", lw=1.6)
                ax.plot([2.57, 2.83], [0.43, 0.43], "k-", lw=1.6)
                ax.plot([2.63, 2.77], [0.36, 0.36], "k-", lw=1.6)
            else:
                fault_circle = plt.Circle((2.7, 0.58), 0.25, color="none", ec="#DC2626", lw=1.6, ls="--")
                ax.add_patch(fault_circle)
                ax.text(2.7, 0.28, "Resonant Tank\nMismatch", ha="center", va="top", fontsize=7.2, color="#DC2626", weight="bold")

        fig.tight_layout()
        fig.savefig(out_path, bbox_inches="tight")
        plt.close(fig)

    draw_single(out_uploaded_path, faulty=is_faulty)
    draw_single(out_expected_path, faulty=False)


def generate_theory_formula_images(
    circuit_type: str,
    params: Dict[str, float],
    out_formula_path: Path,
    out_calc_path: Path
):
    """
    Renders the exact theory formula cards matching Section 5 in the reference image:
    - out_formula_path: Left card displaying general formula
    - out_calc_path: Right card showing step-by-step substitution with extracted values
    """
    out_formula_path.parent.mkdir(parents=True, exist_ok=True)
    out_calc_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Formula Card
    fig1, ax1 = plt.subplots(figsize=(2.2, 0.95), dpi=300)
    ax1.axis("off")

    # 2. Calculation Card
    fig2, ax2 = plt.subplots(figsize=(4.0, 1.3), dpi=300)
    ax2.axis("off")

    if circuit_type == "rc_low_pass":
        r = params.get("R", 10000.0)
        c = params.get("C", 100e-9)
        fc = 1.0 / (2.0 * np.pi * r * c)

        ax1.text(0.5, 0.5, r"$f_c = \frac{1}{2\pi RC}$", fontsize=18, ha="center", va="center", color="#0F172A")

        ax2.text(0.02, 0.88, "Using extracted values:", fontsize=8.5, fontweight="bold", color="#1E293B")
        ax2.text(0.02, 0.62, f"$R = {r/1000:g}\\ \\mathrm{{k\\Omega}} = {r:,.0f}\\ \\Omega$", fontsize=8.5, color="#334155")
        ax2.text(0.02, 0.38, f"$C = {c*1e9:.0f}\\ \\mathrm{{nF}} = {c*1e9:.0f} \\times 10^{{-9}}\\ \\mathrm{{F}}$", fontsize=8.5, color="#334155")
        ax2.text(0.02, 0.10, f"$f_c = \\frac{{1}}{{2\\pi ({r:,.0f})({c*1e9:.0f} \\times 10^{{-9}})}} \\approx {fc:.2f}\\ \\mathrm{{Hz}}$", fontsize=9.0, color="#0F172A", weight="bold")

    elif circuit_type == "voltage_divider":
        r1 = params.get("R1", 10000.0)
        r2 = params.get("R2", 5000.0)
        vin = params.get("Vin", 10.0)
        vout = vin * (r2 / (r1 + r2))

        ax1.text(0.5, 0.5, r"$V_{out} = V_{in} \cdot \frac{R_2}{R_1 + R_2}$", fontsize=17, ha="center", va="center", color="#0F172A")

        ax2.text(0.02, 0.88, "Using extracted values:", fontsize=8.5, fontweight="bold", color="#1E293B")
        ax2.text(0.02, 0.62, f"$R_1 = {r1/1000:g}\\ \\mathrm{{k\\Omega}},\\ R_2 = {r2/1000:g}\\ \\mathrm{{k\\Omega}}$", fontsize=8.5, color="#334155")
        ax2.text(0.02, 0.38, f"$V_{{in}} = {vin:g}\\ \\mathrm{{V\\ DC}}$", fontsize=8.5, color="#334155")
        ax2.text(0.02, 0.10, f"$V_{{out}} = {vin:g} \\cdot \\frac{{{r2:,.0f}}}{{{r1:,.0f} + {r2:,.0f}}} \\approx {vout:.2f}\\ \\mathrm{{V}}$", fontsize=9.0, color="#0F172A", weight="bold")

    elif circuit_type == "rl_high_pass":
        r = params.get("R", 1000.0)
        l = params.get("L", 0.01)
        fc = r / (2.0 * np.pi * l)

        ax1.text(0.5, 0.5, r"$f_c = \frac{R}{2\pi L}$", fontsize=18, ha="center", va="center", color="#0F172A")

        ax2.text(0.02, 0.88, "Using extracted values:", fontsize=8.5, fontweight="bold", color="#1E293B")
        ax2.text(0.02, 0.62, f"$R = {r:,.0f}\\ \\Omega,\\ L = {l*1000:g}\\ \\mathrm{{mH}} = {l:g}\\ \\mathrm{{H}}$", fontsize=8.5, color="#334155")
        ax2.text(0.02, 0.38, f"$\\omega_c = R / L = {r/l:,.0f}\\ \\mathrm{{rad/s}}$", fontsize=8.5, color="#334155")
        ax2.text(0.02, 0.10, f"$f_c = \\frac{{{r:,.0f}}}{{2\\pi ({l:g})}} \\approx {fc/1000:.2f}\\ \\mathrm{{kHz}}$", fontsize=9.0, color="#0F172A", weight="bold")

    else: # rlc_band_pass
        r = params.get("R", 1000.0)
        l = params.get("L", 0.01)
        c = params.get("C", 100e-9)
        f0 = 1.0 / (2.0 * np.pi * np.sqrt(l * c))

        ax1.text(0.5, 0.5, r"$f_0 = \frac{1}{2\pi \sqrt{LC}}$", fontsize=18, ha="center", va="center", color="#0F172A")

        ax2.text(0.02, 0.88, "Using extracted values:", fontsize=8.5, fontweight="bold", color="#1E293B")
        ax2.text(0.02, 0.62, f"$L = {l*1000:g}\\ \\mathrm{{mH}},\\ C = {c*1e9:.0f}\\ \\mathrm{{nF}}$", fontsize=8.5, color="#334155")
        ax2.text(0.02, 0.38, f"$LC = {(l*c):.2e}\\ \\mathrm{{s^2}}$", fontsize=8.5, color="#334155")
        ax2.text(0.02, 0.10, f"$f_0 = \\frac{{1}}{{2\\pi \\sqrt{{{l:g} \\times {c:g}}}}} \\approx {f0/1000:.2f}\\ \\mathrm{{kHz}}$", fontsize=9.0, color="#0F172A", weight="bold")

    fig1.savefig(out_formula_path, bbox_inches="tight", transparent=True)
    fig2.savefig(out_calc_path, bbox_inches="tight", transparent=True)
    plt.close(fig1)
    plt.close(fig2)


def generate_comparison_simulation_plots(
    circuit_type: str,
    params: Dict[str, float],
    is_faulty: bool,
    out_correct_path: Path,
    out_faulty_path: Path
):
    """
    Renders the exact 2-panel simulation plots matching Section 6 in the reference image:
    - out_correct_path: Correct Circuit (Expected Response)
    - out_faulty_path: Uploaded Faulty Circuit (Simulated)
    """
    out_correct_path.parent.mkdir(parents=True, exist_ok=True)
    out_faulty_path.parent.mkdir(parents=True, exist_ok=True)

    f = np.logspace(1, 5, 200)

    # 1. Correct Plot
    fig1, ax1 = plt.subplots(figsize=(3.4, 2.15), dpi=250)
    fig1.patch.set_facecolor("white")
    ax1.set_facecolor("#FCFCFD")

    # 2. Faulty Plot
    fig2, ax2 = plt.subplots(figsize=(3.4, 2.15), dpi=250)
    fig2.patch.set_facecolor("white")
    ax2.set_facecolor("#FCFCFD")

    if circuit_type == "rc_low_pass":
        r = params.get("R", 10000.0)
        c = params.get("C", 100e-9)
        fc = 1.0 / (2.0 * np.pi * r * c)
        h = 1.0 / (1.0 + 1j * 2 * np.pi * f * r * c)
        mag_db = 20 * np.log10(np.abs(h))

        # Expected
        ax1.semilogx(f, mag_db, color="#2563EB", lw=1.8, label="Expected (RC Low-Pass)")
        ax1.axvline(fc, color="#DC2626", linestyle="--", lw=1.2)
        ax1.text(fc * 1.15, -45, f"fc = {fc:.2f} Hz", color="#DC2626", fontsize=7.5, weight="bold")
        ax1.set_title("Frequency Response (Magnitude)", fontsize=8.5, weight="bold", pad=4)
        ax1.set_xlim(10, 100000)
        ax1.set_ylim(-65, 5)
        ax1.set_yticks([0, -10, -20, -30, -40, -50, -60])
        ax1.set_xlabel("Frequency (Hz)", fontsize=7.8)
        ax1.set_ylabel("Magnitude (dB)", fontsize=7.8)
        ax1.grid(True, linestyle=":", alpha=0.6)
        ax1.legend(loc="upper right", fontsize=6.8, framealpha=0.9)

        # Faulty (Capacitor open -> flat 0 dB line)
        mag_fault = np.zeros_like(f) if is_faulty else mag_db
        lbl = "Faulty (Capacitor Open)" if is_faulty else "Nominal Verification"
        ax2.semilogx(f, mag_fault, color="#DC2626", lw=1.8, label=lbl)
        ax2.set_title("Frequency Response (Magnitude)", fontsize=8.5, weight="bold", pad=4)
        ax2.set_xlim(10, 100000)
        ax2.set_ylim(-65, 5)
        ax2.set_yticks([0, -10, -20, -30, -40, -50, -60])
        ax2.set_xlabel("Frequency (Hz)", fontsize=7.8)
        ax2.set_ylabel("Magnitude (dB)", fontsize=7.8)
        ax2.grid(True, linestyle=":", alpha=0.6)
        ax2.legend(loc="lower right" if is_faulty else "upper right", fontsize=6.8, framealpha=0.9)

    elif circuit_type == "voltage_divider":
        r1 = params.get("R1", 10000.0)
        r2 = params.get("R2", 5000.0)
        vin = params.get("Vin", 10.0)
        ratio_nom = r2 / (r1 + r2)
        vout_nom = vin * ratio_nom
        ratio_act = ratio_nom * 0.7 if is_faulty else ratio_nom

        t = np.linspace(0, 0.002, 100)
        ax1.plot(t * 1e3, np.full_like(t, vout_nom), color="#2563EB", lw=1.8, label="Expected Vout = 3.33V")
        ax1.set_title("DC Voltage Transfer", fontsize=8.5, weight="bold", pad=4)
        ax1.set_ylim(0, vin + 1)
        ax1.set_xlabel("Time (ms)", fontsize=7.8)
        ax1.set_ylabel("Output Voltage (V)", fontsize=7.8)
        ax1.grid(True, linestyle=":", alpha=0.6)
        ax1.legend(loc="upper right", fontsize=7.0)

        ax2.plot(t * 1e3, np.full_like(t, vin * ratio_act), color="#DC2626", lw=1.8, label="Simulated Faulty Vout")
        ax2.set_title("DC Voltage Transfer", fontsize=8.5, weight="bold", pad=4)
        ax2.set_ylim(0, vin + 1)
        ax2.set_xlabel("Time (ms)", fontsize=7.8)
        ax2.set_ylabel("Output Voltage (V)", fontsize=7.8)
        ax2.grid(True, linestyle=":", alpha=0.6)
        ax2.legend(loc="upper right", fontsize=7.0)

    elif circuit_type == "rl_high_pass":
        r = params.get("R", 1000.0)
        l = params.get("L", 0.01)
        fc = r / (2.0 * np.pi * l)
        xl = 2 * np.pi * f * l
        h = (1j * xl) / (r + 1j * xl)
        mag_db = 20 * np.log10(np.abs(h))

        ax1.semilogx(f, mag_db, color="#2563EB", lw=1.8, label="Expected (RL High-Pass)")
        ax1.axvline(fc, color="#DC2626", linestyle="--", lw=1.2)
        ax1.text(fc * 0.2, -45, f"fc = {fc/1000:.1f} kHz", color="#DC2626", fontsize=7.5, weight="bold")
        ax1.set_title("Frequency Response (Magnitude)", fontsize=8.5, weight="bold", pad=4)
        ax1.set_xlim(10, 100000)
        ax1.set_ylim(-65, 5)
        ax1.set_yticks([0, -10, -20, -30, -40, -50, -60])
        ax1.set_xlabel("Frequency (Hz)", fontsize=7.8)
        ax1.set_ylabel("Magnitude (dB)", fontsize=7.8)
        ax1.grid(True, linestyle=":", alpha=0.6)
        ax1.legend(loc="lower right", fontsize=6.8)

        # Faulty: Inductor shorted -> -60 dB across band
        mag_fault = np.full_like(f, -60.0) if is_faulty else mag_db
        ax2.semilogx(f, mag_fault, color="#DC2626", lw=1.8, label="Faulty (L Shorted to GND)" if is_faulty else "Nominal")
        ax2.set_title("Frequency Response (Magnitude)", fontsize=8.5, weight="bold", pad=4)
        ax2.set_xlim(10, 100000)
        ax2.set_ylim(-65, 5)
        ax2.set_yticks([0, -10, -20, -30, -40, -50, -60])
        ax2.set_xlabel("Frequency (Hz)", fontsize=7.8)
        ax2.set_ylabel("Magnitude (dB)", fontsize=7.8)
        ax2.grid(True, linestyle=":", alpha=0.6)
        ax2.legend(loc="upper right", fontsize=6.8)

    else: # rlc_band_pass
        r = params.get("R", 1000.0)
        l = params.get("L", 0.01)
        c = params.get("C", 100e-9)
        f0 = 1.0 / (2.0 * np.pi * np.sqrt(l * c))
        w = 2 * np.pi * f
        z_tank = 1.0 / (1j * w * c + 1.0 / (1j * w * l + 1e-9))
        h = z_tank / (r + z_tank)
        mag_db = 20 * np.log10(np.maximum(np.abs(h), 1e-4))

        ax1.semilogx(f, mag_db, color="#2563EB", lw=1.8, label="Expected (RLC Band-Pass)")
        ax1.axvline(f0, color="#DC2626", linestyle="--", lw=1.2)
        ax1.text(f0 * 1.15, -45, f"f0 = {f0/1000:.1f} kHz", color="#DC2626", fontsize=7.5, weight="bold")
        ax1.set_title("Frequency Response (Magnitude)", fontsize=8.5, weight="bold", pad=4)
        ax1.set_xlim(10, 100000)
        ax1.set_ylim(-65, 5)
        ax1.set_yticks([0, -10, -20, -30, -40, -50, -60])
        ax1.set_xlabel("Frequency (Hz)", fontsize=7.8)
        ax1.set_ylabel("Magnitude (dB)", fontsize=7.8)
        ax1.grid(True, linestyle=":", alpha=0.6)
        ax1.legend(loc="upper right", fontsize=6.8)

        mag_fault = mag_db - 15.0 if is_faulty else mag_db
        ax2.semilogx(f, mag_fault, color="#DC2626", lw=1.8, label="Faulty (Tank Degraded)" if is_faulty else "Nominal")
        ax2.set_title("Frequency Response (Magnitude)", fontsize=8.5, weight="bold", pad=4)
        ax2.set_xlim(10, 100000)
        ax2.set_ylim(-65, 5)
        ax2.set_yticks([0, -10, -20, -30, -40, -50, -60])
        ax2.set_xlabel("Frequency (Hz)", fontsize=7.8)
        ax2.set_ylabel("Magnitude (dB)", fontsize=7.8)
        ax2.grid(True, linestyle=":", alpha=0.6)
        ax2.legend(loc="upper right", fontsize=6.8)

    fig1.tight_layout()
    fig2.tight_layout()
    fig1.savefig(out_correct_path, bbox_inches="tight")
    fig2.savefig(out_faulty_path, bbox_inches="tight")
    plt.close(fig1)
    plt.close(fig2)


def generate_single_combined_simulation_plot(
    circuit_type: str,
    params: Dict[str, float],
    is_faulty: bool,
    out_path: Path
):
    """
    Generates the exact single combined simulation plot matching Section 6 in Image 2:
    Both Expected curve and Uploaded Faulty curve plotted on the same axes with cutoff annotation.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6.2, 2.5), dpi=260)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#FCFCFD")

    if circuit_type == "rc_low_pass":
        f = np.logspace(0, 5, 300)
        r = params.get("R", 10000.0)
        c = params.get("C", 100e-9)
        fc = 1.0 / (2.0 * np.pi * r * c)
        h = 1.0 / (1.0 + 1j * 2 * np.pi * f * r * c)
        mag_nom = 20 * np.log10(np.abs(h))
        mag_fault = np.zeros_like(f) if is_faulty else mag_nom

        ax.semilogx(f, mag_nom, color="#2563EB", lw=1.8, label="Expected (RC Low-Pass)")
        if is_faulty:
            ax.semilogx(f, mag_fault, color="#DC2626", lw=1.5, ls="--", label="Uploaded Faulty Circuit (Capacitor Open)")

        ax.axvline(fc, color="#475569", linestyle=":", lw=1.0)
        ax.annotate(
            f"fc = {fc:.2f} Hz",
            xy=(fc, -3.0),
            xytext=(fc * 2.0, -50),
            arrowprops=dict(arrowstyle="->", color="black", lw=1.0),
            fontsize=7.5,
            fontweight="bold",
            bbox=dict(boxstyle="square,pad=0.3", facecolor="white", edgecolor="#94A3B8", lw=0.8)
        )

        ax.set_xlim(1, 100000)
        ax.set_ylim(-85, 25)
        ax.set_yticks([20, 0, -20, -40, -60, -80])
        ax.set_xlabel("Frequency (Hz)", fontsize=8)
        ax.set_ylabel("Magnitude (dB)", fontsize=8)
        ax.grid(True, which="both", linestyle=":", alpha=0.5)
        ax.legend(loc="upper right", fontsize=7.2, framealpha=0.9)

    elif circuit_type == "voltage_divider":
        r1 = params.get("R1", 10000.0)
        r2 = params.get("R2", 5000.0)
        vin = params.get("Vin", 10.0)
        vout_nom = vin * (r2 / (r1 + r2))
        vout_fault = vout_nom * 0.7 if is_faulty else vout_nom
        t = np.linspace(0, 0.002, 100)

        ax.plot(t * 1e3, np.full_like(t, vout_nom), color="#2563EB", lw=1.8, label=f"Expected Vout = {vout_nom:.2f}V")
        if is_faulty:
            ax.plot(t * 1e3, np.full_like(t, vout_fault), color="#DC2626", lw=1.5, ls="--", label="Uploaded Circuit (Drift / Fault)")
        ax.set_ylim(0, vin + 1)
        ax.set_xlabel("Time (ms)", fontsize=8)
        ax.set_ylabel("Voltage (V)", fontsize=8)
        ax.grid(True, linestyle=":", alpha=0.5)
        ax.legend(loc="upper right", fontsize=7.2)

    elif circuit_type == "rl_high_pass":
        f = np.logspace(0, 5, 300)
        r = params.get("R", 1000.0)
        l = params.get("L", 0.01)
        fc = r / (2.0 * np.pi * l)
        xl = 2 * np.pi * f * l
        h = (1j * xl) / (r + 1j * xl)
        mag_nom = 20 * np.log10(np.abs(h))
        mag_fault = np.full_like(f, -60.0) if is_faulty else mag_nom

        ax.semilogx(f, mag_nom, color="#2563EB", lw=1.8, label="Expected (RL High-Pass)")
        if is_faulty:
            ax.semilogx(f, mag_fault, color="#DC2626", lw=1.5, ls="--", label="Uploaded Faulty Circuit (Shorted)")
        ax.axvline(fc, color="#475569", linestyle=":", lw=1.0)
        ax.annotate(
            f"fc = {fc/1000:.1f} kHz",
            xy=(fc, -3.0),
            xytext=(fc * 0.15, -45),
            arrowprops=dict(arrowstyle="->", color="black", lw=1.0),
            fontsize=7.5,
            fontweight="bold",
            bbox=dict(boxstyle="square,pad=0.3", facecolor="white", edgecolor="#94A3B8", lw=0.8)
        )
        ax.set_xlim(1, 100000)
        ax.set_ylim(-85, 25)
        ax.set_yticks([20, 0, -20, -40, -60, -80])
        ax.set_xlabel("Frequency (Hz)", fontsize=8)
        ax.set_ylabel("Magnitude (dB)", fontsize=8)
        ax.grid(True, which="both", linestyle=":", alpha=0.5)
        ax.legend(loc="upper right", fontsize=7.2)

    else: # rlc_band_pass
        f = np.logspace(0, 5, 300)
        r = params.get("R", 1000.0)
        l = params.get("L", 0.01)
        c = params.get("C", 100e-9)
        f0 = 1.0 / (2.0 * np.pi * np.sqrt(l * c))
        w = 2 * np.pi * f
        z_tank = 1.0 / (1j * w * c + 1.0 / (1j * w * l + 1e-9))
        h = z_tank / (r + z_tank)
        mag_nom = 20 * np.log10(np.maximum(np.abs(h), 1e-4))
        mag_fault = mag_nom - 15.0 if is_faulty else mag_nom

        ax.semilogx(f, mag_nom, color="#2563EB", lw=1.8, label="Expected (RLC Band-Pass)")
        if is_faulty:
            ax.semilogx(f, mag_fault, color="#DC2626", lw=1.5, ls="--", label="Uploaded Faulty Circuit (Degraded)")
        ax.axvline(f0, color="#475569", linestyle=":", lw=1.0)
        ax.annotate(
            f"f0 = {f0/1000:.2f} kHz",
            xy=(f0, 0.0),
            xytext=(f0 * 2.0, -45),
            arrowprops=dict(arrowstyle="->", color="black", lw=1.0),
            fontsize=7.5,
            fontweight="bold",
            bbox=dict(boxstyle="square,pad=0.3", facecolor="white", edgecolor="#94A3B8", lw=0.8)
        )
        ax.set_xlim(1, 100000)
        ax.set_ylim(-85, 25)
        ax.set_yticks([20, 0, -20, -40, -60, -80])
        ax.set_xlabel("Frequency (Hz)", fontsize=8)
        ax.set_ylabel("Magnitude (dB)", fontsize=8)
        ax.grid(True, which="both", linestyle=":", alpha=0.5)
        ax.legend(loc="upper right", fontsize=7.2)

    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


