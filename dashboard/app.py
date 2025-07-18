#!/usr/bin/env python3
"""
Osservatorio ISTAT - Dashboard Streamlit
Sistema di visualizzazione interattiva dei dati ISTAT
"""

import json
import sys
import time
from datetime import datetime, timedelta
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

# Aggiungi src al path per import locali
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root))

# Import robusto con fallback - disabilito import problematici per ora
# I moduli src/ hanno import relativi che non funzionano da dashboard
IstatAPITester = None
IstatXMLToPowerBIConverter = None


def get_logger(x):
    return None


# Import new real-time data loader
try:
    from data_loader import get_data_loader
except ImportError as e:
    st.error(f"Errore importazione data loader: {e}")
    st.info("Falling back to mock data mode")
    get_data_loader = None

# Logger con fallback
try:
    logger = get_logger(__name__) if get_logger else None
except:
    logger = None


# Dummy logger per caso di fallback
class DummyLogger:
    def info(self, msg):
        print(f"INFO: {msg}")

    def error(self, msg):
        print(f"ERROR: {msg}")

    def warning(self, msg):
        print(f"WARNING: {msg}")


if logger is None:
    logger = DummyLogger()

# Costanti
CATEGORIES = {
    # Only economia has working datasets as of Week 4 fixes
    "economia": {"emoji": "💰", "priority": 9, "color": "#4ECDC4"},
    # Other categories commented out until dataset discovery is implemented
    # "popolazione": {"emoji": "🏘️", "priority": 10, "color": "#FF6B6B"},
    # "lavoro": {"emoji": "👥", "priority": 8, "color": "#45B7D1"},
    # "territorio": {"emoji": "🏛️", "priority": 7, "color": "#96CEB4"},
    # "istruzione": {"emoji": "🎓", "priority": 6, "color": "#FECA57"},
    # "salute": {"emoji": "🏥", "priority": 5, "color": "#FF9FF3"},
}


