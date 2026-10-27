"""
sender_client.py
Sender client for QDS File Sharing Demo.
Hashes input file, generates QDS quantum state signature, and submits file + signature
to the QubitX /files/upload-and-verify endpoint directly or via a proxy server.
"""
import hashlib
import json
import argparse
import sys
import os
import httpx

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure attacker_common can be imported
sys.path.append(os.path.dirname(__file__))
from attacker_common import make_legit_signature

def main():
    parser = argparse.ArgumentParser(description="QDS File Sharing Demo Sender Client")
    parser.add_argument("--server", required=True, help="Target server URL (e.g. http://localhost:8000)")
    parser.add_argument("--file", required=True, help="Path to file to upload")
    parser.add_argument("--session", default="sess_demo1", help="Session ID (default: sess_demo1)")
    parser.add_argument("--identity", default="alice", help="Client Identity (default: alice)")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: File not found: {args.file}")
        sys.exit(1)

    filename = os.path.basename(args.file)
    with open(args.file, "rb") as f:
        file_bytes = f.read()

    file_hash = hashlib.sha256(file_bytes).hexdigest()
    signature_payload = make_legit_signature(args.session, args.identity, message_hash=file_hash)

    files = {"file": (filename, file_bytes)}
    data = {"signature_json": json.dumps(signature_payload)}

    server_url = args.server.rstrip("/")
    target_endpoint = f"{server_url}/files/upload-and-verify"

    print(f"[SENDER] Preparing QDS File Transfer: '{filename}' ({len(file_bytes)} bytes)")
    print(f"[SENDER] SHA256 Hash: {file_hash[:16]}...")
    print(f"[SENDER] Identity: '{args.identity}' | Session: '{args.session}'")
    print(f"[SENDER] Sending request to: {target_endpoint} ...\n")

    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.post(target_endpoint, files=files, data=data)
        
        if r.status_code not in (200, 403):
            print(f"Server returned status code: {r.status_code}")
            print("Response:", r.text)
            return

        res = r.json()
        verdict = res.get("verdict", "UNKNOWN")
        integrity_ok = res.get("integrity_ok", False)
        attack_type = res.get("attack_type", "none")
        chi2 = res.get("result", {}).get("anomaly_score") or res.get("statistical_check", {}).get("chi2")
        details = res.get("result", {}).get("details") or res.get("details", "")

        status_symbol = "ACCEPT" if verdict == "ACCEPT" else "REJECT"

        print("==================================================")
        print(f"SENT -> Verdict: {status_symbol} {verdict} | integrity_ok: {integrity_ok}")
        print(f"Attack Type Detected: {attack_type}")
        print(f"Chi-Square Anomaly Score: {chi2} (Threshold: 7.815)")
        print(f"Server Details: {details}")
        print("==================================================")

    except Exception as e:
        print(f"Connection Failed: {e}")

if __name__ == "__main__":
    main()
