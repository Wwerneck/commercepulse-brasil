# Streamlit Dashboard

## Status

FASE 20 concluida em 2026-09-06.

O dashboard Streamlit consome a FastAPI local para apresentar KPIs, series Gold, rankings, resultados de ML, anomalias e catalogo de artefatos.

## Execucao Local

Inicie a API:

```bash
uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Inicie o dashboard:

```bash
streamlit run dashboard/app.py --server.address 127.0.0.1 --server.port 8501
```

Interface:

```text
http://127.0.0.1:8501
```

## Configuracao

Por padrao, o dashboard consome:

```text
COMMERCEPULSE_API_URL=http://127.0.0.1:8000
```

Para apontar para outra API, defina a variavel de ambiente `COMMERCEPULSE_API_URL`.

## Paginas

- `Visao Geral`: KPIs executivos, GMV mensal e top categorias.
- `Vendas`: serie diaria, serie mensal, pedidos e ticket medio.
- `Categorias`: dispersao de categorias por pedidos, GMV, itens vendidos e ticket medio.
- `Machine Learning`: forecast, segmentacao de clientes e qualidade de reviews.
- `Anomalias`: comparacao entre z-score e Isolation Forest.
- `Observabilidade`: status operacional, falhas, avisos e checks dos artefatos.
- `Catalogo`: datasets Gold, outputs de ML e relatorios recentes.

## Qualidade

Foram adicionados testes para formatadores do dashboard e a aplicacao foi validada com Streamlit local.
