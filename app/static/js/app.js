/**
 * app.js - Redesigned frontend controller for Circuit Debugging Assistant.
 * Simple, professional engineering workflow:
 * 1. Upload & Inspect -> 2. Analyze -> 3. Review Side-by-Side & 1-2 Page Diagnostic Report.
 */

const AppState = {
  selectedFile: null,
  currentSessionId: null,
  currentCircuitType: 'rc_low_pass',
  currentParameters: {},
  currentAnalysisData: null,
  uploadedImageUrl: null,
  zoomLevels: { 'left-img': 1.0, 'right-img': 1.0 }
};

document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initDashboardUpload();
  initStage1Upload();
  loadDashboardRecent();
  initCircuitLibrary();
});

// SPA Navigation
function initNavigation() {
  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = item.getAttribute('data-target');
      showView(targetId);
      navItems.forEach(n => n.classList.remove('active'));
      item.classList.add('active');
    });
  });
}

function showView(viewId) {
  document.querySelectorAll('.view-section').forEach(sec => sec.classList.remove('active'));
  const target = document.getElementById(viewId);
  if (target) target.classList.add('active');

  if (viewId === 'view-reports') loadReportsHistory();
  if (viewId === 'view-dashboard') loadDashboardRecent();
}

function startNewAnalysis() {
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const navAnalysis = document.querySelector('.nav-item[data-target="view-analysis"]');
  if (navAnalysis) navAnalysis.classList.add('active');
  showView('view-analysis');
  goToStage(1);
}

function goToStage(stageNum) {
  [1, 2, 3].forEach(s => {
    const tab = document.getElementById(`step-tab-${s}`);
    const cont = document.getElementById(`stage-${s}-container`);
    if (tab) tab.classList.toggle('active', s === stageNum);
    if (cont) cont.style.display = s === stageNum ? 'block' : 'none';
  });
}

// =========================================================================
// DASHBOARD HERO UPLOAD
// =========================================================================
function initDashboardUpload() {
  const dropzone = document.getElementById('dashboard-dropzone');
  const fileInput = document.getElementById('dashboard-file-input');

  if (!dropzone || !fileInput) return;

  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
  });

  dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));

  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
      handleSelectedFile(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
      handleSelectedFile(fileInput.files[0]);
    }
  });
}

function handleSelectedFile(file) {
  AppState.selectedFile = file;
  const bar = document.getElementById('dash-preview-bar');
  const nameEl = document.getElementById('dash-preview-filename');
  const sizeEl = document.getElementById('dash-preview-filesize');

  if (bar && nameEl && sizeEl) {
    nameEl.innerText = file.name;
    sizeEl.innerText = `(${(file.size / 1024).toFixed(1)} KB)`;
    bar.style.display = 'flex';
  }
}

function clearSelectedFile() {
  AppState.selectedFile = null;
  const bar = document.getElementById('dash-preview-bar');
  if (bar) bar.style.display = 'none';
  const input = document.getElementById('dashboard-file-input');
  if (input) input.value = '';
}

function proceedFromDashboardUpload() {
  if (!AppState.selectedFile) return;
  startNewAnalysis();
  uploadAndInspectFile(AppState.selectedFile);
}

// =========================================================================
// STAGE 1: UPLOAD & INSPECT
// =========================================================================
function initStage1Upload() {
  const fileInput = document.getElementById('stage1-file-input');
  if (fileInput) {
    fileInput.addEventListener('change', () => {
      if (fileInput.files.length > 0) {
        uploadAndInspectFile(fileInput.files[0]);
      }
    });
  }

  const typeSelect = document.getElementById('stage1-circuit-type');
  if (typeSelect) {
    typeSelect.addEventListener('change', (e) => {
      AppState.currentCircuitType = e.target.value;
      if (AppState.currentCircuitType === 'voltage_divider') {
        AppState.currentParameters = { Vin: 10.0, R1: 10000.0, R2: 5000.0 };
      } else if (AppState.currentCircuitType === 'rc_low_pass') {
        AppState.currentParameters = { Vin: 5.0, R: 10000.0, C: 100e-9 };
      } else if (AppState.currentCircuitType === 'rl_high_pass') {
        AppState.currentParameters = { Vin: 5.0, R: 1000.0, L: 0.01 };
      } else if (AppState.currentCircuitType === 'rlc_band_pass') {
        AppState.currentParameters = { Vin: 1.0, R: 1000.0, L: 0.01, C: 100e-9 };
      }
      rebuildStage1ComponentTable();
    });
  }
}

