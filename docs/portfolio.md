# Portfolio Narrative

## Titulo

CommercePulse Brasil: plataforma de dados e IA para e-commerce com indicadores macroeconomicos brasileiros.

## Pitch

Projeto end-to-end de Engenharia de Dados, Analytics Engineering, Machine Learning e Produto de Dados. Ele ingere dados transacionais da Olist e indicadores oficiais do Banco Central/IBGE, organiza um Data Lake em Bronze/Silver/Gold, carrega um warehouse dimensional em PostgreSQL, materializa marts com dbt, orquestra o pipeline com Airflow, rastreia modelos com MLflow, expoe dados via FastAPI e apresenta insights em Streamlit.

## Problema

Entender como vendas, categorias, clientes, vendedores, frete, entregas e reviews de um e-commerce se relacionam com variaveis economicas brasileiras.

## Stack

Python, Pandas, NumPy, PyArrow, DuckDB, PostgreSQL, dbt, Airflow, scikit-learn, MLflow, FastAPI, Streamlit, Plotly, Docker, Pytest, Ruff e GitHub Actions.

## Entregaveis

- Data Lake Bronze, Silver e Gold.
- Qualidade de dados por camada.
- Warehouse dimensional.
- Modelos dbt.
- KPIs e correlacoes economicas.
- Forecast de GMV.
- Segmentacao RFM com KMeans.
- Deteccao de anomalias.
- Inteligencia de reviews.
- Tracking de experimentos com MLflow.
- API tipada com FastAPI.
- Dashboard Streamlit.
- Observabilidade operacional.
- Docker Compose.
- CI com lint, import checks, DAG check e testes.

## Resultados Locais

- Bronze validada sem falhas.
- Silver validada sem falhas criticas.
- Gold validada sem falhas criticas.
- Warehouse carregado com 9 tabelas analiticas.
- dbt com testes passando.
- MLflow com 4 runs registrados.
- API e dashboard respondendo localmente.
- Observabilidade com `25` checks, `0` falhas e `0` avisos.
- Suite Python com `61` testes passando.

## Como Apresentar

1. Mostre a arquitetura no README.
2. Execute `make ci`.
3. Mostre a API em `/docs`.
4. Mostre o dashboard Streamlit.
5. Mostre o MLflow com os runs.
6. Mostre o relatorio de observabilidade.

## Frase Para Recrutador

Construí uma plataforma de dados e IA de ponta a ponta, cobrindo ingestao, lakehouse local, modelagem dimensional, analytics engineering, machine learning, tracking de experimentos, API, dashboard, observabilidade, Docker e CI.
