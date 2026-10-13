"""
generate_synthetic_data.py - Generates clean reference schematic images for the 4 benchmark circuits
and saves them to data/sample_schematics/ for instant testing and demonstration.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.config import SAMPLE_DIR
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

def draw_voltage_divider(out_path: Path):
    fig, ax = plt.subplots(figsize=(6, 4), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.axis("off")

    # Title
    ax.text(0.5, 0.95, "Voltage Divider Schematic", ha="center", va="top", fontsize=14, weight="bold", color="#0F172A")
    ax.text(0.5, 0.88, "R1 = 10kΩ, R2 = 10kΩ, Vin = 10V", ha="center", va="top", fontsize=10, color="#475569")

    # Wires & components
    # Vin terminal
    ax.plot([0.15, 0.35], [0.7, 0.7], 'k-', lw=2)
    ax.plot(0.15, 0.7, 'ko', ms=6)
    ax.text(0.12, 0.7, "Vin\n(10V)", ha="right", va="center", fontsize=11, weight="bold")

    # R1 box/zigzag
    ax.plot([0.35, 0.40, 0.43, 0.47, 0.50, 0.53, 0.57, 0.60, 0.65],
            [0.7, 0.7, 0.75, 0.65, 0.75, 0.65, 0.75, 0.7, 0.7], 'b-', lw=2.5)
    ax.text(0.5, 0.78, "R1: 10kΩ", ha="center", fontsize=10, weight="bold", color="#1E40AF")

    # Middle node
    ax.plot([0.65, 0.85], [0.7, 0.7], 'k-', lw=2)
    ax.plot(0.70, 0.7, 'ko', ms=6) # Junction dot
    ax.plot(0.85, 0.7, 'ko', ms=6)
    ax.text(0.88, 0.7, "Vout", ha="left", va="center", fontsize=11, weight="bold")

    # Branch down to R2
    ax.plot([0.70, 0.70], [0.7, 0.55], 'k-', lw=2)
    ax.plot([0.70, 0.70, 0.65, 0.75, 0.65, 0.75, 0.65, 0.70, 0.70],
            [0.55, 0.50, 0.47, 0.43, 0.40, 0.37, 0.33, 0.30, 0.25], 'b-', lw=2.5)
    ax.text(0.77, 0.40, "R2: 10kΩ", ha="left", fontsize=10, weight="bold", color="#1E40AF")

    # Ground
    ax.plot([0.70, 0.70], [0.25, 0.15], 'k-', lw=2)
    ax.plot([0.62, 0.78], [0.15, 0.15], 'k-', lw=2)
    ax.plot([0.65, 0.75], [0.12, 0.12], 'k-', lw=2)
    ax.plot([0.68, 0.72], [0.09, 0.09], 'k-', lw=2)
    ax.text(0.70, 0.04, "GND", ha="center", fontsize=10, color="#475569")

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    plt.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def draw_rc_low_pass(out_path: Path):
    fig, ax = plt.subplots(figsize=(6, 4), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.axis("off")

    ax.text(0.5, 0.95, "RC Low-Pass Filter Schematic", ha="center", va="top", fontsize=14, weight="bold", color="#0F172A")
    ax.text(0.5, 0.88, "R = 1kΩ, C = 100nF, fc ≈ 1.59 kHz", ha="center", va="top", fontsize=10, color="#475569")

    # Vin
    ax.plot([0.15, 0.35], [0.7, 0.7], 'k-', lw=2)
    ax.plot(0.15, 0.7, 'ko', ms=6)
    ax.text(0.12, 0.7, "Vin", ha="right", va="center", fontsize=11, weight="bold")

    # R series
    ax.plot([0.35, 0.40, 0.43, 0.47, 0.50, 0.53, 0.57, 0.60, 0.65],
            [0.7, 0.7, 0.75, 0.65, 0.75, 0.65, 0.75, 0.7, 0.7], 'b-', lw=2.5)
    ax.text(0.5, 0.78, "R: 1kΩ", ha="center", fontsize=10, weight="bold", color="#1E40AF")

    # Node Vout
    ax.plot([0.65, 0.85], [0.7, 0.7], 'k-', lw=2)
    ax.plot(0.70, 0.7, 'ko', ms=6) # Junction dot
    ax.plot(0.85, 0.7, 'ko', ms=6)
    ax.text(0.88, 0.7, "Vout", ha="left", va="center", fontsize=11, weight="bold")

    # Branch down to C
    ax.plot([0.70, 0.70], [0.7, 0.45], 'k-', lw=2)
    # Capacitor plates
    ax.plot([0.62, 0.78], [0.45, 0.45], 'b-', lw=3)
    ax.plot([0.62, 0.78], [0.38, 0.38], 'b-', lw=3)
    ax.text(0.80, 0.42, "C: 100nF", ha="left", fontsize=10, weight="bold", color="#1E40AF")

    # Ground
    ax.plot([0.70, 0.70], [0.38, 0.20], 'k-', lw=2)
    ax.plot([0.62, 0.78], [0.20, 0.20], 'k-', lw=2)
    ax.plot([0.65, 0.75], [0.17, 0.17], 'k-', lw=2)
    ax.plot([0.68, 0.72], [0.14, 0.14], 'k-', lw=2)
    ax.text(0.70, 0.08, "GND", ha="center", fontsize=10, color="#475569")

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    plt.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def draw_rl_high_pass(out_path: Path):
    fig, ax = plt.subplots(figsize=(6, 4), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.axis("off")

    ax.text(0.5, 0.95, "RL High-Pass Filter Schematic", ha="center", va="top", fontsize=14, weight="bold", color="#0F172A")
    ax.text(0.5, 0.88, "R = 1kΩ, L = 100mH, fc ≈ 1.59 kHz", ha="center", va="top", fontsize=10, color="#475569")

    # Vin
    ax.plot([0.15, 0.35], [0.7, 0.7], 'k-', lw=2)
    ax.plot(0.15, 0.7, 'ko', ms=6)
    ax.text(0.12, 0.7, "Vin", ha="right", va="center", fontsize=11, weight="bold")

    # R series
    ax.plot([0.35, 0.40, 0.43, 0.47, 0.50, 0.53, 0.57, 0.60, 0.65],
            [0.7, 0.7, 0.75, 0.65, 0.75, 0.65, 0.75, 0.7, 0.7], 'b-', lw=2.5)
    ax.text(0.5, 0.78, "R: 1kΩ", ha="center", fontsize=10, weight="bold", color="#1E40AF")

    # Node Vout
    ax.plot([0.65, 0.85], [0.7, 0.7], 'k-', lw=2)
    ax.plot(0.70, 0.7, 'ko', ms=6) # Junction dot
    ax.plot(0.85, 0.7, 'ko', ms=6)
    ax.text(0.88, 0.7, "Vout", ha="left", va="center", fontsize=11, weight="bold")

    # Branch down to Inductor
    ax.plot([0.70, 0.70], [0.7, 0.55], 'k-', lw=2)
    # Inductor loops
    theta = np.linspace(0, 4*np.pi, 100)
    y_ind = np.linspace(0.55, 0.30, 100)
    x_ind = 0.70 + 0.04 * np.sin(theta)
    ax.plot(x_ind, y_ind, 'b-', lw=2.5)
    ax.text(0.77, 0.42, "L: 100mH", ha="left", fontsize=10, weight="bold", color="#1E40AF")

    # Ground
    ax.plot([0.70, 0.70], [0.30, 0.18], 'k-', lw=2)
    ax.plot([0.62, 0.78], [0.18, 0.18], 'k-', lw=2)
    ax.plot([0.65, 0.75], [0.15, 0.15], 'k-', lw=2)
    ax.plot([0.68, 0.72], [0.12, 0.12], 'k-', lw=2)
    ax.text(0.70, 0.06, "GND", ha="center", fontsize=10, color="#475569")

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    plt.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def draw_rlc_band_pass(out_path: Path):
    fig, ax = plt.subplots(figsize=(6, 4), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.axis("off")

    ax.text(0.5, 0.95, "RLC Band-Pass Filter Schematic", ha="center", va="top", fontsize=14, weight="bold", color="#0F172A")
    ax.text(0.5, 0.88, "R = 1kΩ, L = 10mH, C = 25.33nF, f0 ≈ 10 kHz", ha="center", va="top", fontsize=10, color="#475569")

    # Vin
    ax.plot([0.10, 0.25], [0.7, 0.7], 'k-', lw=2)
    ax.plot(0.10, 0.7, 'ko', ms=6)
    ax.text(0.08, 0.7, "Vin", ha="right", va="center", fontsize=11, weight="bold")

    # R series
    ax.plot([0.25, 0.30, 0.33, 0.37, 0.40, 0.43, 0.47, 0.50, 0.55],
            [0.7, 0.7, 0.75, 0.65, 0.75, 0.65, 0.75, 0.7, 0.7], 'b-', lw=2.5)
    ax.text(0.40, 0.78, "R: 1kΩ", ha="center", fontsize=10, weight="bold", color="#1E40AF")

    # Top bus to parallel L and C
    ax.plot([0.55, 0.88], [0.7, 0.7], 'k-', lw=2)
    ax.plot(0.62, 0.7, 'ko', ms=5)
    ax.plot(0.78, 0.7, 'ko', ms=5)
    ax.plot(0.88, 0.7, 'ko', ms=6)
    ax.text(0.90, 0.7, "Vout", ha="left", va="center", fontsize=11, weight="bold")

    # L Branch (left)
    ax.plot([0.62, 0.62], [0.7, 0.55], 'k-', lw=2)
    theta = np.linspace(0, 4*np.pi, 100)
    y_ind = np.linspace(0.55, 0.35, 100)
    x_ind = 0.62 + 0.03 * np.sin(theta)
    ax.plot(x_ind, y_ind, 'b-', lw=2.5)
    ax.plot([0.62, 0.62], [0.35, 0.22], 'k-', lw=2)
    ax.text(0.56, 0.45, "L: 10mH", ha="right", fontsize=9, weight="bold", color="#1E40AF")

    # C Branch (right)
    ax.plot([0.78, 0.78], [0.7, 0.48], 'k-', lw=2)
    ax.plot([0.72, 0.84], [0.48, 0.48], 'b-', lw=3)
    ax.plot([0.72, 0.84], [0.42, 0.42], 'b-', lw=3)
    ax.plot([0.78, 0.78], [0.42, 0.22], 'k-', lw=2)
    ax.text(0.86, 0.45, "C: 25.3nF", ha="left", fontsize=9, weight="bold", color="#1E40AF")

    # Bottom common bus
    ax.plot([0.62, 0.78], [0.22, 0.22], 'k-', lw=2)
    ax.plot(0.70, 0.22, 'ko', ms=5)

    # Ground
    ax.plot([0.70, 0.70], [0.22, 0.14], 'k-', lw=2)
    ax.plot([0.62, 0.78], [0.14, 0.14], 'k-', lw=2)
    ax.plot([0.65, 0.75], [0.11, 0.11], 'k-', lw=2)
    ax.plot([0.68, 0.72], [0.08, 0.08], 'k-', lw=2)
    ax.text(0.70, 0.03, "GND", ha="center", fontsize=10, color="#475569")

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    plt.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)

if __name__ == "__main__":
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    draw_voltage_divider(SAMPLE_DIR / "sample_voltage_divider.png")
    draw_rc_low_pass(SAMPLE_DIR / "sample_rc_low_pass.png")
    draw_rl_high_pass(SAMPLE_DIR / "sample_rl_high_pass.png")
    draw_rlc_band_pass(SAMPLE_DIR / "sample_rlc_band_pass.png")
    print(f"Generated 4 sample schematics in {SAMPLE_DIR}")
