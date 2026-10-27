import sys
import time
import random
import requests

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

API_URL = "http://localhost:8000/api"

ATTACK_TYPES = ["none", "forgery", "replay", "impersonation", "intercept_resend"]
CLIENT_NAMES = ["legitimate_alpha", "legitimate_beta", "forger_x", "replay_bot", "impersonator_zero", "eve_interceptor"]

MESSAGES = [
    "Transfer $50,000 to Account #991",
    "Authorize Quantum Key Distribution",
    "Update Core Security Policy v2.4",
    "Request Secret Teleportation Payload",
    "Heartbeat Status Ping"
]

def run_simulation(count=20, interval=1.5):
    print(f"🚀 Starting Batch Simulation ({count} requests at {interval}s interval)...")
    for i in range(count):
        is_attack = random.random() > 0.6
        attack_type = random.choice(["forgery", "replay", "impersonation", "intercept_resend"]) if is_attack else "none"
        client_id = f"node_{random.choice(CLIENT_NAMES)}"
        message = random.choice(MESSAGES)
        
        sign_resp = requests.post(f"{API_URL}/sign", json={"client_id": client_id, "message": message}).json()
        sig_params = sign_resp["signature_params"]
        
        if is_attack:
            sig_params["theta"] = round(sig_params["theta"] * random.uniform(1.8, 3.5), 3)

        payload = {
            "client_id": client_id,
            "message": message,
            "signature_params": sig_params,
            "attack_type": attack_type
        }

        res = requests.post(f"{API_URL}/verify", json=payload).json()
        print(f"[{i+1}/{count}] [{attack_type.upper():<16}] Score: {res['anomaly_score']:>5.2f} | Verdict: {res['verdict']}")
        time.sleep(interval)

if __name__ == "__main__":
    run_simulation(count=30, interval=1.2)
