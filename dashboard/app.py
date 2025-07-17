#!/usr/bin/env python3
"""
Osservatorio ISTAT - Dashboard Streamlit
Sistema di visualizzazione interattiva dei dati ISTAT
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Aggiungi src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from api.istat_api import IstatAPITester
    from converters.powerbi_converter import IstatXMLToPowerBIConverter
    from utils.logger import get_logger
except ImportError as e:
    st.error(f"Errore importazione moduli: {e}")
    st.stop()

# Configurazione pagina
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

# Logger
logger = get_logger(__name__)

# Costanti
CATEGORIES = {
    "popolazione": {"emoji": "🏘️", "priority": 10, "color": "#FF6B6B"},
    "economia": {"emoji": "💰", "priority": 9, "color": "#4ECDC4"},
    "lavoro": {"emoji": "👥", "priority": 8, "color": "#45B7D1"},
    "territorio": {"emoji": "🏛️", "priority": 7, "color": "#96CEB4"},
    "istruzione": {"emoji": "🎓", "priority": 6, "color": "#FECA57"},
    "salute": {"emoji": "🏥", "priority": 5, "color": "#FF9FF3"},
}


# Cache per i dati
@st.cache_data(ttl=3600)
def load_sample_data():
    """Carica dati di esempio dalla directory processed"""
    try:
        data_dir = Path(__file__).parent.parent / "data" / "processed" / "powerbi"

        # Trova i file più recenti per categoria
        datasets = {}

        for category in CATEGORIES.keys():
            csv_files = list(data_dir.glob(f"{category}_*.csv"))
            if csv_files:
                # Prendi il file più recente
                latest_file = max(csv_files, key=lambda f: f.stat().st_mtime)
                try:
                    df = pd.read_csv(latest_file)
                    datasets[category] = df
                    logger.info(f"Caricato dataset {category}: {len(df)} righe")
                except Exception as e:
                    logger.error(f"Errore caricamento {category}: {e}")
                    continue

        return datasets
    except Exception as e:
        logger.error(f"Errore caricamento dati: {e}")
        return {}


@st.cache_data(ttl=1800)
def get_system_stats():
    """Ottieni statistiche del sistema"""
    try:
        # Conta file processati
        data_dir = Path(__file__).parent.parent / "data" / "processed" / "powerbi"
        total_files = len(list(data_dir.glob("*.csv")))

        # Ultima elaborazione
        csv_files = list(data_dir.glob("*.csv"))
        if csv_files:
            latest_file = max(csv_files, key=lambda f: f.stat().st_mtime)
            last_update = datetime.fromtimestamp(latest_file.stat().st_mtime)
        else:
            last_update = datetime.now()

        return {
            "total_datasets": total_files,
            "last_update": last_update,
            "categories_available": len(CATEGORIES),
            "system_status": "🟢 Online",
        }
    except Exception as e:
        logger.error(f"Errore statistiche sistema: {e}")
        return {
            "total_datasets": 0,
            "last_update": datetime.now(),
            "categories_available": 0,
            "system_status": "🔴 Errore",
        }


def render_header():
    """Render dell'header principale"""
    st.title("🇮🇹 Osservatorio Dati ISTAT")
    st.markdown(
        """
    ### La piattaforma open-source per l'analisi dei dati statistici italiani

    Esplora oltre **509+ dataset ISTAT** con visualizzazioni interattive e analisi avanzate.
    """
    )

    # Metrics row
    stats = get_system_stats()
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📊 Dataset Disponibili", stats["total_datasets"])

    with col2:
        st.metric("📅 Ultimo Aggiornamento", stats["last_update"].strftime("%d/%m/%Y"))

    with col3:
        st.metric("🗂️ Categorie", stats["categories_available"])

    with col4:
        st.metric("🔄 Status Sistema", stats["system_status"])


