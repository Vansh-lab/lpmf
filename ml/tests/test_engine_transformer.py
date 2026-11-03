"""transformer: IEC 60076-7 ageing against the PPT worked example
(slide 7: "40 °C, full load -> 10x"; slide 4: "Hot-spot 118 °C, ageing 10x")."""

from __future__ import annotations

import pytest

from lpmf.engines.transformer import steady_state_hotspot_c, transformer_ageing
from lpmf.provenance import ProvenanceKind


def test_ppt_example_40c_full_load_gives_hotspot_118c():
    assert steady_state_hotspot_c(40.0, 1.0) == pytest.approx(118.0)


def test_ppt_example_hotspot_118c_ages_about_10x():
    v = transformer_ageing(118.0)["ageing_rate_v"]
    assert v == pytest.approx(2 ** (20 / 6))
    assert round(v) == 10


def test_reference_point_and_six_degree_doubling():
    assert transformer_ageing(98.0)["ageing_rate_v"] == pytest.approx(1.0)
    assert transformer_ageing(104.0)["ageing_rate_v"] == pytest.approx(2.0)
    assert transformer_ageing(92.0)["ageing_rate_v"] == pytest.approx(0.5)


def test_rated_load_at_20c_reference_ambient_is_98c():
    assert steady_state_hotspot_c(20.0, 1.0) == pytest.approx(98.0)


def test_life_used_sums_v_over_the_hours():
    out = transformer_ageing([98.0, 104.0, 110.0, 118.0])
    assert out["life_hours_used"] == pytest.approx(1 + 2 + 4 + 2 ** (20 / 6))
    assert out["hours_elapsed"] == 4.0
    half_hourly = transformer_ageing([104.0, 104.0], hours_per_step=0.5)
    assert half_hourly["life_hours_used"] == pytest.approx(2.0)


def test_part_load_runs_cooler_than_rated():
    assert steady_state_hotspot_c(40.0, 0.5) < steady_state_hotspot_c(40.0, 1.0)


def test_provenance_follows_the_input():
    assert transformer_ageing(118.0)["provenance"] == ProvenanceKind.REAL
    out = transformer_ageing(118.0, provenance=ProvenanceKind.SYNTHETIC)
    assert out["provenance"] == ProvenanceKind.SYNTHETIC


def test_rejects_non_finite_temperatures_and_bad_steps():
    with pytest.raises(ValueError):
        transformer_ageing(float("nan"))
    with pytest.raises(ValueError):
        transformer_ageing(118.0, hours_per_step=0.0)
