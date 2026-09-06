select
    date_key,
    orders,
    customers,
    items_sold,
    revenue,
    freight_value,
    gmv,
    average_ticket,
    average_freight
from {{ source('analytics', 'fact_sales_daily') }}
