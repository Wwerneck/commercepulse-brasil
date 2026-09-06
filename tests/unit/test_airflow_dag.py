import importlib.util
from pathlib import Path


def _load_dag_module():
    path = Path("airflow/dags/commercepulse_pipeline.py")
    spec = importlib.util.spec_from_file_location("commercepulse_pipeline", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_airflow_dag_declares_expected_tasks() -> None:
    module = _load_dag_module()

    assert "ingest_olist" in module.PIPELINE_TASKS
    assert "dbt_test" in module.PIPELINE_TASKS
    assert "observability_report" in module.PIPELINE_TASKS
    assert len(module.PIPELINE_TASKS) == 21


def test_airflow_dag_orders_bronze_before_silver_and_dbt_last() -> None:
    module = _load_dag_module()

    assert ("validate_bronze", "build_silver") in module.TASK_DEPENDENCIES
    assert ("load_warehouse", "dbt_run") in module.TASK_DEPENDENCIES
    assert ("dbt_run", "dbt_test") in module.TASK_DEPENDENCIES
    assert ("dbt_test", "train_forecast") in module.TASK_DEPENDENCIES
    assert ("review_intelligence", "observability_report") in module.TASK_DEPENDENCIES
