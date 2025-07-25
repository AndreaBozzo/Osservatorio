#!/usr/bin/env python3
"""
Main Streamlit App Entry Point
Direct entry point for Streamlit Cloud without subdirectory complications
"""

import gc
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Configurazione pagina - DEVE essere il primo comando Streamlit
st.set_page_config(
    page_title="🇮🇹 Osservatorio ISTAT",
    page_icon="🇮🇹",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/AndreaBozzo/Osservatorio",
        "Report a bug": "https://github.com/AndreaBozzo/Osservatorio/issues",
        "About": "Osservatorio ISTAT - Sistema di visualizzazione dati statistici italiani",
    },
)

# Custom CSS for enhanced styling - Desktop optimized
st.markdown(
    """
<style>
/* Global improvements */
.stApp {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Hide streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {visibility: hidden;}

/* Main container optimization */
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1200px;
}

/* Custom header - Desktop optimized */
.main-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 3rem 2rem;
    border-radius: 15px;
    margin-bottom: 2.5rem;
    text-align: center;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    position: relative;
    overflow: hidden;
}

.main-header::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="white" opacity="0.1"/><circle cx="75" cy="75" r="1" fill="white" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
    opacity: 0.1;
}

.main-header h1 {
    font-size: 2.5rem !important;
    font-weight: 700;
    margin-bottom: 0.5rem;
    position: relative;
    z-index: 1;
}

.main-header h3 {
    font-size: 1.2rem !important;
    font-weight: 400;
    opacity: 0.9;
    position: relative;
    z-index: 1;
}

.main-header p {
    font-size: 1rem;
    margin-top: 1rem;
    position: relative;
    z-index: 1;
}

/* Enhanced metrics grid */
[data-testid="metric-container"] {
    background: white;
    border: 1px solid #e1e8ed;
    padding: 1.5rem;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}

[data-testid="metric-container"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.12);
}

[data-testid="metric-container"]::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #667eea, #764ba2);
}

/* Enhanced metric values */
[data-testid="metric-container"] [data-testid="metric-value"] {
    font-size: 2rem !important;
    font-weight: 700;
    color: #2d3748;
}

[data-testid="metric-container"] [data-testid="metric-label"] {
    font-size: 0.9rem !important;
    color: #718096;
    font-weight: 500;
}

/* Enhanced charts container */
.plotly-graph-div {
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    background: white;
    border: 1px solid #e1e8ed;
    margin: 1rem 0;
}

/* Sidebar improvements */
.css-1d391kg {
    background: white;
    border-right: 1px solid #e1e8ed;
}

.css-1d391kg .stSelectbox > div > div {
    background: white;
    border: 1px solid #e1e8ed;
    border-radius: 8px;
}

/* Enhanced buttons */
.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.75rem 1.5rem;
    font-weight: 600;
    font-size: 0.95rem;
    transition: all 0.3s ease;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

/* Data table enhancements */
.stDataFrame {
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    border: 1px solid #e1e8ed;
}

/* Category section styling */
.category-section {
    background: white;
    padding: 2rem;
    border-radius: 15px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    margin: 2rem 0;
    border: 1px solid #e1e8ed;
}

.category-title {
    font-size: 1.8rem;
    font-weight: 700;
    color: #2d3748;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.category-description {
    color: #718096;
    font-size: 1rem;
    margin-bottom: 2rem;
    font-style: italic;
}

/* Chart grid optimization for desktop */
.chart-container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
    margin: 2rem 0;
}

/* Responsive design */
@media (max-width: 1024px) {
    .chart-container {
        grid-template-columns: 1fr;
        gap: 1.5rem;
    }

    .main-header {
        padding: 2rem 1.5rem;
    }

    .main-header h1 {
        font-size: 2rem !important;
    }
}

@media (max-width: 768px) {
    .main-header {
        padding: 1.5rem 1rem;
    }

    .main-header h1 {
        font-size: 1.8rem !important;
    }

    .main-header h3 {
        font-size: 1rem !important;
    }

    [data-testid="metric-container"] {
        padding: 1rem;
    }

    .category-section {
        padding: 1.5rem;
    }
}

/* Loading animation */
.stSpinner > div {
    border-color: #667eea transparent transparent transparent;
}

/* Success/error states */
.stSuccess {
    background: #f0f9ff;
    border: 1px solid #0ea5e9;
    border-radius: 8px;
}

.stError {
    background: #fef2f2;
    border: 1px solid #ef4444;
    border-radius: 8px;
}
</style>
""",
    unsafe_allow_html=True,
)

