# bot_legit.py -- runs on Device 1
import httpx, time, argparse, sys
from pathlib import Path

# Add backend directory to sys.path to import attacker_common / qds_core if needed
sys.path.append(str(Path(__file__).parent.parent / "backend"))
from attacker_common import make_legit_signature

p = argparse.ArgumentParser()
p.add_argument("--server", required=True)      # e.g. http://192.168.1.10:8000
p.add_argument("--session", required=True)
p.add_argument("--identity", default="alice")
p.add_argument("--rate", type=float, default=1.0)
args = p.parse_args()

client = httpx.Client()
url = f"{args.server}/qds/verify"

while True:
    payload = make_legit_signature(args.session, args.identity)
    r = client.post(url, json=payload)
    print("LEGIT ->", r.json()["verdict"])
    time.sleep(1.0 / args.rate)
