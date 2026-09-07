from pathlib import Path

import mlflow

from src.config import Settings
from src.ml.tracking import EXPERIMENT_NAME, configure_mlflow, log_dict_metrics, log_dict_params


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        app_env="test",
        log_level="INFO",
        data_dir=tmp_path / "data",
        models_dir=tmp_path / "models",
        bcb_base_url="https://example.com/bcb",
        ibge_sidra_base_url="https://example.com/ibge",
        request_timeout_seconds=30,
        request_retries=3,
        postgres_host="localhost",
        postgres_port=55432,
        postgres_db="commercepulse",
        postgres_user="commercepulse",
        postgres_password="commercepulse",
        mlflow_tracking_uri=f"sqlite:///{tmp_path / 'mlflow.db'}",
    )


def test_configure_mlflow_sets_local_experiment(tmp_path: Path) -> None:
    configure_mlflow(_settings(tmp_path))

    experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)

    assert experiment is not None
    assert experiment.name == EXPERIMENT_NAME


def test_tracking_helpers_skip_null_metrics_and_log_params(tmp_path: Path) -> None:
    configure_mlflow(_settings(tmp_path))

    with mlflow.start_run(run_name="unit_test_tracking_helpers") as run:
        log_dict_params(mlflow, {"model": "baseline", "rows": 10})
        log_dict_metrics(mlflow, {"mae": 1.5, "mape": None})

    client = mlflow.tracking.MlflowClient()
    stored = client.get_run(run.info.run_id)

    assert stored.data.params["model"] == "baseline"
    assert stored.data.params["rows"] == "10"
    assert stored.data.metrics["mae"] == 1.5
    assert "mape" not in stored.data.metrics
