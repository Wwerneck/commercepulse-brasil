# Architecture Review

## Status

FASE 26 concluida em 2026-09-06.

## Resumo

O projeto esta estruturado como uma plataforma local de Engenharia de Dados e IA para e-commerce brasileiro, combinando dados transacionais da Olist com indicadores oficiais do Banco Central e IBGE.

## Pontos Fortes

- Separacao clara entre Bronze, Silver e Gold.
- Ingestoes economicas configuraveis por JSON.
- Validacoes de qualidade por camada.
- Gold gerada com DuckDB sobre Parquet.
- Warehouse dimensional em PostgreSQL.
- dbt com staging, intermediate e marts.
- Airflow orquestrando a CLI existente.
- MLflow rastreando experimentos e artefatos.
- FastAPI expondo contratos tipados.
- Streamlit consumindo a API.
- Observabilidade operacional sobre datasets e relatorios.
- Docker Compose e GitHub Actions preparados para reproducibilidade.

## Decisoes Validadas

- Parquet e DuckDB sao adequados para desenvolvimento local e analise colunar.
- PostgreSQL entra como camada de warehouse, nao como copia bruta dos arquivos.
- A CLI central em `src.pipeline` evita duplicacao entre execucao local e Airflow.
- A API le artefatos Gold e ML sem acoplar o dashboard a detalhes de armazenamento.
- A observabilidade roda depois dos processos analiticos e de ML, como fechamento operacional.

## Riscos e Limitacoes

- O dataset Olist e historico, entao previsoes sao demonstrativas e nao operacionais em tempo real.
- Algumas execucoes completas dependem dos arquivos locais em `data/` e `models/`, que nao sao versionados.
- Docker nao foi executado neste ambiente porque o CLI `docker` nao esta disponivel no PATH.
- O Airflow local nao foi iniciado com pacote nativo instalado; a DAG foi validada por import estatico e preparada para Docker.

## Melhorias Futuras

- Publicar artefatos de exemplo reduzidos para demo sem baixar todo o dataset.
- Adicionar endpoint de forecast inferencial usando modelo registrado.
- Adicionar camada de permissao/autenticacao caso a API seja exposta publicamente.
- Evoluir CI para build Docker quando Docker estiver disponivel no runner.
- Criar release tag e screenshots do dashboard para o README.
