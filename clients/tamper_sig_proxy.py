"""
tamper_sig_proxy.py
Proxy server for Scenario C (Signature Tampering / Forgery Demo).
Intercepts upload request, keeps original file pristine, but corrupts QDS signature pauli_corrections,
demonstrating the Quantum Statistical Anomaly Detector (Chi-Square test) catching cryptographic forgery.

Run with: python clients/tamper_sig_proxy.py --port 8003 --target http://localhost:8000
"""
import argparse
import json
import random
import sys
import httpx
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse
import uvicorn

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

TARGET_BACKEND = "http://localhost:8000"

async def tamper_signature(request):
    print("[SIG PROXY] Intercepting file upload request...")
    form = await request.form()
    file_item = form.get("file")
    signature_raw = form.get("signature_json")

    if not file_item or not signature_raw:
        return JSONResponse({"error": "Missing file or signature_json in form data"}, status_code=400)

    file_bytes = await file_item.read()
    filename = getattr(file_item, "filename", "file.pdf")

    payload = json.loads(signature_raw)
    
    # Keep file & message_hash unchanged, but corrupt Pauli correction states
    # Simulates adversary attempting quantum signature forgery / key guess
    forged_corrections = random.choices(["I", "X", "Y", "Z"], weights=[0.60, 0.15, 0.15, 0.10], k=32)
    payload["signature_data"]["pauli_corrections"] = forged_corrections

    tampered_sig_json = json.dumps(payload)

    print(f"[SIG PROXY] Kept file '{filename}' pristine ({len(file_bytes)} bytes)")
    print("[SIG PROXY] Corrupted Pauli corrections in signature_json to simulate QDS forgery attack.")
    print(f"[SIG PROXY] Forwarding to defender backend ({TARGET_BACKEND})...")

    files = {"file": (filename, file_bytes)}
    data = {"signature_json": tampered_sig_json}

    async with httpx.AsyncClient(base_url=TARGET_BACKEND, timeout=10.0) as client:
        resp = await client.post("/files/upload-and-verify", files=files, data=data)

    return JSONResponse(status_code=resp.status_code, content=resp.json())

app = Starlette(routes=[
    Route("/files/upload-and-verify", tamper_signature, methods=["POST"])
])

def main():
    global TARGET_BACKEND
    parser = argparse.ArgumentParser(description="Scenario C: Signature Tampering Proxy Server")
    parser.add_argument("--port", type=int, default=8003, help="Port to run proxy on (default: 8003)")
    parser.add_argument("--host", default="0.0.0.0", help="Host address (default: 0.0.0.0)")
    parser.add_argument("--target", default="http://localhost:8000", help="Target defender backend URL")
    args = parser.parse_args()

    TARGET_BACKEND = args.target.rstrip("/")
    print(f"Starting Signature Tamper Proxy on {args.host}:{args.port} -> Targeting {TARGET_BACKEND}")
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
