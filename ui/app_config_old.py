"""
Configuration globale de l'application Streamlit
Gestion de la page et initialisation des managers
"""

import streamlit as st
from pathlib import Path
import sys

# Ajouter le backend au path
backend_path = Path(__file__).parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.append(str(backend_path))

from backend.data_manager import DataManager
from backend.change_detector import ChangeDetector
from backend.history_manager import HistoryManager
from backend.pdf_exporter import PDFExporter
from backend.watchlist_manager import WatchlistManager
from backend.risk_analyzer import RiskAnalyzer
from backend.alert_system import AlertSystem
from backend.logger import get_logger


# Initialiser le logger
logger = get_logger()


def configure_page():
    """Configure les paramètres de la page Streamlit"""
    st.set_page_config(
        page_title="Suivi des Substances Chimiques ECHA",
        page_icon=":test_tube:",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://github.com/your-repo',
            'Report a bug': 'https://github.com/your-repo/issues',
            'About': """
            # Application ECHA v2.0
            
            Application de suivi des substances chimiques ECHA.
            
            **Fonctionnalités:**
            - Suivi des substances chimiques
            - Historique des changements
            - Analyse des risques
            - Surveillance personnalisée
            - Export PDF
            
            Développé avec Streamlit et Python.
            """
        }
    )
    
    # CSS personnalisé
    st.markdown("""
        <style>
        /* Améliorer l'apparence des onglets */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            padding-left: 20px;
            padding-right: 20px;
            background-color: #f0f2f6;
            border-radius: 5px 5px 0 0;
        }
        
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: #ffffff;
        }
        
        /* Améliorer les métriques */
        div[data-testid="stMetricValue"] {
            font-size: 28px;
            font-weight: bold;
        }
        
        div[data-testid="stMetricDelta"] {
            font-size: 16px;
        }
        
        /* Améliorer les expanders */
        .streamlit-expanderHeader {
            font-size: 18px;
            font-weight: 600;
        }
        
        /* Améliorer les boutons */
        .stButton > button {
            border-radius: 5px;
            font-weight: 500;
        }
        
        .stButton > button[kind="primary"] {
            background-color: #FF4B4B;
        }
        
        /* Améliorer les dataframes */
        .dataframe {
            font-size: 14px;
        }
        
        /* Footer personnalisé */
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #f0f2f6;
            color: #666;
            text-align: center;
            padding: 10px;
            font-size: 12px;
            border-top: 1px solid #ddd;
        }
        
        /* Cacher le hamburger menu et footer Streamlit par défaut */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Améliorer les alerts */
        .stAlert {
            border-radius: 5px;
        }
        
        /* Améliorer les sidebar */
        section[data-testid="stSidebar"] {
            background-color: #f8f9fa;
        }
        
        /* Améliorer les inputs */
        .stTextInput > div > div > input {
            border-radius: 5px;
        }
        
        .stSelectbox > div > div > select {
            border-radius: 5px;
        }
        
        /* Améliorer les dividers */
        hr {
            margin-top: 1.5rem;
            margin-bottom: 1.5rem;
        }
        </style>
    """, unsafe_allow_html=True)


@st.cache_resource
def initialize_managers():
    """
    Initialise tous les managers de l'application
    
    Returns:
        dict: Dictionnaire contenant tous les managers
            - 'data': DataManager
            - 'change': ChangeDetector
            - 'history': HistoryManager
            - 'watchlist': WatchlistManager
            - 'risk': RiskAnalyzer
            - 'alert': AlertSystem
            - 'pdf': PDFExporter
    """
    logger.info("Initialisation des managers de l'application")
    
    try:
        managers = {
            'data': DataManager(),
            'change': ChangeDetector(),
            'history': HistoryManager(),
            'watchlist': WatchlistManager(),
            'risk': RiskAnalyzer(),
            'alert': AlertSystem(),
            'pdf': PDFExporter()
        }
        
        logger.info("Tous les managers ont été initialisés avec succès")
        return managers
    
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation des managers: {e}")
        st.error(f"Erreur d'initialisation: {e}")
        
        # Retourner des managers vides pour éviter le crash
        return {
            'data': None,
            'change': None,
            'history': None,
            'watchlist': None,
            'risk': None,
            'alert': None,
            'pdf': None
        }


def get_manager(manager_name: str):
    """
    Récupère un manager spécifique
    
    Args:
        manager_name: Nom du manager ('data', 'change', etc.)
    
    Returns:
        Manager correspondant
    """
    managers = initialize_managers()
    return managers.get(manager_name)


def initialize_session_state():
    """
    Initialise les variables de session state globales
    """
    # Initialiser les clés communes si elles n'existent pas
    if 'app_initialized' not in st.session_state:
        st.session_state.app_initialized = True
        logger.info("Session state initialisé")
    
    # Initialiser d'autres variables globales si nécessaire
    if 'current_user' not in st.session_state:
        st.session_state.current_user = "Utilisateur"
    
    if 'theme' not in st.session_state:
        st.session_state.theme = "light"
    
    if 'language' not in st.session_state:
        st.session_state.language = "fr"


