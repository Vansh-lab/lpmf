"""DSM ₹ calculator engine: deviation charge per 15-min block.

    C_b = min(|D|, VL) · NR / 4  +  max(|D| - VL, 0) · k · NR / 4

D = deviation from schedule (MW), VL = volume limit (MW), NR = normal rate
(₹/MWh), k = multiplier on the excess. /4 converts MW over one 15-min block
to MWh.

Always ILLUSTRATIVE: CERC DSM Regulations 2024 (Reg. 7) tie NR to grid
frequency and the DERC 2024 order sets the intra-state limits; those tables
are not encoded here, so a flat NR and one multiplier only show the shape of
the charge. Never present the output as a real penalty figure.
"""

from __future__ import annotations

import numpy as np

from lpmf.provenance import ProvenanceKind

ILLUSTRATIVE_NOTE = (
    "Illustrative only: flat normal rate and a single excess multiplier; the CERC "
    "frequency-linked normal-rate tables are not encoded."
)


def dsm_penalty(
    deviation_mw: float | np.ndarray | list[float],
    normal_rate_per_mwh: float,
    schedule_limit_mw: float,
    excess_multiplier: float = 1.5,
) -> dict:
    """Deviation charge in ₹. `deviation_mw` is one block's deviation or one
    value per 15-min block; the charge is summed over the blocks given.
    Over- and under-drawal are charged alike (|D|)."""
    for name, value in (
        ("normal_rate_per_mwh", normal_rate_per_mwh),
        ("schedule_limit_mw", schedule_limit_mw),
        ("excess_multiplier", excess_multiplier),
    ):
        if value < 0:
            raise ValueError(f"{name} must be >= 0, got {value}.")
    deviation = np.abs(np.atleast_1d(np.asarray(deviation_mw, dtype=float)))
    if not np.isfinite(deviation).all():
        raise ValueError("deviation_mw must be finite.")

    within = np.minimum(deviation, schedule_limit_mw) * normal_rate_per_mwh / 4.0
    excess = (
        np.maximum(deviation - schedule_limit_mw, 0.0)
        * excess_multiplier
        * normal_rate_per_mwh
        / 4.0
    )
    per_block = within + excess
    return {
        "penalty_rupees": float(per_block.sum()),
        "per_block_rupees": per_block.tolist(),
        "n_blocks": int(per_block.size),
        "is_illustrative": True,
        "note": ILLUSTRATIVE_NOTE,
        "provenance": ProvenanceKind.ILLUSTRATIVE,
    }
