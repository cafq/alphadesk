import sys
_os = __import__("os")
ROOT_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)
from utils.ai_assistant import render_chat_widget, build_context

render_chat_widget("home")

# Home.py

import streamlit as st
import yfinance as yf
from dotenv import load_dotenv
import json
import os

load_dotenv()

# ───────────────────────────────────────
# CONFIG
# ───────────────────────────────────────
DEFAULT_WATCHLIST = ["BTC-USD", "ETH-USD", "AAPL", "EURUSD=X", "^GSPC", "GC=F"]
WATCHLIST_FILE = "data_watchlist.json"

def load_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r") as f:
                return json.load(f)
        except:
            return DEFAULT_WATCHLIST.copy()
    return DEFAULT_WATCHLIST.copy()

def save_watchlist():
    try:
        with open(WATCHLIST_FILE, "w") as f:
            json.dump(st.session_state.watchlist, f)
    except:
        pass

st.set_page_config(
    page_title="AlphaDesk",
    page_icon="▲",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ───────────────────────────────────────
# STYLE
# ───────────────────────────────────────
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
    section[data-testid="stSidebar"] span { color: #e0e0e0 !important; }
    section[data-testid="stSidebar"] [aria-selected="true"] span {
        color: #4F46E5 !important;
        font-weight: 600 !important;
    }
    h1, h2, h3 { color: #ffffff !important; font-weight: 600 !important; }
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
    .caption { color: #555e6e !important; font-size: 0.75rem; }
    .section-label {
        color: #8b9ab0;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 12px;
    }
    .module-card {
        background: #1c1f26;
        border: 1px solid #2a2d35;
        border-radius: 10px;
        padding: 20px 22px;
        margin-bottom: 4px;
    }
    .module-card:hover { border-color: #4F46E5; }
    .module-icon { font-size: 1.4rem; margin-bottom: 6px; }
    .module-title { font-size: 0.85rem; font-weight: 700; color: #ffffff; }
    .module-desc { font-size: 0.78rem; color: #8b9ab0; margin-top: 3px; }

    [data-testid="stMetricValue"] {
        color: #E0E0E0 !important;
        font-size: 1.4rem !important;
        font-weight: 600 !important;
        font-variant-numeric: tabular-nums !important;
        overflow: visible !important;
        white-space: nowrap !important;
    }

    [data-testid="stMetricLabel"] {
        color: #8b9ab0 !important;
        font-size: 0.7rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.1em !important;
    }

    [data-testid="stMetricDelta"] > div {
        font-size: 0.78rem !important;
        font-weight: 500 !important;
    }

    [data-testid="stMetricDelta"] svg {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)


# ───────────────────────────────────────
# COOKIES (persistance par appareil)
# ───────────────────────────────────────

# ───────────────────────────────────────
# SESSION STATE (avec chargement cookies)
# ───────────────────────────────────────
from state import init_state
init_state()

# ───────────────────────────────────────
# HEADER
# ───────────────────────────────────────
st.markdown("""
<div style='padding: 30px 0 10px 0; text-align: center;'>
    <div style='font-size:2.6rem; font-weight:800; color:#ffffff; letter-spacing:-0.04em;'>
        Alpha<span style='color:#4F46E5;'>Desk</span>
    </div>
    <p style='color:#8b9ab0; font-size:0.9rem; margin-top:8px;'>
        Financial intelligence terminal &nbsp;·&nbsp;
        Markets · Macro · Signals · Portfolio · Screener · Backtest
    </p>
</div>
""", unsafe_allow_html=True)

st.divider()


# ───────────────────────────────────────
# WATCHLIST
# ───────────────────────────────────────
st.markdown("<p class='section-label'>📌 Ma Watchlist</p>", unsafe_allow_html=True)

c1, c2, c3 = st.columns([4, 1, 1])
with c1:
    new_ticker = st.text_input(
        "ticker",
        placeholder="Ajouter : TSLA, BTC-USD, MC.PA, EURUSD=X...",
        label_visibility="collapsed",
    )
with c2:
    if st.button("+ Ajouter", use_container_width=True):
        if new_ticker:
            t = new_ticker.upper().strip()
            if t not in st.session_state.watchlist:
                st.session_state.watchlist.append(t)
                save_watchlist()   # ← persistance
                st.rerun()
            else:
                st.warning("Déjà dans ta watchlist")
with c3:
    if st.button("↺ Reset", use_container_width=True):
        st.session_state.watchlist = DEFAULT_WATCHLIST.copy()
        save_watchlist()           # ← persistance
        st.rerun()

# Affichage prix
if st.session_state.watchlist:
    n = len(st.session_state.watchlist)
    cols_per_row = min(n, 6)
    price_cols = st.columns(cols_per_row)

    for i, ticker in enumerate(st.session_state.watchlist):
        col = price_cols[i % cols_per_row]
        try:
            info   = yf.Ticker(ticker).fast_info
            price  = info["last_price"]
            prev   = info["previous_close"]
            change = (price - prev) / prev * 100
            col.metric(
                label=ticker.replace("-USD","").replace("=X","").replace("^",""),
                value=f"{price:,.2f}",
                delta=f"{change:+.2f}%",
            )
        except:
            col.metric(label=ticker, value="—", delta="—")

    st.markdown("<p class='caption' style='margin-top:8px;'>Supprimer :</p>", unsafe_allow_html=True)
    del_cols = st.columns(min(n, 8))
    to_remove = None
    for i, ticker in enumerate(st.session_state.watchlist):
        if del_cols[i % min(n, 8)].button(f"✕ {ticker}", key=f"del_{ticker}"):
            to_remove = ticker
    if to_remove:
        st.session_state.watchlist.remove(to_remove)
        save_watchlist()           # ← persistance
        st.rerun()

st.divider()


# ───────────────────────────────────────
# SNAPSHOT MARCHÉ
# ───────────────────────────────────────
st.markdown("<p class='section-label'>🌍 Snapshot marché</p>", unsafe_allow_html=True)

SNAPSHOT_TICKERS = {
    "S&P 500": "^GSPC",
    "Nasdaq":  "^IXIC",
    "BTC":     "BTC-USD",
    "Gold":    "GC=F",
    "EUR/USD": "EURUSD=X",
    "VIX":     "^VIX",
}

snap_cols = st.columns(len(SNAPSHOT_TICKERS))
for col, (label, sym) in zip(snap_cols, SNAPSHOT_TICKERS.items()):
    try:
        info   = yf.Ticker(sym).fast_info
        price  = info["last_price"]
        prev   = info["previous_close"]
        change = (price - prev) / prev * 100
        col.metric(label, f"{price:,.2f}", f"{change:+.2f}%")
    except:
        col.metric(label, "—", "—")

st.divider()


# ───────────────────────────────────────
# MODULES
# ───────────────────────────────────────
st.markdown("<p class='section-label'>🧩 Modules</p>", unsafe_allow_html=True)

MODULES = [
    ("📈", "Markets",   "Prix temps réel, chandeliers, RSI, MACD, VWAP",        "pages/1_Markets.py"),
    ("📰", "News",      "Actualités financières mondiales + sentiment",          "pages/2_News.py"),
    ("🌍", "Macro",     "Taux directeurs, inflation, PIB, courbe des taux",      "pages/3_Macro.py"),
    ("⚡", "Signaux",   "RSI, MACD, Bollinger, EMA — score technique global",   "pages/4_Signals.py"),
    ("💼", "Portfolio", "Performance, Markowitz, VaR, corrélations",            "pages/5_Portfolio.py"),
    ("🔍", "Screener",  "Filtrer les actifs par performance, RSI, Sharpe",      "pages/6_Screener.py"),
    ("🔁", "Backtest",  "Tester tes stratégies, SL/TP, Monte Carlo",            "pages/7_Backtest.py"),
    ("🌱", "ESG",       "Scores ESG, controverses, reporting responsable",      "pages/8_ESG.py"),
]

col1, col2 = st.columns(2)
for i, (icon, title, desc, page) in enumerate(MODULES):
    col = col1 if i % 2 == 0 else col2
    with col:
        st.markdown(f"""
        <div class='module-card'>
            <div class='module-icon'>{icon}</div>
            <div class='module-title'>{title}</div>
            <div class='module-desc'>{desc}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"Ouvrir {title}", key=f"btn_{title}", use_container_width=True):
            st.switch_page(page)

st.divider()
st.markdown(
    "<p class='caption' style='text-align:center;'>AlphaDesk v1.0 &nbsp;·&nbsp; Yahoo Finance · NewsAPI · FRED · Finnhub</p>",
    unsafe_allow_html=True,
)
