# 🎓 Circuit Debugging Assistant (CDA) — Offline Demonstration Guide

This guide provides everything you need to successfully demonstrate this project to your professor or teacher in an **offline laboratory or classroom with zero internet connection**.

---

## ⚡ 1. Quick Start (Double-Click Execution)

1. Open your project folder:
   ```
   C:\Users\sande\.gemini\antigravity\scratch\circuit-debugging-assistant
   ```
2. **Double-click** the file:
   👉 **`run_offline.bat`**
3. It will automatically:
   - Verify Python.
   - Launch the local diagnostic engine on port 8000.
   - Open your web browser directly to **`http://localhost:8000`**.

> **Note:** The server is already currently running in the background. If you already have your browser open, simply go to [http://localhost:8000](http://localhost:8000).

---

## 🔌 2. Proof of 100% Offline Independence

You can turn off your laptop's Wi-Fi / enable Airplane Mode to prove to your teacher that the system does not depend on cloud APIs:
- **Numerical Solvers:** Pure local NumPy and SciPy frequency-domain calculation.
- **Computer Vision:** Local OpenCV bilateral filter and line tracing algorithms.
- **Plotly Graphs:** Localized Plotly engine (`/static/js/plotly-2.27.0.min.js`) stored on your machine.
- **Report Generation:** Local ReportLab PDF engine compiling print-ready A4 reports.
- **Database:** Local SQLite database (`data/circuit_debugger.db`).

---

## 📁 3. Ready-to-Use Demo Schematics

We have organized a dedicated folder for your presentation with clean test images ready to drag and drop:
📂 **`DEMO_SCHEMATICS_FOR_PRESENTATION/`**

| File | Scenario | What Happens |
| :--- | :--- | :--- |
| `01_RC_Low_Pass_Nominal_10k_100nF.png` | **Nominal Circuit** | Passes verification; $f_c = 159.15\text{ Hz}$, $0\text{ dB}$ passband. |
| `02_RC_Low_Pass_Faulty_Drift_120nF.png` | **Component Drift** | Residual solver detects capacitor shifted to $120\text{ nF}$ with shifted cutoff. |
| `03_RC_Low_Pass_Missing_Ground.png` | **Topological Error** | Flags missing circuit ground net with red status warning. |
| `04_Voltage_Divider.png` | **Resistive Divider** | Extracts $R_1, R_2$ and verifies attenuation factor. |
| `05_RL_High_Pass_Filter.png` | **Inductive Filter** | Computes inductive reactance and corner frequency. |
| `06_RLC_Band_Pass_Filter.png` | **Resonant Tank** | Solves second-order $LC$ resonance frequency $f_0$. |

---

## 🗣️ 4. Five-Minute Presentation Script for Your Teacher

Follow this structured presentation flow:

### ⏱️ Minute 1: The Problem & Dashboard Overview
- **Say:** *"Sir/Ma'am, traditional circuit debugging requires tedious multimeter probing. Our project, **Circuit Debugging Assistant**, is an automated, hybrid simulation- and evidence-driven fault localization system based on recent research."*
- **Action:** Show the **Circuit Analysis Workspace** dashboard with the restrained EDA aesthetic, status bar (*Mahajan et al., 2026*), and recent verified analyses.

### ⏱️ Minute 2: Schematic Upload & Interpretation
- **Say:** *"The user begins by uploading an image of a schematic diagram."*
- **Action:** Drag and drop `01_RC_Low_Pass_Nominal_10k_100nF.png` into the upload zone and click **Inspect Circuit**.
- **Point out:** The system automatically identifies the circuit topology as an **RC Low-Pass Filter**, extracts $R_1 = 10\text{ k}\Omega$ and $C_1 = 100\text{ nF}$, and constructs an editable netlist table.

### ⏱️ Minute 3: Simulation & Fault Localization
- **Say:** *"Next, we evaluate expected electrical behaviour against theoretical models using a residual scoring metric."*
- **Action:** Click **Confirm Circuit & Run Analysis**.
- **Point out:**
  - The live **Bode Plot** showing Magnitude (dB) and Phase (degrees).
  - The calculated $-3\text{ dB}$ cutoff frequency: $f_c = \frac{1}{2\pi RC} \approx 159.2\text{ Hz}$.
  - The normalized residual score indicating physical agreement.

### ⏱️ Minute 4: Demonstrating Fault Diagnosis
- **Say:** *"When a student or engineer uploads an incorrect or drifting circuit..."*
- **Action:** Upload `02_RC_Low_Pass_Faulty_Drift_120nF.png`.
- **Point out:** The engine detects a frequency deviation, flags candidate hypothesis `C Drift +20%`, and displays the uploaded schematic side-by-side with the canonical reference circuit.

### ⏱️ Minute 5: Technical Assistant & PDF Report Generation
- **Say:** *"To ensure students understand the physics without generic chatbot hallucinations, we have a deterministic Technical Assistant and formal technical reporting."*
- **Action 1:** Click the **Technical Assistant** button (bottom right) and click *"Why this classification?"* or *"Recommended bench test"*. Show the exact mathematical explanation.
- **Action 2:** Click **Download PDF Report**. Show the 2-page publication-grade diagnostic report containing side-by-side schematics, Bode plots, equations, and bench test recommendations.

---

## 📱 5. Optional: Showing it on Your Teacher's Phone / Tablet

If your teacher wants to test it on their own mobile phone or tablet without touching your laptop:
1. Turn on your laptop's **Mobile Hotspot** or connect both devices to the same college Wi-Fi.
2. Open PowerShell and run:
   ```powershell
   ipconfig
   ```
   Look for your **IPv4 Address** (e.g. `192.168.1.105` or `192.168.137.1`).
3. Tell your teacher to open Chrome / Safari on their phone and go to:
   ```
   http://<YOUR-IP>:8000
   ```
   *(Example: `http://192.168.1.105:8000`)*
4. Because the server is listening on `0.0.0.0:8000`, the full application will load on their phone instantly.
