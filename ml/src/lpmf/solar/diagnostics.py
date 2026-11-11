"""Per-inverter data-quality diagnostics for the real solar plant data:
checks for a Plant-1-style DC/AC unit mismatch, and looks for a
statistically distinguishable "faulty" subset of inverters based on their
zero-output rate during strong, unambiguous daylight -- never based on how
excluding them would affect the formula's fit (that would be cherry-
picking the data to match the model, not a data-quality decision).
"""

from __future__ import annotations

import pandas as pd

STRONG_IRRADIATION_FLOOR = 0.6  # kW/m^2: well above "any daylight" (0.1)


def dc_ac_ratio(gen: pd.DataFrame) -> float:
    """sum(AC_POWER) / sum(DC_POWER) over the whole file. Plant 1's own
    data has a ~10x DC/AC mismatch (ratio ~0.10) -- most likely a units or
    per-string-vs-per-inverter scaling quirk in that file, not a real
    ~90% inverter loss. A ratio near a plausible real inverter efficiency
    (~0.95-0.99) means no such mismatch."""
    total_dc = gen["DC_POWER"].sum()
    if total_dc == 0:
        return float("nan")
    return float(gen["AC_POWER"].sum() / total_dc)


def per_inverter_zero_rate(
    gen: pd.DataFrame,
    weather: pd.DataFrame,
    irradiation_floor: float = STRONG_IRRADIATION_FLOOR,
) -> pd.DataFrame:
    """For each inverter (SOURCE_KEY), the fraction of strong-irradiance
    blocks (IRRADIATION > `irradiation_floor`) where it reports exactly
    zero AC_POWER -- a healthy, uncurtailed inverter should essentially
    never do this. Also reports each inverter's mean AC_POWER in those
    blocks and how many such blocks it has data for (uneven coverage is
    itself a data-quality signal, e.g. late commissioning)."""
    merged = gen.merge(weather[["DATE_TIME", "IRRADIATION"]], on="DATE_TIME", how="inner")
    strong = merged[merged["IRRADIATION"] > irradiation_floor]
    out = strong.groupby("SOURCE_KEY").agg(
        n_strong_blocks=("AC_POWER", "size"),
        frac_zero_at_strong_irradiation=("AC_POWER", lambda s: float((s == 0).mean())),
        mean_ac_power_kw=("AC_POWER", "mean"),
    )
    return out.sort_values("frac_zero_at_strong_irradiation", ascending=False)


def iqr_outlier_inverters(zero_rates: pd.Series, k: float = 1.5) -> list[str]:
    """Standard Tukey IQR rule on the zero-rate distribution across
    inverters: flags an inverter only if its zero-rate sits above
    Q3 + k*IQR of the *other inverters'* own distribution -- a boundary
    set from the data's own spread, not picked to match any particular
    exclusion count or downstream fit."""
    q1, q3 = zero_rates.quantile(0.25), zero_rates.quantile(0.75)
    iqr = q3 - q1
    upper_fence = q3 + k * iqr
    return zero_rates[zero_rates > upper_fence].index.tolist()
