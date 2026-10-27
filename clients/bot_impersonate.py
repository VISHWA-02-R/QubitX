# bot_impersonate.py -- runs on Device 4
import httpx, time, argparse, sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "backend"))
from attacker_common import make_legit_signature

p = argparse.ArgumentParser()
p.add_argument("--server", required=True)
p.add_argument("--session", required=True)
p.add_argument("--fake-identity", default="bob")
args = p.parse_args()

client = httpx.Client()
url = f"{args.server}/qds/verify"

payload = make_legit_signature(args.session, args.fake_identity if hasattr(args, 'fake_identity') else "bob")
r = client.post(url, json=payload)
print("IMPERSONATE ->", r.json())
