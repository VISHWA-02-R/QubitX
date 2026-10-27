import sys
import requests

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

API_URL = "http://localhost:8000/api"

def run_impersonation_attack():
    print("==========================================")
    print("🔴 IMPERSONATION ATTACKER CLIENT")
    print("==========================================")
    
    attacker_id = "impersonator_fake_alice"
    message = "Request Admin Privilege Escalation"
    
    payload = {
        "attacker_id": attacker_id,
        "attack_type": "impersonation",
        "message": message,
        "signature_params": {"theta": 3.14, "phi": 1.57}
    }

    print(f"[Impersonation] Attempting unauthorized verification with mismatched Bell basis...")
    try:
        res = requests.post(f"{API_URL}/attack", json=payload).json()
        print("\n--- ATTACK DETECTION RESULT ---")
        print(f"Verdict:       {res['verdict']} ❌")
        print(f"Status Code:   {res['status_code']}")
        print(f"Fidelity:      {res['fidelity']}")
        print(f"Anomaly Score: {res['anomaly_score']} (Threshold: {res['threshold']})")
        print(f"Details:       {res['details']}")
        print("--------------------------------\n")
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")

if __name__ == "__main__":
    run_impersonation_attack()
