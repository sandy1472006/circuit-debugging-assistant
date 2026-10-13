# Circuit Debugging Assistant

**A Hybrid Simulation- and Evidence-Driven Framework for Electronic Circuit Fault Localization**  
*Based on the research paper by Sandesh Mahajan, Snehal Khalkar, Sabiya Pathan (Department of Electronics and Telecommunication Engineering, K. K. Wagh Institute of Engineering Education and Research, Nashik, India, 2026).*

---

## 1. Architectural Overview

The **Circuit Debugging Assistant** bridges classical analog fault dictionaries with AI-assisted EDA workflows:

1. **Deterministic Diagnostic Core**: Circuit equations, multi-domain simulation, and normalized residual scoring remain the authoritative source of truth. The LLM is never the source of electrical truth.
2. **Multi-Evidence Fusion**: Transfer functions alone cannot separate ambiguous parameter shifts (e.g. $+20\%$ on $R$ vs $+20\%$ on $C$ produce identical cutoff shifts in $RC$ filters). By fusing an independent observable (initial step current or DC branch current), Top-1 accuracy jumps from **$79.89\%$** to **$98.43\%$** under $5\%$ Gaussian measurement noise.
3. **Adaptive Test Selection ($U(t)$)**: Dynamically recommends the next bench measurement yielding maximum Shannon entropy reduction per unit test cost.
4. **4-Panel Circuit Verification**: Side-by-side inspection of Original Upload, Reconstructed Graph, Target Reference, and Proposed Corrected Circuit.
5. **Publication-Grade Report Generation**: Automated 24-section PDF report with embedded Bode diagrams, step responses, residual rankings, and reproducibility appendices.

---

## 2. Directory Structure

```text
circuit-debugging-assistant/
├── README.md
├── requirements.txt
├── app/
│   ├── main.py                  # FastAPI application entry point
│   ├── config.py                # Environment & directory configurations
│   ├── api/
│   │   ├── analysis.py          # Upload, Stage A->B->C analysis pipeline
│   │   ├── simulation.py        # Numerical simulation endpoints
│   │   ├── reports.py           # PDF, SPICE (.cir), and CSV downloads
│   │   ├── benchmarks.py        # Live 28,800 test case benchmark runner
│   │   ├── assistant.py         # Grounded conversational explanation assistant
│   │   └── history.py           # SQLite session management
│   ├── core/
│   │   ├── circuit_models.py    # Analytical solvers (Voltage Divider, RC, RL, RLC)
│   │   ├── fault_engine.py      # Residual calculation, dictionary, and U(t)
│   │   ├── netlist_parser.py    # Graph G=(V,E), SPICE exporter, 4-category validation
│   │   ├── reference_generator.py # Reference & Corrected circuit generator with SVG
│   │   └── database.py          # SQLite persistence
│   ├── vision/
│   │   ├── preprocessor.py      # Bilateral filtering, Otsu binarization, deskew
│   │   ├── symbol_detector.py   # Geometric & morphological contour symbol classifier
│   │   ├── wire_tracer.py       # Wire skeletonization & junction dot detection
│   │   ├── ocr_engine.py        # Engineering value & unit regex parser (10k, 100nF, etc.)
│   │   ├── reconstructor.py     # Graph synthesizer & archetype classifier
│   │   └── inference.py         # High-level vision orchestrator
│   ├── reports/
│   │   ├── pdf_generator.py     # ReportLab 24-section scientific PDF generator
│   │   └── plot_generator.py    # High-resolution Matplotlib scientific plot generator
│   └── static/
│       ├── css/style.css        # Restrained technical EDA design system
│       ├── js/app.js            # SPA controller & stage manager
│       ├── js/plots.js          # Plotly.js scientific plotting integration
│       └── index.html           # Full desktop-first EDA workbench interface
├── notebooks/
│   └── train_circuit_vision_model.ipynb # Google Colab YOLOv8 training pipeline
├── scripts/
│   ├── run_benchmark.py         # Independent runner for 28,800 instances
│   ├── generate_synthetic_data.py # Reference schematic generator
│   └── test_pipeline.py         # End-to-end integration test
└── tests/
    ├── test_circuits.py         # Analytical model unit tests
    ├── test_fault_engine.py     # Residual scoring & U(t) unit tests
    ├── test_netlist_parser.py   # Graph & topology validation unit tests
    ├── test_pdf_report.py       # PDF generator unit tests
    └── test_vision_pipeline.py  # Computer vision extraction unit tests
```

---

## 3. Mathematical Core

### Normalized Residual Metric
For feature $k$ and candidate fault $f$:
$$e_k(f) = \frac{|x_k - y_k(f)|}{s_k + \epsilon}$$
where $x_k$ is the observed measurement, $y_k(f)$ is the predicted response, $s_k$ is the nominal feature scale, and $\epsilon = 10^{-6}$.

### Aggregate Residual Score
$$S(f) = \sum_{k=1}^K w_k e_k(f)$$
Candidates are ranked in ascending order of $S(f)$ (lower indicates closer physical agreement).

### Adaptive Value-of-Information Metric
$$U(t) = \frac{H(F) - \mathbb{E}[H(F \mid X_t)]}{C(t)}$$
where $H(F)$ is the Shannon entropy over the candidate fault distribution, and $C(t)$ is the physical bench measurement cost.

---

## 4. Running the Application

### 1. Installation
Ensure Python 3.10+ is installed:
```powershell
pip install -r requirements.txt
```

### 2. Generate Reference Schematics
```powershell
python scripts/generate_synthetic_data.py
```

### 3. Run Automated Tests
```powershell
python -m pytest tests -v
```

### 4. Run End-to-End Integration Verification
```powershell
python scripts/test_pipeline.py
```

### 5. Launch the Web Workbench
```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Open your browser and navigate to:
**`http://127.0.0.1:8000`**

---

## 5. Replicating the 28,800 Test-Case Benchmark

To reproduce Tables III and IV from the research paper across the 4 archetypes (36 fault signatures) with 200 noisy trials per fault:
```powershell
python scripts/run_benchmark.py 200
```
This runs 28,800 noisy evaluations with $0\%, 1\%, 3\%, 5\%$ relative Gaussian noise and outputs the exact accuracy progression.

---

## 6. Vision Model Training (Google Colab)

To fine-tune YOLO on schematic symbols:
1. Open `notebooks/train_circuit_vision_model.ipynb` in Google Colab.
2. Follow steps 1 through 6 to train and export `best.pt`.
3. Place exported weights into `app/vision/weights/best.pt`.
