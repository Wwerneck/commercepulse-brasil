# Docker and CI

## Status

FASE 21 e FASE 24 concluidas em 2026-09-06.

O projeto possui configuracao Docker para PostgreSQL, MLflow, FastAPI, Streamlit e Airflow, alem de CI no GitHub Actions para lint, parse da DAG, import da API/dashboard e testes.

## Servicos

- `postgres`: banco PostgreSQL 16 para warehouse.
- `mlflow`: tracking server MLflow 3 com backend SQLite persistido em volume.
- `api`: FastAPI em `http://127.0.0.1:8000`.
- `dashboard`: Streamlit em `http://127.0.0.1:8501`.
- `airflow`: Airflow standalone em `http://127.0.0.1:8080`.

No Docker Compose, o PostgreSQL usa a porta `5432`. Nos scripts PowerShell locais, a instancia isolada do projeto usa `55432` para evitar conflito com instalacoes existentes.

## Execucao Com Docker

Build:

```bash
docker compose build
```

Subir ambiente:

```bash
docker compose up -d
```

Logs:

```bash
docker compose logs -f
```

Encerrar:

```bash
docker compose down
```

## Volumes

- `postgres_data`: dados do PostgreSQL.
- `mlflow_data`: metadados e artefatos do MLflow server.
- `./data:/app/data`: dados locais usados pela API.
- `./models:/app/models`: outputs e relatorios de ML usados pela API.

## Health Checks

O Compose valida:

- PostgreSQL com `pg_isready`;
- MLflow via HTTP;
- FastAPI em `/health`;
- Streamlit via HTTP.

## CI

Workflow:

```text
.github/workflows/ci.yml
```

Etapas:

- checkout;
- Python 3.11;
- instalacao de dependencias;
- `ruff check .`;
- parse estatico da DAG Airflow;
- import de API e dashboard;
- `pytest`.

Os testes de contrato da API mockam a camada de servico para nao depender de Parquets locais no GitHub Actions.
