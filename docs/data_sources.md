# Data Sources

## Olist

Dataset publico transacional usado como base de e-commerce. A ingestao espera os arquivos CSV originais em um diretorio local informado pelo usuario.

## Banco Central do Brasil

O projeto usa o SGS. O formato validado e:

```text
https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo_serie}/dados?formato=json&dataInicial={DD/MM/AAAA}&dataFinal={DD/MM/AAAA}
```

As series serao mantidas em configuracao para permitir inclusao futura sem duplicar URLs pelo codigo.
As primeiras series configuradas ficam em `config/economic_indicators.json`.

## IBGE/SIDRA

O projeto usa o endpoint:

```text
https://apisidra.ibge.gov.br/values/t/{tabela}/...
```

Codigos de tabelas, variaveis, periodos, territorios e classificacoes devem ser documentados antes de entrar em producao no pipeline.
As consultas SIDRA tambem ficam em `config/economic_indicators.json`.
