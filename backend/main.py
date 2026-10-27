"""
main.py
FastAPI defender server: signature verification, file upload + verify,
and a WebSocket channel that pushes every verdict to the live dashboard.
Run with:  uvicorn main:app --host 0.0.0.0 --port 8000
"""
import hashlib
import time
import json
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.dirname(__file__))

import starlette.routing
_orig_router_init = starlette.routing.Router.__init__
def _patched_router_init(self, *args, **kwargs):
    kwargs.pop("on_startup", None)
    kwargs.pop("on_shutdown", None)
    _orig_router_init(self, *args, **kwargs)
starlette.routing.Router.__init__ = _patched_router_init
FastAPI.max_body_size = None



from detection import evaluate_request
from database import init_db, log_verification, get_recent_history, get_stats_summary


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="QDS Threat Detection Defender", lifespan=lifespan)

# Enable CORS for React Frontend & LAN clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# session_id -> {"identity": "alice", ...}
SESSION_REGISTRY: dict[str, dict] = {
    "sess_demo1": {"identity": "alice"},
    "demo_none_session": {"identity": "demo_legitimate_client"},
    "demo_forgery_session": {"identity": "demo_forgery_client"},
    "demo_replay_session": {"identity": "demo_replay_client"},
    "demo_impersonation_session": {"identity": "demo_impersonation_client"},
    "demo_intercept_resend_session": {"identity": "demo_intercept_resend_client"}
}

# Active dashboard sockets
DASHBOARD_CLIENTS: list[WebSocket] = []


async def broadcast(event: dict):
    dead = []
    for ws in DASHBOARD_CLIENTS:
        try:
            await ws.send_text(json.dumps(event))
        except Exception:
            dead.append(ws)
    for ws in dead:
        DASHBOARD_CLIENTS.remove(ws)


@app.websocket("/ws/dashboard")
async def dashboard_socket(ws: WebSocket):
    await ws.accept()
    DASHBOARD_CLIENTS.append(ws)
    try:
        while True:
            await ws.receive_text()  # keep-alive; dashboard doesn't send data
    except WebSocketDisconnect:
        if ws in DASHBOARD_CLIENTS:
            DASHBOARD_CLIENTS.remove(ws)


@app.websocket("/ws")
async def ws_compatibility_endpoint(ws: WebSocket):
    """Compatibility websocket endpoint for existing React frontend."""
    await ws.accept()
    DASHBOARD_CLIENTS.append(ws)
    try:
        recent_history = get_recent_history(limit=50)
        stats = get_stats_summary()
        # Send initial connected message with history & stats
        await ws.send_text(json.dumps({
            "event_type": "CONNECTED",
            "recent_history": recent_history,
            "stats": stats
        }))
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        if ws in DASHBOARD_CLIENTS:
            DASHBOARD_CLIENTS.remove(ws)


@app.get("/api/stats")
async def api_get_stats():
    return JSONResponse(get_stats_summary())


@app.get("/api/history")
async def api_get_history(limit: int = 50):
    return JSONResponse(get_recent_history(limit=limit))


@app.post("/qds/verify")
async def qds_verify(payload: dict):
    result = await evaluate_request(payload, SESSION_REGISTRY)
    fidelity = 1.0 if result["verdict"] == "ACCEPT" else 0.55
    anomaly_score = result["statistical_check"].get("chi2") or (0.0 if result["verdict"] == "ACCEPT" else 25.0)
    status_code = "200" if result["verdict"] == "ACCEPT" else "403"
    details = f"Chi2: {result['statistical_check'].get('chi2')}" if result["statistical_check"].get("chi2") is not None else (result.get("replay_check", {}).get("reason") or result.get("identity_check", {}).get("reason") or "Verified")
    attack_type = result.get("attack_type") or "none"
    message_text = payload.get("signature_data", {}).get("message_hash", "Signature verification")
    client_id = payload.get("identity", "unknown")
    req_id = payload.get("nonce") or str(uuid.uuid4())

    try:
        log_verification(
            request_id=req_id,
            client_id=client_id,
            attack_type=attack_type,
            message=message_text,
            fidelity=fidelity,
            anomaly_score=anomaly_score,
            threshold=7.815,
            verdict=result["verdict"],
            status_code=status_code,
            details=details
        )
    except Exception as e:
        print("Database log error:", e)

    event = {
        "event_type": "VERIFICATION_COMPLETED",
        "type": "verdict",
        "request_id": req_id,
        "client_id": client_id,
        "source": client_id,
        "session_id": payload.get("session_id"),
        "attack_type": attack_type,
        "message": message_text,
        "timestamp": time.time(),
        "result": {
            "fidelity": fidelity,
            "anomaly_score": anomaly_score,
            "threshold": 7.815,
            "verdict": result["verdict"],
            "status_code": status_code,
            "details": details
        },
        **result,
    }
    await broadcast(event)
    return JSONResponse(event)


