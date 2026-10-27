"""
qds_core.py
Quantum-inspired teleportation-based signature core.
Uses NumPy to model Pauli eigenstate measurement outcomes.
(Swap in Qiskit's statevector simulator for a full circuit-level
 implementation -- this module keeps the same public interface.)
"""
import numpy as np

PAULI_BASES = ["I", "X", "Y", "Z"]

# Expected outcome distribution for a LEGITIMATE teleportation round.
# In a real circuit this comes from Bell-state statistics; here it is
# the reference distribution the detector compares against.
EXPECTED_DIST = np.array([0.25, 0.25, 0.25, 0.25])


def generate_session_key(rng: np.random.Generator, rounds: int = 32):
    """Alice's secret basis choices for this signing session."""
    return rng.integers(0, 4, size=rounds)  # indices into PAULI_BASES


def sign_message(message_hash: str, session_key: np.ndarray,
                  rng: np.random.Generator, rounds: int = 32):
    """
    Simulate teleportation-based signing:
    for each round, Alice measures in a basis derived from session_key
    and the message hash, producing a Pauli-correction sequence.
    """
    seed_bits = int(message_hash[:8], 16)
    corrections = []
    for i in range(rounds):
        basis_idx = (session_key[i] + (seed_bits >> (i % 8))) % 4
        # legitimate measurement outcome follows EXPECTED_DIST
        outcome = rng.choice(4, p=EXPECTED_DIST)
        corrections.append(PAULI_BASES[(basis_idx + outcome) % 4])
    return corrections


def verify_round_distribution(observed_corrections: list) -> dict:
    """
    Projective-measurement-style verification:
    count observed Pauli outcomes and compare to EXPECTED_DIST.
    Returns counts + normalized frequencies for the detector.
    """
    counts = np.array([observed_corrections.count(b) for b in PAULI_BASES], dtype=float)
    total = counts.sum() if counts.sum() > 0 else 1
    freqs = counts / total
    return {"counts": counts.tolist(), "freqs": freqs.tolist(), "n": int(total)}