def render_sidebar():
    """Render della sidebar con filtri"""
    st.sidebar.header("🔍 Filtri e Navigazione")

    # Selezione categoria
    category_options = [
        f"{info['emoji']} {cat.title()}" for cat, info in CATEGORIES.items()
    ]

    selected = st.sidebar.selectbox("Seleziona Categoria", category_options, index=0)

    # Estrai il nome categoria
    category = selected.split(" ")[1].lower()

    # Info categoria
    info = CATEGORIES[category]
    st.sidebar.markdown(
        f"""
    **{info['emoji']} {category.title()}**
    - Priorità: {info['priority']}/10
    - Colore: {info['color']}
    """
    )

    # Filtri temporali
    st.sidebar.subheader("📅 Periodo")
    year_range = st.sidebar.slider(
        "Anni", min_value=2000, max_value=2024, value=(2020, 2024), step=1
    )

    # Filtri geografici
    st.sidebar.subheader("🌍 Area Geografica")
    geo_filter = st.sidebar.selectbox(
        "Livello", ["Nazionale", "Regionale", "Provinciale", "Comunale"]
    )

    # Pulsanti azione
    st.sidebar.subheader("⚡ Azioni")
    col1, col2 = st.sidebar.columns(2)

    with col1:
        if st.button("🔄 Aggiorna", help="Ricarica i dati"):
            st.cache_data.clear()
            st.rerun()

    with col2:
        if st.button("📥 Export", help="Scarica i dati"):
            st.sidebar.info("Feature in sviluppo...")

    return category, year_range, geo_filter


