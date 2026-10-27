import sys
import requests

# Fix Windows console UTF-8 output encoding
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

API_URL = "http://localhost:8000/api"

def run_legitimate_client():
    print("==========================================")
    print("🟢 LEGITIMATE CLIENT: QDS Signature Flow")
    print("==========================================")
    
    message = "Authorize High-Security Quantum Data Exchange Protocol #8821"
    client_id = "legitimate_node_alpha"

    print(f"[Legitimate] Requesting signature parameters for message: '{message}'...")
    try:
        sign_resp = requests.post(f"{API_URL}/sign", json={"client_id": client_id, "message": message})
        sign_data = sign_resp.json()
        print(f" -> Signature State Generated: {sign_data['signature_params']}")
        
        print(f"[Legitimate] Submitting QDS teleportation verification request...")
        verify_payload = {
            "client_id": client_id,
            "message": message,
            "signature_params": sign_data["signature_params"],
            "attack_type": "none"
        }
        verify_resp = requests.post(f"{API_URL}/verify", json=verify_payload)
        res = verify_resp.json()
        
        print("\n--- VERIFICATION RESULT ---")
        print(f"Request ID:    {res['request_id']}")
        print(f"Verdict:       {res['verdict']} ✅")
        print(f"Fidelity:      {res['fidelity']} (High)")
        print(f"Anomaly Score: {res['anomaly_score']} (Threshold: {res['threshold']})")
        print(f"Details:       {res['details']}")
        print("----------------------------\n")

    except Exception as e:
        print(f"❌ Error connecting to server: {e}")

if __name__ == "__main__":
    run_legitimate_client()