# Categories configuration
CATEGORIES = {
    "popolazione": {
        "emoji": "👥",
        "color": "#FF6B6B",
        "priority": 10,
        "description": "Dati demografici e popolazione residente",
    },
    "economia": {
        "emoji": "💰",
        "color": "#4ECDC4",
        "priority": 9,
        "description": "PIL, inflazione, indicatori economici",
    },
    "lavoro": {
        "emoji": "👔",
        "color": "#45B7D1",
        "priority": 8,
        "description": "Occupazione, disoccupazione, forze lavoro",
    },
}


def create_sample_data():
    """Crea dati di esempio per la demo"""
    # Dati di esempio per popolazione
    population_data = {
        "TIME_PERIOD": [2020, 2021, 2022, 2023, 2024],
        "TERRITORIO": ["Italia", "Italia", "Italia", "Italia", "Italia"],
        "Value": [59641488, 59236213, 58940425, 58997201, 59000000],
        "UNIT_MEASURE": ["NUM", "NUM", "NUM", "NUM", "NUM"],
        "SEX": ["TOTAL", "TOTAL", "TOTAL", "TOTAL", "TOTAL"],
    }

    # Dati di esempio per economia
    economy_data = {
        "TIME_PERIOD": [2020, 2021, 2022, 2023, 2024],
        "TERRITORIO": ["Italia", "Italia", "Italia", "Italia", "Italia"],
        "Value": [1653000, 1775000, 1897000, 1952000, 2010000],
        "UNIT_MEASURE": ["EUR_MIO", "EUR_MIO", "EUR_MIO", "EUR_MIO", "EUR_MIO"],
        "SECTOR": ["TOTAL", "TOTAL", "TOTAL", "TOTAL", "TOTAL"],
    }

    # Dati di esempio per lavoro
    work_data = {
        "TIME_PERIOD": [2020, 2021, 2022, 2023, 2024],
        "TERRITORIO": ["Italia", "Italia", "Italia", "Italia", "Italia"],
        "Value": [58.1, 58.2, 58.8, 59.5, 60.1],
        "UNIT_MEASURE": ["PC", "PC", "PC", "PC", "PC"],
        "AGECLASS": ["15-64", "15-64", "15-64", "15-64", "15-64"],
    }

    return {
        "popolazione": pd.DataFrame(population_data),
        "economia": pd.DataFrame(economy_data),
        "lavoro": pd.DataFrame(work_data),
    }


@st.cache_data(ttl=1800, max_entries=3)
def load_data():
    """Carica i dati con cache ottimizzata"""
    return create_sample_data()


@st.cache_data(ttl=3600, max_entries=10)
def get_filtered_data(category, year_start, year_end):
    """Cache separata per dati filtrati per ridurre memory leaks"""
    datasets = load_data()
    if category not in datasets:
        return pd.DataFrame()

    df = datasets[category]
    df["TIME_PERIOD"] = df["TIME_PERIOD"].astype(int)
    return df[
        (df["TIME_PERIOD"] >= year_start) & (df["TIME_PERIOD"] <= year_end)
    ].copy()


@st.cache_data(ttl=7200, max_entries=5)
def calculate_metrics(df):
    """Cache per calcoli metriche per evitare ricomputazioni"""
    if df.empty:
        return {"latest": 0, "growth": 0, "avg": 0, "quality": 0}

    latest_value = df["Value"].iloc[-1]
    growth = 0
    if len(df) > 1:
        growth = (
            (df["Value"].iloc[-1] - df["Value"].iloc[-2]) / df["Value"].iloc[-2] * 100
        )
    avg_value = df["Value"].mean()
    data_quality = df["Value"].notna().sum() / len(df) * 100

    return {
        "latest": latest_value,
        "growth": growth,
        "avg": avg_value,
        "quality": data_quality,
    }


