import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BcbSgsIndicator:
    name: str
    series_code: int
    description: str
    frequency: str


@dataclass(frozen=True)
class SidraIndicator:
    name: str
    table: str
    path: str
    description: str


@dataclass(frozen=True)
class EconomicIndicatorConfig:
    bcb_sgs: list[BcbSgsIndicator]
    ibge_sidra: list[SidraIndicator]


def load_economic_indicator_config(path: Path) -> EconomicIndicatorConfig:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return EconomicIndicatorConfig(
        bcb_sgs=[BcbSgsIndicator(**item) for item in payload.get("bcb_sgs", [])],
        ibge_sidra=[SidraIndicator(**item) for item in payload.get("ibge_sidra", [])],
    )
