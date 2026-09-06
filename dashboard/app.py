from __future__ import annotations

import os
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

API_BASE_URL = os.getenv("COMMERCEPULSE_API_URL", "http://127.0.0.1:8000")

PAGES = [
    "Resumo Executivo",
    "Vendas",
    "Categorias",
    "Analise Economica",
    "Aprendizado de Maquina",
    "Anomalias",
    "Observabilidade",
    "Catalogo",
]

METRIC_LABELS = {
    "gmv": "GMV",
    "orders": "Pedidos",
    "average_ticket": "Ticket medio",
    "mae": "MAE",
    "rmse": "RMSE",
    "mape": "MAPE",
}

SEGMENT_LABELS = {
    "at_risk": "Em risco",
    "recent": "Recentes",
    "standard": "Padrao",
    "vip": "VIP",
}

STATUS_LABELS = {"passed": "Aprovado", "warning": "Atencao", "failed": "Falha"}

st.set_page_config(page_title="CommercePulse Brasil", layout="wide")


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.6rem;
            padding-bottom: 2rem;
            max-width: 1320px;
        }
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e6e8eb;
            border-radius: 8px;
            padding: 14px 16px;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
        }
        div[data-testid="stMetricLabel"] p {
            color: #475467;
            font-size: 0.86rem;
        }
        div[data-testid="stMetricValue"] {
            color: #101828;
            font-weight: 700;
        }
        .executive-strip {
            border: 1px solid #e6e8eb;
            border-radius: 8px;
            padding: 14px 16px;
            background: #f8fafc;
            color: #344054;
            margin: 0.35rem 0 1rem 0;
        }
        .status-ok {
            color: #067647;
            font-weight: 700;
        }
        .status-off {
            color: #b42318;
            font-weight: 700;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


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


def format_percent(value: float | int | None) -> str:
    if value is None:
        return "-"
    return f"{value:.2%}".replace(".", ",")


def api_status() -> bool:
    try:
        fetch_json("/health")
    except requests.RequestException:
        return False
    return True


def style_figure(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        height=390,
        margin={"l": 20, "r": 20, "t": 45, "b": 20},
        font={"family": "Arial", "size": 13, "color": "#344054"},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#eef2f6")
    return fig


def render_header() -> str:
    st.title("CommercePulse Brasil")
    online = api_status()
    status_class = "status-ok" if online else "status-off"
    status_text = "online" if online else "offline"
    st.markdown(
        f"""
        <div class="executive-strip">
            Plataforma executiva de dados e IA para e-commerce brasileiro.
            API <span class="{status_class}">{status_text}</span> em {API_BASE_URL}.
        </div>
        """,
        unsafe_allow_html=True,
    )
    return st.selectbox("Selecionar visao", PAGES, index=0, label_visibility="collapsed")


def render_overview() -> None:
    kpis = fetch_json("/kpis/latest")
    monthly = dataframe_from_api("/sales/monthly", {"limit": 24}).sort_values("period")
    categories = dataframe_from_api("/categories/top", {"limit": 10})
    segments = dataframe_from_api("/customers/segments")

    cols = st.columns(5)
    cols[0].metric("GMV total", format_currency(kpis["gmv_total"]))
    cols[1].metric("Receita de produtos", format_currency(kpis["revenue_total"]))
    cols[2].metric("Pedidos", format_number(kpis["orders_total"]))
    cols[3].metric("Clientes", format_number(kpis["customers_total"]))
    cols[4].metric("Avaliacao media", f"{kpis['average_review_score']:.2f}")

    cols = st.columns(4)
    cols[0].metric("Ticket medio", format_currency(kpis["average_ticket"]))
    cols[1].metric("Frete medio", format_currency(kpis["average_freight"]))
    cols[2].metric("Entrega media", f"{kpis['average_delivery_days']:.2f} dias")
    cols[3].metric("Taxa de atraso", format_percent(kpis["average_delay_rate"]))

    st.markdown(
        f"""
        <div class="executive-strip">
            Periodo analisado: <strong>{kpis["period_start"]}</strong> a
            <strong>{kpis["period_end"]}</strong>. Categoria lider por GMV:
            <strong>{kpis["top_category_by_gmv"]}</strong>.
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns((2, 1))
    with left:
        fig = px.line(
            monthly,
            x="period",
            y="gmv",
            markers=True,
            title="Evolucao mensal do GMV",
            labels={"period": "Mes", "gmv": "GMV"},
        )
        st.plotly_chart(style_figure(fig), use_container_width=True)
    with right:
        categories_chart = categories.sort_values("gmv")
        fig = px.bar(
            categories_chart,
            x="gmv",
            y="category",
            orientation="h",
            title="Categorias lideres",
            labels={"gmv": "GMV", "category": "Categoria"},
        )
        st.plotly_chart(style_figure(fig), use_container_width=True)

    segments["segmento"] = segments["ml_segment"].map(SEGMENT_LABELS).fillna(segments["ml_segment"])
    fig = px.treemap(
        segments,
        path=["segmento"],
        values="customers",
        color="average_monetary",
        title="Composicao da base por segmento de cliente",
    )
    st.plotly_chart(style_figure(fig), use_container_width=True)


def render_sales() -> None:
    st.subheader("Vendas")
    daily_limit = st.slider("Dias recentes", min_value=7, max_value=180, value=60, step=1)
    daily = dataframe_from_api("/sales/daily", {"limit": daily_limit}).sort_values("period")
    monthly = dataframe_from_api("/sales/monthly", {"limit": 24}).sort_values("period")

    metric = st.segmented_control(
        "Metrica",
        ["gmv", "orders", "average_ticket"],
        format_func=lambda item: METRIC_LABELS[item],
        default="gmv",
    )
    fig = px.line(
        daily,
        x="period",
        y=metric,
        labels={"period": "Data", metric: METRIC_LABELS[metric]},
        title=f"{METRIC_LABELS[metric]} diario",
    )
    st.plotly_chart(style_figure(fig), use_container_width=True)

    cols = st.columns(2)
    with cols[0]:
        fig = px.bar(monthly, x="period", y="orders", title="Pedidos mensais")
        st.plotly_chart(style_figure(fig), use_container_width=True)
    with cols[1]:
        fig = px.line(monthly, x="period", y="average_ticket", markers=True, title="Ticket medio")
        st.plotly_chart(style_figure(fig), use_container_width=True)
    st.dataframe(daily, use_container_width=True, hide_index=True)


def render_categories() -> None:
    st.subheader("Categorias")
    limit = st.slider("Quantidade de categorias", min_value=5, max_value=50, value=20)
    categories = dataframe_from_api("/categories/top", {"limit": limit})

    fig = px.scatter(
        categories,
        x="orders",
        y="gmv",
        size="items_sold",
        color="average_ticket",
        hover_name="category",
        title="Categorias por escala, GMV e ticket medio",
        labels={
            "orders": "Pedidos",
            "gmv": "GMV",
            "items_sold": "Itens vendidos",
            "average_ticket": "Ticket medio",
        },
    )
    st.plotly_chart(style_figure(fig), use_container_width=True)
    st.dataframe(categories, use_container_width=True, hide_index=True)


def render_economic_analysis() -> None:
    st.subheader("Analise Economica")
    report = fetch_json("/ml/reports/economic/latest")["payload"]
    correlations = pd.DataFrame(report["correlations"])
    correlations["correlacao_abs"] = correlations["correlation"].abs()
    strongest = correlations.sort_values("correlacao_abs", ascending=False).iloc[0]

    cols = st.columns(4)
    cols[0].metric("Correlacoes", format_number(len(correlations)))
    cols[1].metric("Maior relacao", f"{strongest['metric']} x {strongest['indicator']}")
    cols[2].metric("Correlacao", f"{strongest['correlation']:.3f}")
    cols[3].metric("Observacoes", format_number(strongest["observations"]))

    fig = px.bar(
        correlations.sort_values("correlation"),
        x="correlation",
        y="indicator",
        color="metric",
        orientation="h",
        title="Correlacoes entre vendas e indicadores economicos",
        labels={"correlation": "Correlacao", "indicator": "Indicador", "metric": "Metrica"},
    )
    st.plotly_chart(style_figure(fig), use_container_width=True)
    st.info("As correlacoes sao descritivas e nao implicam causalidade.")
    st.dataframe(
        correlations.drop(columns=["correlacao_abs"]),
        use_container_width=True,
        hide_index=True,
    )


def render_ml() -> None:
    st.subheader("Aprendizado de Maquina")
    forecast = fetch_json("/ml/reports/forecast/latest")["payload"]
    segmentation = fetch_json("/ml/reports/segmentation/latest")["payload"]
    reviews = fetch_json("/ml/reports/reviews/latest")["payload"]
    segments = dataframe_from_api("/customers/segments")
    segments["segmento"] = segments["ml_segment"].map(SEGMENT_LABELS).fillna(segments["ml_segment"])

    cols = st.columns(4)
    cols[0].metric("Melhor modelo", forecast["best_model"])
    cols[1].metric("Clientes segmentados", format_number(segmentation["rows"]))
    cols[2].metric("K selecionado", segmentation["selected_k"])
    cols[3].metric("Cobertura textual", format_percent(reviews["text_coverage_ratio"]))

    fig = px.bar(
        segments,
        x="segmento",
        y="customers",
        color="average_monetary",
        title="Clientes por segmento",
        labels={"segmento": "Segmento", "customers": "Clientes", "average_monetary": "Valor medio"},
    )
    st.plotly_chart(style_figure(fig), use_container_width=True)

    metric_rows = pd.DataFrame(forecast["metrics"]).rename(columns=METRIC_LABELS)
    fig = px.bar(
        metric_rows,
        x="model_name",
        y=["MAE", "RMSE", "MAPE"],
        barmode="group",
        title="Comparacao dos modelos de forecast",
        labels={"model_name": "Modelo", "value": "Valor", "variable": "Metrica"},
    )
    st.plotly_chart(style_figure(fig), use_container_width=True)
    st.dataframe(segments, use_container_width=True, hide_index=True)


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
    fig = px.scatter(
        anomalies,
        x="date",
        y="gmv",
        size="orders",
        color="anomaly_method_overlap",
        title="Dias com comportamento anomalo",
        labels={
            "date": "Data",
            "gmv": "GMV",
            "orders": "Pedidos",
            "anomaly_method_overlap": "Sobreposicao",
        },
    )
    st.plotly_chart(style_figure(fig), use_container_width=True)
    st.dataframe(anomalies, use_container_width=True, hide_index=True)


def render_observability() -> None:
    st.subheader("Observabilidade")
    report = fetch_json("/observability")
    cols = st.columns(4)
    cols[0].metric("Status geral", STATUS_LABELS.get(report["status"], report["status"]))
    cols[1].metric("Checks", report["checks_total"])
    cols[2].metric("Falhas criticas", report["checks_failed"])
    cols[3].metric("Avisos", report["checks_warned"])

    checks = pd.DataFrame(report["checks"])
    if checks.empty:
        st.info("Nenhum check registrado.")
        return
    checks["status"] = checks["status"].map(STATUS_LABELS).fillna(checks["status"])
    fig = px.histogram(
        checks,
        x="status",
        color="severity",
        barmode="group",
        title="Distribuicao dos checks operacionais",
        labels={"status": "Status", "severity": "Severidade"},
    )
    st.plotly_chart(style_figure(fig), use_container_width=True)
    st.dataframe(checks.drop(columns=["details"]), use_container_width=True, hide_index=True)


def render_catalog() -> None:
    st.subheader("Catalogo")
    catalog = fetch_json("/catalog")
    st.write("Datasets Gold")
    st.dataframe(pd.DataFrame(catalog["gold"]), use_container_width=True, hide_index=True)
    st.write("Outputs de aprendizado de maquina")
    st.dataframe(pd.DataFrame(catalog["model_outputs"]), use_container_width=True, hide_index=True)
    st.write("Relatorios recentes")
    st.json(catalog["latest_reports"])


def main() -> None:
    apply_theme()
    page = render_header()
    if not api_status():
        st.error("API indisponivel. Inicie com: uvicorn api.main:app --host 127.0.0.1 --port 8000")
        return

    if page == "Resumo Executivo":
        render_overview()
    elif page == "Vendas":
        render_sales()
    elif page == "Categorias":
        render_categories()
    elif page == "Analise Economica":
        render_economic_analysis()
    elif page == "Aprendizado de Maquina":
        render_ml()
    elif page == "Anomalias":
        render_anomalies()
    elif page == "Observabilidade":
        render_observability()
    else:
        render_catalog()


if __name__ == "__main__":
    main()
