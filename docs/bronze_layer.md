# Bronze Layer

## Status da Execucao

Ultima execucao completa da Bronze em 2026-09-06:

- Olist: 9 arquivos Parquet gravados, 1.550.922 registros lidos, 0 arquivos ausentes.
- Banco Central SGS: 3 arquivos Parquet gravados, 629 registros lidos.
- IBGE/SIDRA: 1 arquivo Parquet gravado, 13 registros lidos.
- Validacao Bronze: 13 arquivos Parquet checados, 0 falhas.

## Fontes Ingeridas

### Olist

Fonte primaria oficial: Kaggle, dataset `olistbr/brazilian-ecommerce`.

Para viabilizar a execucao local sem credenciais Kaggle, os CSVs foram obtidos de um espelho publico no GitHub contendo os arquivos do dataset Olist. A documentacao final deve manter atribuicao ao dataset original da Olist e respeitar a licenca aplicavel.

Arquivos esperados:

- `olist_customers_dataset.csv`
- `olist_orders_dataset.csv`
- `olist_order_items_dataset.csv`
- `olist_order_payments_dataset.csv`
- `olist_order_reviews_dataset.csv`
- `olist_products_dataset.csv`
- `olist_sellers_dataset.csv`
- `olist_geolocation_dataset.csv`
- `product_category_name_translation.csv`

### Banco Central

Endpoint oficial SGS:

```text
https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo_serie}/dados
```

Series ingeridas na execucao atual:

- `selic_target`
- `usd_brl`
- `ibc_br`

### IBGE

Endpoint oficial SIDRA:

```text
https://apisidra.ibge.gov.br/values
```

Consulta ingerida na execucao atual:

- `ipca`

## Metadados Bronze

Todos os arquivos Parquet Bronze devem conter:

- `source`
- `ingestion_timestamp`
- `batch_id`

Quando aplicavel, a ingestao tambem preserva:

- `source_file`
- `indicator_name`
- codigo de serie ou referencia SIDRA no manifesto

## Artefatos Gerados

- Dados: `data/bronze/{source}/{dataset}/{batch_id}.parquet`
- Manifestos: `data/bronze/{source}/_manifests/{batch_id}.json`
- Relatorios de qualidade: `data/bronze/_quality_reports/*.json`

Esses artefatos sao dados gerados e permanecem fora do Git.
