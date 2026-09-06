# Gold Layer

## Status da Execucao

Ultima execucao completa em 2026-09-06:

- 13 datasets Gold construidos com DuckDB a partir da Silver.
- 13 arquivos Parquet Gold gravados.
- Validacao Gold: 13 datasets checados, 0 falhas criticas.

## Datasets e Grains

| Dataset | Grain |
| --- | --- |
| `sales_daily` | uma linha por data de compra |
| `sales_monthly` | uma linha por mes de compra |
| `category_performance` | uma linha por categoria |
| `customer_metrics` | uma linha por `customer_id` |
| `seller_metrics` | uma linha por `seller_id` |
| `delivery_metrics` | uma linha por data de compra |
| `review_metrics` | uma linha por data de criacao do review |
| `economic_indicators` | uma linha por mes de referencia |
| `sales_economic_features` | uma linha por mes de venda |
| `customer_rfm` | uma linha por `customer_id` com pedido |
| `ml_features` | uma linha por data de compra |
| `anomaly_metrics` | uma linha por data de compra |
| `dim_date` | uma linha por data calendario |

## KPIs Criados

- GMV.
- Receita de produtos.
- Numero de pedidos.
- Clientes unicos.
- Itens vendidos.
- Ticket medio.
- Frete total e frete medio.
- Crescimento MoM de GMV.
- Prazo medio de entrega.
- Taxa de atraso.
- Review medio.
- Reviews positivos e negativos.
- Performance por categoria.
- Metricas por cliente e vendedor.

## Integracao Economica

O dataset `sales_economic_features` integra vendas mensais com:

- `selic_target`
- `usd_brl`
- `ibc_br`
- `ipca`

Tambem cria variacoes mensais quando ha dados disponiveis:

- `selic_target_change`
- `usd_brl_change`
- `ibc_br_change`
- `ipca_change`
- `sales_growth`
- `ticket_growth`

Correlacoes e interpretacoes causais ainda nao foram afirmadas nesta camada.

## Feature Engineering

O dataset `ml_features` cria:

- `sales_lag_1`
- `sales_lag_7`
- `sales_lag_30`
- `rolling_mean_7`
- `rolling_mean_30`
- `rolling_std_7`
- `rolling_std_30`
- `log_gmv`

`np.log1p` foi aplicado ao GMV para preparar uma versao estabilizada da serie para modelos futuros.

## Anomalias

O dataset `anomaly_metrics` usa z-score com NumPy para marcar anomalias em:

- `gmv`
- `orders`
- `average_ticket`
- `freight_value`

As anomalias sao flags analiticas, nao exclusoes.

## Resultados Reais Conferidos

- `sales_daily`: 616 linhas.
- `sales_monthly`: 24 linhas.
- GMV total: 15.843.553,24.
- Pedidos com itens: 98.666.
- Ticket medio por item: 140,64.
- Categoria com maior GMV: `health_beauty`, com 1.441.248,07.
- Dias com anomalia de GMV por z-score: 2.

## Qualidade Gold

Validacoes aplicadas:

- existencia de todos os datasets esperados;
- datasets nao vazios;
- chaves unicas nos grains principais;
- datas obrigatorias;
- GMV, pedidos e ticket nao negativos;
- dimensao calendario com `date_key` unico.

Relatorios:

- Build: `data/gold/_reports/*.json`
- Qualidade: `data/gold/_quality_reports/*.json`

## Comandos

```bash
python -m src.pipeline build-gold
python -m src.pipeline validate-gold
```
