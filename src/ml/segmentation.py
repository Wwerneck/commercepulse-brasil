import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from src.config import Settings, get_settings
from src.ml.tracking import log_artifact_if_exists, log_dict_metrics, log_dict_params, mlflow_run
from src.utils.parquet import read_parquet, write_parquet


@dataclass(frozen=True)
class ClusterScore:
    k: int
    inertia: float
    silhouette: float | None


@dataclass(frozen=True)
class SegmentationReport:
    generated_at: datetime
    rows: int
    selected_k: int
    scores: list[ClusterScore]
    segment_counts: dict[str, int]
    output_path: str
    report_path: str


def build_customer_segmentation(settings: Settings | None = None) -> SegmentationReport:
    cfg = settings or get_settings()
    rfm = read_parquet(cfg.gold_dir / "customer_rfm" / "customer_rfm.parquet")
    features = rfm[["recency_days", "frequency", "monetary"]].dropna()
    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)
    sample_size = min(len(features), 10000)
    sample = (
        features.sample(n=sample_size, random_state=42)
        if len(features) > sample_size
        else features
    )
    sample_scaled = scaler.transform(sample)
    scores: list[ClusterScore] = []
    best_k = 3
    best_silhouette = -1.0
    for k in range(2, 7):
        model = KMeans(n_clusters=k, random_state=42, n_init=10)
        sample_labels = model.fit_predict(sample_scaled)
        silhouette = float(silhouette_score(sample_scaled, sample_labels))
        scores.append(ClusterScore(k=k, inertia=float(model.inertia_), silhouette=silhouette))
        if silhouette > best_silhouette:
            best_silhouette = silhouette
            best_k = k

    final_model = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    rfm = rfm.loc[features.index].copy()
    rfm["cluster"] = final_model.fit_predict(scaled)
    centroids = rfm.groupby("cluster")[["recency_days", "frequency", "monetary"]].mean()
    monetary_rank = centroids["monetary"].rank(method="first")
    recency_rank = centroids["recency_days"].rank(method="first", ascending=False)
    labels = {}
    for cluster, row in centroids.iterrows():
        if monetary_rank.loc[cluster] == monetary_rank.max() and recency_rank.loc[cluster] >= 4:
            labels[cluster] = "vip"
        elif row["recency_days"] > centroids["recency_days"].quantile(0.75):
            labels[cluster] = "at_risk"
        elif row["recency_days"] < centroids["recency_days"].quantile(0.25):
            labels[cluster] = "recent"
        else:
            labels[cluster] = "standard"
    rfm["ml_segment"] = rfm["cluster"].map(labels)

    generated_at = datetime.now(UTC)
    output_path = Path("models") / "outputs" / "customer_segments.parquet"
    report_path = (
        Path("models") / "reports" / f"customer_segmentation_{generated_at:%Y%m%dT%H%M%SZ}.json"
    )
    write_parquet(rfm, output_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = SegmentationReport(
        generated_at=generated_at,
        rows=len(rfm),
        selected_k=best_k,
        scores=scores,
        segment_counts={str(k): int(v) for k, v in rfm["ml_segment"].value_counts().items()},
        output_path=str(output_path),
        report_path=str(report_path),
    )
    payload: dict[str, Any] = {**asdict(report), "generated_at": generated_at.isoformat()}
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    with mlflow_run("customer_segmentation", settings=cfg) as (mlflow, _run):
        log_dict_params(
            mlflow,
            {
                "algorithm": "kmeans",
                "selected_k": best_k,
                "rows": len(rfm),
                "sample_size": sample_size,
                "feature_columns": "recency_days,frequency,monetary",
            },
        )
        for score in scores:
            log_dict_metrics(
                mlflow,
                {
                    f"k_{score.k}_inertia": score.inertia,
                    f"k_{score.k}_silhouette": score.silhouette,
                },
            )
        for segment, count in report.segment_counts.items():
            mlflow.log_metric(f"segment_{segment}_count", count)
        mlflow.sklearn.log_model(final_model, name="model")
        log_artifact_if_exists(mlflow, output_path)
        log_artifact_if_exists(mlflow, report_path)
    return report
