select
    month,
    orders,
    customers,
    items_sold,
    revenue,
    freight_value,
    gmv,
    average_ticket,
    gmv_mom_growth
from {{ source('analytics', 'fact_sales_monthly') }}
