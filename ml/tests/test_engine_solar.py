"""solar.solar_output_mw, solar.net_load_mw: formula and worked examples."""

from __future__ import annotations

import numpy as np
import pytest

from lpmf.engines.solar import DELHI_ROOFTOP_CAPACITY_MWP, net_load_mw, solar_output_mw
from lpmf.provenance import ProvenanceKind


def test_solar_output_at_stc_irradiance_equals_capacity_times_pr():
    # GHI = 1000 W/m^2 (the STC reference): output = capacity x PR exactly.
    out = solar_output_mw(1000.0, 300.0, performance_ratio=0.8)
    assert out["output_mw"] == pytest.approx(240.0)
    assert out["provenance"] == ProvenanceKind.MODELLED


def test_solar_output_scales_linearly_with_ghi():
    assert solar_output_mw(500.0, 300.0, 0.8)["output_mw"] == pytest.approx(120.0)
    assert solar_output_mw(0.0, 300.0, 0.8)["output_mw"] == pytest.approx(0.0)


def test_solar_output_clips_negative_ghi_to_zero():
    assert solar_output_mw(-5.0, 300.0)["output_mw"] == pytest.approx(0.0)


def test_solar_output_rejects_invalid_capacity_or_pr():
    with pytest.raises(ValueError):
        solar_output_mw(500.0, -1.0)
    with pytest.raises(ValueError):
        solar_output_mw(500.0, 300.0, performance_ratio=0.0)
    with pytest.raises(ValueError):
        solar_output_mw(500.0, 300.0, performance_ratio=1.5)


def test_solar_output_works_elementwise_on_a_series():
    out = solar_output_mw(np.array([0.0, 500.0, 1000.0]), 300.0, 0.8)
    assert out["output_mw"] == pytest.approx([0.0, 120.0, 240.0])


def test_net_load_subtracts_solar_from_load():
    out = net_load_mw(5000.0, 120.0)
    assert out["net_load_mw"] == pytest.approx(4880.0)
    assert out["provenance"] == ProvenanceKind.MODELLED


def test_net_load_can_go_below_load_minus_full_solar_on_a_series():
    out = net_load_mw([5000.0, 4500.0], [100.0, 240.0])
    assert out["net_load_mw"] == pytest.approx([4900.0, 4260.0])


def test_net_load_rejects_mismatched_lengths():
    with pytest.raises(ValueError):
        net_load_mw([5000.0, 4500.0], [100.0])


def test_rooftop_capacity_benchmark_is_tagged_foreign():
    # Public MNRE/Renewable Watch estimate, not a DERC-audited Delhi figure.
    assert DELHI_ROOFTOP_CAPACITY_MWP["provenance"] == ProvenanceKind.FOREIGN
    assert DELHI_ROOFTOP_CAPACITY_MWP["capacity_mwp"] == pytest.approx(302.0)
