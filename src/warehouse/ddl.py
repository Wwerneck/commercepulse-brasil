WAREHOUSE_DDL = """
create schema if not exists raw;
create schema if not exists staging;
create schema if not exists analytics;
create schema if not exists monitoring;

create table if not exists analytics.dim_date (
    date_key integer primary key,
    date date not null unique,
    day integer not null,
    day_of_week integer not null,
    day_name text not null,
    week integer not null,
    month integer not null,
    month_name text not null,
    quarter integer not null,
    year integer not null,
    is_weekend boolean not null
);

create table if not exists analytics.dim_customer (
    customer_id text primary key,
    customer_unique_id text not null,
    customer_state text,
    customer_city text
);

create table if not exists analytics.dim_seller (
    seller_id text primary key,
    seller_state text,
    seller_city text
);

create table if not exists analytics.dim_category (
    category_key bigserial primary key,
    category text not null unique
);

create table if not exists analytics.dim_economic_indicator (
    indicator_name text primary key,
    source text
);

create table if not exists analytics.fact_sales_daily (
    date_key integer primary key references analytics.dim_date(date_key),
    orders bigint not null,
    customers bigint not null,
    items_sold bigint not null,
    revenue numeric(18, 2),
    freight_value numeric(18, 2),
    gmv numeric(18, 2),
    average_ticket numeric(18, 2),
    average_freight numeric(18, 2)
);

create table if not exists analytics.fact_sales_monthly (
    month date primary key,
    orders bigint not null,
    customers bigint not null,
    items_sold bigint not null,
    revenue numeric(18, 2),
    freight_value numeric(18, 2),
    gmv numeric(18, 2),
    average_ticket numeric(18, 2),
    gmv_mom_growth double precision
);

create table if not exists analytics.fact_category_performance (
    category text primary key references analytics.dim_category(category),
    orders bigint not null,
    items_sold bigint not null,
    revenue numeric(18, 2),
    freight_value numeric(18, 2),
    gmv numeric(18, 2),
    average_ticket numeric(18, 2)
);

create table if not exists analytics.fact_economic_indicators (
    reference_month date primary key,
    selic_target double precision,
    usd_brl double precision,
    ibc_br double precision,
    ipca double precision
);
"""

TRUNCATE_ANALYTICS_SQL = """
truncate table
    analytics.fact_economic_indicators,
    analytics.fact_category_performance,
    analytics.fact_sales_monthly,
    analytics.fact_sales_daily,
    analytics.dim_economic_indicator,
    analytics.dim_category,
    analytics.dim_seller,
    analytics.dim_customer,
    analytics.dim_date
restart identity cascade;
"""
