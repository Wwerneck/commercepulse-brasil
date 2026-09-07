from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

API_BASE_URL = os.getenv("COMMERCEPULSE_API_URL", "http://127.0.0.1:8000")
SAMPLE_DATA_PATH = Path(__file__).with_name("sample_data.json")

EXECUTIVE_COLORS = ["#1F4E79", "#2E7D6B", "#B07D2B", "#6E5A8A", "#A64B3C", "#4F6F52"]

PAGES = [
    "Resumo Executivo",
    "Vendas",
    "Categorias",
    "Análise Econômica",
    "Aprendizado de Máquina",
    "Anomalias",
    "Observabilidade",
    "Catálogo",
]
PAGE_QUERY_VALUES = {
    "resumo": "Resumo Executivo",
    "vendas": "Vendas",
    "categorias": "Categorias",
    "economia": "Análise Econômica",
    "ml": "Aprendizado de Máquina",
    "anomalias": "Anomalias",
    "observabilidade": "Observabilidade",
    "catalogo": "Catálogo",
}

METRIC_LABELS = {
    "gmv": "GMV",
    "orders": "Pedidos",
    "average_ticket": "Ticket médio",
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

STATUS_LABELS = {"passed": "Aprovado", "warning": "Atenção", "failed": "Falha"}

REPORT_LABELS = {
    "kpis": "Indicadores-chave de desempenho",
    "economic": "Análise econômica",
    "forecast": "Previsão de vendas",
    "segmentation": "Segmentação de clientes",
    "anomaly": "Detecção de anomalias",
    "reviews": "Inteligência de avaliações",
}

st.set_page_config(page_title="CommercePulse Brasil", layout="wide")


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        #MainMenu, footer, header, [data-testid="stToolbar"], [data-testid="stDecoration"] {
            visibility: hidden;
            height: 0;
        }
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
            padding: 18px 20px;
            box-shadow: 0 8px 22px rgba(23, 32, 51, 0.06);
            min-height: 136px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            border-top: 4px solid #1F4E79;
            margin-bottom: 1rem;
            overflow: hidden;
        }
        .kpi-label {
            color: #5d6678;
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0;
            white-space: nowrap;
        }
        .kpi-value {
            color: #0f1b2d;
            font-size: clamp(1.55rem, 2vw, 2rem);
            line-height: 1.08;
            font-weight: 700;
            margin-top: 8px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .kpi-note {
            color: #667085;
            font-size: 0.78rem;
            margin-top: 8px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
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
    try:
        response = requests.get(f"{API_BASE_URL}{path}", params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return sample_response(path, params=params)


@st.cache_data
def load_sample_data() -> dict[str, Any]:
    if not SAMPLE_DATA_PATH.exists():
        return {}
    return json.loads(SAMPLE_DATA_PATH.read_text(encoding="utf-8"))


def sample_response(path: str, params: dict[str, Any] | None = None) -> Any:
    sample = load_sample_data()
    limit = int((params or {}).get("limit", 500))

    if path == "/health":
        return {"status": "demo", "app": "commercepulse-brasil", "version": "0.1.0"}
    if path == "/kpis/latest":
        return sample["kpis"]
    if path == "/sales/daily":
        return sample["sales_daily"][:limit]
    if path == "/sales/monthly":
        return sample["sales_monthly"][:limit]
    if path == "/categories/top":
        return sample["categories_top"][:limit]
    if path == "/customers/segments":
        return sample["customer_segments"]
    if path == "/customers/segments/categories":
        return sample.get("segment_categories", [])
    if path == "/anomalies":
        anomalies = sample["anomalies"]
        if (params or {}).get("only_overlap"):
            anomalies = [item for item in anomalies if item["anomaly_method_overlap"]]
        return anomalies[:limit]
    if path == "/observability":
        return sample["observability"]
    if path == "/catalog":
        return sample["catalog"]
    if path.startswith("/ml/reports/") and path.endswith("/latest"):
        report_type = path.split("/")[3]
        return {"report_type": report_type, "path": "", "payload": sample["reports"][report_type]}
    raise requests.HTTPError(f"Unsupported sample endpoint: {path}")


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
        return f"R$ {value / 1_000_000:.1f} mi".replace(".", ",")
    if abs(value) >= 1_000:
        return f"R$ {value / 1_000:.1f} mil".replace(".", ",")
    return format_currency(value)


def format_compact_number(value: float | int | None) -> str:
    if value is None:
        return "-"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f} mi".replace(".", ",")
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f} mil".replace(".", ",")
    return format_number(value)


def add_bar_labels(fig: go.Figure) -> go.Figure:
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(uniformtext={"mode": "hide", "minsize": 10})
    return fig


def format_age(value: float | int | None) -> str:
    if value is None:
        return "-"
    if value < 1:
        return f"{value * 60:.0f} min"
    return f"{value:.1f} h"


def observability_area(name: str) -> str:
    if name.startswith("gold_"):
        return "Gold"
    if name.startswith("model_output_"):
        return "ML outputs"
    if name.startswith("report_"):
        return "Relatórios"
    return "Sistema"


def humanize_label(value: str) -> str:
    words = value.replace("_", " ").split()
    return " ".join(word.capitalize() for word in words)


def normalize_path(value: str) -> str:
    return value.replace("\\", "/")


def page_index_from_query(page_value: str | None) -> int:
    if not page_value:
        return 0
    page = PAGE_QUERY_VALUES.get(page_value.lower(), page_value)
    return PAGES.index(page) if page in PAGES else 0


def api_status() -> bool:
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=3)
        response.raise_for_status()
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
    status_text = "online" if online else "modo demonstracao"
    st.title("CommercePulse Brasil")
    st.markdown(
        f"""
        <div class="hero-panel">
            <div class="hero-title">Painel executivo de performance, economia e IA</div>
            <div class="hero-text">
                E-commerce brasileiro integrado a indicadores oficiais, modelos analíticos
                e observabilidade operacional.
                API <span class="{status_class}">{status_text}</span>.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    requested_page = st.query_params.get("page")
    return st.selectbox(
        "Selecionar visão",
        PAGES,
        index=page_index_from_query(requested_page),
        label_visibility="collapsed",
    )


def render_overview() -> None:
    kpis = fetch_json("/kpis/latest")
    monthly = dataframe_from_api("/sales/monthly", {"limit": 24}).sort_values("period")
    categories = dataframe_from_api("/categories/top", {"limit": 10})
    segments = dataframe_from_api("/customers/segments")

    cols = st.columns(3)
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

    cols = st.columns(3)
    with cols[0]:
        render_kpi_card(
            "Clientes",
            format_compact_number(kpis["customers_total"]),
            "Base atendida",
            "#6E5A8A",
        )
    with cols[1]:
        render_kpi_card("Avaliação", f"{kpis['average_review_score']:.2f}", "Nota média", "#A64B3C")
    with cols[2]:
        render_kpi_card("Ticket médio", format_currency(kpis["average_ticket"]), "Por item vendido")

    cols = st.columns(3)
    with cols[0]:
        render_kpi_card(
            "Frete médio",
            format_currency(kpis["average_freight"]),
            "Media diaria",
            "#2E7D6B",
        )
    with cols[2]:
        render_kpi_card(
            "Entrega media",
            f"{kpis['average_delivery_days']:.2f} dias",
            "Prazo médio",
            "#B07D2B",
        )
    with cols[1]:
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
            <strong>{kpis["period_end"]}</strong>. Categoria líder por GMV:
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
            title="Evolução mensal do GMV",
            labels={"period": "Mês", "GMV": "GMV"},
            hover_data={"orders": ":,.0f", "customers": ":,.0f", "average_ticket": ":.2f"},
        )
        fig.update_traces(line={"width": 3, "color": "#1F4E79"}, marker={"size": 8})
        st.plotly_chart(style_figure(fig), use_container_width=True)
    with right:
        categories_chart = categories.sort_values("gmv")
        categories_chart["categoria"] = categories_chart["category"].map(humanize_label)
        categories_chart["gmv_label"] = categories_chart["gmv"].map(format_compact_currency)
        fig = px.bar(
            categories_chart,
            x="gmv",
            y="categoria",
            orientation="h",
            text="gmv_label",
            title="Categorias líderes",
            labels={"gmv": "GMV", "categoria": "Categoria"},
            hover_data={"orders": ":,.0f", "items_sold": ":,.0f", "average_ticket": ":.2f"},
        )
        fig.update_traces(marker={"color": "#2E7D6B"})
        add_bar_labels(fig)
        st.plotly_chart(style_figure(fig), use_container_width=True)

    segments["segmento"] = segments["ml_segment"].map(SEGMENT_LABELS).fillna(segments["ml_segment"])
    segments["clientes"] = segments["customers"].map(format_compact_number)
    segments["valor_medio"] = segments["average_monetary"].map(format_currency)
    segments_chart = segments.sort_values("customers", ascending=True)

    left, right = st.columns((2, 1))
    with left:
        fig = px.bar(
            segments_chart,
            x="customers",
            y="segmento",
            orientation="h",
            text="clientes",
            color="average_monetary",
            color_continuous_scale=["#dfe8f2", "#1F4E79"],
            title="Clientes por segmento",
            labels={
                "customers": "Clientes",
                "segmento": "Segmento",
                "average_monetary": "Valor medio",
            },
            hover_data={
                "clientes": False,
                "average_monetary": ":.2f",
                "average_recency_days": ":.1f",
                "average_frequency": ":.2f",
            },
        )
        fig.update_layout(coloraxis_colorbar={"title": "Valor medio"})
        add_bar_labels(fig)
        st.plotly_chart(style_figure(fig), use_container_width=True)
    with right:
        segment_table = segments.sort_values("customers", ascending=False)[
            ["segmento", "clientes", "valor_medio", "average_recency_days"]
        ].rename(
            columns={
                "segmento": "Segmento",
                "clientes": "Clientes",
                "valor_medio": "Valor medio",
                "average_recency_days": "Recencia media",
            }
        )
        segment_table["Recencia media"] = segment_table["Recencia media"].map(
            lambda value: f"{value:.1f} dias"
        )
        st.dataframe(segment_table, use_container_width=True, hide_index=True)

    segment_categories = dataframe_from_api("/customers/segments/categories")
    if not segment_categories.empty:
        segment_categories["segmento"] = (
            segment_categories["ml_segment"]
            .map(SEGMENT_LABELS)
            .fillna(segment_categories["ml_segment"])
        )
        segment_categories["categoria"] = segment_categories["category"].map(humanize_label)
        segment_categories["gmv_label"] = segment_categories["gmv"].map(format_compact_currency)
        segment_categories["pedidos"] = segment_categories["orders"].map(format_number)
        segment_categories["itens"] = segment_categories["items"].map(format_number)
        st.subheader("Categorias mais desejadas por segmento")
        for tab, segment_name in zip(
            st.tabs(["Padrão", "Recentes", "Em risco"]),
            ["Padrao", "Recentes", "Em risco"],
            strict=False,
        ):
            with tab:
                segment_slice = segment_categories[
                    segment_categories["segmento"] == segment_name
                ].sort_values("gmv", ascending=True)
                if segment_slice.empty:
                    st.info("Sem categorias para este segmento.")
                    continue
                fig = px.bar(
                    segment_slice,
                    x="gmv",
                    y="categoria",
                    orientation="h",
                    text="gmv_label",
                    title=f"Top categorias - {segment_name}",
                    labels={"gmv": "GMV", "categoria": "Categoria"},
                    hover_data={
                        "pedidos": False,
                        "itens": False,
                        "orders": ":,.0f",
                        "items": ":,.0f",
                    },
                )
                fig.update_traces(marker={"color": "#1F4E79"})
                add_bar_labels(fig)
                st.plotly_chart(style_figure(fig), use_container_width=True)
                st.dataframe(
                    segment_slice.sort_values("gmv", ascending=False)[
                        ["categoria", "gmv_label", "pedidos", "itens"]
                    ].rename(
                        columns={
                            "categoria": "Categoria",
                            "gmv_label": "GMV",
                            "pedidos": "Pedidos",
                            "itens": "Itens",
                        }
                    ),
                    use_container_width=True,
                    hide_index=True,
                )


def render_sales() -> None:
    st.subheader("Vendas")
    daily_limit = st.slider("Dias recentes", min_value=7, max_value=180, value=60, step=1)
    daily = dataframe_from_api("/sales/daily", {"limit": daily_limit}).sort_values("period")
    monthly = dataframe_from_api("/sales/monthly", {"limit": 24}).sort_values("period")

    metric = st.segmented_control(
        "Métrica",
        ["gmv", "orders", "average_ticket"],
        format_func=lambda item: METRIC_LABELS[item],
        default="gmv",
    )
    fig = px.line(
        daily,
        x="period",
        y=metric,
        labels={"period": "Data", metric: METRIC_LABELS[metric]},
        title=f"{METRIC_LABELS[metric]} diário",
        hover_data={"orders": ":,.0f", "gmv": ":.2f", "average_ticket": ":.2f"},
    )
    fig.update_traces(line={"width": 3, "color": "#1F4E79"}, marker={"size": 7})
    st.plotly_chart(style_figure(fig), use_container_width=True)

    cols = st.columns(2)
    with cols[0]:
        monthly["orders_label"] = monthly["orders"].map(format_compact_number)
        fig = px.bar(
            monthly,
            x="period",
            y="orders",
            text="orders_label",
            title="Pedidos mensais",
            labels={"period": "Mês", "orders": "Pedidos"},
            hover_data={"gmv": ":.2f", "average_ticket": ":.2f"},
        )
        fig.update_traces(marker={"color": "#2E7D6B"})
        add_bar_labels(fig)
        st.plotly_chart(style_figure(fig), use_container_width=True)
    with cols[1]:
        fig = px.line(
            monthly,
            x="period",
            y="average_ticket",
            markers=True,
            title="Ticket médio mensal",
            labels={"period": "Mês", "average_ticket": "Ticket médio"},
            hover_data={"orders": ":,.0f", "gmv": ":.2f"},
        )
        fig.update_traces(line={"width": 3, "color": "#B07D2B"}, marker={"size": 7})
        st.plotly_chart(style_figure(fig), use_container_width=True)
    st.dataframe(daily, use_container_width=True, hide_index=True)


def render_categories() -> None:
    st.subheader("Categorias")
    limit = st.slider("Quantidade de categorias", min_value=5, max_value=50, value=20)
    categories = dataframe_from_api("/categories/top", {"limit": limit})
    categories["categoria"] = categories["category"].map(humanize_label)
    categories["gmv_label"] = categories["gmv"].map(format_compact_currency)

    fig = px.scatter(
        categories,
        x="orders",
        y="gmv",
        size="items_sold",
        color="average_ticket",
        text="categoria",
        hover_name="categoria",
        color_continuous_scale=["#dfe8f2", "#1F4E79"],
        title="Categorias por escala, GMV e ticket médio",
        labels={
            "orders": "Pedidos",
            "gmv": "GMV",
            "items_sold": "Itens vendidos",
            "average_ticket": "Ticket médio",
        },
        hover_data={"gmv_label": False, "revenue": ":.2f", "freight_value": ":.2f"},
    )
    fig.update_traces(textposition="top center")
    st.plotly_chart(style_figure(fig), use_container_width=True)
    st.dataframe(categories, use_container_width=True, hide_index=True)


def render_economic_analysis() -> None:
    st.subheader("Análise Econômica")
    report = fetch_json("/ml/reports/economic/latest")["payload"]
    correlations = pd.DataFrame(report["correlations"])
    correlations["correlacao_abs"] = correlations["correlation"].abs()
    strongest = correlations.sort_values("correlacao_abs", ascending=False).iloc[0]

    cols = st.columns(4)
    with cols[0]:
        render_kpi_card("Correlações", format_number(len(correlations)), "Combinações avaliadas")
    with cols[1]:
        render_kpi_card(
            "Maior relação",
            f"{strongest['metric']} x {strongest['indicator']}",
            "Maior valor absoluto",
            "#2E7D6B",
        )
    with cols[2]:
        render_kpi_card("Correlação", f"{strongest['correlation']:.3f}", "Coeficiente", "#B07D2B")
    with cols[3]:
        render_kpi_card(
            "Observações",
            format_number(strongest["observations"]),
            "Meses analisados",
            "#6E5A8A",
        )

    fig = px.bar(
        correlations.sort_values("correlation"),
        x="correlation",
        y="indicator",
        color="metric",
        orientation="h",
        title="Correlações entre vendas e indicadores econômicos",
        labels={"correlation": "Correlação", "indicator": "Indicador", "metric": "Métrica"},
        color_discrete_sequence=EXECUTIVE_COLORS,
    )
    st.plotly_chart(style_figure(fig), use_container_width=True)
    st.info("As correlações são descritivas e não implicam causalidade.")
    st.dataframe(
        correlations.drop(columns=["correlacao_abs"]),
        use_container_width=True,
        hide_index=True,
    )


def render_ml() -> None:
    st.subheader("Aprendizado de Máquina")
    forecast = fetch_json("/ml/reports/forecast/latest")["payload"]
    segmentation = fetch_json("/ml/reports/segmentation/latest")["payload"]
    reviews = fetch_json("/ml/reports/reviews/latest")["payload"]
    segments = dataframe_from_api("/customers/segments")
    segments["segmento"] = segments["ml_segment"].map(SEGMENT_LABELS).fillna(segments["ml_segment"])
    segments["clientes"] = segments["customers"].map(format_compact_number)

    cols = st.columns(4)
    with cols[0]:
        render_kpi_card("Melhor modelo", forecast["best_model"], "Menor MAE")
    with cols[1]:
        render_kpi_card(
            "Clientes segmentados",
            format_compact_number(segmentation["rows"]),
            "Base RFM",
            "#2E7D6B",
        )
    with cols[2]:
        render_kpi_card("K selecionado", str(segmentation["selected_k"]), "Clusters", "#B07D2B")
    with cols[3]:
        render_kpi_card(
            "Cobertura textual",
            format_percent(reviews["text_coverage_ratio"]),
            "Reviews com texto",
            "#A64B3C",
        )

    fig = px.bar(
        segments.sort_values("customers", ascending=True),
        x="customers",
        y="segmento",
        orientation="h",
        text="clientes",
        color="average_monetary",
        color_continuous_scale=["#dfe8f2", "#1F4E79"],
        title="Clientes por segmento",
        labels={"segmento": "Segmento", "customers": "Clientes", "average_monetary": "Valor médio"},
    )
    add_bar_labels(fig)
    st.plotly_chart(style_figure(fig), use_container_width=True)

    metric_rows = pd.DataFrame(forecast["metrics"])
    error_rows = metric_rows.melt(
        id_vars=["model_name"],
        value_vars=["mae", "rmse"],
        var_name="metric",
        value_name="value",
    )
    error_rows["metric"] = error_rows["metric"].map(METRIC_LABELS)
    error_rows["value_label"] = error_rows["value"].map(format_compact_currency)
    fig = px.bar(
        error_rows,
        x="model_name",
        y="value",
        color="metric",
        text="value_label",
        barmode="group",
        title="Erro dos modelos de previsão",
        labels={"model_name": "Modelo", "value": "Erro em GMV", "metric": "Métrica"},
        color_discrete_sequence=EXECUTIVE_COLORS,
    )
    add_bar_labels(fig)
    st.plotly_chart(style_figure(fig), use_container_width=True)
    metric_rows["mape"] = metric_rows["mape"].map(format_percent)
    metric_rows["mae"] = metric_rows["mae"].map(format_currency)
    metric_rows["rmse"] = metric_rows["rmse"].map(format_currency)
    metric_rows = metric_rows.rename(
        columns={"model_name": "Modelo", "mae": "MAE", "rmse": "RMSE", "mape": "MAPE"}
    )
    st.dataframe(metric_rows, use_container_width=True, hide_index=True)
    st.dataframe(segments, use_container_width=True, hide_index=True)


def render_anomalies() -> None:
    st.subheader("Anomalias")
    only_overlap = st.toggle("Somente sobreposição entre métodos", value=False)
    anomalies = dataframe_from_api("/anomalies", {"limit": 100, "only_overlap": only_overlap})
    report = fetch_json("/ml/reports/anomaly/latest")["payload"]

    cols = st.columns(3)
    with cols[0]:
        render_kpi_card("Z-score", str(report["zscore_anomaly_days"]), "Dias sinalizados")
    with cols[1]:
        render_kpi_card(
            "Isolation Forest",
            str(report["isolation_forest_anomaly_days"]),
            "Dias sinalizados",
            "#2E7D6B",
        )
    with cols[2]:
        render_kpi_card("Sobreposição", str(report["overlap_days"]), "Ambos os métodos", "#B07D2B")

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
        title="Dias com comportamento anômalo",
        labels={
            "date": "Data",
            "gmv": "GMV",
            "orders": "Pedidos",
            "anomaly_method_overlap": "Sobreposição",
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
            "Não foi possível carregar a observabilidade. "
            "Reinicie a API para garantir que a versão atual esteja em execução."
        )
        st.code(f"uvicorn api.main:app --host 127.0.0.1 --port 8000\n\n{exc}")
        return
    except requests.RequestException as exc:
        st.error("API indisponível no momento.")
        st.code(f"uvicorn api.main:app --host 127.0.0.1 --port 8000\n\n{exc}")
        return
    cols = st.columns(4)
    with cols[0]:
        render_kpi_card("Status geral", STATUS_LABELS.get(report["status"], report["status"]))
    with cols[1]:
        render_kpi_card("Checks", str(report["checks_total"]), "Validações executadas", "#2E7D6B")
    with cols[2]:
        render_kpi_card("Falhas críticas", str(report["checks_failed"]), "Bloqueantes", "#A64B3C")
    with cols[3]:
        render_kpi_card("Avisos", str(report["checks_warned"]), "Não bloqueantes", "#B07D2B")

    checks = pd.DataFrame(report["checks"])
    if checks.empty:
        st.info("Nenhum check registrado.")
        return
    checks["area"] = checks["name"].map(observability_area)
    checks["status_label"] = checks["status"].map(STATUS_LABELS).fillna(checks["status"])
    checks["check"] = checks["name"].map(humanize_label)
    checks["rows"] = checks["details"].map(
        lambda item: item.get("rows") if isinstance(item, dict) else None
    )
    checks["age_hours"] = checks["details"].map(
        lambda item: item.get("age_hours") if isinstance(item, dict) else None
    )
    checks["path"] = checks["details"].map(
        lambda item: normalize_path(item.get("path", item.get("pattern", "")))
        if isinstance(item, dict)
        else ""
    )

    by_area = (
        checks.groupby("area", as_index=False)
        .agg(
            checks=("name", "count"),
            failures=("status", lambda values: int((values == "failed").sum())),
            avg_age_hours=("age_hours", "mean"),
        )
        .sort_values("checks", ascending=True)
    )
    by_area["checks_label"] = by_area["checks"].map(format_number)
    by_area["avg_age"] = by_area["avg_age_hours"].map(format_age)

    left, right = st.columns((1, 1))
    with left:
        fig = px.bar(
            by_area,
            x="checks",
            y="area",
            orientation="h",
            text="checks_label",
            color="failures",
            color_continuous_scale=["#2E7D6B", "#A64B3C"],
            title="Checks por área monitorada",
            labels={"checks": "Checks", "area": "Área", "failures": "Falhas"},
            hover_data={"avg_age": True, "avg_age_hours": False},
        )
        add_bar_labels(fig)
        st.plotly_chart(style_figure(fig), use_container_width=True)
    with right:
        freshness = by_area.sort_values("avg_age_hours", ascending=False)
        st.write("Atualização dos artefatos")
        st.dataframe(
            freshness[["area", "checks_label", "avg_age"]].rename(
                columns={"area": "Área", "checks_label": "Checks", "avg_age": "Idade média"}
            ),
            use_container_width=True,
            hide_index=True,
        )

    attention = checks[checks["status"] == "failed"]
    if attention.empty:
        st.success("Todos os checks monitorados estao aprovados.")
    else:
        st.warning("Existem checks que precisam de revisão.")
        st.dataframe(
            attention[["area", "check", "status_label", "severity", "message", "path"]].rename(
                columns={
                    "area": "Área",
                    "check": "Check",
                    "status_label": "Status",
                    "severity": "Severidade",
                    "message": "Mensagem",
                    "path": "Caminho",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

    audit = checks.sort_values(["area", "severity", "check"])[
        ["area", "check", "status_label", "severity", "rows", "age_hours", "path"]
    ].rename(
        columns={
            "area": "Área",
            "check": "Check",
            "status_label": "Status",
            "severity": "Severidade",
            "rows": "Linhas",
            "age_hours": "Idade",
            "path": "Caminho",
        }
    )
    audit["Linhas"] = audit["Linhas"].map(
        lambda value: "-" if pd.isna(value) else format_number(value)
    )
    audit["Idade"] = audit["Idade"].map(lambda value: None if pd.isna(value) else value)
    audit["Idade"] = audit["Idade"].map(format_age)
    st.write("Inventário de checks")
    st.dataframe(audit, use_container_width=True, hide_index=True)


def render_catalog() -> None:
    st.subheader("Catálogo")
    catalog = fetch_json("/catalog")
    gold = pd.DataFrame(catalog["gold"])
    outputs = pd.DataFrame(catalog["model_outputs"])
    reports = pd.DataFrame(
        [
            {
                "relatório": REPORT_LABELS.get(report_type, humanize_label(report_type)),
                "tipo": report_type,
                "caminho": normalize_path(path),
            }
            for report_type, path in catalog["latest_reports"].items()
        ]
    )

    cols = st.columns(3)
    with cols[0]:
        render_kpi_card("Datasets Gold", format_number(len(gold)), "Camada analitica")
    with cols[1]:
        render_kpi_card(
            "Outputs de ML",
            format_number(len(outputs)),
            "Artefatos consumidos",
            "#2E7D6B",
        )
    with cols[2]:
        render_kpi_card(
            "Relatorios",
            format_number(len(reports)),
            "Ultimos artefatos",
            "#B07D2B",
        )

    st.write("Datasets Gold")
    if gold.empty:
        st.info("Nenhum dataset Gold encontrado.")
    else:
        gold["nome"] = gold["name"].map(humanize_label)
        gold["linhas"] = gold["rows"].map(format_number)
        gold["colunas"] = gold["columns"].map(len)
        gold["caminho"] = gold["path"].map(normalize_path)
        st.dataframe(
            gold[["nome", "linhas", "colunas", "caminho"]],
            use_container_width=True,
            hide_index=True,
        )

    st.write("Outputs de aprendizado de máquina")
    if outputs.empty:
        st.info("Nenhum output de aprendizado de máquina encontrado.")
    else:
        outputs["nome"] = outputs["name"].map(humanize_label)
        outputs["linhas"] = outputs["rows"].map(format_number)
        outputs["colunas"] = outputs["columns"].map(len)
        outputs["caminho"] = outputs["path"].map(normalize_path)
        st.dataframe(
            outputs[["nome", "linhas", "colunas", "caminho"]],
            use_container_width=True,
            hide_index=True,
        )

    st.write("Relatorios recentes")
    if reports.empty:
        st.info("Nenhum relatório recente encontrado.")
    else:
        st.dataframe(reports, use_container_width=True, hide_index=True)


def main() -> None:
    apply_theme()
    page = render_header()

    if page == "Resumo Executivo":
        render_overview()
    elif page == "Vendas":
        render_sales()
    elif page == "Categorias":
        render_categories()
    elif page == "Análise Econômica":
        render_economic_analysis()
    elif page == "Aprendizado de Máquina":
        render_ml()
    elif page == "Anomalias":
        render_anomalies()
    elif page == "Observabilidade":
        render_observability()
    else:
        render_catalog()


if __name__ == "__main__":
    main()
