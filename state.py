# state.py

import streamlit as st
import json
import extra_streamlit_components as stx

DEFAULT_WATCHLIST = ["BTC-USD", "ETH-USD", "AAPL", "EURUSD=X", "^GSPC", "GC=F"]

@st.cache_resource
def get_cookie_manager():
    return stx.CookieManager()

def save_cookie(key: str, value):
    cm = get_cookie_manager()
    cm.set(key, json.dumps(value), max_age=60 * 60 * 24 * 365)

def load_cookie(key: str, default=None):
    cm = get_cookie_manager()
    try:
        val = cm.get(key)
        return json.loads(val) if val else default
    except:
        return default

def init_state():
    """À appeler en haut de CHAQUE page."""

    # Watchlist
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = load_cookie("watchlist", DEFAULT_WATCHLIST.copy())

    # Ticker actif (partagé Markets → Signals → Backtest)
    if "active_ticker" not in st.session_state:
        st.session_state.active_ticker = load_cookie("active_ticker", "AAPL")

    # Tickers venant du Screener → Portfolio
    if "screener_tickers" not in st.session_state:
        st.session_state.screener_tickers = []

    # Stratégies custom (Signals → Backtest)
    if "custom_strategies" not in st.session_state:
        st.session_state.custom_strategies = load_cookie("custom_strategies", {})

    # Tickers portfolio
    if "portfolio_tickers" not in st.session_state:
        st.session_state.portfolio_tickers = load_cookie("portfolio_tickers", [])

    # Période active (partagée entre pages)
    if "active_period" not in st.session_state:
        st.session_state.active_period = load_cookie("active_period", "1y")
