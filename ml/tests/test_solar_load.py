"""solar.load: per-plant generation/weather merge, sums AC_POWER over inverters."""

from __future__ import annotations

from lpmf.solar.load import load_plant


def test_load_plant_1_sums_inverters_and_merges_weather(tmp_path):
    (tmp_path / "Plant_1_Generation_Data.csv").write_text(
        "DATE_TIME,PLANT_ID,SOURCE_KEY,DC_POWER,AC_POWER,DAILY_YIELD,TOTAL_YIELD\n"
        "15-05-2020 00:00,1,invA,0,100.0,0,0\n"
        "15-05-2020 00:00,1,invB,0,150.0,0,0\n"
        "15-05-2020 00:15,1,invA,0,200.0,0,0\n"
        "15-05-2020 00:15,1,invB,0,250.0,0,0\n"
    )
    (tmp_path / "Plant_1_Weather_Sensor_Data.csv").write_text(
        "DATE_TIME,PLANT_ID,SOURCE_KEY,AMBIENT_TEMPERATURE,MODULE_TEMPERATURE,IRRADIATION\n"
        "2020-05-15 00:00:00,1,w,25.0,26.0,0.1\n"
        "2020-05-15 00:15:00,1,w,25.0,26.0,0.2\n"
    )
    ds = load_plant(1, raw_dir=tmp_path)
    assert ds.plant == 1
    assert len(ds.merged) == 2
    assert ds.merged["ac_power_kw"].tolist() == [250.0, 450.0]
    assert ds.merged["irradiation_kw_m2"].tolist() == [0.1, 0.2]


def test_load_plant_rejects_invalid_plant_number(tmp_path):
    import pytest

    with pytest.raises(ValueError):
        load_plant(3, raw_dir=tmp_path)
