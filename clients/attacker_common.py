"""attacker_common.py -- shared helpers for all bot scripts."""
import time, uuid, random, sys, os
import numpy as np

# Ensure backend directory is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from qds_core import generate_session_key, sign_message


RNG = np.random.default_rng()


def make_legit_signature(session_id: str, identity: str, message_hash: str = "0"*64):
    key = generate_session_key(RNG, rounds=32)
    corrections = sign_message(message_hash, key, RNG, rounds=32)
    return {
        "session_id": session_id,
        "identity": identity,
        "nonce": str(uuid.uuid4()),
        "timestamp": time.time(),
        "signature_data": {
            "pauli_corrections": corrections,
            "message_hash": message_hash,
        },
    }


def make_forged_signature(session_id: str, identity: str, message_hash: str = "0"*64):
    # Biased Pauli guesses simulating adversary measurement mismatch/skew
    corrections = random.choices(["I", "X", "Y", "Z"], weights=[0.60, 0.15, 0.15, 0.10], k=32)
    return {
        "session_id": session_id,
        "identity": identity,
        "nonce": str(uuid.uuid4()),
        "timestamp": time.time(),
        "signature_data": {
            "pauli_corrections": corrections,
            "message_hash": message_hash,
        },
    }
