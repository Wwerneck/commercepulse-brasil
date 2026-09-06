.PHONY: install test lint ci pipeline dbt airflow-parse api dashboard mlflow docker-build docker-up docker-down docker-logs

install:
	pip install -r requirements.txt

test:
	pytest

lint:
	ruff check .

ci: lint airflow-parse test

pipeline:
	python -m src.pipeline

dbt:
	cd dbt && dbt run --profiles-dir . && dbt test --profiles-dir .

airflow-parse:
	python -c "import importlib.util; p='airflow/dags/commercepulse_pipeline.py'; s=importlib.util.spec_from_file_location('dag', p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print(len(m.PIPELINE_TASKS))"

api:
	uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload

dashboard:
	streamlit run dashboard/app.py --server.address 127.0.0.1 --server.port 8501

mlflow:
	mlflow ui --backend-store-uri sqlite:///mlflow.db --host 127.0.0.1 --port 5000

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f
