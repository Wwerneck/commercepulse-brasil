select
    date_key,
    date,
    day,
    day_of_week,
    day_name,
    week,
    month,
    month_name,
    quarter,
    year,
    is_weekend
from {{ source('analytics', 'dim_date') }}
