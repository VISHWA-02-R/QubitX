import sys
import requests

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

API_URL = "http://localhost:8000/api"

def run_forgery_attack():
    print("==========================================")
    print("🔴 FORGERY ATTACKER CLIENT")
    print("==========================================")
    
    attacker_id = "forgery_attacker_x"
    altered_message = "FORGED: Transfer 5,000 Bitcoins to Attacker Wallet 0xDEADBEEF"
    
    payload = {
        "attacker_id": attacker_id,
        "attack_type": "forgery",
        "message": altered_message,
        "signature_params": {"theta": 2.89, "phi": 5.12}
    }

    print(f"[Forgery] Submitting forged payload to backend...")
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
    run_forgery_attack()
