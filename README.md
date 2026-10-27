# QubitX — Quantum Digital Signature (QDS) Threat Detection & File Sharing Platform

QubitX is a quantum-inspired threat detection and signature verification platform built to prevent forgery, replay attacks, identity impersonation, and file tampering across quantum-secured communications.

---

## 📐 System Architecture

```
                               ┌──────────────────────────────────────────────┐
                               │             SENDER CLIENT                    │
                               │  - Hashes message / file (SHA-256)           │
                               │  - Generates QDS Pauli corrections           │
                               └──────────────────────┬───────────────────────┘
                                                      │
                                           [Upload / Verify Payload]
                                                      │
                                                      ▼
                       ┌─────────────────────────────────────────────────────────────┐
                       │                   INTERCEPTOR PROXY (OPTIONAL)              │
                       │  - Scenario B: Flips file bytes (File Tampering)             │
                       │  - Scenario C: Corrupts Pauli corrections (Sig Forgery)     │
                       └──────────────────────────────┬──────────────────────────────┘
                                                      │
                                                      ▼
                       ┌─────────────────────────────────────────────────────────────┐
                       │               QUBITX DEFENDER BACKEND ENGINE                │
                       │  1. Check SHA256 file hash integrity (Basic Layer)          │
                       │  2. Identity registry lookup                                │
                       │  3. Replay attack check (Nonce validation)                 │
                       │  4. Quantum Statistical Detector (Chi-Square χ² test)       │
                       └──────────────────────────────┬──────────────────────────────┘
                                                      │
                                            Broadcast Verdict via WS
                                                      ▼
                       ┌─────────────────────────────────────────────────────────────┐
                       │                 LIVE REACT DASHBOARD                        │
                       │  - Real-time telemetry, threat radar & verification log     │
                       └─────────────────────────────────────────────────────────────┘
```

---

## 💡 Core Features

1. **Quantum Digital Signature (QDS) Verification**: Validates state teleportation parameters and Pauli basis measurements (`I`, `X`, `Y`, `Z`).
2. **Quantum Statistical Anomaly Detector ($\chi^2$ Test)**: Detects quantum state perturbation and adversary measurement forgery. If the calculated $\chi^2$ anomaly score exceeds threshold `7.815` ($\alpha = 0.05, \text{df}=3$), the signature is flagged as `FORGERY`.
3. **Nonce Replay Prevention**: Tracks request nonces to prevent token reuse and replay attacks.
4. **Identity Registry Check**: Verifies sender identity against active session registrations.
5. **File Integrity Hash Check**: Verifies SHA-256 hash of uploaded file payloads before performing QDS verification.

---

## 🛠 Repository Structure

```
QubitX/
├── backend/
│   ├── main.py                # FastAPI server (Endpoints, WebSocket broadcasting)
│   ├── detection.py           # Multi-layered threat detection engine
│   ├── qds_core.py            # QDS quantum state generation & verification math
│   ├── qds_engine.py          # Chi-Square statistical calculation logic
│   ├── database.py            # SQLite audit log storage (qds_audit.db)
│   └── telegram_notifier.py   # Automated threat alerting integration
├── clients/
│   ├── sender_client.py       # File sharing demo sender client
│   ├── tamper_file_proxy.py   # Scenario B: Byte-level file tampering proxy (Port 8002)
│   ├── tamper_sig_proxy.py    # Scenario C: Signature forgery proxy (Port 8003)
│   ├── attacker_common.py     # Shared client utilities & signature generator
│   └── run_attacks.py         # Bot attack suite launcher
├── frontend/                  # React + Vite live monitoring dashboard
├── run_demo.sh                # Automated multi-bot demo bash script
└── README.md                  # Project documentation & implementation plan
```

---

## 🔌 Backend API Specification

### 1. `POST /qds/verify`
Evaluates standard JSON QDS payloads for authenticity, replay, and forgery.

*Request Body:*
```json
{
  "session_id": "sess_demo1",
  "identity": "alice",
  "nonce": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": 1725832740.0,
  "signature_data": {
    "pauli_corrections": ["I", "X", "Z", "I", "Y", "..."],
    "message_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  }
}
```

*Response:*
```json
{
  "verdict": "ACCEPT",
  "attack_type": "none",
  "fidelity": 1.0,
  "anomaly_score": 1.25,
  "threshold": 7.815,
  "status_code": "200"
}
```

---

### 2. `POST /files/upload-and-verify`
Handles multipart file uploads along with JSON-encoded QDS signature data.

*Form Parameters:*
- `file`: Multipart file binary data.
- `signature_json`: Stringified JSON signature payload (`session_id`, `identity`, `nonce`, `signature_data`).

*Response:*
```json
{
  "verdict": "ACCEPT",
  "filename": "report.pdf",
  "size": 10240,
  "integrity_ok": true,
  "attack_type": "none",
  "result": {
    "verdict": "ACCEPT",
    "anomaly_score": 1.42,
    "threshold": 7.815,
    "details": "File: report.pdf (Integrity: OK) | Chi2: 1.42"
  }
}
```

