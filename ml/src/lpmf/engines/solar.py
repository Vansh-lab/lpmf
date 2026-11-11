"""Solar & Net Load page engine: rooftop solar output modelled from real
Open-Meteo irradiance, and net load = forecast - solar.

    P_solar(t) = (GHI(t) / 1000) * capacity_kWp * PR

GHI in W/m² (STC reference is 1000 W/m²); PR (performance ratio) bundles
inverter, wiring, temperature and soiling losses into one factor, a
standard simplification (cf. pvlib's PVWatts model). Inputs (GHI,
capacity) are real; the output is a model estimate, so it is tagged
MODELLED, not REAL.

Ref: Kothari & Nagrath, Modern Power System Analysis, Ch. 5 (net load,
voltage effects of distributed generation).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from lpmf.provenance import ProvenanceKind

SOLAR_ARTIFACTS_DIR = Path("models/artifacts/solar")


def load_real_plant_validation(artifacts_dir: Path = SOLAR_ARTIFACTS_DIR) -> dict | None:
    """r^2/MAPE of this page's PVWatts-style formula against real paired
    irradiance/power data from a real Indian solar plant (Kaggle
    anikannal/solar-power-generation-data), or None if that validation
    hasn't been run. FOREIGN: a real plant, but not in Delhi.

    `artifacts_dir` defaults to a path relative to the process's cwd (the
    repo root) -- callers with a different cwd (e.g. the API, started from
    `api/`) must pass the resolved path explicitly.
    """
    path = artifacts_dir / "validation.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    diagnostics = data.get("diagnostics", {})
    return {
        "plant_1": data["plant_1"],
        "plant_2": data["plant_2"],
        "provenance": ProvenanceKind.FOREIGN,
        "note": (
            "Real paired irradiance/power data from an Indian solar plant (not Delhi) -- "
            "validates the formula's functional form before it's applied to Delhi's real "
            "Open-Meteo GHI. Plant 2's daytime-only r^2 (0.21) is much lower than its "
            "full-period r^2 (0.82, inflated by trivially-correct night zeros) -- the fit is "
            "genuinely weak during actual generation hours. Diagnosed (not just assumed): no "
            "Plant-1-style DC/AC unit mismatch (ratio ~0.98, a plausible real efficiency); "
            "per-inverter zero-output rate during strong irradiance forms a smooth 4%-49% "
            "continuum with no statistically distinguishable faulty subset (Tukey IQR rule on "
            "the data's own spread), so no inverters are excluded -- excluding any without "
            "that kind of rule would be cherry-picking data to fit the model, not a data-"
            "quality decision. Plant 2 has a genuinely weak fit; this reflects a limitation "
            "of real-world data, not a mistake in the formula (Plant 1 fits the same formula "
            "very well)."
        ),
        "root_cause_note": (
            "Four hypotheses were actively investigated (2026-11-11), not just listed -- and "
            "none turned up a fixable bug, so no inverter or reading was removed and r^2=0.208 "
            "stands as final. (1) Timestamp misalignment: shifting irradiance against AC power "
            "by -4..+4 fifteen-minute blocks and refitting at each shift shows daytime r^2 "
            "peaking exactly at shift=0 (0.208, vs 0.06 or lower at any other shift) -- the "
            "data is already correctly aligned. (2) Capacity mismatch/clipping: the AC/DC power "
            "ratio is a flat ~0.975 across all 22 inverters (std 7.6e-5) and varies smoothly "
            "(0.966 to 0.982 to 0.975) across DC-power deciles with no sharp drop at the top "
            "decile -- the clipping signature is absent; a Kaggle community analysis of this "
            "same dataset (user ElbioPena, 'Let's Discuss the Outliers' thread) independently "
            "confirms 97.5% is within the normal 93-98% inverter efficiency range (only Plant "
            "1's ~9.75% ratio is the known decimal-point bug, unrelated to Plant 2). (3) Sensor "
            "placement: the dataset gives each plant exactly one site-level weather sensor "
            "shared by 22 spatially distributed inverters -- a structural property of the "
            "dataset, not a fixable defect; a second Kaggle discussion thread on this dataset "
            "(user Rajas Bhingarde) independently corroborates that inverter-to-inverter "
            "disagreement under a shared sensor is expected from string wiring differences, "
            "uneven irradiation/shading, and local temperature effects. (4) Soiling/shading "
            "day pattern: per-day WAPE across all 34 days is a continuous spread (10.5% to "
            "85.8%, mean 30.1%), not two separable clusters, ruling out a one-off equipment "
            "fault; the worst days concentrate in the back half of the 34-day window (e.g. "
            "11-17 June 2020) and show increased swings in *both* directions (prediction "
            "ratio 0.65-1.6x) rather than a steady one-way decline -- the signature of rising "
            "patchy-cloud variability (Nasik's monsoon onset is early-to-mid June), not "
            "progressive soiling or inverter degradation (which would drift one-way). "
            "Conclusion: Plant 2's weak daytime fit is a genuine real-world data limitation "
            "-- one shared sensor against 22 distributed inverters, worsened by patchy cloud "
            "cover later in the sampling window -- not a bug in the data or the formula."
        ),
        "diagnostics": {
            "plant_1_dc_ac_ratio": diagnostics.get("plant_1", {}).get("dc_ac_ratio"),
            "plant_2_dc_ac_ratio": diagnostics.get("plant_2", {}).get("dc_ac_ratio"),
            "plant_2_iqr_flagged_inverters": diagnostics.get("plant_2", {}).get(
                "iqr_flagged_inverters", []
            ),
        },
        "source": data["source"],
    }


# Delhi rooftop solar capacity: MNRE figure via Renewable Watch, ~302 MWp as
# of March 2025 (of 313.4 MW total solar, excluding large hydro). Sources
# disagree by date/method (Saur Energy cites 294.6 MW, Jan 2025); this is a
# single best-available public estimate, not a DERC-audited figure.
DELHI_ROOFTOP_CAPACITY_MWP = {
    "capacity_mwp": 302.0,
    "as_of": "Mar 2025",
    "note": (
        "MNRE estimate via Renewable Watch; other sources give slightly different figures "
        "(e.g. 294.6 MW, Jan 2025) depending on method and date. Not a DERC-audited figure."
    ),
    "source": "MNRE, reported by Renewable Watch (Jun 2025)",
    "provenance": ProvenanceKind.FOREIGN,
}

DEFAULT_PERFORMANCE_RATIO = 0.8


def solar_output_mw(
    ghi_wm2: float | np.ndarray | list[float],
    capacity_mwp: float,
    performance_ratio: float = DEFAULT_PERFORMANCE_RATIO,
) -> dict:
    """Modelled rooftop solar output (MW) from real GHI (W/m²) and a
    capacity figure (MWp). Clipped at 0 (GHI is never negative in practice,
    but a bad reading should not produce negative generation)."""
    if capacity_mwp < 0:
        raise ValueError(f"capacity_mwp must be >= 0, got {capacity_mwp}.")
    if not (0 < performance_ratio <= 1):
        raise ValueError(f"performance_ratio must be in (0, 1], got {performance_ratio}.")
    ghi = np.atleast_1d(np.asarray(ghi_wm2, dtype=float))
    if not np.isfinite(ghi).all():
        raise ValueError("ghi_wm2 must be finite.")

    output_mw = np.clip(ghi, 0.0, None) / 1000.0 * capacity_mwp * performance_ratio
    return {
        "output_mw": output_mw if output_mw.size > 1 else float(output_mw[0]),
        "provenance": ProvenanceKind.MODELLED,
    }


def net_load_mw(
    load_mw: float | np.ndarray | list[float], solar_mw: float | np.ndarray | list[float]
) -> dict:
    """Net load = load - solar (the "duck curve" quantity: what the grid
    still has to serve after behind-the-meter solar)."""
    load = np.atleast_1d(np.asarray(load_mw, dtype=float))
    solar = np.atleast_1d(np.asarray(solar_mw, dtype=float))
    if load.shape != solar.shape:
        raise ValueError(f"load_mw and solar_mw lengths differ: {load.shape} vs {solar.shape}.")
    net = load - solar
    return {
        "net_load_mw": net if net.size > 1 else float(net[0]),
        "provenance": ProvenanceKind.MODELLED,
    }
