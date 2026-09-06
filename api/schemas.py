from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    checked_at: datetime


class DatasetInfo(BaseModel):
    name: str
    path: str
    rows: int
    columns: list[str]


class CatalogResponse(BaseModel):
    gold: list[DatasetInfo]
    model_outputs: list[DatasetInfo]
    latest_reports: dict[str, str]


class KpiResponse(BaseModel):
    period_start: date
    period_end: date
    gmv_total: float
    revenue_total: float
    orders_total: int
    customers_total: int
    items_sold_total: int
    average_ticket: float
    average_freight: float
    active_sellers: int | None = None
    average_delivery_days: float | None = None
    average_delay_rate: float | None = None
    average_review_score: float | None = None
    best_month_by_gmv: date | None = None
    top_category_by_gmv: str | None = None
    report_path: str


class SalesPoint(BaseModel):
    period: date
    orders: int
    customers: int
    items_sold: int
    revenue: float
    freight_value: float
    gmv: float
    average_ticket: float


class CategoryPerformance(BaseModel):
    category: str
    orders: int
    items_sold: int
    revenue: float
    freight_value: float
    gmv: float
    average_ticket: float


class CustomerSegmentSummary(BaseModel):
    ml_segment: str
    customers: int
    average_recency_days: float
    average_frequency: float
    average_monetary: float


class AnomalyDay(BaseModel):
    date: date
    gmv: float
    orders: int
    average_ticket: float
    freight_value: float
    isolation_forest_anomaly: bool
    any_zscore_anomaly: bool
    anomaly_method_overlap: bool


class ReportResponse(BaseModel):
    report_type: str
    path: str
    payload: dict[str, Any] = Field(default_factory=dict)


class ObservabilityCheckResponse(BaseModel):
    name: str
    status: str
    severity: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ObservabilityResponse(BaseModel):
    generated_at: datetime
    status: str
    checks_total: int
    checks_failed: int
    checks_warned: int
    checks: list[ObservabilityCheckResponse]
    report_path: str