---

## 🎯 Part 11 — File Sharing Demo Workflow

The File Sharing Demo validates quantum digital signatures applied to arbitrary file transfers (e.g. `report.pdf`). It demonstrates how QubitX distinguishes between standard byte-level file tampering and advanced quantum statistical signature forgery.

### Sender Client Code (`sender_client.py`)

```python
import hashlib, httpx, argparse, json
from attacker_common import make_legit_signature

p = argparse.ArgumentParser()
p.add_argument("--server", required=True)
p.add_argument("--file", required=True)
p.add_argument("--session", default="sess_demo1")
p.add_argument("--identity", default="alice")
args = p.parse_args()

with open(args.file, "rb") as f:
    file_bytes = f.read()

file_hash = hashlib.sha256(file_bytes).hexdigest()
signature_payload = make_legit_signature(args.session, args.identity, message_hash=file_hash)

files = {"file": (args.file, file_bytes)}
data = {"signature_json": json.dumps(signature_payload)}

r = httpx.post(f"{args.server}/files/upload-and-verify", files=files, data=data)
print("SENT ->", r.json()["verdict"], "| integrity_ok:", r.json()["integrity_ok"])
```

---

### Proxy Interceptors (`tamper_file_proxy.py` & `tamper_sig_proxy.py`)

#### Scenario B — File Tampering Proxy (`tamper_file_proxy.py`)
Flips file bytes in-transit while keeping the sender's QDS signature untouched.
```python
# Intercepts upload, modifies byte index 10:
tampered = bytearray(file_bytes)
tampered[10] ^= 0xFF
```
- **Target Backend Response**: `REJECT (integrity_ok: false, attack_type: TAMPERED_PAYLOAD)`.

#### Scenario C — Signature Tampering Proxy (`tamper_sig_proxy.py`)
Keeps file bytes pristine, but corrupts `pauli_corrections` in `signature_json`.
```python
# Intercepts upload, replaces Pauli corrections with forged distribution:
payload["signature_data"]["pauli_corrections"] = random.choices(["I", "X", "Y", "Z"], weights=[0.60, 0.15, 0.15, 0.10], k=32)
```
- **Target Backend Response**: `REJECT (FORGERY, chi2 > 7.815)`.

---

## 📋 Judge Demonstration Matrix

| Step | Action / Command | Expected Dashboard Output | Security Defense Mechanism Highlighted |
|---|---|---|---|
| **1** | `python clients/sender_client.py --server http://localhost:8000 --file report.pdf` | ✅ **ACCEPT** (integrity_ok: true) | Baseline legitimate transfer. Hash matches & $\chi^2 < 7.815$. |
| **2** | `python clients/sender_client.py --server http://localhost:8002 --file report.pdf` | 🚨 **REJECT** — `integrity mismatch` | **File Integrity Hashing (Basic Layer)**: Hash mismatch caught immediately. |
| **3** | `python clients/sender_client.py --server http://localhost:8003 --file report.pdf` | 🚨 **REJECT** — `FORGERY` ($\chi^2 = 24.6 > 7.815$) | **Quantum Statistical Anomaly Detector (Core Innovation)**: File hash passes, but quantum state disturbance is detected! |
| **4** | Re-run Scenario 1 command with identical nonce | 🚨 **REJECT** — `REPLAY` attack | **Nonce Replay Prevention**: Prevents re-submission of intercepted valid signatures. |

---

## 🔑 Key Distinction to Emphasize for Judges

> **Important Narrative Distinction**:
> - **Step 2 (File Tampering)** demonstrates traditional **SHA-256 Integrity Hashing** (pre-check defense).
> - **Step 3 (Signature Tampering)** showcases our **Quantum-Inspired Statistical Detector** ($\chi^2$ anomaly scoring).
> 
> Even if an attacker passes the file hash check by modifying signatures directly, QubitX's statistical engine detects the physical/statistical perturbation induced by signature manipulation.

---

## 🚀 Running the Full System

### 1. Start Defender Backend
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 2. Start Proxy Interceptors (In separate terminal windows)
```bash
# Terminal 2: File Tamper Proxy (Port 8002)
python clients/tamper_file_proxy.py --port 8002

# Terminal 3: Signature Tamper Proxy (Port 8003)
python clients/tamper_sig_proxy.py --port 8003
```

### 3. Launch Frontend Dashboard
```bash
cd frontend
npm run dev
```

### 4. Execute Demonstration Steps
```bash
# Clean upload (Scenario A)
python clients/sender_client.py --server http://localhost:8000 --file report.pdf

# File Tamper Proxy upload (Scenario B)
python clients/sender_client.py --server http://localhost:8002 --file report.pdf

# Signature Forgery Proxy upload (Scenario C)
python clients/sender_client.py --server http://localhost:8003 --file report.pdf
```
