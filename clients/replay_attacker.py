import sys
import requests

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

API_URL = "http://localhost:8000/api"

def run_replay_attack():
    print("==========================================")
    print("🔴 REPLAY ATTACKER CLIENT")
    print("==========================================")
    
    attacker_id = "replay_attacker_bot"
    replayed_message = "Authorize High-Security Quantum Data Exchange Protocol #8821"
    
    payload = {
        "attacker_id": attacker_id,
        "attack_type": "replay",
        "message": replayed_message,
        "signature_params": {"theta": 1.047, "phi": 0.785}
    }

    print(f"[Replay] Re-sending stale quantum signature parameters...")
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
    run_replay_attack()
