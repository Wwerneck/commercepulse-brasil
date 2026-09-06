select
    month,
    orders,
    customers,
    items_sold,
    revenue,
    freight_value,
    gmv,
    average_ticket,
    gmv_mom_growth,
    selic_target,
    usd_brl,
    ibc_br,
    ipca
from {{ ref('int_sales_economic_monthly') }}
