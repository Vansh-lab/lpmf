"""Transformer health page engine: insulation ageing from hot-spot temperature
(IEC 60076-7:2018, loading guide for oil-immersed power transformers).

    V = 2 ^ ((θ_h - 98) / 6)          relative ageing rate (non-upgraded paper)
    life used = Σ V · Δt              equivalent hours at the 98 °C reference

Steady-state hot-spot (IEC 60076-7 difference equations at equilibrium):

    θ_h = θ_a + Δθ_or · ((1 + R·K²) / (1 + R))^x + H·g_r · K^y

Defaults are the standard's distribution-transformer ONAN characteristics
(Δθ_or = 55 K, H·g_r = 23 K, R = 5, x = 0.8, y = 1.6). At rated load (K = 1)
the hot-spot sits 78 K above ambient, which is what puts it at 98 °C for the
20 °C reference ambient; R, x and y only matter at part or over load.
"""

from __future__ import annotations

import numpy as np

from lpmf.provenance import ProvenanceKind

REFERENCE_HOTSPOT_C = 98.0
DOUBLING_STEP_K = 6.0


def steady_state_hotspot_c(
    ambient_c: float | np.ndarray,
    load_pu: float | np.ndarray = 1.0,
    *,
    top_oil_rise_k: float = 55.0,
    hotspot_gradient_k: float = 23.0,
    loss_ratio_r: float = 5.0,
    oil_exponent_x: float = 0.8,
    winding_exponent_y: float = 1.6,
) -> float | np.ndarray:
    k = np.asarray(load_pu, dtype=float)
    oil = top_oil_rise_k * ((1 + loss_ratio_r * k**2) / (1 + loss_ratio_r)) ** oil_exponent_x
    hotspot = np.asarray(ambient_c, dtype=float) + oil + hotspot_gradient_k * k**winding_exponent_y
    return float(hotspot) if hotspot.ndim == 0 else hotspot


def transformer_ageing(
    hotspot_temp_c: float | np.ndarray | list[float],
    *,
    hours_per_step: float = 1.0,
    provenance: ProvenanceKind = ProvenanceKind.REAL,
) -> dict:
    """Ageing rate V for each hot-spot value and the insulation life used,
    in equivalent hours at 98 °C, treating each value as lasting
    `hours_per_step` hours."""
    theta = np.asarray(hotspot_temp_c, dtype=float)
    if not np.isfinite(theta).all():
        raise ValueError("hotspot_temp_c must be finite.")
    if hours_per_step <= 0:
        raise ValueError(f"hours_per_step must be > 0, got {hours_per_step}.")
    v = 2.0 ** ((theta - REFERENCE_HOTSPOT_C) / DOUBLING_STEP_K)
    return {
        "ageing_rate_v": float(v) if v.ndim == 0 else v.tolist(),
        "life_hours_used": float(v.sum() * hours_per_step),
        "hours_elapsed": float(v.size * hours_per_step),
        "provenance": provenance,
    }
