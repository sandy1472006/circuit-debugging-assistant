/**
 * plots.js - Scientific plotting utilities using Plotly.js
 * Restrained engineering aesthetic: crisp lines, explicit units, clean grid.
 */

window.CircuitPlots = {
  renderBodePlot: function(domId, simData) {
    if (!window.Plotly || !document.getElementById(domId)) return;

    const freqs = simData.frequencies;
    const magNom = simData.mag_nominal_db;
    const phaseNom = simData.phase_nominal_deg;
    const magAct = simData.mag_actual_db;
    const phaseAct = simData.phase_actual_deg;

    const traceMagNom = {
      x: freqs,
      y: magNom,
      name: 'Nominal Mag (dB)',
      type: 'scatter',
      mode: 'lines',
      line: { color: '#1E40AF', width: 2 }
    };

    const traceMagAct = {
      x: freqs,
      y: magAct,
      name: 'Observed Mag (dB)',
      type: 'scatter',
      mode: 'lines',
      line: { color: '#DC2626', width: 2, dash: 'dash' }
    };

    const tracePhaseNom = {
      x: freqs,
      y: phaseNom,
      name: 'Nominal Phase (°)',
      type: 'scatter',
      mode: 'lines',
      yaxis: 'y2',
      line: { color: '#059669', width: 1.5, dash: 'dot' }
    };

    const tracePhaseAct = {
      x: freqs,
      y: phaseAct,
      name: 'Observed Phase (°)',
      type: 'scatter',
      mode: 'lines',
      yaxis: 'y2',
      line: { color: '#D97706', width: 1.5, dash: 'dashdot' }
    };

    const layout = {
      title: { text: 'Bode Frequency Response [Transfer Function H(f)]', font: { size: 13, color: '#0F172A' } },
      xaxis: {
        type: 'log',
        title: { text: 'Frequency (Hz)', font: { size: 11, color: '#475569' } },
        gridcolor: '#E2E8F0',
        zeroline: false
      },
      yaxis: {
        title: { text: 'Magnitude (dB)', font: { size: 11, color: '#1E40AF' } },
        gridcolor: '#E2E8F0',
        zerolinecolor: '#CBD5E1'
      },
      yaxis2: {
        title: { text: 'Phase (°)', font: { size: 11, color: '#059669' } },
        overlaying: 'y',
        side: 'right',
        gridcolor: '#F1F5F9'
      },
      margin: { t: 40, b: 40, l: 50, r: 50 },
      paper_bgcolor: '#FFFFFF',
      plot_bgcolor: '#FCFCFD',
      legend: { orientation: 'h', y: -0.2, x: 0.1, font: { size: 10 } }
    };

    Plotly.newPlot(domId, [traceMagNom, traceMagAct, tracePhaseNom, tracePhaseAct], layout, { responsive: true, displayModeBar: true });
  },

  renderStepPlot: function(domId, simData) {
    if (!window.Plotly || !document.getElementById(domId)) return;

    const t = simData.time_points; // ms
    const vNom = simData.step_nominal;
    const vAct = simData.step_actual;

    const traceNom = {
      x: t,
      y: vNom,
      name: 'Nominal Step Response',
      type: 'scatter',
      mode: 'lines',
      line: { color: '#1E40AF', width: 2 }
    };

    const traceAct = {
      x: t,
      y: vAct,
      name: 'Observed Step Response',
      type: 'scatter',
      mode: 'lines',
      line: { color: '#DC2626', width: 2, dash: 'dash' }
    };

    const layout = {
      title: { text: 'Transient Step Response', font: { size: 13, color: '#0F172A' } },
      xaxis: {
        title: { text: 'Time (ms)', font: { size: 11, color: '#475569' } },
        gridcolor: '#E2E8F0'
      },
      yaxis: {
        title: { text: 'Output Voltage Vout (V)', font: { size: 11, color: '#475569' } },
        gridcolor: '#E2E8F0'
      },
      margin: { t: 40, b: 40, l: 50, r: 20 },
      paper_bgcolor: '#FFFFFF',
      plot_bgcolor: '#FCFCFD',
      legend: { orientation: 'h', y: -0.2, x: 0.2, font: { size: 10 } }
    };

    Plotly.newPlot(domId, [traceNom, traceAct], layout, { responsive: true });
  },

  renderResidualChart: function(domId, candidates) {
    if (!window.Plotly || !document.getElementById(domId)) return;

    const top = candidates.slice(0, 8).reverse();
    const labels = top.map(c => c.label);
    const scores = top.map(c => c.residual_score);
    const colors = top.map((c, i) => (i === top.length - 1 ? '#059669' : '#3B82F6'));

    const trace = {
      x: scores,
      y: labels,
      type: 'bar',
      orientation: 'h',
      marker: { color: colors },
      text: scores.map(s => s.toFixed(3)),
      textposition: 'auto'
    };

    const layout = {
      title: { text: 'Candidate Fault Residual Scores S(f) [Lower = Stronger Match]', font: { size: 13, color: '#0F172A' } },
      xaxis: {
        title: { text: 'Normalized Residual Score', font: { size: 11, color: '#475569' } },
        gridcolor: '#E2E8F0'
      },
      yaxis: {
        automargin: true,
        tickfont: { size: 11 }
      },
      margin: { t: 40, b: 40, l: 120, r: 20 },
      paper_bgcolor: '#FFFFFF',
      plot_bgcolor: '#FCFCFD'
    };

    Plotly.newPlot(domId, [trace], layout, { responsive: true });
  },

  renderBenchmarkChart: function(domId, benchmarkData) {
    if (!window.Plotly || !document.getElementById(domId)) return;

    const noiseLevels = benchmarkData.map(d => `${d.noise_pct}% Noise`);
    const baselineAcc = benchmarkData.map(d => d.baseline);
    const proposedAcc = benchmarkData.map(d => d.proposed);

    const traceBase = {
      x: noiseLevels,
      y: baselineAcc,
      name: 'Baseline (Primary Transfer Only)',
      type: 'bar',
      marker: { color: '#94A3B8' }
    };

    const traceProp = {
      x: noiseLevels,
      y: proposedAcc,
      name: 'Proposed (Multi-Evidence Fusion)',
      type: 'bar',
      marker: { color: '#1E40AF' }
    };

    const layout = {
      barmode: 'group',
      title: { text: 'Overall Top-1 Localization Accuracy vs. Measurement Noise', font: { size: 13, color: '#0F172A' } },
      yaxis: {
        title: { text: 'Top-1 Accuracy (%)', font: { size: 11, color: '#475569' } },
        range: [40, 105],
        gridcolor: '#E2E8F0'
      },
      xaxis: {
        title: { text: 'Gaussian Measurement Noise Level', font: { size: 11, color: '#475569' } }
      },
      margin: { t: 40, b: 40, l: 50, r: 20 },
      paper_bgcolor: '#FFFFFF',
      plot_bgcolor: '#FCFCFD',
      legend: { orientation: 'h', y: -0.2, x: 0.15, font: { size: 10 } }
    };

    Plotly.newPlot(domId, [traceBase, traceProp], layout, { responsive: true });
  }
};
