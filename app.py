import streamlit as st
import yfinance as yf
from dotenv import load_dotenv

DEFAULT_WATCHLIST = ["BTC-USD", "ETH-USD", "AAPL", "EURUSD=X", "^GSPC", "GC=F"]
load_dotenv()


st.set_page_config(
    page_title="AlphaDesk",
    page_icon="▲",
    layout="wide",
    initial_sidebar_state="collapsed"
)


st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .stDivider { border-color: #2a2d35; }
    section[data-testid="stSidebar"] {
        background-color: #13161d;
        border-right: 1px solid #2a2d35;
    }
    .stMetric {
        background-color: #1c1f26;
        padding: 16px;
        border-radius: 8px;
        border: 1px solid #2a2d35;
    }
    .stMetric label {
        color: #8b9ab0 !important;
        font-size: 0.7rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    .caption { color: #555e6e !important; font-size: 0.75rem; }
    .module-card {
        background: #1c1f26;
        border: 1px solid #2a2d35;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 12px;
    }
    .module-title {
        font-size: 0.8rem;
        font-weight: 700;
        color: #4F46E5;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    .module-desc { font-size: 0.82rem; color: #8b9ab0; margin-top: 4px; }
    .stTextInput input {
        background-color: #1c1f26 !important;
        border: 1px solid #2a2d35 !important;
        color: #e0e0e0 !important;
        border-radius: 6px !important;
    }
    div.stButton > button {
        background-color: #4F46E5 !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
    }
    div.stButton > button:hover { background-color: #4338ca !important; }
    </style>
""", unsafe_allow_html=True)
# ═══════════════════════════════════════════════════════════════
# SYSTÈME DE LOGIN - NOUVEAU !
# ═══════════════════════════════════════════════════════════════


# Init session utilisateur
if "user_logged_in" not in st.session_state:
    st.session_state.user_logged_in = False
    st.session_state.username = None
    st.session_state.watchlist = DEFAULT_WATCHLIST.copy()


# Login form (sidebar)
with st.sidebar:
    st.markdown("## 🔐 Connexion")
   
    # Champs login
    username = st.text_input("Nom d'utilisateur", placeholder="ton_nom")
    password = st.text_input("Mot de passe", type="password", placeholder="*****")
   
    if st.button("Se connecter", use_container_width=True):
        # Login simple (à sécuriser plus tard)
        if username and password:
            st.session_state.username = username
            st.session_state.user_logged_in = True
            st.session_state.watchlist = ["BTC-USD", "ETH-USD"]  # Watchlist par défaut
            st.rerun()
        else:
            st.error("⚠️ Remplis tous les champs")
   
    if st.session_state.user_logged_in:
        st.success(f"👋 Bienvenue {st.session_state.username}")
        if st.button("🔓 Déconnexion", use_container_width=True):
            st.session_state.user_logged_in = False
            st.session_state.username = None
            st.session_state.watchlist = []
            st.rerun()
    else:
        st.info("👤 Crée ton espace perso")


# Vérifier si connecté
if not st.session_state.user_logged_in:
    st.markdown("""
    <div style='padding: 100px; text-align: center;'>
        <h1 style='color:#8b9ab0; font-size:2.5rem;'>🔐 Connexion requise</h1>
        <p style='color:#555e6e; font-size:1.1rem; margin-top:20px;'>
            Connecte-toi via la barre latérale pour accéder à ton espace AlphaDesk
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()  # Arrête l'app si pas connecté


# ── Le reste de ton code continue ici (HEADER, WATCHLIST...)


# ── WATCHLIST STATE ──────────────────────────────────────
DEFAULT_WATCHLIST = ["BTC-USD", "ETH-USD", "AAPL", "EURUSD=X", "^GSPC", "GC=F"]


if "watchlist" not in st.session_state:
    st.session_state.watchlist = DEFAULT_WATCHLIST.copy()


# ── HEADER ───────────────────────────────────────────────
st.markdown("""
<div style='padding: 30px 0 10px 0; text-align: center;'>
    <div style='font-size:2.2rem; font-weight:800; color:#ffffff; letter-spacing:-0.04em;'>
        Alpha<span style='color:#4F46E5;'>Desk</span>
    </div>
    <p style='color:#8b9ab0; font-size:0.88rem; margin-top:8px;'>
        Financial intelligence terminal — Real-time markets, macro analytics & trading signals
    </p>
</div>
""", unsafe_allow_html=True)


st.divider()


# ── WATCHLIST ────────────────────────────────────────────
st.markdown("<p style='color:#8b9ab0; font-size:0.75rem; font-weight:600; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:12px;'>Ma Watchlist</p>", unsafe_allow_html=True)


c1, c2, c3 = st.columns([4, 1, 1])
with c1:
    new_ticker = st.text_input(
        "ticker",
        placeholder="Ajouter un actif : TSLA, BTC-USD, MC.PA, EURUSD=X...",
        label_visibility="collapsed"
    )
with c2:
    if st.button("Ajouter", use_container_width=True):
        if new_ticker:
            t = new_ticker.upper().strip()
            if t not in st.session_state.watchlist:
                st.session_state.watchlist.append(t)
                st.rerun()
            else:
                st.warning("Déjà dans ta watchlist")
with c3:
    if st.button("Réinitialiser", use_container_width=True):
        st.session_state.watchlist = DEFAULT_WATCHLIST.copy()
        st.rerun()


# Affichage des prix
if st.session_state.watchlist:
    n = len(st.session_state.watchlist)
    cols_per_row = min(n, 6)
    cols = st.columns(cols_per_row)
    for i, ticker in enumerate(st.session_state.watchlist):
        col = cols[i % cols_per_row]
        try:
            data = yf.Ticker(ticker)
            price = data.fast_info['last_price']
            prev = data.fast_info['previous_close']
            change = ((price - prev) / prev) * 100
            col.metric(label=ticker, value=f"{price:,.2f}", delta=f"{change:+.2f}%")
        except:
            col.metric(label=ticker, value="N/A", delta="—")


    # Supprimer actifs
    st.markdown("<p style='color:#555e6e; font-size:0.72rem; margin-top:10px;'>Supprimer :</p>", unsafe_allow_html=True)
    del_cols = st.columns(min(n, 8))
    for i, ticker in enumerate(st.session_state.watchlist):
        if del_cols[i % min(n, 8)].button(f"✕ {ticker}", key=f"del_{ticker}"):
            st.session_state.watchlist.remove(ticker)
            st.rerun()


st.divider()


# ── MODULES ──────────────────────────────────────────────
st.markdown("<p style='color:#8b9ab0; font-size:0.75rem; font-weight:600; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:16px;'>Modules</p>", unsafe_allow_html=True)


modules = [
    ("Markets",   "Real-time prices, candlestick charts, RSI & MACD",   "pages/1_Markets.py"),
    ("News",      "Global financial news with sentiment filtering",       "pages/2_News.py"),
    ("Macro",     "Central bank rates, inflation, GDP, yield curve",      "pages/3_Macro.py"),
    ("Signals",   "Trading signals with Telegram alerts",                 "pages/4_Signals.py"),
    ("Portfolio", "P&L tracking, allocation & performance metrics",       "pages/5_Portfolio.py"),
    ("Screener",  "Multi-asset screener with technical filters",          "pages/6_Screener.py"),
    ("Backtest",  "Strategy backtesting with performance analytics",      "pages/7_Backtest.py"),
]


col1, col2 = st.columns(2)
for i, (title, desc, page) in enumerate(modules):
    col = col1 if i % 2 == 0 else col2
    with col:
        st.markdown(f"""
        <div class='module-card'>
            <div class='module-title'>{title}</div>
            <div class='module-desc'>{desc}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"Ouvrir {title}", key=f"btn_{title}", use_container_width=True):
            st.switch_page(page)


st.divider()
st.markdown("<p class='caption' style='text-align:center;'>AlphaDesk v1.0 &nbsp;·&nbsp; Yahoo Finance · Alpha Vantage · NewsAPI · FRED · Finnhub</p>", unsafe_allow_html=True)