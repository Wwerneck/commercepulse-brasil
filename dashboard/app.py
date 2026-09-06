from __future__ import annotations

import os
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

API_BASE_URL = os.getenv("COMMERCEPULSE_API_URL", "http://127.0.0.1:8000")

EXECUTIVE_COLORS = ["#1F4E79", "#2E7D6B", "#B07D2B", "#6E5A8A", "#A64B3C", "#4F6F52"]

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
            padding-top: 1.2rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }
        h1 {
            color: #172033;
            font-size: 2.45rem !important;
            line-height: 1.05;
            margin-bottom: 0.35rem;
        }
        h2, h3 {
            color: #172033;
            letter-spacing: 0;
        }
        .stSelectbox div[data-baseweb="select"] > div {
            background: #eef1f5;
            border: 1px solid #d7dde6;
            border-radius: 8px;
            min-height: 52px;
        }
        .hero-panel {
            border: 1px solid #d9e1ea;
            border-radius: 8px;
            padding: 18px 20px;
            background: linear-gradient(135deg, #172033 0%, #1F4E79 62%, #2E7D6B 100%);
            color: #ffffff;
            margin: 0.35rem 0 1rem 0;
        }
        .hero-title {
            font-size: 1.02rem;
            font-weight: 700;
            margin-bottom: 4px;
        }
        .hero-text {
            color: #e9eef5;
            font-size: 0.92rem;
        }
        .kpi-card {
            background: #ffffff;
            border: 1px solid #dfe5ec;
            border-radius: 8px;
            padding: 16px 18px;
            box-shadow: 0 8px 22px rgba(23, 32, 51, 0.06);
            min-height: 128px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            border-top: 4px solid #1F4E79;
            margin-bottom: 1rem;
        }
        .kpi-label {
            color: #5d6678;
            font-size: 0.82rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0;
            white-space: nowrap;
        }
        .kpi-value {
            color: #0f1b2d;
            font-size: clamp(1.55rem, 2.4vw, 2.2rem);
            line-height: 1.05;
            font-weight: 700;
            margin-top: 8px;
            white-space: nowrap;
        }
        .kpi-note {
            color: #667085;
            font-size: 0.8rem;
            margin-top: 8px;
        }
        .executive-strip {
            border: 1px solid #dfe5ec;
            border-radius: 8px;
            padding: 15px 18px;
            background: #f7f9fb;
            color: #344054;
            margin: 0.35rem 0 1rem 0;
            box-shadow: 0 4px 16px rgba(23, 32, 51, 0.04);
        }
        .status-ok {
            color: #7FE0B5;
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


def format_compact_currency(value: float | int | None) -> str:
    if value is None:
        return "-"
    if abs(value) >= 1_000_000:
        return f"R$ {value / 1_000_000:.2f} mi".replace(".", ",")
    if abs(value) >= 1_000:
        return f"R$ {value / 1_000:.1f} mil".replace(".", ",")
    return format_currency(value)


def format_compact_number(value: float | int | None) -> str:
    if value is None:
        return "-"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f} mi".replace(".", ",")
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f} mil".replace(".", ",")
    return format_number(value)


def humanize_label(value: str) -> str:
    words = value.replace("_", " ").split()
    return " ".join(word.capitalize() for word in words)


def api_status() -> bool:
    try:
        fetch_json("/health")
    except requests.RequestException:
        return False
    return True


def style_figure(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        height=420,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        colorway=EXECUTIVE_COLORS,
        margin={"l": 28, "r": 24, "t": 62, "b": 34},
        font={"family": "Arial", "size": 13, "color": "#344054"},
        title={"font": {"size": 18, "color": "#172033"}, "x": 0.02, "xanchor": "left"},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor="#d9e1ea")
    fig.update_yaxes(gridcolor="#edf1f5", zeroline=False, linecolor="#d9e1ea")
    return fig