def create_sample_data():
    """Crea dati di esempio per demo quando i file non sono disponibili"""
    # Dati di esempio per popolazione
    population_data = {
        "TIME_PERIOD": ["2020", "2021", "2022", "2023", "2024"],
        "TERRITORIO": ["Italia", "Italia", "Italia", "Italia", "Italia"],
        "Value": [60244639, 59030133, 58997201, 58850717, 58761146],
        "UNIT_MEASURE": ["N", "N", "N", "N", "N"],
        "SEXISTAT1": ["T", "T", "T", "T", "T"],
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


# Cache per i dati con TTL più breve per dati real-time
@st.cache_data(ttl=1800)  # 30 minuti per dati real-time
def load_real_time_data():
    """Carica dati real-time dall'API ISTAT con enhanced error handling"""
    if get_data_loader is None:
        logger.warning("Data loader non disponibile, usando dati di esempio")
        return create_sample_data()

    try:
        data_loader = get_data_loader()
        datasets = {}
        failed_categories = []

        # Carica dati per ogni categoria con enhanced error handling
        for category in CATEGORIES.keys():
            try:
                logger.info(f"Caricando dati real-time per {category}")

                # Add timeout handling for each category
                start_time = time.time()
                df = data_loader.load_category_data(category)
                load_time = time.time() - start_time

                if df is not None and not df.empty:
                    datasets[category] = df
                    logger.info(
                        f"Caricato dataset {category}: {len(df)} righe in {load_time:.2f}s"
                    )
                else:
                    logger.warning(f"Nessun dato per {category}, usando fallback")
                    failed_categories.append(category)

            except Exception as e:
                logger.error(f"Errore caricamento {category}: {e}")
                failed_categories.append(category)
                continue

        # Create fallback data for failed categories
        if failed_categories:
            logger.warning(f"Creando dati di fallback per: {failed_categories}")
            sample_data = create_sample_data()
            for category in failed_categories:
                if category in sample_data:
                    datasets[category] = sample_data[category]
                    logger.info(f"Fallback data creato per {category}")

        # Se non ci sono dataset, crea dati di esempio
        if not datasets:
            logger.warning("Nessun dataset caricato, usando dati di esempio completi")
            return create_sample_data()

        # Validate data quality
        for category, df in datasets.items():
            if df.empty:
                logger.warning(f"Dataset vuoto per {category}")
            elif len(df) < 2:
                logger.warning(
                    f"Dataset {category} ha pochissimi dati: {len(df)} righe"
                )

        return datasets

    except Exception as e:
        logger.error(f"Errore critico caricamento dati real-time: {e}")
        logger.error(f"Traceback: {str(e)}")
        return create_sample_data()


# Funzione legacy per compatibilità
@st.cache_data(ttl=3600)
def load_sample_data():
    """Carica dati - ora usa real-time come default"""
    return load_real_time_data()


@st.cache_data(ttl=1800)
def get_system_stats():
    """Ottieni statistiche del sistema real-time"""
    if get_data_loader is None:
        return {
            "total_datasets": 0,
            "last_update": datetime.now(),
            "categories_available": len(CATEGORIES),
            "system_status": "🟡 Mock Data Mode",
        }

    try:
        data_loader = get_data_loader()
        stats = data_loader.get_system_stats()

        # Aggiungi info sulle categorie
        stats["categories_available"] = len(CATEGORIES)

        return stats

    except Exception as e:
        logger.error(f"Errore statistiche sistema: {e}")
        return {
            "total_datasets": 0,
            "last_update": datetime.now(),
            "categories_available": 0,
            "system_status": f"🔴 Error: {str(e)[:20]}",
        }


def render_header():
    """Render dell'header principale"""
    # Custom CSS for better styling
    st.markdown(
        """
    <style>
    .main-header {
        background: linear-gradient(90deg, #0066CC, #004499);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stMetric {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

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
    """Render della sidebar con filtri e status feedback"""
    # Enhanced sidebar styling
    st.sidebar.markdown(
        """
    <style>
    .sidebar-header {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 4px solid #0066CC;
    }
    .category-info {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin: 1rem 0;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown(
        """
    <div class="sidebar-header">
        <h3>🔍 Filtri e Navigazione</h3>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # System Status Card
    st.sidebar.subheader("📊 Status Sistema")
    system_stats = get_system_stats()

    # Create status indicator with enhanced styling
    if "🟢" in system_stats.get("system_status", ""):
        st.sidebar.success("✅ Sistema Operativo")
    elif "🟡" in system_stats.get("system_status", ""):
        st.sidebar.warning("⚠️ Modalità Limitata")
    else:
        st.sidebar.error("❌ Sistema Non Disponibile")

    # Show response time if available
    if "api_response_time" in system_stats:
        st.sidebar.metric("⏱️ Tempo Risposta", system_stats["api_response_time"])

    # Selezione categoria
    category_options = [
        f"{info['emoji']} {cat.title()}" for cat, info in CATEGORIES.items()
    ]

    selected = st.sidebar.selectbox("Seleziona Categoria", category_options, index=0)

    # Estrai il nome categoria
    category = selected.split(" ")[1].lower()

    # Info categoria con enhanced feedback
    info = CATEGORIES[category]
    st.sidebar.markdown(
        f"""
    **{info['emoji']} {category.title()}**
    - Priorità: {info['priority']}/10
    - Colore: {info['color']}
    """
    )

    # Data Quality Indicator
    try:
        datasets = load_sample_data()
        if category in datasets:
            df = datasets[category]
            if df is not None and not df.empty:
                quality_score = min(100, int((len(df) / 1000) * 100))
                st.sidebar.metric("📈 Qualità Dati", f"{quality_score}%")
            else:
                st.sidebar.warning("⚠️ Dati non disponibili")
        else:
            st.sidebar.info("📊 Caricamento in corso...")
    except Exception as e:
        st.sidebar.error("❌ Errore verifica dati")

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

    # Pulsanti azione con enhanced feedback
    st.sidebar.subheader("⚡ Azioni")
    col1, col2 = st.sidebar.columns(2)

    with col1:
        if st.button("🔄 Aggiorna", help="Ricarica i dati"):
            with st.spinner("Aggiornamento in corso..."):
                st.cache_data.clear()
                time.sleep(0.5)  # Give user feedback
                st.rerun()

    with col2:
        if st.button("📥 Export", help="Scarica i dati"):
            st.sidebar.info("Feature in sviluppo...")

    # Show last update time
    st.sidebar.markdown("---")
    st.sidebar.caption(f"Ultimo aggiornamento: {datetime.now().strftime('%H:%M:%S')}")

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


def add_global_css():
    """Aggiungi CSS globale per migliorare l'aspetto"""
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

    /* Custom containers */
    .dashboard-container {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 1rem 0;
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

    /* Improved sidebar */
    .stSidebar {
        background: #f8f9fa;
    }

    /* Better selectbox */
    .stSelectbox > div > div {
        background: white;
        border-radius: 8px;
    }

    /* Responsive design */
    @media (max-width: 768px) {
        .dashboard-container {
            padding: 1rem;
        }

        .main-header {
            padding: 1rem !important;
        }
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def main():
    """Funzione principale dell'app"""
    try:
        # Add global CSS
        add_global_css()

        # Add metadata for better SEO and sharing
        st.markdown(
            """
        <meta name="description" content="Osservatorio ISTAT - Piattaforma open-source per l'analisi dei dati statistici italiani">
        <meta name="keywords" content="ISTAT, dati statistici, Italia, visualizzazione dati, dashboard, open source">
        <meta name="author" content="Andrea Bozzo">
        <meta property="og:title" content="Osservatorio ISTAT - Dashboard Dati Statistici">
        <meta property="og:description" content="Esplora oltre 509+ dataset ISTAT con visualizzazioni interattive">
        <meta property="og:type" content="website">
        <meta property="twitter:card" content="summary_large_image">
        """,
            unsafe_allow_html=True,
        )

        # Header
        render_header()

        # Sidebar
        selected_category, year_range, geo_filter = render_sidebar()

        # Enhanced loading states with progress indicators
        loading_container = st.container()
        with loading_container:
            # Main progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Step 1: Connection check
            status_text.text("🔍 Verifica connessione API...")
            progress_bar.progress(10)

            # Check system status first
            system_stats = get_system_stats()
            if "🔴" in system_stats.get("system_status", ""):
                st.warning(
                    "⚠️ API ISTAT non disponibile. Utilizzando dati di fallback."
                )
                time.sleep(0.5)

            # Step 2: Data loading
            status_text.text("📊 Caricamento dati in corso...")
            progress_bar.progress(30)

            try:
                datasets = load_sample_data()
                progress_bar.progress(70)

                if not datasets:
                    progress_bar.progress(100)
                    status_text.text("❌ Nessun dataset disponibile")
                    st.error(
                        "Nessun dataset disponibile. Esegui prima il processo di conversione."
                    )
                    st.info(
                        "Esegui: `python convert_to_powerbi.py` per generare i dati."
                    )
                    return

                # Step 3: Data validation
                status_text.text("✅ Validazione dati...")
                progress_bar.progress(90)

                # Check if selected category has data
                df = datasets.get(selected_category, None)
                if df is None or df.empty:
                    st.warning(
                        f"⚠️ Nessun dato disponibile per {selected_category}. Mostrando dati di esempio."
                    )

                # Step 4: Complete
                status_text.text("🎉 Caricamento completato!")
                progress_bar.progress(100)
                time.sleep(0.5)

            except Exception as e:
                progress_bar.progress(100)
                status_text.text("❌ Errore durante il caricamento")
                logger.error(f"Errore caricamento dati: {e}")
                st.error(f"Errore durante il caricamento: {e}")
                st.info("Provo a utilizzare dati di fallback...")

                # Try fallback data
                datasets = create_sample_data()
                df = datasets.get(selected_category, None)

                if df is None:
                    st.error("Anche i dati di fallback non sono disponibili.")
                    return

            # Clear loading indicators
            loading_container.empty()

        # Add connection status indicator
        col1, col2 = st.columns([3, 1])
        with col2:
            if "🟢" in system_stats.get("system_status", ""):
                st.success("API Connessa")
            elif "🟡" in system_stats.get("system_status", ""):
                st.warning("Modalità Demo")
            else:
                st.error("API Disconnessa")

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

        # Show debug info in sidebar
        with st.sidebar:
            st.subheader("🔧 Debug Info")
            st.text(f"Errore: {str(e)[:50]}...")
            st.text(f"Timestamp: {datetime.now().strftime('%H:%M:%S')}")
            if st.button("🔄 Riprova"):
                st.rerun()


if __name__ == "__main__":
    main()
