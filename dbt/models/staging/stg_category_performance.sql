select
    category,
    orders,
    items_sold,
    revenue,
    freight_value,
    gmv,
    average_ticket
from {{ source('analytics', 'fact_category_performance') }}