async function uploadAndInspectFile(file) {
  AppState.selectedFile = file;
  const viewport = document.getElementById('stage1-image-viewport');
  if (viewport) {
    viewport.innerHTML = `<span style="color:var(--text-secondary);">Analyzing schematic image...</span>`;
  }

  const formData = new FormData();
  formData.append('file', file);
  // Do NOT send forced hint on fresh upload; let server ORB & contour model detect the circuit archetype

  try {
    const res = await fetch('/api/analysis/upload', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Upload failed');
    }

    const data = await res.json();
    AppState.currentSessionId = data.session_id;
    AppState.currentCircuitType = data.circuit_type;
    AppState.currentParameters = data.extracted_parameters;
    AppState.uploadedImageUrl = data.image_url;

    // Update Stage 1 Viewport
    if (viewport) {
      viewport.innerHTML = `<img src="${data.image_url}" style="max-width:100%; max-height:270px; object-fit:contain;" alt="Uploaded Schematic" />`;
    }

    // Set dropdown to detected type
    const typeSelect = document.getElementById('stage1-circuit-type');
    if (typeSelect) typeSelect.value = data.circuit_type;

    // Build Component Table
    rebuildStage1ComponentTable();
  } catch (error) {
    if (viewport) {
      viewport.innerHTML = `<span style="color:var(--danger);">Error: ${error.message}</span>`;
    }
  }
}

