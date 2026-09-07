import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

import numpy as np

from src.config import Settings, get_settings
from src.ml.tracking import log_artifact_if_exists, log_dict_metrics, log_dict_params, mlflow_run
from src.utils.parquet import read_parquet


@dataclass(frozen=True)
class ModelMetrics:
    model_name: str
    mae: float
    rmse: float
    mape: float | None


@dataclass(frozen=True)
class ForecastReport:
    generated_at: datetime
    target: str
    train_rows: int
    test_rows: int
    feature_columns: list[str]
    metrics: list[ModelMetrics]
    best_model: str
    report_path: str


def _mape(y_true: np.ndarray, y_pred: np.ndarray) -> float | None:
    mask = y_true != 0
    if not mask.any():
        return None
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])))


def train_sales_forecast_baseline(settings: Settings | None = None) -> ForecastReport:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_absolute_error, mean_squared_error

    cfg = settings or get_settings()
    df = read_parquet(cfg.gold_dir / "ml_features" / "ml_features.parquet").sort_values("date")
    df["day_of_week"] = df["date"].dt.dayofweek
    df["month"] = df["date"].dt.month
    feature_columns = [
        "orders",
        "customers",
        "items_sold",
        "freight_value",
        "average_ticket",
        "sales_lag_1",
        "sales_lag_7",
        "rolling_mean_7",
        "rolling_mean_30",
        "day_of_week",
        "month",
    ]
    model_df = df.dropna(subset=feature_columns + ["gmv"]).copy()
    split_index = int(len(model_df) * 0.8)
    train = model_df.iloc[:split_index]
    test = model_df.iloc[split_index:]
    x_train = train[feature_columns]
    y_train = train["gmv"].to_numpy(dtype=float)
    x_test = test[feature_columns]
    y_test = test["gmv"].to_numpy(dtype=float)

    models = {
        "linear_regression": LinearRegression(),
        "random_forest": RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1),
    }
    metrics: list[ModelMetrics] = []
    fitted_models: dict[str, Any] = {}
    for model_name, model in models.items():
        model.fit(x_train, y_train)
        fitted_models[model_name] = model
        predictions = model.predict(x_test)
        metrics.append(
            ModelMetrics(
                model_name=model_name,
                mae=float(mean_absolute_error(y_test, predictions)),
                rmse=float(mean_squared_error(y_test, predictions) ** 0.5),
                mape=_mape(y_test, predictions),
            )
        )

    best = min(metrics, key=lambda item: item.mae)
    generated_at = datetime.now(UTC)
    report_path = cfg.models_dir / "reports" / f"sales_forecast_{generated_at:%Y%m%dT%H%M%SZ}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = ForecastReport(
        generated_at=generated_at,
        target="gmv",
        train_rows=len(train),
        test_rows=len(test),
        feature_columns=feature_columns,
        metrics=metrics,
        best_model=best.model_name,
        report_path=str(report_path),
    )
    payload: dict[str, Any] = {**asdict(report), "generated_at": generated_at.isoformat()}
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    with mlflow_run("sales_forecast_baseline", settings=cfg) as (mlflow, _run):
        log_dict_params(
            mlflow,
            {
                "target": report.target,
                "train_rows": report.train_rows,
                "test_rows": report.test_rows,
                "feature_count": len(feature_columns),
                "models_compared": ",".join(models),
                "best_model": best.model_name,
            },
        )
        for item in metrics:
            log_dict_metrics(
                mlflow,
                {
                    f"{item.model_name}_mae": item.mae,
                    f"{item.model_name}_rmse": item.rmse,
                    f"{item.model_name}_mape": item.mape,
                },
            )
        log_dict_metrics(
            mlflow,
            {
                "best_mae": best.mae,
                "best_rmse": best.rmse,
                "best_mape": best.mape,
            },
        )
        mlflow.sklearn.log_model(fitted_models[best.model_name], name="model")
        log_artifact_if_exists(mlflow, report_path)
    return report
