"""Integration tests for the six page endpoints: a happy path and at least one
edge case each. Endpoints that read pipeline outputs skip when those outputs
have not been built (they are gitignored)."""

from __future__ import annotations

import math

import pytest
from fastapi.testclient import TestClient

from app import data
from app.main import app
from app.routers import analytics, weather

client = TestClient(app)

needs_15min = pytest.mark.skipif(not data.FIFTEEN_MIN.exists(), reason="delhi_15min not built")
needs_bands = pytest.mark.skipif(not data.BANDS.exists(), reason="conformal bands not built")


def _get(url: str, status: int = 200) -> dict:
    resp = client.get(url)
    assert resp.status_code == status, resp.text
    return resp.json()


# --- overview -----------------------------------------------------------------


@needs_bands
def test_overview_latest_day_peak_and_no_alert_below_the_record():
    body = _get("/overview")
    assert body["date"] == "2026-01-12"
    assert body["issued_at"].startswith("2026-01-11T23:45")
    assert (
        body["peak_block"] == int(body["peak_time"][:2]) * 4 + int(body["peak_time"][3:]) // 15 + 1
    )
    assert body["limit_mw"] == 8748.0 and body["alert"] is False
    assert body["provenance"] == "REAL" and body["source"]


@needs_bands
def test_overview_alerts_when_the_limit_is_below_the_peak():
    peak = _get("/overview?date=2025-07-28")["peak_mw"]
    assert _get(f"/overview?date=2025-07-28&limit_mw={peak - 1}")["alert"] is True
    assert _get(f"/overview?date=2025-07-28&limit_mw={peak}")["alert"] is False


@needs_bands
def test_overview_unknown_day_and_bad_limit():
    assert "test days run" in _get("/overview?date=2024-01-01", 404)["detail"]
    _get("/overview?limit_mw=0", 422)


# --- analytics ----------------------------------------------------------------


@needs_15min
def test_analytics_full_series_lf_par_and_ldc_shape():
    body = _get("/analytics")
    assert body["load_factor"] == pytest.approx(body["p_avg_mw"] / body["p_max_mw"])
    assert body["par"] == pytest.approx(1 / body["load_factor"])
    ldc = body["load_duration_curve"]
    assert len(ldc) == 101 and ldc[0]["rank_pct"] == 0 and ldc[-1]["rank_pct"] == 100
    assert ldc[0]["load_mw"] == body["p_max_mw"]
    loads = [p["load_mw"] for p in ldc]
    assert loads == sorted(loads, reverse=True)
    assert body["provenance"] == "REAL"


@needs_15min
def test_analytics_one_day_and_point_count():
    body = _get("/analytics?start=2025-06-12&end=2025-06-12&points=11")
    assert body["n_blocks"] <= 96 and len(body["load_duration_curve"]) == 11
    assert 0 < body["load_factor"] <= 1


@needs_15min
def test_analytics_bad_ranges():
    _get("/analytics?start=2025-01-02&end=2025-01-01", 422)
    _get("/analytics?start=2030-01-01&end=2030-01-02", 404)
    _get("/analytics?points=1", 422)


# --- weather ------------------------------------------------------------------


@needs_15min
def test_weather_beta_matches_the_engine_and_scatter_is_daily():
    body = _get("/weather")
    assert round(body["beta_mw_per_c"], 1) == 112.0
    assert 0 < body["r_squared"] < 1
    assert body["scatter_granularity"] == "daily_mean"
    days = [p["date"] for p in body["scatter"]]
    assert len(days) == len(set(days)) and 900 < len(days) < 1100
    assert body["provenance"] == "REAL"


def test_weather_without_built_data_is_503(monkeypatch, tmp_path):
    monkeypatch.setattr(data, "FIFTEEN_MIN", tmp_path / "missing.parquet")
    data.fifteen_min.cache_clear()
    weather._weather.cache_clear()
    try:
        assert "missing" in _get("/weather", 503)["detail"]
    finally:
        monkeypatch.undo()
        data.fifteen_min.cache_clear()
        weather._weather.cache_clear()
        analytics._analytics.cache_clear()


# --- forecast -----------------------------------------------------------------


@needs_bands
def test_forecast_shap_day_has_96_blocks_band_and_top5():
    body = _get("/forecast?date=2025-10-20")
    blocks = body["blocks"]
    assert [b["block"] for b in blocks] == list(range(1, 97))
    assert all(b["p10_mw"] <= b["predicted_mw"] <= b["p90_mw"] for b in blocks)
    assert body["band"]["confidence_level"] == 0.8
    assert 0.8 < body["band"]["empirical_test_coverage"] < 0.9
    shap = body["shap"]
    assert shap["day_label"] == "festival" and len(shap["top_contributors"]) == 5
    assert shap["top_contributors"][0]["feature"] == "tlag_1day"
    assert body["provenance"] == "REAL"


@needs_bands
def test_forecast_dates_and_a_day_without_shap():
    dates = _get("/forecast/dates")
    assert dates["dates"][0] == "2025-07-13" and dates["dates"][-1] == "2026-01-12"
    assert dates["shap_dates"]["festival"] == "2025-10-20"
    assert _get("/forecast?date=2025-12-01")["shap"] is None


@needs_bands
def test_forecast_outside_the_test_set_is_404():
    assert "/forecast/dates" in _get("/forecast?date=2025-01-01", 404)["detail"]
    _get("/forecast?date=not-a-date", 422)


# --- dsm ----------------------------------------------------------------------


def test_dsm_defaults_reproduce_the_deck_example():
    body = _get("/dsm")
    assert body["penalty_rupees"] == 347_500.0
    assert body["per_block_rupees"] == [86_875.0] * 4
    assert body["is_illustrative"] is True and body["provenance"] == "ILLUSTRATIVE"


def test_dsm_within_limit_and_invalid_inputs():
    within = _get("/dsm?deviation_mw=15&blocks=1")
    assert within["penalty_rupees"] == 15 * 5000 / 4 and within["is_illustrative"] is True
    _get("/dsm?schedule_limit_mw=-1", 422)
    _get("/dsm?deviation_mw=nan", 422)
    _get("/dsm?blocks=0", 422)


# --- transformer --------------------------------------------------------------


def test_transformer_default_is_the_deck_118c_case():
    body = _get("/transformer")
    assert body["ageing_rate_v"] == pytest.approx(2 ** (20 / 6))
    assert body["life_hours_used"] == pytest.approx(body["ageing_rate_v"])
    assert body["provenance"] == "ILLUSTRATIVE"


def test_transformer_hours_scale_life_used():
    body = _get("/transformer?hotspot_temp_c=104&hours=2")
    assert body["ageing_rate_v"] == pytest.approx(2.0) and body["life_hours_used"] == 4.0


@pytest.mark.parametrize("query", ["hotspot_temp_c=400", "hotspot_temp_c=-100", "hours=0"])
def test_transformer_out_of_range_inputs_are_422(query):
    _get(f"/transformer?{query}", 422)


def test_every_page_response_carries_provenance():
    for url in ("/dsm", "/transformer"):
        assert _get(url)["provenance"] in {"REAL", "SYNTHETIC", "FOREIGN", "ILLUSTRATIVE"}
    assert not math.isnan(_get("/dsm")["penalty_rupees"])
