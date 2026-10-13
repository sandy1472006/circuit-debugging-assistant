"""
generate_test_suite_images.py - Generates an extended test suite of schematic images
covering both nominal and fault/error conditions specified in Section 14:
1. Nominal Benchmark Schematics
2. Parameter Drift (RC with C = 120nF from paper Section V.A)
3. Missing Ground Error
4. Shorted Component Error
5. Dangling / Floating Wire Error
6. Noisy / Degraded Schematic (simulated phone photo / low contrast)
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.config import SAMPLE_DIR
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

def draw_rc_drift_120nf(out_path: Path):
    """Paper Section V.A Debugging Case: C = 120nF (+20% drift)."""
    fig, ax = plt.subplots(figsize=(6, 4), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.axis("off")

    ax.text(0.5, 0.95, "RC Low-Pass Filter (Drifted C)", ha="center", va="top", fontsize=14, weight="bold", color="#0F172A")
    ax.text(0.5, 0.88, "R = 1kΩ, C = 120nF (+20% Drift), fc ≈ 1.33 kHz", ha="center", va="top", fontsize=10, color="#DC2626")

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
    ax.plot(0.70, 0.7, 'ko', ms=6)
    ax.plot(0.85, 0.7, 'ko', ms=6)
    ax.text(0.88, 0.7, "Vout", ha="left", va="center", fontsize=11, weight="bold")

    # C branch with drifted label
    ax.plot([0.70, 0.70], [0.7, 0.45], 'k-', lw=2)
    ax.plot([0.62, 0.78], [0.45, 0.45], 'r-', lw=3)
    ax.plot([0.62, 0.78], [0.38, 0.38], 'r-', lw=3)
    ax.text(0.80, 0.42, "C: 120nF", ha="left", fontsize=10, weight="bold", color="#DC2626")

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


def draw_missing_ground(out_path: Path):
    """Voltage Divider with missing ground reference."""
    fig, ax = plt.subplots(figsize=(6, 4), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.axis("off")

    ax.text(0.5, 0.95, "Voltage Divider (Missing Ground Error)", ha="center", va="top", fontsize=14, weight="bold", color="#DC2626")
    ax.text(0.5, 0.88, "R1 = 10kΩ, R2 = 10kΩ, Lower rail left floating", ha="center", va="top", fontsize=10, color="#475569")

    # Vin
    ax.plot([0.15, 0.35], [0.7, 0.7], 'k-', lw=2)
    ax.plot(0.15, 0.7, 'ko', ms=6)
    ax.text(0.12, 0.7, "Vin", ha="right", va="center", fontsize=11, weight="bold")

    # R1
    ax.plot([0.35, 0.40, 0.43, 0.47, 0.50, 0.53, 0.57, 0.60, 0.65],
            [0.7, 0.7, 0.75, 0.65, 0.75, 0.65, 0.75, 0.7, 0.7], 'b-', lw=2.5)
    ax.text(0.5, 0.78, "R1: 10kΩ", ha="center", fontsize=10, weight="bold", color="#1E40AF")

    # Node Vout
    ax.plot([0.65, 0.85], [0.7, 0.7], 'k-', lw=2)
    ax.plot(0.70, 0.7, 'ko', ms=6)
    ax.plot(0.85, 0.7, 'ko', ms=6)
    ax.text(0.88, 0.7, "Vout", ha="left", va="center", fontsize=11, weight="bold")

    # R2
    ax.plot([0.70, 0.70], [0.7, 0.55], 'k-', lw=2)
    ax.plot([0.70, 0.70, 0.65, 0.75, 0.65, 0.75, 0.65, 0.70, 0.70],
            [0.55, 0.50, 0.47, 0.43, 0.40, 0.37, 0.33, 0.30, 0.25], 'b-', lw=2.5)
    ax.text(0.77, 0.40, "R2: 10kΩ", ha="left", fontsize=10, weight="bold", color="#1E40AF")

    # NO GROUND SYMBOL - Floating wire endpoint
    ax.plot([0.70, 0.70], [0.25, 0.18], 'k-', lw=2)
    ax.plot(0.70, 0.18, 'ro', ms=7) # Open red circle
    ax.text(0.70, 0.12, "NO GROUND (FLOATING NET)", ha="center", fontsize=10, weight="bold", color="#DC2626")

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    plt.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def draw_shorted_component(out_path: Path):
    """Voltage Divider with R1 shorted by an unintended bypass wire."""
    fig, ax = plt.subplots(figsize=(6, 4), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.axis("off")

    ax.text(0.5, 0.95, "Voltage Divider (Shorted Component Error)", ha="center", va="top", fontsize=14, weight="bold", color="#DC2626")
    ax.text(0.5, 0.88, "R1 bypassed by direct short wire (Vout = Vin)", ha="center", va="top", fontsize=10, color="#475569")

    # Vin
    ax.plot([0.15, 0.35], [0.65, 0.65], 'k-', lw=2)
    ax.plot(0.15, 0.65, 'ko', ms=6)
    ax.text(0.12, 0.65, "Vin", ha="right", va="center", fontsize=11, weight="bold")

    # R1
    ax.plot([0.35, 0.40, 0.43, 0.47, 0.50, 0.53, 0.57, 0.60, 0.65],
            [0.65, 0.65, 0.70, 0.60, 0.70, 0.60, 0.70, 0.65, 0.65], 'b-', lw=2.5)
    ax.text(0.5, 0.60, "R1: 10kΩ", ha="center", fontsize=10, weight="bold", color="#1E40AF")

    # Direct bypass short wire over R1 (Red line)
    ax.plot(0.30, 0.65, 'ro', ms=6)
    ax.plot([0.30, 0.30, 0.70, 0.70], [0.65, 0.82, 0.82, 0.65], 'r-', lw=2.5)
    ax.plot(0.70, 0.65, 'ro', ms=6)
    ax.text(0.50, 0.86, "DIRECT SHORT WIRE", ha="center", fontsize=10, weight="bold", color="#DC2626")

    # Node Vout
    ax.plot([0.65, 0.85], [0.65, 0.65], 'k-', lw=2)
    ax.plot(0.85, 0.65, 'ko', ms=6)
    ax.text(0.88, 0.65, "Vout", ha="left", va="center", fontsize=11, weight="bold")

    # R2
    ax.plot([0.70, 0.70], [0.65, 0.50], 'k-', lw=2)
    ax.plot([0.70, 0.70, 0.65, 0.75, 0.65, 0.75, 0.65, 0.70, 0.70],
            [0.50, 0.45, 0.42, 0.38, 0.35, 0.32, 0.28, 0.25, 0.20], 'b-', lw=2.5)
    ax.text(0.77, 0.35, "R2: 10kΩ", ha="left", fontsize=10, weight="bold", color="#1E40AF")

    # Ground
    ax.plot([0.70, 0.70], [0.20, 0.12], 'k-', lw=2)
    ax.plot([0.62, 0.78], [0.12, 0.12], 'k-', lw=2)
    ax.plot([0.65, 0.75], [0.09, 0.09], 'k-', lw=2)
    ax.plot([0.68, 0.72], [0.06, 0.06], 'k-', lw=2)
    ax.text(0.70, 0.01, "GND", ha="center", fontsize=10, color="#475569")

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    plt.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def draw_dangling_wire(out_path: Path):
    """RC filter with dangling open wire endpoint."""
    fig, ax = plt.subplots(figsize=(6, 4), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.axis("off")

    ax.text(0.5, 0.95, "RC Filter (Dangling Unconnected Wire)", ha="center", va="top", fontsize=14, weight="bold", color="#DC2626")
    ax.text(0.5, 0.88, "Dangling node / floating terminal detected", ha="center", va="top", fontsize=10, color="#475569")

    # Vin
    ax.plot([0.15, 0.35], [0.7, 0.7], 'k-', lw=2)
    ax.plot(0.15, 0.7, 'ko', ms=6)
    ax.text(0.12, 0.7, "Vin", ha="right", va="center", fontsize=11, weight="bold")

    # R series
    ax.plot([0.35, 0.40, 0.43, 0.47, 0.50, 0.53, 0.57, 0.60, 0.65],
            [0.7, 0.7, 0.75, 0.65, 0.75, 0.65, 0.75, 0.7, 0.7], 'b-', lw=2.5)
    ax.text(0.5, 0.78, "R: 1kΩ", ha="center", fontsize=10, weight="bold", color="#1E40AF")

    # Dangling wire branching off to nowhere
    ax.plot(0.50, 0.70, 'ro', ms=6)
    ax.plot([0.50, 0.50], [0.70, 0.88], 'r--', lw=2.5)
    ax.plot(0.50, 0.88, 'rx', ms=8, mew=2)
    ax.text(0.50, 0.91, "DANGLING WIRE ENDPOINT", ha="center", fontsize=9, weight="bold", color="#DC2626")

    # Node Vout
    ax.plot([0.65, 0.85], [0.7, 0.7], 'k-', lw=2)
    ax.plot(0.70, 0.7, 'ko', ms=6)
    ax.plot(0.85, 0.7, 'ko', ms=6)
    ax.text(0.88, 0.7, "Vout", ha="left", va="center", fontsize=11, weight="bold")

    # C branch
    ax.plot([0.70, 0.70], [0.7, 0.45], 'k-', lw=2)
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


if __name__ == "__main__":
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    draw_rc_drift_120nf(SAMPLE_DIR / "test_rc_drift_120nf.png")
    draw_missing_ground(SAMPLE_DIR / "test_missing_ground.png")
    draw_shorted_component(SAMPLE_DIR / "test_shorted_component.png")
    draw_dangling_wire(SAMPLE_DIR / "test_dangling_wire.png")
    print(f"Generated 4 additional test images in {SAMPLE_DIR}")
