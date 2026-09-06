select
    d.date,
    d.year,
    d.month,
    d.month_name,
    d.quarter,
    d.is_weekend,
    s.orders,
    s.customers,
    s.items_sold,
    s.revenue,
    s.freight_value,
    s.gmv,
    s.average_ticket,
    s.average_freight
from {{ ref('stg_sales_daily') }} s
join {{ ref('stg_dim_date') }} d
    on s.date_key = d.date_key
