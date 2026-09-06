from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import FastAPI, Query

from api import services
from api.schemas import (
    AnomalyDay,
    CatalogResponse,
    CategoryPerformance,
    CustomerSegmentSummary,
    HealthResponse,
    KpiResponse,
    ObservabilityResponse,
    ReportResponse,
    SalesPoint,
)

app = FastAPI(title="CommercePulse Brasil API", version="0.1.0")


LimitParam = Annotated[int, Query(ge=1, le=500)]


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        app="commercepulse-brasil",
        version=app.version,
        checked_at=datetime.now(UTC),
    )


@app.get("/catalog", response_model=CatalogResponse, tags=["metadata"])
def catalog() -> dict[str, Any]:
    return services.catalog()


@app.get("/kpis/latest", response_model=KpiResponse, tags=["analytics"])
def latest_kpis() -> KpiResponse:
    return services.kpis()


@app.get("/sales/daily", response_model=list[SalesPoint], tags=["analytics"])
def sales_daily(limit: LimitParam = 30) -> list[SalesPoint]:
    return services.sales_daily(limit=limit)


@app.get("/sales/monthly", response_model=list[SalesPoint], tags=["analytics"])
def sales_monthly(limit: LimitParam = 24) -> list[SalesPoint]:
    return services.sales_monthly(limit=limit)


@app.get("/categories/top", response_model=list[CategoryPerformance], tags=["analytics"])
def top_categories(limit: LimitParam = 10) -> list[CategoryPerformance]:
    return services.top_categories(limit=limit)


@app.get("/customers/segments", response_model=list[CustomerSegmentSummary], tags=["ml"])
def customer_segments() -> list[CustomerSegmentSummary]:
    return services.customer_segments()


@app.get("/anomalies", response_model=list[AnomalyDay], tags=["ml"])
def anomalies(
    limit: LimitParam = 50,
    only_overlap: bool = False,
) -> list[AnomalyDay]:
    return services.anomalies(limit=limit, only_overlap=only_overlap)


@app.get("/ml/reports/{report_type}/latest", response_model=ReportResponse, tags=["ml"])
def latest_ml_report(report_type: str) -> ReportResponse:
    path = services.latest_report_path(report_type)
    return ReportResponse(
        report_type=report_type,
        path=services._normalize_path(path),
        payload=services.latest_report(report_type),
    )


@app.get("/observability", response_model=ObservabilityResponse, tags=["system"])
def observability() -> ObservabilityResponse:
    return services.observability()
