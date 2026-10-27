# bot_intercept.py -- runs on its own device as a relay/proxy
# Honest framing: this is an APPLICATION-LAYER relay simulating a
# compromised intermediary, not a wire-level MITM.
import argparse, httpx
from fastapi import FastAPI, Request
import uvicorn

p = argparse.ArgumentParser()
p.add_argument("--upstream", required=True)   # http://192.168.1.10:8000
p.add_argument("--port", type=int, default=8001)
args = p.parse_args()

app = FastAPI()
upstream = httpx.AsyncClient(base_url=args.upstream)

@app.post("/qds/verify")
async def intercept(request: Request):
    body = await request.json()
    corr = body["signature_data"]["pauli_corrections"]
    # tamper: flip a handful of Pauli corrections mid-transit
    for i in range(0, len(corr), 5):
        corr[i] = "X" if corr[i] != "X" else "I"
    body["signature_data"]["pauli_corrections"] = corr
    resp = await upstream.post("/qds/verify", json=body)
    return resp.json()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=args.port)
