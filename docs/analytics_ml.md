# Analytics, Economic Intelligence and ML

## Status

Executado em 2026-09-06.

## Analytics e KPIs

- Periodo de vendas: 2016-09-04 a 2018-09-03.
- GMV total: 15.843.553,24.
- Receita de produtos: 13.591.643,70.
- Pedidos com itens: 98.666.
- Itens vendidos: 112.650.
- Ticket medio por item: 140,64.
- Frete medio diario: 19,79.
- Prazo medio de entrega: 12,59 dias.
- Taxa media de atraso: 0,0631.
- Review medio: 3,98.
- Melhor mes por GMV: 2017-11.
- Categoria lider por GMV: `health_beauty`.

## Economic Intelligence

Os indicadores economicos foram realinhados ao periodo Olist antes da analise.

- BCB: 2016-09-01 a 2018-09-30.
- IBGE/IPCA: `201609-201809`.
- `sales_economic_features`: 24 meses.
- Correlacoes calculadas com NumPy: 12.
- Observacoes por correlacao: 24.

Principais correlacoes descritivas:

- GMV x SELIC: -0,8254.
- Pedidos x SELIC: -0,8243.
- GMV x IBC-Br: 0,3528.
- Pedidos x IBC-Br: 0,3418.
- GMV x dolar: 0,1650.
- GMV x IPCA: 0,1148.

Correlacao nao implica causalidade.

## Feature Engineering

Features utilizadas para forecast:

- `sales_lag_1`
- `sales_lag_7`
- `sales_lag_30`
- `rolling_mean_7`
- `rolling_mean_30`
- `rolling_std_7`
- `rolling_std_30`
- `log_gmv`
- dia da semana
- mes

## Machine Learning

Sales Forecast:

- Split temporal, sem embaralhamento.
- Treino: 487 linhas.
- Teste: 122 linhas.
- Target: `gmv`.
- Melhor modelo por MAE: `linear_regression`.
- Linear Regression: MAE 2.083,55; RMSE 2.595,61; MAPE 0,2333.
- Random Forest: MAE 2.226,65; RMSE 3.365,30; MAPE 0,0958.

Customer Segmentation:

- RFM com StandardScaler e KMeans.
- Linhas segmentadas: 98.666.
- K selecionado por silhouette: 4.
- Melhor silhouette: 0,4949.
- `standard`: 39.129.
- `recent`: 36.449.
- `at_risk`: 23.088.

Anomaly Detection:

- Dias analisados: 616.
- Dias anomalos por z-score: 18.
- Dias anomalos por Isolation Forest: 19.
- Sobreposicao entre metodos: 12.

Review Intelligence:

- Reviews analisados: 99.224.
- Cobertura de texto: 0,4127.
- Review score medio: 4,0864.
- Ratio de reviews negativos: 0,1469.
- Recomendacao: qualidade textual suficiente para NLP futuro.

## Comandos

```bash
python -m src.pipeline analytics-report
python -m src.pipeline economic-analysis
python -m src.pipeline train-forecast
python -m src.pipeline segment-customers
python -m src.pipeline detect-anomalies
python -m src.pipeline review-intelligence
```
