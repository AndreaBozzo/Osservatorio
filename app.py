#!/usr/bin/env python3
"""
Main Streamlit App Entry Point
Direct entry point for Streamlit Cloud without subdirectory complications
"""

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

# Custom CSS for enhanced styling
st.markdown(
    """
<style>
/* Global improvements */
.stApp {
    background: #f8f9fa;
}

/* Hide streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Custom header */
.main-header {
    background: linear-gradient(90deg, #0066CC, #004499);
    color: white;
    padding: 2rem;
    border-radius: 10px;
    margin-bottom: 2rem;
    text-align: center;
}

/* Improved metrics */
[data-testid="metric-container"] {
    background: white;
    border: 1px solid #e0e0e0;
    padding: 1rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Enhanced charts */
.plotly-graph-div {
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

/* Better buttons */
.stButton > button {
    background: #0066CC;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.5rem 1rem;
    font-weight: 500;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    background: #004499;
    transform: translateY(-2px);
}

/* Responsive design */
@media (max-width: 768px) {
    .main-header {
        padding: 1rem !important;
    }
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
        "TIME_PERIOD": ["2020", "2021", "2022", "2023", "2024"],
        "TERRITORIO": ["Italia", "Italia", "Italia", "Italia", "Italia"],
        "Value": [59641488, 59236213, 58940425, 58997201, 59000000],
        "UNIT_MEASURE": ["NUM", "NUM", "NUM", "NUM", "NUM"],
        "SEX": ["TOTAL", "TOTAL", "TOTAL", "TOTAL", "TOTAL"],
    }

    # Dati di esempio per economia
    economy_data = {
        "TIME_PERIOD": ["2020", "2021", "2022", "2023", "2024"],
        "TERRITORIO": ["Italia", "Italia", "Italia", "Italia", "Italia"],
        "Value": [1653000, 1775000, 1897000, 1952000, 2010000],
        "UNIT_MEASURE": ["EUR_MIO", "EUR_MIO", "EUR_MIO", "EUR_MIO", "EUR_MIO"],
        "SECTOR": ["TOTAL", "TOTAL", "TOTAL", "TOTAL", "TOTAL"],
    }

    # Dati di esempio per lavoro
    work_data = {
        "TIME_PERIOD": ["2020", "2021", "2022", "2023", "2024"],
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


@st.cache_data(ttl=1800)
def load_data():
    """Carica i dati con cache"""
    return create_sample_data()


def render_header():
    """Render dell'header principale"""
    st.markdown(
        """
    <div class="main-header">
        <h1>🇮🇹 Osservatorio Dati ISTAT</h1>
        <h3>La piattaforma open-source per l'analisi dei dati statistici italiani</h3>
        <p>Esplora oltre <strong>509+ dataset ISTAT</strong> con visualizzazioni interattive e analisi avanzate.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📊 Dataset Disponibili", "509+")

    with col2:
        st.metric("📈 Categorie", len(CATEGORIES))

    with col3:
        st.metric("🕐 Ultimo Aggiornamento", datetime.now().strftime("%d/%m %H:%M"))

    with col4:
        st.metric("🔄 Status Sistema", "🟢 Operativo")


def render_sidebar():
    """Render della sidebar"""
    st.sidebar.header("🔍 Filtri e Navigazione")

    # Status indicator
    st.sidebar.success("✅ Sistema Operativo")

    # Category selection
    category_options = [
        f"{info['emoji']} {cat.title()}" for cat, info in CATEGORIES.items()
    ]

    selected = st.sidebar.selectbox("Seleziona Categoria", category_options, index=0)
    category = selected.split(" ")[1].lower()

    # Category info
    info = CATEGORIES[category]
    st.sidebar.markdown(
        f"""
    **{info['emoji']} {category.title()}**
    - Priorità: {info['priority']}/10
    - Descrizione: {info['description']}
    """
    )

    # Filters
    st.sidebar.subheader("📋 Filtri")
    year_range = st.sidebar.slider("Anno", 2020, 2024, (2020, 2024))
    geo_filter = st.sidebar.selectbox("Territorio", ["Italia", "Nord", "Centro", "Sud"])

    return category, year_range, geo_filter


def render_category_dashboard(category, datasets):
    """Render della dashboard per una categoria"""
    if category not in datasets:
        st.error(f"Dati non disponibili per la categoria: {category}")
        return

    df = datasets[category]
    info = CATEGORIES[category]

    st.markdown(f"## {info['emoji']} Analisi {category.title()}")
    st.markdown(f"*{info['description']}*")

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        # Time series chart
        fig_line = px.line(
            df,
            x="TIME_PERIOD",
            y="Value",
            title=f"Trend {category.title()} nel Tempo",
            color_discrete_sequence=[info["color"]],
        )
        fig_line.update_layout(
            plot_bgcolor="white", paper_bgcolor="white", font=dict(size=12)
        )
        st.plotly_chart(fig_line, use_container_width=True)

    with col2:
        # Bar chart
        fig_bar = px.bar(
            df,
            x="TIME_PERIOD",
            y="Value",
            title=f"Valori {category.title()} per Anno",
            color_discrete_sequence=[info["color"]],
        )
        fig_bar.update_layout(
            plot_bgcolor="white", paper_bgcolor="white", font=dict(size=12)
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # Data table
    st.subheader("📋 Dati Dettagliati")
    st.dataframe(df, use_container_width=True)


def main():
    """Funzione principale dell'app"""
    try:
        # Header
        render_header()

        # Sidebar
        selected_category, year_range, geo_filter = render_sidebar()

        # Load data
        with st.spinner("Caricamento dati..."):
            datasets = load_data()

        # Main dashboard
        if datasets:
            render_category_dashboard(selected_category, datasets)
        else:
            st.error("Nessun dataset disponibile")

        # Footer
        st.markdown("---")
        st.markdown("Made with ❤️ in Italy | Powered by Streamlit")

    except Exception as e:
        st.error(f"Errore nell'applicazione: {str(e)}")
        st.info("Ricarica la pagina per riprovare")


if __name__ == "__main__":
    main()