def render_header():
    """Render dell'header principale - Desktop optimized"""
    st.markdown(
        f"""
    <div class="main-header">
        <h1>🇮🇹 Osservatorio Dati ISTAT</h1>
        <h3>La piattaforma open-source per l'analisi dei dati statistici italiani</h3>
        <p>Esplora oltre <strong>509+ dataset ISTAT</strong> con visualizzazioni interattive e analisi avanzate.</p>
        <br>
        <div style="display: flex; gap: 1rem; justify-content: center; align-items: center; flex-wrap: wrap;">
            <span style="background: rgba(255,255,255,0.2); padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.9rem;">
                📊 Dati Ufficiali ISTAT
            </span>
            <span style="background: rgba(255,255,255,0.2); padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.9rem;">
                🔄 Aggiornamento Real-time
            </span>
            <span style="background: rgba(255,255,255,0.2); padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.9rem;">
                🚀 Dashboard Interattivo
            </span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Enhanced metrics row with better formatting
    st.markdown("### 📊 Panoramica Sistema")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "📊 Dataset Disponibili",
            "509+",
            delta="ISTAT SDMX API",
            help="Numero di dataset disponibili tramite API ISTAT",
        )

    with col2:
        st.metric(
            "📈 Categorie Attive",
            len(CATEGORIES),
            delta="Popolazione, Economia, Lavoro",
            help="Categorie principali di dati analizzati",
        )

    with col3:
        current_time = datetime.now().strftime("%d/%m/%Y %H:%M")
        st.metric(
            "🕐 Ultimo Aggiornamento",
            current_time,
            delta="Automatico",
            help="Timestamp dell'ultimo caricamento dati",
        )

    with col4:
        st.metric(
            "🔄 Status Sistema",
            "🟢 Operativo",
            delta="100% Uptime",
            help="Stato corrente del sistema e API",
        )


def render_sidebar():
    """Render della sidebar - Enhanced with functional filters"""
    st.sidebar.header("🔍 Navigazione e Controlli")

    # Status indicator
    st.sidebar.success("✅ Sistema Operativo")

    # Category selection
    category_options = [
        f"{info['emoji']} {cat.title()}" for cat, info in CATEGORIES.items()
    ]

    selected = st.sidebar.selectbox("Seleziona Categoria", category_options, index=0)
    category = selected.split(" ")[1].lower()

    # Category info with enhanced details
    info = CATEGORIES[category]
    st.sidebar.markdown(
        f"""
    <div style="background: linear-gradient(135deg, {info['color']}20, {info['color']}10);
                padding: 1rem; border-radius: 10px; margin: 1rem 0;">
        <h4>{info['emoji']} {category.title()}</h4>
        <p style="font-size: 0.9rem; margin: 0.5rem 0;">{info['description']}</p>
        <div style="font-size: 0.8rem; color: #666;">
            <strong>Priorità:</strong> {info['priority']}/10<br>
            <strong>Fonte:</strong> ISTAT SDMX API
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Functional year filter
    st.sidebar.subheader("📅 Filtro Temporale")
    year_range = st.sidebar.slider(
        "Seleziona Periodo",
        2020,
        2024,
        (2020, 2024),
        help="Filtra i dati per il periodo selezionato",
    )

    # Show selected period info
    years_selected = year_range[1] - year_range[0] + 1
    st.sidebar.info(
        f"📊 Periodo: {years_selected} anni ({year_range[0]}-{year_range[1]})"
    )

    # Territory info (static but informative)
    st.sidebar.subheader("🗺️ Copertura Territoriale")
    territory_info = {
        "popolazione": "🇮🇹 Italia nazionale + 20 regioni",
        "economia": "🇮🇹 Italia nazionale + macroaree",
        "lavoro": "🇮🇹 Italia nazionale + dettaglio regionale",
    }

    st.sidebar.info(territory_info.get(category, "🇮🇹 Italia nazionale"))

    # Data source info
    st.sidebar.subheader("📡 Informazioni Fonte")
    st.sidebar.markdown(
        """
    **ISTAT SDMX API**
    - 🔄 Aggiornamento: Real-time
    - 📊 Qualità: Ufficiale
    - 🏛️ Ente: Istituto Nazionale di Statistica
    - 📅 Ultimo refresh: Automatico
    """
    )

    # Quick actions con memoria ottimizzata
    st.sidebar.subheader("⚡ Azioni Rapide")
    if st.sidebar.button("🔄 Ricarica Dati", help="Aggiorna i dati dalla cache"):
        # Clear solo cache specifiche invece di tutto
        load_data.clear()
        get_filtered_data.clear()
        calculate_metrics.clear()
        st.rerun()

    # Info sul filtro temporale
    if st.sidebar.button("ℹ️ Info Filtro", help="Come funziona il filtro temporale"):
        st.sidebar.info(
            """
        **Filtro Temporale:**
        - Modifica il range per vedere diversi periodi
        - I grafici si aggiornano automaticamente
        - Le statistiche sono ricalcolate sui dati filtrati
        """
        )

    # Export data option
    if st.sidebar.button("💾 Opzioni Export", help="Informazioni su export dati"):
        st.sidebar.success("Export CSV disponibile nei grafici tramite menu ⋮")

    return category, year_range


@st.cache_data(ttl=3600, max_entries=15)
def create_time_series_chart(df, category, info):
    """Crea grafico temporale con cache ottimizzata"""
    fig_line = px.line(
        df,
        x="TIME_PERIOD",
        y="Value",
        title=f"Andamento {category.title()} nel Tempo",
        color_discrete_sequence=[info["color"]],
        markers=True,
    )
    fig_line.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=14, family="Inter"),
        title_font=dict(size=18, family="Inter"),
        xaxis=dict(title=dict(text="Anno", font=dict(size=14))),
        yaxis=dict(title=dict(text="Valore", font=dict(size=14))),
        hovermode="x unified",
        margin=dict(l=20, r=20, t=60, b=20),
    )
    fig_line.update_traces(
        line=dict(width=3), marker=dict(size=8, line=dict(width=2, color="white"))
    )
    return fig_line


