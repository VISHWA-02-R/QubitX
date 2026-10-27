# bot_forge.py -- runs on Device 3
import httpx, time, argparse, sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "backend"))
from attacker_common import make_forged_signature

p = argparse.ArgumentParser()
p.add_argument("--server", required=True)
p.add_argument("--session", required=True)
p.add_argument("--identity", default="alice")
p.add_argument("--rate", type=float, default=0.7)
args = p.parse_args()

client = httpx.Client()
url = f"{args.server}/qds/verify"

while True:
    payload = make_forged_signature(args.session, args.identity)
    r = client.post(url, json=payload)
    print("FORGE ->", r.json()["verdict"], r.json()["statistical_check"])
    time.sleep(1.0 / args.rate)
