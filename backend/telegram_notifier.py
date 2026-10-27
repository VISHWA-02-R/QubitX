import os
import httpx

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

async def send_telegram_alert(
    attack_type: str,
    client_id: str,
    anomaly_score: float,
    threshold: float,
    fidelity: float,
    verdict: str,
    details: str
):
    """
    Sends real-time security alert notification to Telegram chat if BOT_TOKEN & CHAT_ID are configured.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[Telegram Alert Skipped] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not configured.")
        return False

    message_text = (
        f"🚨 <b>QUANTUM SECURITY ALERT</b> 🚨\n\n"
        f"<b>Attack Type:</b> {attack_type.upper()}\n"
        f"<b>Client ID:</b> <code>{client_id}</code>\n"
        f"<b>Anomaly Score:</b> {anomaly_score}\n"
        f"<b>Threshold:</b> {threshold}\n"
        f"<b>Quantum Fidelity:</b> {fidelity}\n"
        f"<b>Verdict:</b> {verdict} ❌\n\n"
        f"<b>Details:</b> {details}"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message_text,
        "parse_mode": "HTML"
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.post(url, json=payload)
            return res.status_code == 200
    except Exception as e:
        print(f"[Telegram Alert Failed] {e}")
        return False
