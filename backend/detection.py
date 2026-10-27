"""
detection.py
Non-AI statistical threat detection engine.
- Multi-round chi-square goodness-of-fit test (fixes single-sample issue)
- Identity binding check (separates impersonation from forgery)
- Nonce + timestamp replay defense with an asyncio lock (concurrency-safe)
"""
import time
import asyncio
from scipy import stats
import numpy as np
from qds_core import EXPECTED_DIST, verify_round_distribution

CHI2_REJECT_THRESHOLD = 7.815   # df=3, alpha=0.05
REPLAY_WINDOW_SECONDS = 30

_seen_nonces: dict[str, float] = {}
_nonce_lock = asyncio.Lock()


async def check_replay(nonce: str, timestamp: float) -> dict:
    """Reject reused nonces and stale timestamps (thread/async-safe)."""
    now = time.time()
    async with _nonce_lock:
        # purge old entries
        expired = [n for n, t in _seen_nonces.items() if now - t > REPLAY_WINDOW_SECONDS]
        for n in expired:
            _seen_nonces.pop(n, None)

        if abs(now - timestamp) > REPLAY_WINDOW_SECONDS:
            return {"replay": True, "reason": "stale timestamp"}
        if nonce in _seen_nonces:
            return {"replay": True, "reason": "nonce reused"}

        _seen_nonces[nonce] = now
        return {"replay": False, "reason": None}


def check_identity_binding(claimed_identity: str, session_registry: dict, session_id: str) -> dict:
    """Separate impersonation detection from signature-forgery detection."""
    expected_identity = session_registry.get(session_id, {}).get("identity")
    if expected_identity is None:
        return {"impersonation": True, "reason": "unknown session"}
    if claimed_identity != expected_identity:
        return {"impersonation": True, "reason": "identity mismatch"}
    return {"impersonation": False, "reason": None}


def statistical_forgery_test(observed_corrections: list) -> dict:
    """
    Multi-round chi-square goodness-of-fit test against EXPECTED_DIST.
    Requires >= 20 rounds for the test to be statistically meaningful.
    """
    result = verify_round_distribution(observed_corrections)
    counts = np.array(result["counts"])
    n = result["n"]

    if n < 20:
        return {"forged": True, "reason": "insufficient rounds for valid test",
                "chi2": None, "p_value": None, "n_rounds": n}

    expected_counts = EXPECTED_DIST * n
    chi2, p_value = stats.chisquare(counts, f_exp=expected_counts)

    forged = chi2 > CHI2_REJECT_THRESHOLD
    forgery_probability = 1 - stats.chi2.cdf(chi2, df=3) if not forged else min(0.99, chi2 / 20)

    return {
        "forged": bool(forged),
        "chi2": float(chi2),
        "p_value": float(p_value),
        "forgery_probability": float(forgery_probability),
        "n_rounds": n,
    }


async def evaluate_request(payload: dict, session_registry: dict) -> dict:
    """Top-level detection pipeline combining all three checks."""
    sig = payload["signature_data"]

    replay = await check_replay(payload["nonce"], payload["timestamp"])
    identity = check_identity_binding(payload["identity"], session_registry, payload["session_id"])
    stats_result = statistical_forgery_test(sig["pauli_corrections"])

    if replay["replay"]:
        verdict, attack_type = "REJECT", "REPLAY"
    elif identity["impersonation"]:
        verdict, attack_type = "REJECT", "IMPERSONATION"
    elif stats_result["forged"]:
        verdict, attack_type = "REJECT", "FORGERY"
    else:
        verdict, attack_type = "ACCEPT", None

    return {
        "verdict": verdict,
        "attack_type": attack_type,
        "replay_check": replay,
        "identity_check": identity,
        "statistical_check": stats_result,
    }