def render_popolazione_dashboard(df):
    """Render del dashboard popolazione"""
    st.header("🏘️ Analisi Popolazione")

    if df is None or df.empty:
        st.warning("Nessun dato disponibile per la categoria Popolazione")
        return

    # Pulizia dati
    df_clean = df.dropna(subset=["Value"])

    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_pop = df_clean["Value"].sum()
        st.metric("👥 Popolazione Totale", f"{total_pop:,.0f}")

    with col2:
        avg_pop = df_clean["Value"].mean()
        st.metric("📊 Media", f"{avg_pop:,.0f}")

    with col3:
        max_pop = df_clean["Value"].max()
        st.metric("📈 Massimo", f"{max_pop:,.0f}")

    with col4:
        records = len(df_clean)
        st.metric("📋 Record", f"{records:,}")

    # Grafici
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Trend Temporale")
        if "Time" in df_clean.columns or "TIME_PERIOD" in df_clean.columns:
            time_col = "Time" if "Time" in df_clean.columns else "TIME_PERIOD"

            # Aggrega per tempo
            time_trend = df_clean.groupby(time_col)["Value"].sum().reset_index()

            fig = px.line(
                time_trend,
                x=time_col,
                y="Value",
                title="Evoluzione Popolazione nel Tempo",
                color_discrete_sequence=[CATEGORIES["popolazione"]["color"]],
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Dati temporali non disponibili")

    with col2:
        st.subheader("🗺️ Distribuzione Geografica")
        if "TERRITORIO" in df_clean.columns or "Territory" in df_clean.columns:
            territory_col = (
                "TERRITORIO" if "TERRITORIO" in df_clean.columns else "Territory"
            )

            # Top 10 territori
            top_territories = (
                df_clean.groupby(territory_col)["Value"]
                .sum()
                .nlargest(10)
                .reset_index()
            )

            fig = px.bar(
                top_territories,
                x="Value",
                y=territory_col,
                orientation="h",
                title="Top 10 Territori per Popolazione",
                color_discrete_sequence=[CATEGORIES["popolazione"]["color"]],
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Dati geografici non disponibili")

    # Tabella dati
    st.subheader("📊 Dati Dettagliati")

    # Mostra un campione dei dati
    sample_df = df_clean.head(100)
    st.dataframe(sample_df, use_container_width=True)

    # Statistiche descrittive
    st.subheader("📈 Statistiche Descrittive")
    st.write(df_clean.describe())


def render_economia_dashboard(df):
    """Render del dashboard economia"""
    st.header("💰 Analisi Economica")

    if df is None or df.empty:
        st.warning("Nessun dato disponibile per la categoria Economia")
        return

    st.info("Dashboard economia in sviluppo...")

    # Visualizzazione base
    df_clean = df.dropna(subset=["Value"])

    col1, col2 = st.columns(2)

    with col1:
        st.metric("💰 Totale Economia", f"{df_clean['Value'].sum():,.0f}")

    with col2:
        st.metric("📊 Record", f"{len(df_clean):,}")

    # Tabella dati
    st.dataframe(df_clean.head(50), use_container_width=True)


def render_lavoro_dashboard(df):
    """Render del dashboard lavoro"""
    st.header("👥 Analisi Mercato del Lavoro")

    if df is None or df.empty:
        st.warning("Nessun dato disponibile per la categoria Lavoro")
        return

    st.info("Dashboard lavoro in sviluppo...")

    # Visualizzazione base
    df_clean = df.dropna(subset=["Value"])

    col1, col2 = st.columns(2)

    with col1:
        st.metric("👥 Totale Lavoro", f"{df_clean['Value'].sum():,.0f}")

    with col2:
        st.metric("📊 Record", f"{len(df_clean):,}")

    # Tabella dati
    st.dataframe(df_clean.head(50), use_container_width=True)


def render_other_dashboard(category, df):
    """Render generico per altre categorie"""
    info = CATEGORIES[category]
    st.header(f"{info['emoji']} Analisi {category.title()}")

    if df is None or df.empty:
        st.warning(f"Nessun dato disponibile per la categoria {category.title()}")
        return

    st.info(f"Dashboard {category} in sviluppo...")

    # Visualizzazione base
    df_clean = df.dropna(subset=["Value"])

    col1, col2 = st.columns(2)

    with col1:
        st.metric(f"{info['emoji']} Totale", f"{df_clean['Value'].sum():,.0f}")

    with col2:
        st.metric("📊 Record", f"{len(df_clean):,}")

    # Tabella dati
    st.dataframe(df_clean.head(50), use_container_width=True)


def render_footer():
    """Render del footer"""
    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
        **🇮🇹 Osservatorio ISTAT**

        Sistema open-source per l'analisi
        dei dati statistici italiani
        """
        )

    with col2:
        st.markdown(
            """
        **🔗 Link Utili**

        - [GitHub Repository](https://github.com/AndreaBozzo/Osservatorio)
        - [Documentazione](https://github.com/AndreaBozzo/Osservatorio/blob/main/README.md)
        - [ISTAT Ufficiale](https://www.istat.it/)
        """
        )

    with col3:
        st.markdown(
            """
        **📊 Statistiche Sistema**

        - Test: 173/173 ✅
        - Coverage: 41%
        - Datasets: 509+
        """
        )

    st.markdown("---")
    st.markdown("Made with ❤️ in Italy | Powered by Streamlit")


def main():
    """Funzione principale dell'app"""
    try:
        # Header
        render_header()

        # Sidebar
        selected_category, year_range, geo_filter = render_sidebar()

        # Caricamento dati
        with st.spinner("Caricamento dati..."):
            datasets = load_sample_data()

        # Verifica disponibilità dati
        if not datasets:
            st.error(
                "Nessun dataset disponibile. Esegui prima il processo di conversione."
            )
            st.info("Esegui: `python convert_to_powerbi.py` per generare i dati.")
            return

        # Rendering dashboard per categoria
        df = datasets.get(selected_category, None)

        if selected_category == "popolazione":
            render_popolazione_dashboard(df)
        elif selected_category == "economia":
            render_economia_dashboard(df)
        elif selected_category == "lavoro":
            render_lavoro_dashboard(df)
        else:
            render_other_dashboard(selected_category, df)

        # Footer
        render_footer()

    except Exception as e:
        logger.error(f"Errore applicazione: {e}")
        st.error(f"Errore nell'applicazione: {e}")
        st.info("Ricarica la pagina o contatta il supporto.")


if __name__ == "__main__":
    main()
