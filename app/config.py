import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
SESSION_DIR = DATA_DIR / "sessions"
REPORT_DIR = DATA_DIR / "reports"
DATASET_DIR = DATA_DIR / "datasets"
SAMPLE_DIR = DATA_DIR / "sample_schematics"
REFERENCE_DIR = DATA_DIR / "reference_circuits"
DATABASE_PATH = DATA_DIR / "circuit_assistant.db"

# Create directories if not exist
for directory in [UPLOAD_DIR, SESSION_DIR, REPORT_DIR, DATASET_DIR, SAMPLE_DIR, REFERENCE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

APP_NAME = "Circuit Debugging Assistant"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "A Hybrid Simulation- and Evidence-Driven Framework for Electronic Circuit Fault Localization"

# File upload limits
MAX_UPLOAD_SIZE_MB = 20
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf"}

# Benchmark Circuits
SUPPORTED_CIRCUITS = [
    "voltage_divider",
    "rc_low_pass",
    "rl_high_pass",
    "rlc_band_pass"
]

# Fault classes from research paper:
# -20%, +20%, open, short
FAULT_TYPES = ["-20%", "+20%", "open", "short"]
NOISE_LEVELS = [0.0, 0.01, 0.03, 0.05]
DEFAULT_TRIALS_PER_FAULT = 200
