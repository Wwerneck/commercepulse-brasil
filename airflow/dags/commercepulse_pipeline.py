from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(os.getenv("COMMERCEPULSE_PROJECT_ROOT", Path(__file__).resolve().parents[2]))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_ENV = {
    "PYTHONPATH": str(PROJECT_ROOT),
    "DATA_DIR": os.getenv("DATA_DIR", "data"),
    "POSTGRES_HOST": os.getenv("POSTGRES_HOST", "localhost"),
    "POSTGRES_PORT": os.getenv("POSTGRES_PORT", "55432"),
    "POSTGRES_DB": os.getenv("POSTGRES_DB", "commercepulse"),
    "POSTGRES_USER": os.getenv("POSTGRES_USER", "commercepulse"),
    "POSTGRES_PASSWORD": os.getenv("POSTGRES_PASSWORD", "commercepulse"),
}

PIPELINE_TASKS = {
    "ingest_olist": "python -m src.pipeline ingest-olist --source-dir data/raw/olist",
    "ingest_bcb": (
        "python -m src.pipeline ingest-bcb "
        "--start-date 01/01/2020 --end-date 31/12/2020"
    ),
    "ingest_ibge": "python -m src.pipeline ingest-ibge",
    "validate_bronze": "python -m src.pipeline validate-bronze",
    "build_silver": "python -m src.pipeline build-silver",
    "validate_silver": "python -m src.pipeline validate-silver",
    "silver_outliers": "python -m src.pipeline silver-outliers",
    "build_gold": "python -m src.pipeline build-gold",
    "validate_gold": "python -m src.pipeline validate-gold",
    "check_warehouse_inputs": "python -m src.pipeline check-warehouse-inputs",
    "init_warehouse": "python -m src.pipeline init-warehouse",
    "load_warehouse": "python -m src.pipeline load-warehouse",
    "dbt_run": "cd dbt && dbt run --profiles-dir .",
    "dbt_test": "cd dbt && dbt test --profiles-dir .",
    "analytics_report": "python -m src.pipeline analytics-report",
    "economic_analysis": "python -m src.pipeline economic-analysis",
    "train_forecast": "python -m src.pipeline train-forecast",
    "segment_customers": "python -m src.pipeline segment-customers",
    "detect_anomalies": "python -m src.pipeline detect-anomalies",
    "review_intelligence": "python -m src.pipeline review-intelligence",
    "observability_report": "python -m src.pipeline observability-report",
}

TASK_DEPENDENCIES = [
    ("ingest_olist", "validate_bronze"),
    ("ingest_bcb", "validate_bronze"),
    ("ingest_ibge", "validate_bronze"),
    ("validate_bronze", "build_silver"),
    ("build_silver", "validate_silver"),
    ("validate_silver", "silver_outliers"),
    ("silver_outliers", "build_gold"),
    ("build_gold", "validate_gold"),
    ("validate_gold", "check_warehouse_inputs"),
    ("check_warehouse_inputs", "init_warehouse"),
    ("init_warehouse", "load_warehouse"),
    ("load_warehouse", "dbt_run"),
    ("dbt_run", "dbt_test"),
    ("dbt_test", "analytics_report"),
    ("dbt_test", "economic_analysis"),
    ("dbt_test", "train_forecast"),
    ("dbt_test", "segment_customers"),
    ("dbt_test", "detect_anomalies"),
    ("dbt_test", "review_intelligence"),
    ("analytics_report", "observability_report"),
    ("economic_analysis", "observability_report"),
    ("train_forecast", "observability_report"),
    ("segment_customers", "observability_report"),
    ("detect_anomalies", "observability_report"),
    ("review_intelligence", "observability_report"),
]


try:
    from airflow.operators.bash import BashOperator

    from airflow import DAG

    with DAG(
        dag_id="commercepulse_pipeline",
        description="CommercePulse Brasil Bronze to dbt orchestration",
        start_date=datetime(2026, 9, 1),
        schedule="@daily",
        catchup=False,
        max_active_runs=1,
        default_args={
            "owner": "commercepulse",
            "depends_on_past": False,
            "retries": 2,
            "retry_delay": timedelta(minutes=5),
        },
        tags=["commercepulse", "data-engineering", "ecommerce", "macro"],
    ) as dag:
        tasks = {
            task_id: BashOperator(  # type: ignore[call-arg]
                task_id=task_id,
                bash_command=command,
                cwd=str(PROJECT_ROOT),
                env=DEFAULT_ENV,
                append_env=True,
            )
            for task_id, command in PIPELINE_TASKS.items()
        }

        for upstream, downstream in TASK_DEPENDENCIES:
            tasks[upstream] >> tasks[downstream]
except ImportError:
    dag = None
