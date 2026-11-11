"""solar.solar_output_mw, solar.net_load_mw: formula and worked examples."""

from __future__ import annotations

import numpy as np
import pytest

from lpmf.engines.solar import (
    DELHI_ROOFTOP_CAPACITY_MWP,
    load_real_plant_validation,
    net_load_mw,
    solar_output_mw,
)
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


def test_load_real_plant_validation_returns_none_when_artifacts_are_missing(tmp_path):
    assert load_real_plant_validation(tmp_path / "does-not-exist") is None


def test_load_real_plant_validation_loads_and_shapes_the_real_artifact(tmp_path):
    import json

    data = {
        "plant_1": {
            "plant": 1,
            "r_squared": 0.99,
            "r_squared_daytime": 0.97,
            "mape_daytime_pct": 6.3,
        },
        "plant_2": {
            "plant": 2,
            "r_squared": 0.82,
            "r_squared_daytime": 0.21,
            "mape_daytime_pct": 36.0,
        },
        "source": "Kaggle anikannal/solar-power-generation-data",
        "diagnostics": {
            "plant_1": {"dc_ac_ratio": 0.098, "iqr_flagged_inverters": ["a", "b"]},
            "plant_2": {"dc_ac_ratio": 0.978, "iqr_flagged_inverters": []},
        },
    }
    (tmp_path / "validation.json").write_text(json.dumps(data))

    out = load_real_plant_validation(tmp_path)

    assert out["provenance"] == ProvenanceKind.FOREIGN
    assert out["plant_1"]["r_squared"] == pytest.approx(0.99)
    assert out["plant_2"]["mape_daytime_pct"] == pytest.approx(36.0)
    assert out["diagnostics"]["plant_1_dc_ac_ratio"] == pytest.approx(0.098)
    assert out["diagnostics"]["plant_2_dc_ac_ratio"] == pytest.approx(0.978)
    assert out["diagnostics"]["plant_2_iqr_flagged_inverters"] == []
    assert "weak fit" in out["note"]
    assert "Sensor placement" in out["root_cause_note"]
    assert "clipping" in out["root_cause_note"]
    assert "Soiling/shading" in out["root_cause_note"]
    assert "Timestamp misalignment" in out["root_cause_note"]