@app.post("/api/verify")
async def api_verify(payload: dict):
    """Frontend legacy route compatibility."""
    import uuid, numpy as np
    from qds_core import generate_session_key, sign_message
    
    rng = np.random.default_rng()
    key = generate_session_key(rng, rounds=32)
    msg_hash = hashlib.sha256(payload.get("message", "demo").encode()).hexdigest()
    corrections = sign_message(msg_hash, key, rng, rounds=32)

    full_payload = {
        "session_id": "sess_demo1",
        "identity": payload.get("client_id", "alice"),
        "nonce": str(uuid.uuid4()),
        "timestamp": time.time(),
        "signature_data": {
            "pauli_corrections": corrections,
            "message_hash": msg_hash
        }
    }
    return await qds_verify(full_payload)


@app.post("/api/attack")
async def api_attack(payload: dict):
    """Frontend attack simulation compatibility endpoint."""
    import uuid, random
    attack_type = payload.get("attack_type", "forgery")
    attacker_id = payload.get("attacker_id", "demo_attacker")
    msg_hash = hashlib.sha256(payload.get("message", "demo").encode()).hexdigest()

    if attack_type == "forgery":
        corrections = random.choices(["I", "X", "Y", "Z"], weights=[0.60, 0.15, 0.15, 0.10], k=32)
        full_payload = {
            "session_id": "sess_demo1",
            "identity": "alice",
            "nonce": str(uuid.uuid4()),
            "timestamp": time.time(),
            "signature_data": {
                "pauli_corrections": corrections,
                "message_hash": msg_hash
            }
        }
    elif attack_type == "impersonation":
        corrections = ["I"] * 32
        full_payload = {
            "session_id": "sess_demo1",
            "identity": attacker_id,  # Unregistered identity mismatch
            "nonce": str(uuid.uuid4()),
            "timestamp": time.time(),
            "signature_data": {
                "pauli_corrections": corrections,
                "message_hash": msg_hash
            }
        }
    elif attack_type == "replay":
        corrections = ["I"] * 32
        reused_nonce = "fixed_replayed_nonce_12345"
        # First register nonce
        await evaluate_request({
            "session_id": "sess_demo1",
            "identity": "alice",
            "nonce": reused_nonce,
            "timestamp": time.time(),
            "signature_data": {"pauli_corrections": corrections, "message_hash": msg_hash}
        }, SESSION_REGISTRY)

        full_payload = {
            "session_id": "sess_demo1",
            "identity": "alice",
            "nonce": reused_nonce,  # Reused
            "timestamp": time.time(),
            "signature_data": {
                "pauli_corrections": corrections,
                "message_hash": msg_hash
            }
        }
    else:  # intercept_resend / default
        corrections = ["X", "Y", "Z", "I"] * 8
        full_payload = {
            "session_id": "sess_demo1",
            "identity": "alice",
            "nonce": str(uuid.uuid4()),
            "timestamp": time.time(),
            "signature_data": {
                "pauli_corrections": corrections,
                "message_hash": msg_hash
            }
        }

    return await qds_verify(full_payload)


@app.post("/files/upload-and-verify")
async def upload_and_verify(file: UploadFile = File(...), signature_json: str = Form(...)):
    payload = json.loads(signature_json)
    file_bytes = await file.read()
    received_hash = hashlib.sha256(file_bytes).hexdigest()
    claimed_hash = payload["signature_data"].get("message_hash")

    integrity_ok = received_hash == claimed_hash
    detection_result = await evaluate_request(payload, SESSION_REGISTRY)

    verdict = detection_result["verdict"]
    attack_type = detection_result.get("attack_type") or "none"
    if not integrity_ok:
        verdict = "REJECT"
        attack_type = "TAMPERED_PAYLOAD"

    fidelity = 1.0 if verdict == "ACCEPT" else 0.55
    anomaly_score = detection_result["statistical_check"].get("chi2") or (0.0 if verdict == "ACCEPT" else 25.0)
    status_code = "200" if verdict == "ACCEPT" else "403"
    details = f"File: {file.filename} (Integrity: {'OK' if integrity_ok else 'FAILED'}) | Chi2: {detection_result['statistical_check'].get('chi2')}"
    req_id = payload.get("nonce") or str(uuid.uuid4())
    client_id = payload.get("identity", "alice")

    try:
        log_verification(
            request_id=req_id,
            client_id=client_id,
            attack_type=attack_type,
            message=f"File: {file.filename} ({len(file_bytes)} bytes)",
            fidelity=fidelity,
            anomaly_score=anomaly_score,
            threshold=7.815,
            verdict=verdict,
            status_code=status_code,
            details=details
        )
    except Exception as e:
        print("Database log error:", e)

    event = {
        "event_type": "VERIFICATION_COMPLETED",
        "type": "file_verdict",
        "request_id": req_id,
        "client_id": client_id,
        "source": client_id,
        "session_id": payload.get("session_id"),
        "attack_type": attack_type,
        "message": f"File: {file.filename} ({len(file_bytes)} bytes)",
        "filename": file.filename,
        "size": len(file_bytes),
        "received_hash": received_hash,
        "claimed_hash": claimed_hash,
        "integrity_ok": integrity_ok,
        "timestamp": time.time(),
        "result": {
            "fidelity": fidelity,
            "anomaly_score": anomaly_score,
            "threshold": 7.815,
            "verdict": verdict,
            "status_code": status_code,
            "details": details
        },
        **detection_result,
        "verdict": verdict,
    }
    await broadcast(event)
    return JSONResponse(event)
