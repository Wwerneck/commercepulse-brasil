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
from {{ ref('stg_sales_monthly') }}
