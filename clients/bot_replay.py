# bot_replay.py -- runs on Device 2
# Captures one legit payload once, then resends it verbatim on a loop.
import httpx, time, argparse, sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "backend"))
from attacker_common import make_legit_signature

p = argparse.ArgumentParser()
p.add_argument("--server", required=True)
p.add_argument("--session", required=True)
p.add_argument("--identity", default="alice")
args = p.parse_args()

client = httpx.Client()
url = f"{args.server}/qds/verify"

captured = make_legit_signature(args.session, args.identity)
client.post(url, json=captured)          # first send: ACCEPT
print("captured payload sent once (should ACCEPT)")

time.sleep(3)
r = client.post(url, json=captured)      # resend: should be REJECT / REPLAY
print("REPLAY ->", r.json())