def display_sidebar_info():
    """
    Affiche des informations utiles dans la sidebar
    """
    with st.sidebar:
        st.markdown("---")
        st.markdown("### ℹ️ Informations")
        
        # Informations sur l'application
        st.caption("**Version:** 2.0.0")
        st.caption("**Dernière mise à jour:** 01/01/2026")
        
        st.markdown("---")
        
        # Raccourcis utiles
        st.markdown("### 🔗 Liens Utiles")
        st.markdown("[📚 Documentation](https://docs.example.com)")
        st.markdown("[🐛 Signaler un bug](https://github.com/example/issues)")
        st.markdown("[💡 Suggestions](https://github.com/example/discussions)")
        
        st.markdown("---")
        
        # Statistiques globales
        try:
            managers = initialize_managers()
            if managers['data']:
                aggregated_df = managers['data'].load_aggregated_data()
                
                st.markdown("### 📊 Statistiques")
                st.metric("Total Substances", len(aggregated_df) if not aggregated_df.empty else 0)
                
                if managers['alert']:
                    unread = managers['alert'].get_unread_count()
                    st.metric("Alertes Non Lues", unread)
        except Exception as e:
            logger.warning(f"Impossible de charger les statistiques: {e}")


def check_backend_availability():
    """
    Vérifie que tous les modules backend sont disponibles
    
    Returns:
        Tuple (est_disponible, liste_erreurs)
    """
    errors = []
    
    try:
        from backend.data_manager import DataManager
    except ImportError:
        errors.append("DataManager non disponible")
    
    try:
        from backend.change_detector import ChangeDetector
    except ImportError:
        errors.append("ChangeDetector non disponible")
    
    try:
        from backend.history_manager import HistoryManager
    except ImportError:
        errors.append("HistoryManager non disponible")
    
    try:
        from backend.pdf_exporter import PDFExporter
    except ImportError:
        errors.append("PDFExporter non disponible")
    
    try:
        from backend.watchlist_manager import WatchlistManager
    except ImportError:
        errors.append("WatchlistManager non disponible")
    
    try:
        from backend.risk_analyzer import RiskAnalyzer
    except ImportError:
        errors.append("RiskAnalyzer non disponible")
    
    try:
        from backend.alert_system import AlertSystem
    except ImportError:
        errors.append("AlertSystem non disponible")
    
    return len(errors) == 0, errors


def display_error_page(errors: list):
    """
    Affiche une page d'erreur si les modules backend ne sont pas disponibles
    
    Args:
        errors: Liste des erreurs
    """
    st.error("🚨 Erreur de Configuration")
    
    st.markdown("""
    ## Modules Backend Manquants
    
    L'application ne peut pas démarrer car certains modules backend sont manquants.
    """)
    
    st.markdown("### Modules manquants:")
    for error in errors:
        st.markdown(f"- ❌ {error}")
    
    st.markdown("""
    ### Solution:
    
    1. Vérifiez que le dossier `backend/` existe à la racine du projet
    2. Vérifiez que tous les fichiers Python sont présents dans `backend/`
    3. Relancez l'application
    
    Si le problème persiste, consultez la documentation ou contactez le support.
    """)


def get_app_config():
    """
    Retourne la configuration de l'application
    
    Returns:
        Dict de configuration
    """
    return {
        'app_name': 'Suivi ECHA',
        'version': '2.0.0',
        'theme': st.session_state.get('theme', 'light'),
        'language': st.session_state.get('language', 'fr'),
        'max_upload_size_mb': 200,
        'supported_file_types': ['.xlsx', '.xls', '.csv'],
        'log_level': 'INFO',
        'cache_ttl': 3600,  # secondes
    }


def clear_all_caches():
    """
    Efface tous les caches de l'application
    """
    st.cache_data.clear()
    st.cache_resource.clear()
    logger.info("Tous les caches ont été effacés")
    st.success("✅ Caches effacés avec succès")


def display_debug_info():
    """
    Affiche des informations de debug (uniquement en mode développement)
    """
    if st.sidebar.checkbox("🔧 Mode Debug", value=False):
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🐛 Debug Info")
        
        with st.sidebar.expander("Session State"):
            st.json(dict(st.session_state))
        
        with st.sidebar.expander("Configuration"):
            st.json(get_app_config())
        
        with st.sidebar.expander("Managers Status"):
            managers = initialize_managers()
            status = {
                name: "✅ OK" if manager is not None else "❌ Error"
                for name, manager in managers.items()
            }
            st.json(status)
        
        if st.sidebar.button("🗑️ Effacer les caches"):
            clear_all_caches()