select
    reference_month,
    selic_target,
    usd_brl,
    ibc_br,
    ipca
from {{ source('analytics', 'fact_economic_indicators') }}
