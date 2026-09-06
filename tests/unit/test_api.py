from datetime import UTC, date, datetime

from fastapi import HTTPException
from fastapi.testclient import TestClient

from api import services
from api.main import app
from api.schemas import (
    AnomalyDay,
    CategoryPerformance,
    CustomerSegmentSummary,
    KpiResponse,
    ObservabilityResponse,
    SalesPoint,
)

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_catalog_endpoint_lists_gold_and_reports(monkeypatch) -> None:
    monkeypatch.setattr(
        services,
        "catalog",
        lambda: {
            "gold": [],
            "model_outputs": [],
            "latest_reports": {"kpis": "data/gold/_analytics_reports/kpis.json"},
        },
    )

    response = client.get("/catalog")

    assert response.status_code == 200
    assert "kpis" in response.json()["latest_reports"]


def test_latest_kpis_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        services,
        "kpis",
        lambda: KpiResponse(
            period_start=date(2016, 9, 4),
            period_end=date(2018, 9, 3),
            gmv_total=1000.0,
            revenue_total=900.0,
            orders_total=10,
            customers_total=9,
            items_sold_total=12,
            average_ticket=100.0,
            average_freight=20.0,
            average_review_score=4.2,
            report_path="report.json",
        ),
    )

    response = client.get("/kpis/latest")

    assert response.status_code == 200
    payload = response.json()
    assert payload["gmv_total"] == 1000.0
    assert payload["orders_total"] == 10


def test_sales_daily_endpoint_respects_limit(monkeypatch) -> None:
    def fake_sales_daily(limit: int) -> list[SalesPoint]:
        return [
            SalesPoint(
                period=date(2018, 1, day),
                orders=day,
                customers=day,
                items_sold=day,
                revenue=100.0,
                freight_value=10.0,
                gmv=110.0,
                average_ticket=100.0,
            )
            for day in range(1, limit + 1)
        ]

    monkeypatch.setattr(services, "sales_daily", fake_sales_daily)

    response = client.get("/sales/daily?limit=3")

    assert response.status_code == 200
    assert len(response.json()) == 3


def test_sales_daily_endpoint_rejects_invalid_limit() -> None:
    response = client.get("/sales/daily?limit=0")

    assert response.status_code == 422


def test_categories_top_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        services,
        "top_categories",
        lambda limit: [
            CategoryPerformance(
                category=f"category_{index}",
                orders=10 - index,
                items_sold=20 - index,
                revenue=100.0 - index,
                freight_value=10.0,
                gmv=110.0 - index,
                average_ticket=10.0,
            )
            for index in range(limit)
        ],
    )

    response = client.get("/categories/top?limit=5")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 5
    assert payload[0]["gmv"] >= payload[-1]["gmv"]


def test_customer_segments_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        services,
        "customer_segments",
        lambda: [
            CustomerSegmentSummary(
                ml_segment="standard",
                customers=100,
                average_recency_days=50.0,
                average_frequency=1.0,
                average_monetary=200.0,
            )
        ],
    )

    response = client.get("/customers/segments")

    assert response.status_code == 200
    assert sum(item["customers"] for item in response.json()) == 100


def test_anomalies_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        services,
        "anomalies",
        lambda limit, only_overlap=False: [
            AnomalyDay(
                date=date(2018, 1, 1),
                gmv=100.0,
                orders=1,
                average_ticket=100.0,
                freight_value=10.0,
                isolation_forest_anomaly=True,
                any_zscore_anomaly=False,
                anomaly_method_overlap=False,
            )
        ][:limit],
    )

    response = client.get("/anomalies?limit=5")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_latest_ml_report_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(services, "latest_report_path", lambda report_type: "report.json")
    monkeypatch.setattr(
        services,
        "latest_report",
        lambda report_type: {
            "generated_at": datetime.now(UTC).isoformat(),
            "best_model": "linear_regression",
        },
    )

    response = client.get("/ml/reports/forecast/latest")

    assert response.status_code == 200
    payload = response.json()
    assert payload["report_type"] == "forecast"
    assert payload["payload"]["best_model"] == "linear_regression"


def test_unknown_report_type_returns_404(monkeypatch) -> None:
    def raise_unknown_report(report_type: str) -> str:
        raise HTTPException(status_code=404, detail=f"Unknown report type: {report_type}")

    monkeypatch.setattr(services, "latest_report_path", raise_unknown_report)

    response = client.get("/ml/reports/unknown/latest")

    assert response.status_code == 404


def test_observability_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        services,
        "observability",
        lambda: ObservabilityResponse(
            generated_at=datetime.now(UTC),
            status="passed",
            checks_total=1,
            checks_failed=0,
            checks_warned=0,
            checks=[],
            report_path="data/gold/_monitoring_reports/observability.json",
        ),
    )

    response = client.get("/observability")

    assert response.status_code == 200
    assert response.json()["status"] == "passed"
