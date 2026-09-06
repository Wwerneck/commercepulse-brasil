from src.ingestion.bcb_ingestion import build_sgs_url
from src.ingestion.ibge_ingestion import build_sidra_url


def test_build_sgs_url_uses_official_shape() -> None:
    url = build_sgs_url("https://api.bcb.gov.br/dados/serie", 432)

    assert url == "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados"


def test_build_sidra_url_uses_values_shape() -> None:
    url = build_sidra_url("https://apisidra.ibge.gov.br/values", "1737", "n1/all/v/63/p/last")

    assert url == "https://apisidra.ibge.gov.br/values/t/1737/n1/all/v/63/p/last"