function rebuildStage1ComponentTable() {
  const tbody = document.getElementById('stage1-components-tbody');
  if (!tbody) return;
  tbody.innerHTML = '';

  const ctype = AppState.currentCircuitType;
  let defaultComps = [];

  if (ctype === 'rc_low_pass') {
    defaultComps = [
      { ref: 'R1', type: 'Resistor', val: AppState.currentParameters.R || 10000.0, unit: 'Ω', param: 'R' },
      { ref: 'C1', type: 'Capacitor', val: AppState.currentParameters.C || 100e-9, unit: 'F', param: 'C' }
    ];
  } else if (ctype === 'rl_high_pass') {
    defaultComps = [
      { ref: 'R1', type: 'Resistor', val: AppState.currentParameters.R || 1000.0, unit: 'Ω', param: 'R' },
      { ref: 'L1', type: 'Inductor', val: AppState.currentParameters.L || 0.01, unit: 'H', param: 'L' }
    ];
  } else if (ctype === 'rlc_band_pass') {
    defaultComps = [
      { ref: 'R1', type: 'Resistor', val: AppState.currentParameters.R || 1000.0, unit: 'Ω', param: 'R' },
      { ref: 'L1', type: 'Inductor', val: AppState.currentParameters.L || 0.01, unit: 'H', param: 'L' },
      { ref: 'C1', type: 'Capacitor', val: AppState.currentParameters.C || 100e-9, unit: 'F', param: 'C' }
    ];
  } else { // Voltage divider
    defaultComps = [
      { ref: 'R1', type: 'Resistor', val: AppState.currentParameters.R1 || 10000.0, unit: 'Ω', param: 'R1' },
      { ref: 'R2', type: 'Resistor', val: AppState.currentParameters.R2 || 5000.0, unit: 'Ω', param: 'R2' }
    ];
  }

  defaultComps.forEach(c => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${c.ref}</strong></td>
      <td>${c.type}</td>
      <td>
        <input type="number" step="any" class="stage1-param-input" data-param="${c.param}" value="${c.val}" 
               style="width: 120px; padding: 4px; border: 1px solid #CBD5E1; border-radius: 4px; font-size:12px;" />
        <span style="font-size:11px; color:#64748B; margin-left:4px;">${c.unit}</span>
      </td>
      <td><span class="badge badge-passed">Extracted</span></td>
    `;
    tbody.appendChild(tr);
  });
}

function confirmCircuitAndProceed() {
  const typeSelect = document.getElementById('stage1-circuit-type');
  if (typeSelect) {
    AppState.currentCircuitType = typeSelect.value;
  }
  // Read confirmed values from inputs
  const confirmed = {};
  document.querySelectorAll('.stage1-param-input').forEach(input => {
    const p = input.getAttribute('data-param');
    confirmed[p] = parseFloat(input.value);
  });
  AppState.currentParameters = confirmed;
  goToStage(2);
}

// =========================================================================
// STAGE 2: ANALYZE THE CIRCUIT
// =========================================================================
async function executeCircuitAnalysis() {
  const btn = document.getElementById('btn-run-analysis');
  const progBox = document.getElementById('analysis-progress-box');
  const progBar = document.getElementById('analysis-progress-bar');
  const progLabel = document.getElementById('progress-status-label');

  btn.disabled = true;
  progBox.style.display = 'block';

  // Simulated smooth progression while server runs deterministic numerical core
  progBar.style.width = '30%';
  progLabel.innerText = 'Validating electrical network topology...';

  setTimeout(() => {
    progBar.style.width = '70%';
    progLabel.innerText = 'Evaluating transfer response & multi-domain observables...';
  }, 150);

  try {
    const res = await fetch('/api/analysis/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: AppState.currentSessionId,
        circuit_type: AppState.currentCircuitType,
        parameters: AppState.currentParameters,
        use_multi_evidence: true
      })
    });

    if (!res.ok) throw new Error('Analysis execution failed');
    const data = await res.json();
    AppState.currentAnalysisData = data;

    progBar.style.width = '100%';
    progLabel.innerText = 'Analysis complete.';

    setTimeout(() => {
      progBox.style.display = 'none';
      btn.disabled = false;
      renderStage3(data);
      goToStage(3);
    }, 250);

  } catch (error) {
    progBox.style.display = 'none';
    btn.disabled = false;
    alert(`Analysis error: ${error.message}`);
  }
}

// =========================================================================
// STAGE 3: REVIEW RESULTS & SIDE-BY-SIDE COMPARISON
// =========================================================================
function renderStage3(data) {
  const diag = data.diagnosis;
  const top = diag.top_candidate;
  const findings = data.findings || [];
  const isFaulty = top && top.component !== 'None';
  const hasCritical = findings.some(f => f.severity === 'Critical');

  // 1. Summary Banner (Compact and clear)
  const summaryBanner = document.getElementById('stage3-summary-banner');
  let statusBadge = '<span class="badge badge-passed">NO ISSUES DETECTED</span>';
  let summaryText = 'All verified checks passed. Circuit conforms to expected nominal specifications.';

  if (hasCritical || (isFaulty && top.mode.includes('short'))) {
    statusBadge = '<span class="badge badge-error">CRITICAL FLAW DETECTED</span>';
    summaryText = `Identified confirmed issue: ${top.label} (Normalized residual: ${top.residual_score.toFixed(3)}).`;
  } else if (isFaulty || findings.length > 0) {
    statusBadge = '<span class="badge badge-warning">POTENTIAL ISSUE IDENTIFIED</span>';
    summaryText = `Observed parameter shift consistent with ${top ? top.label : 'anomaly'}.`;
  }

  summaryBanner.innerHTML = `
    <div style="display:flex; align-items:center; gap:8px;">
      ${statusBadge}
      <strong style="color:var(--text-main); font-size:13px;">${summaryText}</strong>
    </div>
  `;

  // 2. Left Panel: Uploaded Circuit
  const leftPanel = document.getElementById('stage3-left-panel');
  if (AppState.uploadedImageUrl) {
    leftPanel.innerHTML = `<img id="left-img" src="${AppState.uploadedImageUrl}" alt="Uploaded Circuit" />`;
  } else {
    leftPanel.innerHTML = data.panels.reconstructed_svg;
  }

  // 3. Right Panel: Expected Reference Circuit (User's Canonical Reference)
  const rightPanel = document.getElementById('stage3-right-panel');
  const rightTitle = document.getElementById('right-panel-title');
  rightTitle.innerText = 'Expected Reference Circuit';
  if (data.panels.reference_image_url) {
    rightPanel.innerHTML = `<img id="right-img" src="${data.panels.reference_image_url}" alt="Expected Reference Circuit" style="max-width:100%; max-height:260px; object-fit:contain;" />`;
  } else if (isFaulty && data.panels.corrected_svg) {
    rightPanel.innerHTML = data.panels.corrected_svg;
  } else {
    rightPanel.innerHTML = data.panels.reference_svg;
  }

  // 4. Proposed Modifications Diff Table
  const diffCard = document.getElementById('correction-diff-card');
  const diffTbody = document.getElementById('correction-diff-tbody');
  const corr = data.panels.corrected_info;

  if (corr && corr.changes && corr.changes.length > 0) {
    diffCard.style.display = 'block';
    diffTbody.innerHTML = '';
    corr.changes.forEach(ch => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>${ch.component}</strong></td>
        <td style="color:var(--danger);">${ch.original_value}</td>
        <td style="color:var(--success); font-weight:600;">${ch.corrected_value}</td>
        <td>${ch.rationale}</td>
        <td style="text-align:right;">
          <button class="btn btn-secondary btn-sm" onclick="acceptCorrection('${ch.component}', ${ch.corrected_value})">Apply Correction</button>
        </td>
      `;
      diffTbody.appendChild(tr);
    });
  } else {
    diffCard.style.display = 'none';
  }

  // 5. Compact Flaws Table (Part 4)
  const flawsTbody = document.getElementById('stage3-flaws-tbody');
  flawsTbody.innerHTML = '';

  const allFindings = [...findings];
  if (isFaulty) {
    allFindings.push({
      status_label: 'Potential issue',
      badge_class: 'badge-warning',
      finding: `Frequency response deviation matches ${top.label} signature`,
      location: top.component,
      action: `Verify ${top.component} with an LCR meter or replace with nominal value.`
    });
  }

  if (allFindings.length === 0) {
    flawsTbody.innerHTML = `
      <tr>
        <td><span class="badge badge-passed">Passed</span></td>
        <td>All topological and electrical checks passed.</td>
        <td>All Components</td>
        <td>Ready for laboratory bench testing.</td>
      </tr>
    `;
  } else {
    allFindings.forEach(f => {
      const sev = f.severity || 'Warning';
      const bClass = sev === 'Critical' ? 'badge-error' : (sev === 'Major' ? 'badge-warning' : 'badge-passed');
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><span class="badge ${bClass}">${sev}</span></td>
        <td>${f.finding || f.evidence || f.observed_behavior}</td>
        <td><code>${f.location || f.component_or_net}</code></td>
        <td><em>${f.action || f.recommended_correction}</em></td>
      `;
      flawsTbody.appendChild(tr);
    });
  }

  // 6. Detailed Analysis Content (Clean Text Equations & Plots)
  renderDetailedAnalysis(data);
}

function renderDetailedAnalysis(data) {
  const eqBox = document.getElementById('detailed-equations-box');
  const ctype = data.circuit_type;
  const p = data.diagnosis.top_candidate ? data.diagnosis.top_candidate.params : AppState.currentParameters;

  let eqHtml = '';
  if (ctype === 'rc_low_pass') {
    const r = p.R || 1000.0;
    const c = p.C || 100e-9;
    const fc = 1.0 / (2.0 * Math.PI * r * c);
    const iStep = (p.Vin || 1.0) / r;
    eqHtml = `
      <div><strong>Cutoff Frequency Formula:</strong> fc = 1 / (2π · R · C)</div>
      <div><strong>Calculated Cutoff:</strong> 1 / (2π · ${r}Ω · ${(c*1e9).toFixed(1)}nF) = <strong>${fc.toFixed(2)} Hz</strong></div>
      <div><strong>Initial Step Current (Independent Observable):</strong> I_step(0+) = Vin / R = <strong>${(iStep*1e3).toFixed(2)} mA</strong></div>
    `;
  } else if (ctype === 'rl_high_pass') {
    const r = p.R || 1000.0;
    const l = p.L || 0.1;
    const fc = r / (2.0 * Math.PI * l);
    eqHtml = `
      <div><strong>Cutoff Frequency Formula:</strong> fc = R / (2π · L)</div>
      <div><strong>Calculated Cutoff:</strong> ${r}Ω / (2π · ${(l*1e3).toFixed(1)}mH) = <strong>${fc.toFixed(2)} Hz</strong></div>
    `;
  } else if (ctype === 'rlc_band_pass') {
    const r = p.R || 1000.0;
    const l = p.L || 0.01;
    const c = p.C || 25.33e-9;
    const f0 = 1.0 / (2.0 * Math.PI * Math.sqrt(l * c));
    eqHtml = `
      <div><strong>Resonant Frequency Formula:</strong> f0 = 1 / (2π · √(L · C))</div>
      <div><strong>Calculated Resonance:</strong> <strong>${f0.toFixed(2)} Hz</strong></div>
    `;
  } else {
    const r1 = p.R1 || 10000.0;
    const r2 = p.R2 || 10000.0;
    const vin = p.Vin || 10.0;
    const vout = vin * (r2 / (r1 + r2));
    eqHtml = `
      <div><strong>Divider Ratio Formula:</strong> Vout = Vin · [R2 / (R1 + R2)]</div>
      <div><strong>Calculated Output Voltage:</strong> ${vin}V · [${r2} / (${r1} + ${r2})] = <strong>${vout.toFixed(2)} V</strong></div>
    `;
  }
  eqBox.innerHTML = eqHtml;

  // Render plots into detailed drawer
  if (ctype !== 'voltage_divider') {
    document.getElementById('det-bode-box').style.display = 'block';
    CircuitPlots.renderBodePlot('det-plot-bode', data.simulation);
  } else {
    document.getElementById('det-bode-box').style.display = 'none';
  }
  CircuitPlots.renderStepPlot('det-plot-step', data.simulation);
}

function toggleDetailedAnalysis() {
  const drawer = document.getElementById('detailed-analysis-drawer');
  const btn = document.getElementById('btn-toggle-details');
  if (drawer.classList.contains('open')) {
    drawer.classList.remove('open');
    btn.innerText = 'View Detailed Analysis';
  } else {
    drawer.classList.add('open');
    btn.innerText = 'Hide Detailed Analysis';
  }
}

function acceptCorrection(component, correctedVal) {
  AppState.currentParameters[component] = correctedVal;
  alert(`Applied nominal correction for ${component} (${correctedVal}). Re-running analysis...`);
  executeCircuitAnalysis();
}

function downloadDiagnosticPDF() {
  if (!AppState.currentSessionId) return;
  window.open(`/api/reports/${AppState.currentSessionId}/pdf?t=${Date.now()}`, '_blank');
}

function exportSPICEFile() {
  if (!AppState.currentSessionId) return;
  window.location.href = `/api/reports/${AppState.currentSessionId}/spice`;
}

function downloadCSVData() {
  if (!AppState.currentSessionId) return;
  window.location.href = `/api/reports/${AppState.currentSessionId}/csv`;
}

function downloadOriginalUploaded() {
  if (AppState.uploadedImageUrl) {
    const a = document.createElement('a');
    a.href = AppState.uploadedImageUrl;
    a.download = `uploaded_${AppState.currentSessionId}.png`;
    a.click();
  }
}

function exportSchematicSVG() {
  if (AppState.currentAnalysisData && AppState.currentAnalysisData.panels) {
    const svgStr = AppState.currentAnalysisData.panels.reference_svg;
    const blob = new Blob([svgStr], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `reference_${AppState.currentSessionId}.svg`;
    a.click();
  }
}

// Zoom / Pan helpers for side-by-side comparison
function zoomImage(targetId, factor) {
  AppState.zoomLevels[targetId] = (AppState.zoomLevels[targetId] || 1.0) * factor;
  const el = document.getElementById(targetId);
  if (el) el.style.transform = `scale(${AppState.zoomLevels[targetId]})`;
}

function resetZoom(targetId) {
  AppState.zoomLevels[targetId] = 1.0;
  const el = document.getElementById(targetId);
  if (el) el.style.transform = 'scale(1.0)';
}

// =========================================================================
// RECENT ANALYSES & LIBRARY
// =========================================================================

const CIRCUIT_META = {
  rc_low_pass: { title: "RC Low-Pass Filter", sub: "First-order passive", refImg: "/references/ref_rc_low_pass.png" },
  voltage_divider: { title: "Voltage Divider", sub: "Resistive attenuator", refImg: "/references/ref_voltage_divider.png" },
  rl_high_pass: { title: "RL High-Pass Filter", sub: "First-order inductive", refImg: "/references/ref_rl_high_pass.png" },
  rlc_band_pass: { title: "RLC Band-Pass Filter", sub: "Second-order resonant", refImg: "/references/ref_rlc_band_pass.png" }
};

function getStatusBadge(status) {
  const s = (status || 'Completed').trim();
  if (s === 'Completed') {
    return `<span class="pill-badge pill-completed"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg> Completed</span>`;
  } else if (s === 'Needs Review') {
    return `<span class="pill-badge pill-review"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg> Needs Review</span>`;
  } else {
    return `<span class="pill-badge pill-failed"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg> Analysis Failed</span>`;
  }
}

async function loadDashboardRecent() {
  const tbody = document.getElementById('recent-analyses-tbody');
  if (!tbody) return;
  tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; color:#64748B; padding:20px;">Loading circuit analyses...</td></tr>';

  try {
    const res = await fetch('/api/history/');
    const list = await res.json();
    tbody.innerHTML = '';

    if (!list || list.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="8" style="text-align:center; padding:32px; color:#64748B;">
            No analyses performed yet.
            <button class="btn btn-primary btn-sm" style="margin-left:12px;" onclick="startNewAnalysis()">Start First Analysis</button>
          </td>
        </tr>
      `;
      return;
    }

    list.slice(0, 8).forEach((item, index) => {
      const ctype = item.circuit_type || 'rc_low_pass';
      const meta = CIRCUIT_META[ctype] || {
        title: (ctype).replace(/_/g, ' ').toUpperCase(),
        sub: "Electronic Circuit",
        refImg: "/references/ref_rc_low_pass.png"
      };

      const dateObj = new Date(item.created_at * 1000);
      const dateFormatted = dateObj.toLocaleDateString('en-GB', {
        day: '2-digit', month: 'short', year: 'numeric'
      }) + ', ' + dateObj.toLocaleTimeString('en-GB', {
        hour: '2-digit', minute: '2-digit'
      });

      const filename = item.upload_filename || `${ctype}.png`;
      const badgeHtml = getStatusBadge(item.status);

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td style="color:#64748B; font-weight:600;">${index + 1}</td>
        <td>
          <div class="preview-thumb-box">
            <img src="${meta.refImg}" class="preview-thumb-img" alt="${meta.title}" onerror="this.style.display='none'" />
          </div>
        </td>
        <td>
          <div class="circuit-type-title">${meta.title}</div>
          <div class="circuit-type-sub">${meta.sub}</div>
        </td>
        <td>
          <span class="filename-code">${filename}</span>
        </td>
        <td>
          <span class="date-text">${dateFormatted}</span>
        </td>
        <td>
          ${badgeHtml}
        </td>
        <td style="text-align:right;">
          <a href="/api/reports/${item.id}/pdf?t=${Date.now()}" target="_blank" class="btn-view-report">
            View Report
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
              <polyline points="15 3 21 3 21 9"></polyline>
              <line x1="10" y1="14" x2="21" y2="3"></line>
            </svg>
          </a>
        </td>
        <td style="text-align:center;">
          <button class="row-actions-btn" title="Options">⋮</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; color:#DC2626; padding:20px;">Failed to load recent sessions.</td></tr>';
  }
}

// =========================================================================
// MINIMAL TECHNICAL ASSISTANT
// =========================================================================
function toggleAssistantDrawer() {
  const drawer = document.getElementById('assistant-drawer');
  if (drawer) {
    drawer.classList.toggle('open');
    if (drawer.classList.contains('open')) {
      const input = document.getElementById('assistant-input');
      if (input) setTimeout(() => input.focus(), 150);
    }
  }
}

function askAssistantQuick(promptText) {
  const input = document.getElementById('assistant-input');
  if (input) input.value = promptText;
  sendAssistantQuery();
}

async function sendAssistantQuery() {
  const input = document.getElementById('assistant-input');
  const messagesList = document.getElementById('assistant-messages-list');
  if (!input || !messagesList) return;

  const query = input.value.trim();
  if (!query) return;

  // Add user query message
  const userDiv = document.createElement('div');
  userDiv.className = 'assistant-msg assistant-msg-user';
  userDiv.innerHTML = `<div class="msg-content">${escapeHtml(query)}</div>`;
  messagesList.appendChild(userDiv);
  input.value = '';
  messagesList.scrollTop = messagesList.scrollHeight;

  // Loading indicator bot message
  const loadingDiv = document.createElement('div');
  loadingDiv.className = 'assistant-msg assistant-msg-bot';
  loadingDiv.innerHTML = `<div class="msg-content" style="color:var(--text-muted); font-style:italic;">Consulting diagnostic engine...</div>`;
  messagesList.appendChild(loadingDiv);
  messagesList.scrollTop = messagesList.scrollHeight;

  try {
    const payload = {
      session_id: AppState.currentSessionId || null,
      query: query,
      circuit_context: {
        circuit_type: AppState.currentCircuitType,
        parameters: AppState.currentParameters,
        findings: AppState.currentAnalysisData ? (AppState.currentAnalysisData.findings || []) : []
      }
    };

    const res = await fetch('/api/assistant/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error('Query failed');
    const data = await res.json();

    let botContent = `<div class="msg-content">${data.response || 'No explanation generated.'}</div>`;
    const evidenceList = data.evidence_points || data.evidence || [];
    if (evidenceList.length > 0) {
      botContent += `<div class="msg-evidence-box"><strong>Evidence Points:</strong><ul style="margin:4px 0 0 16px;">`;
      evidenceList.forEach(ev => {
        botContent += `<li>${escapeHtml(ev)}</li>`;
      });
      botContent += `</ul></div>`;
    }
    loadingDiv.innerHTML = botContent;
  } catch (err) {
    loadingDiv.innerHTML = `<div class="msg-content" style="color:var(--danger);">Error: Could not reach diagnostic engine.</div>`;
  }
  messagesList.scrollTop = messagesList.scrollHeight;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.innerText = text;
  return div.innerHTML;
}


async function loadReportsHistory() {
  const tbody = document.getElementById('history-reports-tbody');
  if (!tbody) return;
  tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:#64748B;">Loading sessions...</td></tr>';

  try {
    const res = await fetch('/api/history/');
    const list = await res.json();
    tbody.innerHTML = '';

    if (list.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:20px; color:#64748B;">No previous reports saved.</td></tr>';
      return;
    }

    list.forEach(item => {
      const d = new Date(item.created_at * 1000).toLocaleString();
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>${(item.circuit_type || 'Circuit').replace(/_/g, ' ').toUpperCase()}</strong></td>
        <td><code>${item.id}</code></td>
        <td>${d}</td>
        <td><span class="badge badge-passed">${item.report_summary || 'Completed'}</span></td>
        <td style="text-align:right;">
          <a href="/api/reports/${item.id}/pdf?t=${Date.now()}" target="_blank" class="btn btn-secondary btn-sm">Download PDF</a>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:#DC2626;">Error loading reports history.</td></tr>';
  }
}

async function initCircuitLibrary() {
  const grid = document.getElementById('library-grid');
  if (!grid) return;

  try {
    const res = await fetch('/api/analysis/samples');
    const samples = await res.json();
    grid.innerHTML = '';

    samples.forEach(s => {
      const card = document.createElement('div');
      card.className = 'eng-card';
      card.innerHTML = `
        <div style="font-weight:600; font-size:12.5px; margin-bottom:6px;">${s.name}</div>
        <img src="${s.url}" style="width:100%; height:120px; object-fit:contain; background:#FAFAFA; border:1px solid #E2E8F0; border-radius:4px; margin-bottom:8px;" />
        <button class="btn btn-secondary btn-sm" style="width:100%;">Load into Workspace</button>
      `;
      card.querySelector('button').addEventListener('click', () => loadLibrarySample(s));
      grid.appendChild(card);
    });
  } catch (e) {
    grid.innerHTML = '<span style="color:#DC2626;">Failed to load library samples.</span>';
  }
}

async function loadLibrarySample(sample) {
  AppState.currentSessionId = `SAMPLE-${sample.id.toUpperCase()}`;
  AppState.currentCircuitType = sample.type;
  AppState.currentParameters = sample.default_params;
  AppState.uploadedImageUrl = sample.url;

  startNewAnalysis();

  // Populate Stage 1 view directly
  const viewport = document.getElementById('stage1-image-viewport');
  if (viewport) {
    viewport.innerHTML = `<img src="${sample.url}" style="max-width:100%; max-height:270px; object-fit:contain;" alt="${sample.name}" />`;
  }
  const typeSelect = document.getElementById('stage1-circuit-type');
  if (typeSelect) typeSelect.value = sample.type;

  rebuildStage1ComponentTable();
}

// Advanced Benchmark Runner (For Advanced Section)
async function runAdvancedBenchmark() {
  const btn = document.getElementById('btn-run-adv-bench');
  const status = document.getElementById('adv-bench-status');
  btn.disabled = true;
  status.innerText = 'Evaluating Monte Carlo benchmark trials...';

  try {
    const res = await fetch('/api/benchmarks/run?trials=20');
    const data = await res.json();
    status.innerText = `Evaluated ${data.total_instances_evaluated} instances in ${data.execution_time_seconds.toFixed(2)}s.`;
    CircuitPlots.renderBenchmarkChart('plot-adv-bench', data.replicated_table_3);
  } catch (e) {
    status.innerText = `Error: ${e.message}`;
  } finally {
    btn.disabled = false;
  }
}
