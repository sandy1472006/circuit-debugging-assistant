from pathlib import Path
from app.reports.pdf_generator import build_pdf_report

circuits = [
    {
        'id': 'RC_LOW_PASS',
        'created_at': 1760378400,
        'circuit_type': 'rc_low_pass',
        'upload_filename': 'rc_filter_open_cap.png',
        'status': 'Needs Review',
        'parameters': {'R': 10000.0, 'C': 100e-9, 'Vin': 5.0},
        'findings': [
            {
                'severity': 'Error',
                'component': 'C1 (Capacitor)',
                'finding': 'Ground terminal unconnected (open node detected).',
                'recommendation': 'Connect bottom terminal of C1 to circuit ground plane.'
            }
        ]
    },
    {
        'id': 'VOLTAGE_DIVIDER',
        'created_at': 1760378400,
        'circuit_type': 'voltage_divider',
        'upload_filename': 'voltage_divider_fault.png',
        'status': 'Needs Review',
        'parameters': {'R1': 10000.0, 'R2': 5000.0, 'Vin': 10.0},
        'findings': [
            {
                'severity': 'Warning',
                'component': 'R2 (Resistor)',
                'finding': 'Output voltage divider offset shift detected.',
                'recommendation': 'Verify nominal resistor tolerance and grounding.'
            }
        ]
    },
    {
        'id': 'RL_HIGH_PASS',
        'created_at': 1760378400,
        'circuit_type': 'rl_high_pass',
        'upload_filename': 'rl_high_pass.png',
        'status': 'Nominal',
        'parameters': {'R': 1000.0, 'L': 0.01, 'Vin': 5.0},
        'findings': []
    },
    {
        'id': 'RLC_BAND_PASS',
        'created_at': 1760378400,
        'circuit_type': 'rlc_band_pass',
        'upload_filename': 'rlc_band_pass.png',
        'status': 'Nominal',
        'parameters': {'R': 1000.0, 'L': 0.01, 'C': 25.33e-9, 'Vin': 1.0},
        'findings': []
    }
]

reports_dir = Path('data/reports')
reports_dir.mkdir(parents=True, exist_ok=True)
plot_temp = reports_dir / 'plots'

for c in circuits:
    out_pdf = reports_dir / f"{c['id']}_Diagnostic_Report.pdf"
    build_pdf_report(c, out_pdf, plot_temp)
    print(f"Generated: {out_pdf.name} ({out_pdf.stat().st_size} bytes)")
