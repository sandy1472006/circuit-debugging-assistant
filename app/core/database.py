"""
database.py - SQLite persistence layer for analysis sessions, reports, and history.
"""

import sqlite3
import json
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
from app.config import DATABASE_PATH

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        created_at REAL,
        circuit_type TEXT,
        upload_filename TEXT,
        file_checksum TEXT,
        status TEXT,
        parameters_json TEXT,
        observations_json TEXT,
        findings_json TEXT,
        diagnosis_json TEXT,
        report_pdf_path TEXT,
        report_summary TEXT
    )
    """)
    conn.commit()

    # Seed demo records if database is empty
    cursor.execute("SELECT COUNT(*) FROM sessions")
    count = cursor.fetchone()[0]
    if count == 0:
        demo_sessions = [
            (
                "ANALYSIS-DEMO-RC", 1791834240.0, "rc_low_pass", "rc_lowpass.png", "", "Completed",
                json.dumps({"R": 10000.0, "C": 100e-9, "Vin": 5.0}), "{}", "[]",
                json.dumps({"top_candidate": {"label": "Nominal", "residual_score": 0.001}}),
                None, "Completed nominal verification."
            ),
            (
                "ANALYSIS-DEMO-VD", 1791731880.0, "voltage_divider", "voltage_divider.pdf", "", "Needs Review",
                json.dumps({"R1": 10000.0, "R2": 5000.0, "Vin": 10.0}), "{}",
                json.dumps([{"id": "FIND-01", "severity": "Warning", "component_or_net": "R2", "evidence": "Output voltage ratio shift."}]),
                json.dumps({"top_candidate": {"label": "R2 Drift -15%", "residual_score": 0.082}}),
                None, "Identified potential divider attenuation drift."
            ),
            (
                "ANALYSIS-DEMO-RLC", 1791635820.0, "rlc_band_pass", "rlc_bandpass.png", "", "Completed",
                json.dumps({"R": 1000.0, "L": 0.01, "C": 100e-9, "Vin": 1.0}), "{}", "[]",
                json.dumps({"top_candidate": {"label": "Nominal", "residual_score": 0.002}}),
                None, "Verified resonant passband."
            ),
            (
                "ANALYSIS-DEMO-RL", 1791524700.0, "rl_high_pass", "rl_highpass.png", "", "Analysis Failed",
                json.dumps({"R": 1000.0, "L": 0.01, "Vin": 5.0}), "{}",
                json.dumps([{"id": "FIND-02", "severity": "Critical", "component_or_net": "L1", "evidence": "Inductor shorted to ground plane."}]),
                json.dumps({"top_candidate": {"label": "L1 Shorted", "residual_score": 0.941}}),
                None, "Confirmed short-circuit failure."
            ),
        ]
        cursor.executemany("""
        INSERT INTO sessions (
            id, created_at, circuit_type, upload_filename, file_checksum,
            status, parameters_json, observations_json, findings_json,
            diagnosis_json, report_pdf_path, report_summary
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, demo_sessions)
        conn.commit()

    conn.close()

def save_session(session_data: Dict[str, Any]):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO sessions (
        id, created_at, circuit_type, upload_filename, file_checksum,
        status, parameters_json, observations_json, findings_json,
        diagnosis_json, report_pdf_path, report_summary
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_data.get("id"),
        session_data.get("created_at", time.time()),
        session_data.get("circuit_type"),
        session_data.get("upload_filename"),
        session_data.get("file_checksum"),
        session_data.get("status", "completed"),
        json.dumps(session_data.get("parameters", {})),
        json.dumps(session_data.get("observations", {})),
        json.dumps(session_data.get("findings", [])),
        json.dumps(session_data.get("diagnosis", {})),
        session_data.get("report_pdf_path"),
        session_data.get("report_summary", "")
    ))
    conn.commit()
    conn.close()

def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "circuit_type": row["circuit_type"],
        "upload_filename": row["upload_filename"],
        "file_checksum": row["file_checksum"],
        "status": row["status"],
        "parameters": json.loads(row["parameters_json"] or "{}"),
        "observations": json.loads(row["observations_json"] or "{}"),
        "findings": json.loads(row["findings_json"] or "[]"),
        "diagnosis": json.loads(row["diagnosis_json"] or "{}"),
        "report_pdf_path": row["report_pdf_path"],
        "report_summary": row["report_summary"]
    }

def list_sessions(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, created_at, circuit_type, upload_filename, status, report_summary FROM sessions ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_session(session_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

# Initialize DB on import
init_db()
