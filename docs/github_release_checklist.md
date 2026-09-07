# GitHub Release Checklist

## Antes de Publicar

- Confirmar que `.env` nao esta versionado.
- Confirmar que `data/`, `models/`, `mlruns/`, `mlartifacts/`, `mlflow.db`, `.local/`, `dbt/target/` e `dbt/logs/` nao entram no Git.
- Rodar `make ci`.
- Rodar `python -m src.pipeline observability-report`.
- Abrir `http://127.0.0.1:8000/docs` e validar a API.
- Abrir `http://127.0.0.1:8501` e validar o dashboard.
- Abrir `http://127.0.0.1:5000` e validar os runs do MLflow.
- Conferir README e docs principais.
- No Windows sem `make`, rodar os comandos equivalentes: `ruff check .`, parse da DAG e `pytest`.

## Comandos Sugeridos

```bash
git add .
git status
git commit -m "Finalize CommercePulse Brasil portfolio release"
git remote add origin <github-repo-url>
git push -u origin main
```

## Arquivos Que Devem Ficar Fora Do Git

- `.env`
- `.venv/`
- `data/bronze/`
- `data/silver/`
- `data/gold/`
- `models/`
- `mlruns/`
- `mlartifacts/`
- `mlflow.db`
- `.local/`
- `dbt/target/`
- `dbt/logs/`
- `dbt/.user.yml`

## Sugestao De Descricao Do Repositorio

End-to-end Data Engineering and AI platform for Brazilian e-commerce analytics with Bronze/Silver/Gold lake, PostgreSQL, dbt, Airflow, MLflow, FastAPI, Streamlit, Docker and CI.
