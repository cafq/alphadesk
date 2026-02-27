import streamlit as st
import yfinance as yf
from dotenv import load_dotenv

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

    /* Cartes modules */
    .module-card {
        background: #1c1f26;
        border: 1px solid #2a2d35;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 12px;
        transition: border-color 0.2s;
        cursor: pointer;
    }
    .module-card:hover { border-color: #4F46E5; }
    .module-title {
        font-size: 0.8rem;
        font-weight: 700;
        color: #4F46E5;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    .module-desc {
        font-size: 0.82rem;
        color: #8b9ab0;
        margin-top: 4px;
    }

    /* Boutons invisibles sur les cartes */
    div[data-testid="stButton"] button {
        background: transparent !important;
        border: none !important;
        color: transparent !important;
        position: absolute;
        width: 100%;
        height: 100%;
        top: 0; left: 0;
        cursor: pointer;
    }
    </style>
""", unsafe_allow_html=True)

# ── HEADER ──────────────────────────────────────────────
st.markdown("""
<div style='padding: 40px 0 10px 0; text-align: center;'>
    <div style='font-size:2.2rem; font-weight:800; color:#ffffff; letter-spacing:-0.04em;'>
        Alpha<span style='color:#4F46E5;'>Desk</span>
    </div>
    <p style='color:#8b9ab0; font-size:0.88rem; margin-top:8px;'>
        Financial intelligence terminal — Real-time markets, macro analytics & trading signals
    </p>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── TICKER BAND ─────────────────────────────────────────
tickers = {
    "BTC-USD": "Bitcoin",
    "AAPL": "Apple",
    "EURUSD=X": "EUR/USD",
    "GC=F": "Gold",
    "^GSPC": "S&P 500",
    "^FCHI": "CAC 40"
}

cols = st.columns(6)
for col, (ticker, name) in zip(cols, tickers.items()):
    try:
        data = yf.Ticker(ticker)
        price = data.fast_info['last_price']
        prev = data.fast_info['previous_close']
        change = ((price - prev) / prev) * 100
        col.metric(label=name, value=f"{price:,.2f}", delta=f"{change:+.2f}%")
    except:
        col.metric(label=name, value="—", delta="N/A")

st.divider()

# ── MODULES ─────────────────────────────────────────────
st.markdown("<p style='color:#8b9ab0; font-size:0.75rem; font-weight:600; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:16px;'>Modules</p>", unsafe_allow_html=True)

modules = [
    ("Markets",    "Real-time prices, candlestick charts, RSI & MACD",     "pages/1_Markets.py"),
    ("News",       "Global financial news with sentiment filtering",         "pages/2_News.py"),
    ("Macro",      "Central bank rates, inflation, GDP, yield curve",        "pages/3_Macro.py"),
    ("Signals",    "Trading signals with Telegram alerts",                   "pages/4_Signals.py"),
    ("Portfolio",  "P&L tracking, allocation & performance metrics",         "pages/5_Portfolio.py"),
    ("Screener",   "Multi-asset screener with technical filters",            "pages/6_Screener.py"),
    ("Backtest",   "Strategy backtesting with performance analytics",        "pages/7_Backtest.py"),
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
        if st.button(f"Ouvrir {title}", key=f"btn_{title}"):
            st.switch_page(page)

st.divider()
st.markdown("<p class='caption' style='text-align:center;'>AlphaDesk v1.0 &nbsp;·&nbsp; Yahoo Finance · Alpha Vantage · NewsAPI · FRED · Finnhub</p>", unsafe_allow_html=True)
