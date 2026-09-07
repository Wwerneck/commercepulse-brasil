import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from sklearn.ensemble import IsolationForest

from src.config import Settings, get_settings
from src.ml.tracking import log_artifact_if_exists, log_dict_metrics, log_dict_params, mlflow_run
from src.utils.parquet import read_parquet, write_parquet


@dataclass(frozen=True)
class AnomalyDetectionReport:
    generated_at: datetime
    rows: int
    zscore_anomaly_days: int
    isolation_forest_anomaly_days: int
    overlap_days: int
    output_path: str
    report_path: str


def compare_anomaly_methods(settings: Settings | None = None) -> AnomalyDetectionReport:
    cfg = settings or get_settings()
    df = read_parquet(cfg.gold_dir / "anomaly_metrics" / "anomaly_metrics.parquet")
    features = df[["gmv", "orders", "average_ticket", "freight_value"]].fillna(0)
    model = IsolationForest(contamination=0.03, random_state=42)
    df["isolation_forest_anomaly"] = model.fit_predict(features) == -1
    zscore_columns = [column for column in df.columns if column.endswith("_zscore_anomaly")]
    df["any_zscore_anomaly"] = df[zscore_columns].any(axis=1)
    df["anomaly_method_overlap"] = df["any_zscore_anomaly"] & df["isolation_forest_anomaly"]

    generated_at = datetime.now(UTC)
    output_path = cfg.models_dir / "outputs" / "anomaly_method_comparison.parquet"
    report_path = (
        cfg.models_dir / "reports" / f"anomaly_detection_{generated_at:%Y%m%dT%H%M%SZ}.json"
    )
    write_parquet(df, output_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = AnomalyDetectionReport(
        generated_at=generated_at,
        rows=len(df),
        zscore_anomaly_days=int(df["any_zscore_anomaly"].sum()),
        isolation_forest_anomaly_days=int(df["isolation_forest_anomaly"].sum()),
        overlap_days=int(df["anomaly_method_overlap"].sum()),
        output_path=str(output_path),
        report_path=str(report_path),
    )
    payload: dict[str, Any] = {**asdict(report), "generated_at": generated_at.isoformat()}
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    with mlflow_run("anomaly_detection", settings=cfg) as (mlflow, _run):
        log_dict_params(
            mlflow,
            {
                "algorithm": "isolation_forest",
                "contamination": 0.03,
                "rows": len(df),
                "feature_columns": "gmv,orders,average_ticket,freight_value",
                "zscore_columns": ",".join(zscore_columns),
            },
        )
        log_dict_metrics(
            mlflow,
            {
                "zscore_anomaly_days": report.zscore_anomaly_days,
                "isolation_forest_anomaly_days": report.isolation_forest_anomaly_days,
                "overlap_days": report.overlap_days,
            },
        )
        mlflow.sklearn.log_model(model, name="model")
        log_artifact_if_exists(mlflow, output_path)
        log_artifact_if_exists(mlflow, report_path)
    return report
