select
    s.month,
    s.orders,
    s.customers,
    s.items_sold,
    s.revenue,
    s.freight_value,
    s.gmv,
    s.average_ticket,
    s.gmv_mom_growth,
    e.selic_target,
    e.usd_brl,
    e.ibc_br,
    e.ipca
from {{ ref('stg_sales_monthly') }} s
left join {{ ref('stg_economic_indicators') }} e
    on s.month = e.reference_month
