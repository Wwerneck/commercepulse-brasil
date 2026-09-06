from pathlib import Path

from src.ingestion.indicator_config import load_economic_indicator_config


def test_load_economic_indicator_config() -> None:
    config = load_economic_indicator_config(Path("config/economic_indicators.json"))

    assert config.bcb_sgs
    assert config.bcb_sgs[0].series_code == 432
    assert config.ibge_sidra[0].table == "1737"