def render_kpi_card(label: str, value: str, note: str = "", accent: str = "#1F4E79") -> None:
    st.markdown(
        f"""
        <div class="kpi-card" style="border-top-color: {accent};">
            <div>
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
            </div>
            <div class="kpi-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> str:
    online = api_status()
    status_class = "status-ok" if online else "status-off"
    status_text = "online" if online else "offline"
    st.title("CommercePulse Brasil")
    st.markdown(
        f"""
        <div class="hero-panel">
            <div class="hero-title">Painel executivo de performance, economia e IA</div>
            <div class="hero-text">
                E-commerce brasileiro integrado a indicadores oficiais, modelos analiticos
                e observabilidade operacional.
                API <span class="{status_class}">{status_text}</span>.
            </div>
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
    with cols[0]:
        render_kpi_card(
            "GMV total",
            format_compact_currency(kpis["gmv_total"]),
            "Valor bruto vendido",
        )
    with cols[1]:
        render_kpi_card(
            "Receita",
            format_compact_currency(kpis["revenue_total"]),
            "Produtos sem frete",
            "#2E7D6B",
        )
    with cols[2]:
        render_kpi_card(
            "Pedidos",
            format_compact_number(kpis["orders_total"]),
            "Pedidos com itens",
            "#B07D2B",
        )
    with cols[3]:
        render_kpi_card(
            "Clientes",
            format_compact_number(kpis["customers_total"]),
            "Base atendida",
            "#6E5A8A",
        )
    with cols[4]:
        render_kpi_card("Avaliacao", f"{kpis['average_review_score']:.2f}", "Nota media", "#A64B3C")

    cols = st.columns(4)
    with cols[0]:
        render_kpi_card("Ticket medio", format_currency(kpis["average_ticket"]), "Por item vendido")
    with cols[1]:
        render_kpi_card(
            "Frete medio",
            format_currency(kpis["average_freight"]),
            "Media diaria",
            "#2E7D6B",
        )
    with cols[2]:
        render_kpi_card(
            "Entrega media",
            f"{kpis['average_delivery_days']:.2f} dias",
            "Prazo medio",
            "#B07D2B",
        )
    with cols[3]:
        render_kpi_card(
            "Taxa de atraso",
            format_percent(kpis["average_delay_rate"]),
            "Entregas fora do prazo",
            "#A64B3C",
        )

    st.markdown(
        f"""
        <div class="executive-strip">
            Periodo analisado: <strong>{kpis["period_start"]}</strong> a
            <strong>{kpis["period_end"]}</strong>. Categoria lider por GMV:
            <strong>{humanize_label(kpis["top_category_by_gmv"])}</strong>.
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns((2, 1))
    with left:
        monthly["GMV"] = monthly["gmv"]
        fig = px.line(
            monthly,
            x="period",
            y="GMV",
            markers=True,
            title="Evolucao mensal do GMV",
            labels={"period": "Mes"},
        )
        fig.update_traces(line={"width": 3, "color": "#1F4E79"}, marker={"size": 8})
        st.plotly_chart(style_figure(fig), use_container_width=True)
    with right:
        categories_chart = categories.sort_values("gmv")
        categories_chart["categoria"] = categories_chart["category"].map(humanize_label)
        fig = px.bar(
            categories_chart,
            x="gmv",
            y="categoria",
            orientation="h",
            title="Categorias lideres",
            labels={"gmv": "GMV", "category": "Categoria"},
        )
        fig.update_traces(marker={"color": "#2E7D6B"})
        st.plotly_chart(style_figure(fig), use_container_width=True)

    segments["segmento"] = segments["ml_segment"].map(SEGMENT_LABELS).fillna(segments["ml_segment"])
    fig = px.treemap(
        segments,
        path=["segmento"],
        values="customers",
        color="average_monetary",
        color_continuous_scale=["#dfe8f2", "#1F4E79"],
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
    fig.update_traces(line={"width": 3, "color": "#1F4E79"}, marker={"size": 7})
    st.plotly_chart(style_figure(fig), use_container_width=True)

    cols = st.columns(2)
    with cols[0]:
        fig = px.bar(monthly, x="period", y="orders", title="Pedidos mensais")
        fig.update_traces(marker={"color": "#2E7D6B"})
        st.plotly_chart(style_figure(fig), use_container_width=True)
    with cols[1]:
        fig = px.line(monthly, x="period", y="average_ticket", markers=True, title="Ticket medio")
        fig.update_traces(line={"width": 3, "color": "#B07D2B"}, marker={"size": 7})
        st.plotly_chart(style_figure(fig), use_container_width=True)
    st.dataframe(daily, use_container_width=True, hide_index=True)


def render_categories() -> None:
    st.subheader("Categorias")
    limit = st.slider("Quantidade de categorias", min_value=5, max_value=50, value=20)
    categories = dataframe_from_api("/categories/top", {"limit": limit})
    categories["categoria"] = categories["category"].map(humanize_label)

    fig = px.scatter(
        categories,
        x="orders",
        y="gmv",
        size="items_sold",
        color="average_ticket",
        hover_name="categoria",
        color_continuous_scale=["#dfe8f2", "#1F4E79"],
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
        color_discrete_sequence=EXECUTIVE_COLORS,
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
        color_continuous_scale=["#dfe8f2", "#1F4E79"],
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
        color_discrete_sequence=EXECUTIVE_COLORS,
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
        color_discrete_sequence=["#2E7D6B", "#A64B3C"],
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
    try:
        report = fetch_json("/observability")
    except requests.HTTPError as exc:
        st.error(
            "Nao foi possivel carregar a observabilidade. "
            "Reinicie a API para garantir que a versao atual esteja em execucao."
        )
        st.code(f"uvicorn api.main:app --host 127.0.0.1 --port 8000\n\n{exc}")
        return
    except requests.RequestException as exc:
        st.error("API indisponivel no momento.")
        st.code(f"uvicorn api.main:app --host 127.0.0.1 --port 8000\n\n{exc}")
        return
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
