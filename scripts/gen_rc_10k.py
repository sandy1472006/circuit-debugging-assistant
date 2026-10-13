"""
Generates the RC test schematic with R = 10kΩ and C = 100nF (cutoff ≈ 159.15 Hz).
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

out_path = Path("data/sample_schematics/sample_rc_10k_100nf.png")
fig, ax = plt.subplots(figsize=(6, 4), dpi=300)
fig.patch.set_facecolor("white")
ax.set_facecolor("white")
ax.axis("off")

ax.text(0.5, 0.95, "RC Low-Pass Filter (R = 10kΩ, C = 100nF)", ha="center", va="top", fontsize=14, weight="bold", color="#0F172A")
ax.text(0.5, 0.88, "R = 10kΩ, C = 100nF, fc ≈ 159.15 Hz", ha="center", va="top", fontsize=10, color="#475569")

# Vin
ax.plot([0.15, 0.35], [0.7, 0.7], 'k-', lw=2)
ax.plot(0.15, 0.7, 'ko', ms=6)
ax.text(0.12, 0.7, "Vin", ha="right", va="center", fontsize=11, weight="bold")

# R series
ax.plot([0.35, 0.40, 0.43, 0.47, 0.50, 0.53, 0.57, 0.60, 0.65],
        [0.7, 0.7, 0.75, 0.65, 0.75, 0.65, 0.75, 0.7, 0.7], 'b-', lw=2.5)
ax.text(0.5, 0.78, "R1: 10kΩ", ha="center", fontsize=10, weight="bold", color="#1E40AF")

# Node Vout
ax.plot([0.65, 0.85], [0.7, 0.7], 'k-', lw=2)
ax.plot(0.70, 0.7, 'ko', ms=6)
ax.plot(0.85, 0.7, 'ko', ms=6)
ax.text(0.88, 0.7, "Vout", ha="left", va="center", fontsize=11, weight="bold")

# Branch down to C
ax.plot([0.70, 0.70], [0.7, 0.45], 'k-', lw=2)
ax.plot([0.62, 0.78], [0.45, 0.45], 'b-', lw=3)
ax.plot([0.62, 0.78], [0.38, 0.38], 'b-', lw=3)
ax.text(0.80, 0.42, "C1: 100nF", ha="left", fontsize=10, weight="bold", color="#1E40AF")

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
print(f"Generated {out_path}")
