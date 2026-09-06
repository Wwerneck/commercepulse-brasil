from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from src.config import Settings, get_settings

EXPERIMENT_NAME = "commercepulse-brasil"


def configure_mlflow(settings: Settings | None = None) -> Any:
    import mlflow

    cfg = settings or get_settings()
    mlflow.set_tracking_uri(cfg.mlflow_tracking_uri)
    mlflow.set_experiment(EXPERIMENT_NAME)
    return mlflow


@contextmanager
def mlflow_run(run_name: str, settings: Settings | None = None) -> Iterator[Any]:
    mlflow = configure_mlflow(settings)
    with mlflow.start_run(run_name=run_name) as run:
        mlflow.set_tags(
            {
                "project": "commercepulse-brasil",
                "layer": "ml",
                "environment": (settings or get_settings()).app_env,
            }
        )
        yield mlflow, run


def log_dict_metrics(mlflow: Any, metrics: dict[str, float | int | None]) -> None:
    for key, value in metrics.items():
        if value is not None:
            mlflow.log_metric(key, float(value))


def log_dict_params(mlflow: Any, params: dict[str, Any]) -> None:
    for key, value in params.items():
        mlflow.log_param(key, value)


def log_artifact_if_exists(mlflow: Any, path: str | Path) -> None:
    artifact_path = Path(path)
    if artifact_path.exists():
        mlflow.log_artifact(str(artifact_path))
