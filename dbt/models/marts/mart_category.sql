select
    category,
    orders,
    items_sold,
    revenue,
    freight_value,
    gmv,
    average_ticket
from {{ ref('stg_category_performance') }}
