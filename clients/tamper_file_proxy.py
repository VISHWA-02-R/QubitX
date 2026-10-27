"""
tamper_file_proxy.py
Proxy server for Scenario B (File Tampering Demo).
Intercepts upload request, modifies file bytes in-transit while keeping signature unchanged,
demonstrating SHA256 integrity check rejection before QDS verification.

Run with: python clients/tamper_file_proxy.py --port 8002 --target http://localhost:8000
"""
import argparse
import sys
import httpx
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse
import uvicorn

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

TARGET_BACKEND = "http://localhost:8000"

async def tamper_file(request):
    print("[FILE PROXY] Intercepting file upload request...")
    form = await request.form()
    file_item = form.get("file")
    signature_json = form.get("signature_json")

    if not file_item or not signature_json:
        return JSONResponse({"error": "Missing file or signature_json in form data"}, status_code=400)

    file_bytes = await file_item.read()
    tampered = bytearray(file_bytes)
    
    if len(tampered) > 10:
        tampered[10] ^= 0xFF  # Flip bit pattern at byte index 10
    elif len(tampered) > 0:
        tampered[0] ^= 0xFF
    
    filename = getattr(file_item, "filename", "tampered.file")
    print(f"[FILE PROXY] Corrupted file byte 10 for '{filename}' ({len(file_bytes)} bytes)")
    print(f"[FILE PROXY] Forwarding tampered payload to defender backend ({TARGET_BACKEND})...")

    files = {"file": (filename, bytes(tampered))}
    data = {"signature_json": signature_json}

    async with httpx.AsyncClient(base_url=TARGET_BACKEND, timeout=10.0) as client:
        resp = await client.post("/files/upload-and-verify", files=files, data=data)

    return JSONResponse(status_code=resp.status_code, content=resp.json())

app = Starlette(routes=[
    Route("/files/upload-and-verify", tamper_file, methods=["POST"])
])

def main():
    global TARGET_BACKEND
    parser = argparse.ArgumentParser(description="Scenario B: File Tampering Proxy Server")
    parser.add_argument("--port", type=int, default=8002, help="Port to run proxy on (default: 8002)")
    parser.add_argument("--host", default="0.0.0.0", help="Host address (default: 0.0.0.0)")
    parser.add_argument("--target", default="http://localhost:8000", help="Target defender backend URL")
    args = parser.parse_args()

    TARGET_BACKEND = args.target.rstrip("/")
    print(f"Starting File Tamper Proxy on {args.host}:{args.port} -> Targeting {TARGET_BACKEND}")
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
