# PostgreSQL Data Warehouse

## Status

Concluido em 2026-09-06:

- DDL criado para schemas `raw`, `staging`, `analytics` e `monitoring`.
- Star schema inicial criado em SQL.
- Loader Python criado para carregar datasets Gold em PostgreSQL.
- Pre-checagem de inputs executada: 7 arquivos Gold requeridos, 0 ausentes.
- Instancia PostgreSQL local isolada criada em `.local/postgres`.
- Warehouse inicializado em `localhost:55432`.
- Carga Gold -> PostgreSQL executada: 9 tabelas, 104.082 linhas.

Para ambientes sem Docker, o repositorio inclui scripts PowerShell para subir uma instancia PostgreSQL isolada do projeto em `.local/postgres`, usando porta `55432`.

## Schemas

- `raw`: reservado para cargas brutas no banco, quando necessario.
- `staging`: reservado para tabelas intermediarias antes de marts/dbt.
- `analytics`: star schema e fatos/dimensoes consultaveis.
- `monitoring`: registros de execucao e observabilidade.

## Star Schema Inicial

### Dimensoes

- `analytics.dim_date`
- `analytics.dim_customer`
- `analytics.dim_seller`
- `analytics.dim_category`
- `analytics.dim_economic_indicator`

### Fatos

- `analytics.fact_sales_daily`
- `analytics.fact_sales_monthly`
- `analytics.fact_category_performance`
- `analytics.fact_economic_indicators`

## Tabelas Carregadas

| Tabela | Linhas |
| --- | ---: |
| `analytics.dim_category` | 74 |
| `analytics.dim_customer` | 99.441 |
| `analytics.dim_date` | 730 |
| `analytics.dim_economic_indicator` | 4 |
| `analytics.dim_seller` | 3.095 |
| `analytics.fact_category_performance` | 74 |
| `analytics.fact_economic_indicators` | 24 |
| `analytics.fact_sales_daily` | 616 |
| `analytics.fact_sales_monthly` | 24 |

## Grains

- `fact_sales_daily`: uma linha por data de compra.
- `fact_sales_monthly`: uma linha por mes de compra.
- `fact_category_performance`: uma linha por categoria.
- `fact_economic_indicators`: uma linha por mes de referencia.

## Arquivos

- DDL: `src/warehouse/ddl.py`
- Loader: `src/warehouse/postgres.py`
- Init SQL Docker: `docker/postgres_init.sql`

## Comandos

Verificar se os Parquets Gold necessarios existem:

```bash
python -m src.pipeline check-warehouse-inputs
```

Criar schemas e tabelas no PostgreSQL:

```bash
python -m src.pipeline init-warehouse
```

Carregar Gold no PostgreSQL:

```bash
python -m src.pipeline load-warehouse
```

## Como Desbloquear a Execucao

Instale Docker Desktop ou disponibilize um PostgreSQL acessivel e configure:

```text
POSTGRES_HOST=localhost
POSTGRES_PORT=55432
POSTGRES_DB=commercepulse
POSTGRES_USER=commercepulse
POSTGRES_PASSWORD=commercepulse
```

Depois execute:

```bash
docker compose up -d postgres
python -m src.pipeline init-warehouse
python -m src.pipeline load-warehouse
```

Alternativa local sem Docker no Windows:

```powershell
.\scripts\start_local_postgres.ps1
$env:POSTGRES_PORT = "55432"
python -m src.pipeline init-warehouse
python -m src.pipeline load-warehouse
```

Parar a instancia local:

```powershell
.\scripts\stop_local_postgres.ps1
```
