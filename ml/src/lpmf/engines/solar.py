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
    return {
        "plant_1": data["plant_1"],
        "plant_2": data["plant_2"],
        "provenance": ProvenanceKind.FOREIGN,
        "note": (
            "Real paired irradiance/power data from an Indian solar plant (not Delhi) -- "
            "validates the formula's functional form before it's applied to Delhi's real "
            "Open-Meteo GHI. Plant 2's much weaker fit was not independently root-caused here; "
            "plausibly inverter downtime or sensor gaps in this public dataset, not necessarily "
            "a problem with the formula itself (Plant 1 fits it very well)."
        ),
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