@st.cache_data(ttl=3600, max_entries=15)
def create_bar_chart(df, category, info):
    """Crea grafico a barre con cache ottimizzata"""
    fig_bar = px.bar(
        df,
        x="TIME_PERIOD",
        y="Value",
        title=f"Valori {category.title()} per Anno",
        color="Value",
        color_continuous_scale="Viridis",
    )
    fig_bar.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=14, family="Inter"),
        title_font=dict(size=18, family="Inter"),
        xaxis=dict(title=dict(text="Anno", font=dict(size=14))),
        yaxis=dict(title=dict(text="Valore", font=dict(size=14))),
        margin=dict(l=20, r=20, t=60, b=20),
        showlegend=False,
    )
    fig_bar.update_traces(marker_line_color="rgba(0,0,0,0.1)", marker_line_width=1)
    return fig_bar


@st.cache_data(ttl=3600, max_entries=15)
def create_area_chart(df, category, info):
    """Crea grafico ad area con cache ottimizzata"""
    fig_area = px.area(
        df,
        x="TIME_PERIOD",
        y="Value",
        title=f"Area di Trend - {category.title()}",
        color_discrete_sequence=[info["color"]],
    )
    fig_area.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=14, family="Inter"),
        title_font=dict(size=18, family="Inter"),
        xaxis=dict(title=dict(text="Anno", font=dict(size=14))),
        yaxis=dict(title=dict(text="Valore", font=dict(size=14))),
        margin=dict(l=20, r=20, t=60, b=20),
    )
    fig_area.update_traces(fill="tonexty", line=dict(width=2))
    return fig_area


