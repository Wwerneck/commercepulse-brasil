# Observability

## Status

FASE 23 concluida em 2026-09-06.

A camada de observabilidade gera um relatorio operacional com checks de disponibilidade, leitura, volume e frescor dos principais artefatos do projeto.

## Comando

```bash
python -m src.pipeline observability-report
```

## Saida

Os relatorios sao gravados em:

```text
data/gold/_monitoring_reports/
```

O ultimo resultado executado localmente foi:

```text
status=passed, checks=25, failed=0, warned=0
```

## Checks

A observabilidade valida:

- datasets Gold obrigatorios;
- outputs de ML;
- relatorios de qualidade Bronze, Silver e Gold;
- relatorios analiticos;
- relatorios de forecast, segmentacao, anomalias e reviews;
- leitura dos arquivos Parquet;
- parsing dos arquivos JSON;
- idade dos artefatos em horas.

## API

Endpoint:

```text
GET /observability
```

Esse endpoint gera e retorna o relatorio operacional mais recente em formato tipado pela FastAPI.

## Dashboard

O Streamlit possui uma pagina `Observabilidade` com:

- status geral;
- total de checks;
- falhas criticas;
- avisos;
- distribuicao por status e severidade;
- tabela operacional dos checks.

## Airflow

A DAG `commercepulse_pipeline` possui a tarefa final:

```text
observability_report
```

Ela roda depois de analytics, analise economica e processos de ML.
