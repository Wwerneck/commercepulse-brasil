# dbt

## Status

Projeto dbt inicial criado para rodar sobre o PostgreSQL Data Warehouse.

Execucao concluida em 2026-09-06 contra o PostgreSQL local em `localhost:55432`.

- `dbt parse --profiles-dir .`: passou.
- `dbt run --profiles-dir .`: 10 modelos criados, 0 erros.
- `dbt test --profiles-dir .`: 16 testes passaram, 0 erros.

## Camadas

- `staging`: views finas sobre tabelas do schema `analytics`.
- `intermediate`: joins e enriquecimentos reutilizaveis.
- `marts`: tabelas finais para consumo analitico.

## Modelos

Staging:

- `stg_sales_daily`
- `stg_sales_monthly`
- `stg_category_performance`
- `stg_economic_indicators`
- `stg_dim_date`

Intermediate:

- `int_sales_calendar`
- `int_sales_economic_monthly`

Marts:

- `mart_sales`
- `mart_category`
- `mart_economic_analysis`

## Materializacoes Criadas

- Views em `analytics_staging`.
- Views em `analytics_intermediate`.
- Tabelas em `analytics_marts`.

## Testes dbt

Foram definidos testes de:

- `unique`
- `not_null`

## Comandos

```bash
cd dbt
dbt run --profiles-dir .
dbt test --profiles-dir .
```