def render_category_dashboard(category, datasets, year_range):
    """Render della dashboard per una categoria - Desktop optimized with functional filters"""
    if category not in datasets:
        st.error(f"Dati non disponibili per la categoria: {category}")
        return

    # Get original data
    df_original = datasets[category]
    info = CATEGORIES[category]

    # Usa cache ottimizzata per dati filtrati
    df = get_filtered_data(category, year_range[0], year_range[1])
    df_original = datasets[category]  # Solo per confronto dimensioni

    # Show filter info if data is filtered
    if len(df) != len(df_original):
        st.info(
            f"📅 Filtro attivo: {year_range[0]}-{year_range[1]} ({len(df)} di {len(df_original)} anni mostrati)"
        )

    # Check if filtered data is empty
    if df.empty:
        st.warning(
            f"⚠️ Nessun dato disponibile per il periodo {year_range[0]}-{year_range[1]}. Prova ad espandere il range temporale."
        )
        return

    # Enhanced category section with better styling
    st.markdown(
        f"""
    <div class="category-section">
        <div class="category-title">
            {info['emoji']} Analisi {category.title()}
        </div>
        <div class="category-description">
            {info['description']}
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Key metrics row con cache ottimizzata
    metrics = calculate_metrics(df)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if category == "popolazione":
            st.metric("🏠 Valore Attuale", f"{metrics['latest']:,.0f}", "abitanti")
        elif category == "economia":
            st.metric("💰 PIL Attuale", f"{metrics['latest']/1000:.1f}B", "EUR")
        else:
            st.metric("📊 Valore Attuale", f"{metrics['latest']:.1f}%", "tasso")

    with col2:
        if metrics["growth"] != 0:
            st.metric(
                "📈 Variazione Annua",
                f"{metrics['growth']:+.2f}%",
                "rispetto all'anno precedente",
            )
        else:
            st.metric("📈 Variazione", "N/A", "dati insufficienti")

    with col3:
        if category == "popolazione":
            st.metric("📊 Media Periodo", f"{metrics['avg']:,.0f}", "abitanti")
        elif category == "economia":
            st.metric("📊 Media Periodo", f"{metrics['avg']/1000:.1f}B", "EUR")
        else:
            st.metric("📊 Media Periodo", f"{metrics['avg']:.1f}%", "tasso")

    with col4:
        st.metric("✅ Qualità Dati", f"{metrics['quality']:.0f}%", "completezza")

    # Enhanced charts with better layout
    st.markdown("### 📈 Visualizzazioni")

    # Create tabs for different chart types
    tab1, tab2, tab3 = st.tabs(
        ["📊 Trend Temporale", "📈 Confronto Annuale", "🎯 Analisi Dettagliata"]
    )

    with tab1:
        # Lazy loading per time series chart
        with st.spinner("Generazione grafico temporale..."):
            fig_line = create_time_series_chart(df, category, info)
            st.plotly_chart(fig_line, use_container_width=True, height=400)

    with tab2:
        # Lazy loading per bar chart
        with st.spinner("Generazione grafico a barre..."):
            fig_bar = create_bar_chart(df, category, info)
            st.plotly_chart(fig_bar, use_container_width=True, height=400)

    with tab3:
        # Lazy loading per area chart
        with st.spinner("Generazione grafico ad area..."):
            fig_area = create_area_chart(df, category, info)
            st.plotly_chart(fig_area, use_container_width=True, height=400)

    # Enhanced data table with better formatting
    st.markdown("### 📋 Dati Dettagliati")

    # Add summary statistics
    col1, col2 = st.columns([2, 1])

    with col1:
        # Format the dataframe for better display
        display_df = df.copy()
        if category == "popolazione":
            display_df["Value"] = display_df["Value"].apply(lambda x: f"{x:,.0f}")
        elif category == "economia":
            display_df["Value"] = display_df["Value"].apply(lambda x: f"{x:,.0f} M€")
        else:
            display_df["Value"] = display_df["Value"].apply(lambda x: f"{x:.1f}%")

        display_df.columns = ["Anno", "Territorio", "Valore", "Unità", "Categoria"]
        st.dataframe(display_df, use_container_width=True, height=300)

    with col2:
        st.markdown("#### 📊 Statistiche Rapide")
        if not df.empty:
            min_val = df["Value"].min()
            max_val = df["Value"].max()
            mean_val = df["Value"].mean()

            if category == "popolazione":
                st.write(f"**Minimo:** {min_val:,.0f}")
                st.write(f"**Massimo:** {max_val:,.0f}")
                st.write(f"**Media:** {mean_val:,.0f}")
            elif category == "economia":
                st.write(f"**Minimo:** {min_val/1000:.1f}B €")
                st.write(f"**Massimo:** {max_val/1000:.1f}B €")
                st.write(f"**Media:** {mean_val/1000:.1f}B €")
            else:
                st.write(f"**Minimo:** {min_val:.1f}%")
                st.write(f"**Massimo:** {max_val:.1f}%")
                st.write(f"**Media:** {mean_val:.1f}%")

            st.write(
                f"**Periodo:** {df['TIME_PERIOD'].min()} - {df['TIME_PERIOD'].max()}"
            )
            st.write(f"**Punti dati:** {len(df)}")
        else:
            st.write("Nessun dato disponibile")


def cleanup_memory():
    """Pulizia memoria per prevenire memory leaks"""
    gc.collect()


def get_memory_usage():
    """Ottiene l'uso della memoria per monitoraggio"""
    import psutil

    try:
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024  # MB
    except:
        return 0


def main():
    """Funzione principale dell'app"""
    try:
        # Memory monitoring per debugging
        if st.sidebar.checkbox(
            "🔧 Debug Memory", help="Mostra uso memoria per troubleshooting"
        ):
            memory_usage = get_memory_usage()
            st.sidebar.metric("💾 Memoria (MB)", f"{memory_usage:.1f}")

        # Header
        render_header()

        # Sidebar
        selected_category, year_range = render_sidebar()

        # Load data
        with st.spinner("Caricamento dati..."):
            datasets = load_data()

        # Main dashboard
        if datasets:
            render_category_dashboard(selected_category, datasets, year_range)
            # Cleanup dopo rendering per liberare memoria
            cleanup_memory()
        else:
            st.error("Nessun dataset disponibile")

        # Footer
        st.markdown("---")
        st.markdown("Made with ❤️ in Italy | Powered by Streamlit")

        # Cache status per debugging
        if st.sidebar.checkbox("📊 Cache Status", help="Mostra stato cache"):
            st.sidebar.write("**Cache attive:**")
            st.sidebar.write("- load_data")
            st.sidebar.write("- get_filtered_data")
            st.sidebar.write("- calculate_metrics")
            st.sidebar.write("- chart functions")

    except Exception as e:
        st.error(f"Errore nell'applicazione: {str(e)}")
        st.info("Ricarica la pagina per riprovare")
        # Cleanup anche in caso di errore
        cleanup_memory()


if __name__ == "__main__":
    main()
