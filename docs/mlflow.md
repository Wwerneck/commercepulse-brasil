# MLflow

## Status

FASE 18 concluida em 2026-09-06.

O projeto usa MLflow para rastrear experimentos locais de Machine Learning sem exigir servidor externo.

## Tracking URI

Por padrao, os metadados dos runs sao gravados em SQLite local:

```text
mlflow.db
```

Configuracao padrao:

```text
MLFLOW_TRACKING_URI=sqlite:///mlflow.db
```

Para usar um servidor MLflow, altere a variavel de ambiente para algo como:

```text
MLFLOW_TRACKING_URI=http://localhost:5000
```

## Experimento

Todos os runs usam o experimento:

```text
commercepulse-brasil
```

## Runs Instrumentados

- `sales_forecast_baseline`: compara Linear Regression e Random Forest para previsao diaria de GMV.
- `customer_segmentation`: executa KMeans em RFM e registra scores por K.
- `anomaly_detection`: compara anomalias estatisticas por z-score com Isolation Forest.
- `review_intelligence`: registra indicadores de cobertura textual, reviews negativos e score medio.

## Artefatos

Os runs registram, quando aplicavel:

- relatorios JSON em `models/reports`;
- outputs Parquet em `models/outputs`;
- modelo sklearn do melhor forecast;
- modelo KMeans de segmentacao;
- modelo Isolation Forest de anomalias.

## Execucao

```bash
python -m src.pipeline train-forecast
python -m src.pipeline segment-customers
python -m src.pipeline detect-anomalies
python -m src.pipeline review-intelligence
```

## UI Local

```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db --host 127.0.0.1 --port 5000
```

Interface:

```text
http://127.0.0.1:5000
```

## Observacoes

Os arquivos locais `mlflow.db`, `mlruns/` e `mlartifacts/` nao sao versionados. Isso evita publicar artefatos pesados ou metadados locais no GitHub.
