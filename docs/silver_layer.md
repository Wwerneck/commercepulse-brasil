# Silver Layer

## Status da Execucao

Ultima execucao completa em 2026-09-06:

- 13 datasets Bronze transformados para Silver.
- 13 arquivos Parquet Silver gravados.
- Validacao Silver: 13 arquivos checados, 0 falhas criticas, 1 warning.
- Relatorio de outliers IQR: 7 datasets analisados.

## Transformacoes Aplicadas

### Olist

- Conversao de colunas de data para timestamp em `orders`, `order_items` e `order_reviews`.
- Normalizacao de strings de localidade, estado e categorias para minusculas com trim.
- Conversao numerica explicita para preco, frete, pagamento, review score e atributos de produto.
- Criacao de flags `is_duplicate_key` e `has_invalid_*` para marcar problemas sem remover linhas.
- Nenhum registro foi removido na Silver Olist.

### Banco Central

- Garantia de tipos para `date`, `value` e `series_code`.
- Preservacao de `indicator_name`, `source`, `ingestion_timestamp` e `batch_id`.
- Criacao de flags para data, valor e chave duplicada.

### IBGE/SIDRA

- Remocao explicita da linha de cabecalho retornada pelo SIDRA.
- Renomeacao de colunas tecnicas para nomes analiticos.
- Conversao de `value` para numerico.
- Criacao de `reference_month` a partir de `period_code`.
- Criacao de flags para valor, mes de referencia e chave duplicada.

## Qualidade

As validacoes Silver verificam regras criticas iniciais:

- chaves obrigatorias em pedidos, clientes, itens e reviews;
- unicidade de chaves primarias e chaves compostas;
- integridade referencial entre pedidos, clientes, itens, produtos, sellers e pagamentos;
- `price >= 0`;
- `freight_value >= 0`;
- `review_score` entre 1 e 5;
- dominios aceitos para `order_status` e `payment_type`;
- flags de datas e valores invalidos;
- indicadores economicos com `indicator_name` e `value` preenchidos.

## Achados

- `order_reviews.review_id` possui 1.603 linhas com chave duplicada. Foi classificado como warning, preservado na Silver e marcado por `is_duplicate_key`; a decisao final de grain sera tomada na modelagem dimensional.
- Outliers IQR foram detectados, mas nao removidos automaticamente:
  - `order_items.price`: 8.427 de 112.650.
  - `order_items.freight_value`: 12.134 de 112.650.
  - `order_payments.payment_value`: 7.981 de 103.886.
  - `products.product_weight_g`: 4.551 de 32.949 valores validos.
  - `bcb.ibc_br.value`: 2 de 12.
  - `bcb.usd_brl.value`: 39 de 251.

Relatorios:

- Build: `data/silver/_reports/*.json`
- Qualidade: `data/silver/_quality_reports/*.json`

## Comandos

```bash
python -m src.pipeline build-silver
python -m src.pipeline validate-silver
python -m src.pipeline silver-outliers
```
