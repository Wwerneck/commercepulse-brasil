# FastAPI

## Status

FASE 19 concluida em 2026-09-06.

A API expõe dados Gold, relatórios analíticos e resultados de ML por endpoints versionáveis e tipados com Pydantic.

## Execucao Local

```bash
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

Documentacao interativa:

```text
http://127.0.0.1:8000/docs
```

OpenAPI:

```text
http://127.0.0.1:8000/openapi.json
```

## Endpoints

- `GET /health`: status da aplicacao.
- `GET /catalog`: catalogo dos Parquets Gold, outputs de ML e ultimos relatorios.
- `GET /kpis/latest`: KPIs executivos mais recentes.
- `GET /sales/daily?limit=30`: serie diaria de vendas.
- `GET /sales/monthly?limit=24`: serie mensal de vendas.
- `GET /categories/top?limit=10`: ranking de categorias por GMV.
- `GET /customers/segments`: resumo dos segmentos de clientes gerados por ML.
- `GET /anomalies?limit=50&only_overlap=false`: dias anomalos por z-score e Isolation Forest.
- `GET /ml/reports/{report_type}/latest`: ultimo relatorio para `kpis`, `economic`, `forecast`, `segmentation`, `anomaly` ou `reviews`.
- `GET /observability`: relatorio operacional com status dos principais artefatos.

## Contratos

Os modelos de resposta ficam em:

```text
api/schemas.py
```

A camada de leitura e preparacao dos dados fica em:

```text
api/services.py
```

## Qualidade

A API possui testes com `TestClient` cobrindo:

- saude da aplicacao;
- catalogo;
- KPIs;
- series de vendas;
- validacao de `limit`;
- ranking de categorias;
- segmentos;
- anomalias;
- relatorios de ML;
- erro `404` para tipo de relatorio desconhecido.
