import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

import numpy as np
import pandas as pd

from src.config import Settings, get_settings
from src.utils.parquet import read_parquet


@dataclass(frozen=True)
class EconomicCorrelation:
    metric: str
    indicator: str
    observations: int
    correlation: float | None
    covariance: float | None


@dataclass(frozen=True)
class EconomicAnalysisReport:
    generated_at: datetime
    correlations: list[EconomicCorrelation]
    notes: list[str]
    report_path: str


def _corr_and_cov(df: pd.DataFrame, metric: str, indicator: str) -> EconomicCorrelation:
    values = df[[metric, indicator]].dropna()
    if len(values) < 3:
        return EconomicCorrelation(metric, indicator, len(values), None, None)
    x = values[metric].to_numpy(dtype=float)
    y = values[indicator].to_numpy(dtype=float)
    return EconomicCorrelation(
        metric=metric,
        indicator=indicator,
        observations=int(len(values)),
        correlation=float(np.corrcoef(x, y)[0, 1]),
        covariance=float(np.cov(x, y)[0, 1]),
    )


def build_economic_analysis(settings: Settings | None = None) -> EconomicAnalysisReport:
    cfg = settings or get_settings()
    df = read_parquet(cfg.gold_dir / "sales_economic_features" / "sales_economic_features.parquet")
    metrics = ["gmv", "orders", "average_ticket"]
    indicators = ["selic_target", "usd_brl", "ibc_br", "ipca"]
    correlations = [
        _corr_and_cov(df, metric, indicator)
        for metric in metrics
        for indicator in indicators
        if metric in df.columns and indicator in df.columns
    ]
    generated_at = datetime.now(UTC)
    notes = [
        "Correlations are descriptive and do not imply causality.",
        "Economic coverage depends on the available configured BCB and SIDRA series.",
    ]
    report_path = (
        cfg.gold_dir / "_analytics_reports" / f"economic_{generated_at:%Y%m%dT%H%M%SZ}.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = EconomicAnalysisReport(
        generated_at=generated_at,
        correlations=correlations,
        notes=notes,
        report_path=str(report_path),
    )
    payload: dict[str, Any] = {**asdict(report), "generated_at": generated_at.isoformat()}
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
