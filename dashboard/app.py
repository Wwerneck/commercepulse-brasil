from __future__ import annotations

import os
from typing import Any

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

API_BASE_URL = os.getenv("COMMERCEPULSE_API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="CommercePulse Brasil", layout="wide")


@st.cache_data(ttl=300)
def fetch_json(path: str, params: dict[str, Any] | None = None) -> Any:
    response = requests.get(f"{API_BASE_URL}{path}", params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def dataframe_from_api(path: str, params: dict[str, Any] | None = None) -> pd.DataFrame:
    return pd.DataFrame(fetch_json(path, params=params))


def format_currency(value: float | int | None) -> str:
    if value is None:
        return "-"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_number(value: float | int | None) -> str:
    if value is None:
        return "-"
    return f"{value:,.0f}".replace(",", ".")


def api_status() -> bool:
    try:
        fetch_json("/health")
    except requests.RequestException:
        return False
    return True


def render_header() -> None:
    st.title("CommercePulse Brasil")
    st.caption("E-commerce brasileiro, indicadores economicos, analytics e Machine Learning.")
    status = "online" if api_status() else "offline"
    st.sidebar.metric("API", status)
    st.sidebar.caption(API_BASE_URL)


def render_overview() -> None:
    kpis = fetch_json("/kpis/latest")
    cols = st.columns(5)
    cols[0].metric("GMV", format_currency(kpis["gmv_total"]))
    cols[1].metric("Receita", format_currency(kpis["revenue_total"]))
    cols[2].metric("Pedidos", format_number(kpis["orders_total"]))
    cols[3].metric("Clientes", format_number(kpis["customers_total"]))
    cols[4].metric("Review medio", f"{kpis['average_review_score']:.2f}")

    cols = st.columns(4)
    cols[0].metric("Ticket medio", format_currency(kpis["average_ticket"]))
    cols[1].metric("Frete medio", format_currency(kpis["average_freight"]))
    cols[2].metric("Entrega media", f"{kpis['average_delivery_days']:.2f} dias")
    cols[3].metric("Categoria lider", kpis["top_category_by_gmv"])

    monthly = dataframe_from_api("/sales/monthly", {"limit": 24}).sort_values("period")
    categories = dataframe_from_api("/categories/top", {"limit": 10})

    left, right = st.columns((2, 1))
    with left:
        st.subheader("GMV Mensal")
        st.plotly_chart(
            px.line(monthly, x="period", y="gmv", markers=True, labels={"gmv": "GMV"}),
            use_container_width=True,
        )
    with right:
        st.subheader("Top Categorias")
        st.plotly_chart(
            px.bar(categories, x="gmv", y="category", orientation="h", labels={"gmv": "GMV"}),
            use_container_width=True,
        )


def render_sales() -> None:
    st.subheader("Series de Vendas")
    daily_limit = st.slider("Dias recentes", min_value=7, max_value=180, value=60, step=1)
    daily = dataframe_from_api("/sales/daily", {"limit": daily_limit}).sort_values("period")
    monthly = dataframe_from_api("/sales/monthly", {"limit": 24}).sort_values("period")

    metric = st.segmented_control("Metrica", ["gmv", "orders", "average_ticket"], default="gmv")
    st.plotly_chart(
        px.line(daily, x="period", y=metric, labels={metric: metric}),
        use_container_width=True,
    )

    cols = st.columns(2)
    cols[0].plotly_chart(
        px.bar(monthly, x="period", y="orders", labels={"orders": "Pedidos"}),
        use_container_width=True,
    )
    cols[1].plotly_chart(
        px.line(monthly, x="period", y="average_ticket", markers=True),
        use_container_width=True,
    )
    st.dataframe(daily, use_container_width=True, hide_index=True)


def render_categories() -> None:
    st.subheader("Performance por Categoria")
    limit = st.slider("Categorias", min_value=5, max_value=50, value=20)
    categories = dataframe_from_api("/categories/top", {"limit": limit})

    st.plotly_chart(
        px.scatter(
            categories,
            x="orders",
            y="gmv",
            size="items_sold",
            color="average_ticket",
            hover_name="category",
        ),
        use_container_width=True,
    )
    st.dataframe(categories, use_container_width=True, hide_index=True)


def render_ml() -> None:
    st.subheader("Machine Learning")
    forecast = fetch_json("/ml/reports/forecast/latest")["payload"]
    segmentation = fetch_json("/ml/reports/segmentation/latest")["payload"]
    reviews = fetch_json("/ml/reports/reviews/latest")["payload"]
    segments = dataframe_from_api("/customers/segments")

    cols = st.columns(4)
    cols[0].metric("Melhor forecast", forecast["best_model"])
    cols[1].metric("Clientes segmentados", format_number(segmentation["rows"]))
    cols[2].metric("K selecionado", segmentation["selected_k"])
    cols[3].metric("Cobertura de texto", f"{reviews['text_coverage_ratio']:.1%}")

    st.plotly_chart(
        px.bar(segments, x="ml_segment", y="customers", color="average_monetary"),
        use_container_width=True,
    )
    st.dataframe(segments, use_container_width=True, hide_index=True)

    metric_rows = pd.DataFrame(forecast["metrics"])
    st.plotly_chart(
        px.bar(metric_rows, x="model_name", y=["mae", "rmse", "mape"], barmode="group"),
        use_container_width=True,
    )


def render_anomalies() -> None:
    st.subheader("Anomalias")
    only_overlap = st.toggle("Somente sobreposicao entre metodos", value=False)
    anomalies = dataframe_from_api("/anomalies", {"limit": 100, "only_overlap": only_overlap})
    report = fetch_json("/ml/reports/anomaly/latest")["payload"]

    cols = st.columns(3)
    cols[0].metric("Z-score", report["zscore_anomaly_days"])
    cols[1].metric("Isolation Forest", report["isolation_forest_anomaly_days"])
    cols[2].metric("Sobreposicao", report["overlap_days"])

    if anomalies.empty:
        st.info("Nenhuma anomalia encontrada para o filtro selecionado.")
        return
    st.plotly_chart(
        px.scatter(
            anomalies,
            x="date",
            y="gmv",
            size="orders",
            color="anomaly_method_overlap",
        ),
        use_container_width=True,
    )
    st.dataframe(anomalies, use_container_width=True, hide_index=True)


def render_catalog() -> None:
    st.subheader("Catalogo e Relatorios")
    catalog = fetch_json("/catalog")
    st.write("Datasets Gold")
    st.dataframe(pd.DataFrame(catalog["gold"]), use_container_width=True, hide_index=True)
    st.write("Outputs de ML")
    st.dataframe(pd.DataFrame(catalog["model_outputs"]), use_container_width=True, hide_index=True)
    st.write("Relatorios recentes")
    st.json(catalog["latest_reports"])


def render_observability() -> None:
    st.subheader("Observabilidade")
    report = fetch_json("/observability")
    cols = st.columns(4)
    cols[0].metric("Status", report["status"])
    cols[1].metric("Checks", report["checks_total"])
    cols[2].metric("Falhas criticas", report["checks_failed"])
    cols[3].metric("Avisos", report["checks_warned"])

    checks = pd.DataFrame(report["checks"])
    if checks.empty:
        st.info("Nenhum check registrado.")
        return
    st.plotly_chart(
        px.histogram(checks, x="status", color="severity", barmode="group"),
        use_container_width=True,
    )
    st.dataframe(checks.drop(columns=["details"]), use_container_width=True, hide_index=True)


def main() -> None:
    render_header()
    if not api_status():
        st.error("API indisponivel. Inicie com: uvicorn api.main:app --host 127.0.0.1 --port 8000")
        return

    page = st.sidebar.radio(
        "Pagina",
        [
            "Visao Geral",
            "Vendas",
            "Categorias",
            "Machine Learning",
            "Anomalias",
            "Observabilidade",
            "Catalogo",
        ],
    )
    if page == "Visao Geral":
        render_overview()
    elif page == "Vendas":
        render_sales()
    elif page == "Categorias":
        render_categories()
    elif page == "Machine Learning":
        render_ml()
    elif page == "Anomalias":
        render_anomalies()
    elif page == "Observabilidade":
        render_observability()
    else:
        render_catalog()


if __name__ == "__main__":
    main()
