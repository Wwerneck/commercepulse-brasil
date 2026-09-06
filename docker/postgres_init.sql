create schema if not exists raw;
create schema if not exists staging;
create schema if not exists analytics;
create schema if not exists monitoring;

create table if not exists monitoring.pipeline_runs (
    run_id text primary key,
    pipeline_name text not null,
    started_at timestamptz not null,
    finished_at timestamptz,
    duration_seconds double precision,
    records_read bigint default 0,
    records_written bigint default 0,
    records_rejected bigint default 0,
    source text,
    destination text,
    status text not null,
    error_message text
);
