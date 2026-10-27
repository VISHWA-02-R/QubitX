import sqlite3
import datetime

DB_FILE = "qds_audit.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            client_id TEXT NOT NULL,
            attack_type TEXT NOT NULL,
            message TEXT NOT NULL,
            fidelity REAL NOT NULL,
            anomaly_score REAL NOT NULL,
            threshold REAL NOT NULL,
            verdict TEXT NOT NULL,
            status_code TEXT NOT NULL,
            details TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_verification(
    request_id: str,
    client_id: str,
    attack_type: str,
    message: str,
    fidelity: float,
    anomaly_score: float,
    threshold: float,
    verdict: str,
    status_code: str,
    details: str
):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO audit_logs (
            request_id, timestamp, client_id, attack_type, message,
            fidelity, anomaly_score, threshold, verdict, status_code, details
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        request_id, timestamp, client_id, attack_type, message,
        fidelity, anomaly_score, threshold, verdict, status_code, details
    ))
    conn.commit()
    conn.close()

def get_recent_history(limit: int = 50):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_stats_summary():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM audit_logs")
    total_requests = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE verdict = 'ACCEPT'")
    accepted_count = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE verdict = 'REJECT'")
    rejected_count = cursor.fetchone()[0] or 0

    cursor.execute("SELECT AVG(anomaly_score), AVG(fidelity) FROM audit_logs")
    avg_row = cursor.fetchone()
    avg_anomaly = round(avg_row[0], 2) if avg_row[0] is not None else 0.0
    avg_fidelity = round(avg_row[1], 4) if avg_row[1] is not None else 0.0

    cursor.execute("SELECT attack_type, COUNT(*) FROM audit_logs GROUP BY attack_type")
    attack_breakdown = dict(cursor.fetchall())

    conn.close()

    return {
        "total_requests": total_requests,
        "accepted_count": accepted_count,
        "rejected_count": rejected_count,
        "accept_rate": round((accepted_count / total_requests * 100), 1) if total_requests > 0 else 100.0,
        "avg_anomaly_score": avg_anomaly,
        "avg_fidelity": avg_fidelity,
        "attack_breakdown": attack_breakdown
    }
