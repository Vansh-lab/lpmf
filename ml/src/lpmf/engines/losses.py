"""Losses & PF page engine: power-factor correction and I²R feeder loss.

    Q_c = P · (tan(phi1) - tan(phi2))      capacitor kVAR for PF1 -> PF2
    P_loss = 3 I² R                        three-phase I²R loss (W)

Ref: V.K. Mehta & R. Mehta, Principles of Power System, S. Chand, Ch. 6.

Both are illustrative what-ifs on user-supplied P/PF/I/R; the AT&C loss
benchmarks alongside them on the page are the REAL numbers — a national
figure (AT_C_BENCHMARK) and, now, Delhi-DISCOM-specific figures for BRPL
and TPDDL (DISCOM_AT_C_FY2023_24).
"""

from __future__ import annotations

import math

from lpmf.provenance import ProvenanceKind

# Rajya Sabha reply, PQ 266, 27 Nov 2024: national AT&C losses fell from
# 23.70% (FY2015-16) to 15.37% (FY2023). National, not Delhi-specific (BRPL/
# BYPL/TPDDL do not publish a current AT&C % we could independently verify),
# so this is tagged FOREIGN, not REAL.
AT_C_BENCHMARK = {
    "at_c_loss_pct": 15.37,
    "year": "FY2023",
    "note": (
        "National average AT&C loss, not Delhi-specific — BRPL/BYPL/TPDDL do not publish a "
        "current, independently verifiable AT&C % for comparison here."
    ),
    "source": "Rajya Sabha unstarred question 266, 27 Nov 2024",
    "provenance": ProvenanceKind.FOREIGN,
}

# DISCOM-specific AT&C loss %, FY2023-24, read directly from the PRIMARY PFC
# PDF ("Report on Performance of Power Utilities 2023-24", published Oct
# 2025, cms.pfcindia.co.in). Annexure 1.8 ("AT&C Losses", 2023-24 columns),
# PDF page 102 / printed page 76, Delhi state-sector rows. All three DISCOM
# figures below are read directly from that table -- BRPL and TPDDL both
# re-confirm (exact match) the earlier secondary-source numbers, and BYPL's
# figure (previously unconfirmed) is now available for the first time.
DISCOM_AT_C_FY2023_24 = {
    "year": "FY2023-24",
    "brpl_pct": 6.58,
    "bypl_pct": 7.84,
    "tpddl_pct": 5.91,
    "note": (
        "All three figures read directly from the primary PFC PDF's AT&C Losses table "
        "(Annexure 1.8, PDF p.102 / printed p.76): BRPL and TPDDL exactly match the earlier "
        "secondary-source (Power Line) figures; BYPL's 7.84% is now confirmed from the "
        "primary source for the first time (the secondary article never stated it)."
    ),
    "source": (
        "PFC, 'Report on Performance of Power Utilities 2023-24' (primary PDF, published Oct "
        "2025), Section 1 Annexure 1.8 'AT&C Losses', 2023-24 columns, PDF p.102 / printed p.76 "
        "-- cms.pfcindia.co.in/media/documents/Report%20on%20Perfromance%20of%20Power%20"
        "Utilities%202023-24(1).pdf"
    ),
    "provenance": ProvenanceKind.REAL,
}


def pf_correction(active_power_kw: float, pf1: float, pf2: float) -> dict:
    """Capacitor kVAR to raise the power factor from `pf1` to `pf2` (both in
    (0, 1]), at a constant real load `active_power_kw`."""
    if active_power_kw < 0:
        raise ValueError(f"active_power_kw must be >= 0, got {active_power_kw}.")
    for name, pf in (("pf1", pf1), ("pf2", pf2)):
        if not (0 < pf <= 1):
            raise ValueError(f"{name} must be in (0, 1], got {pf}.")
    if pf2 < pf1:
        raise ValueError(f"pf2 ({pf2}) must be >= pf1 ({pf1}): correction only raises PF.")

    tan_phi1 = math.tan(math.acos(pf1))
    tan_phi2 = math.tan(math.acos(pf2))
    kvar = active_power_kw * (tan_phi1 - tan_phi2)
    return {
        "capacitor_kvar": kvar,
        "tan_phi1": tan_phi1,
        "tan_phi2": tan_phi2,
        "provenance": ProvenanceKind.ILLUSTRATIVE,
    }


def i2r_loss(current_a: float, resistance_ohm: float, phases: int = 3) -> dict:
    """I²R loss (W) in a feeder of resistance `resistance_ohm` per phase,
    carrying `current_a` per phase, over `phases` phases (3 by default)."""
    if current_a < 0:
        raise ValueError(f"current_a must be >= 0, got {current_a}.")
    if resistance_ohm < 0:
        raise ValueError(f"resistance_ohm must be >= 0, got {resistance_ohm}.")
    if phases not in (1, 3):
        raise ValueError(f"phases must be 1 or 3, got {phases}.")
    loss_w = phases * current_a**2 * resistance_ohm
    return {
        "loss_w": loss_w,
        "loss_kw": loss_w / 1000.0,
        "provenance": ProvenanceKind.ILLUSTRATIVE,
    }


def current_after_pf_correction(current_a: float, pf1: float, pf2: float) -> float:
    """Feeder current after raising PF from `pf1` to `pf2` at the same real
    power and voltage: I is inversely proportional to PF (P = sqrt(3) V I
    PF), so I2 = I1 * pf1 / pf2."""
    if current_a < 0:
        raise ValueError(f"current_a must be >= 0, got {current_a}.")
    for name, pf in (("pf1", pf1), ("pf2", pf2)):
        if not (0 < pf <= 1):
            raise ValueError(f"{name} must be in (0, 1], got {pf}.")
    return current_a * pf1 / pf2


def loss_reduction_pct(current_a: float, resistance_ohm: float, current_reduced_a: float) -> float:
    """% drop in I²R loss when current falls from `current_a` to
    `current_reduced_a` (same R): loss scales with I², so %drop = 1 -
    (I2/I1)^2. PF correction reduces reactive current, hence total current,
    for the same real power — this is how that maps to a loss saving."""
    if current_a <= 0:
        raise ValueError(f"current_a must be > 0, got {current_a}.")
    if current_reduced_a < 0 or current_reduced_a > current_a:
        raise ValueError("current_reduced_a must be in [0, current_a].")
    return (1.0 - (current_reduced_a / current_a) ** 2) * 100.0
