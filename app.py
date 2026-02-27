import streamlit as st
import yfinance as yf
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="AlphaDesk",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    .stMetric {
        background-color: #1c1f26;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #2a2d35;
    }
    .stMetric label {
        color: #8b9ab0 !important;
        font-size: 0.75rem !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .stMetric [data-testid="metric-container"] {
        color: #ffffff;
    }
    h1 {
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 1.8rem !important;
        letter-spacing: -0.02em;
    }
    h3 {
        color: #c0cad8 !important;
        font-weight: 500 !important;
    }
    .stDivider { border-color: #2a2d35; }
    section[data-testid="stSidebar"] {
        background-color: #13161d;
        border-right: 1px solid #2a2d35;
    }
    table {
        color: #c0cad8 !important;
        font-size: 0.9rem;
    }
    thead tr th {
        color: #8b9ab0 !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        font-size: 0.75rem !important;
        letter-spacing: 0.05em;
    }
    .caption { color: #555e6e !important; font-size: 0.75rem; }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("## AlphaDesk")
st.markdown("<p style='color:#8b9ab0; font-size:0.85rem; margin-top:-10px;'>Terminal financier — Marchés · News · Macro · Signaux · Portfolio</p>", unsafe_allow_html=True)
st.divider()

# Ticker band
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
        delta_str = f"{change:+.2f}%"
        col.metric(label=name, value=f"{price:,.2f}", delta=delta_str)
    except:
        col.metric(label=name, value="—", delta="N/A")

st.divider()

# Navigation guide
st.markdown("### Navigation")
st.markdown("""
| Page | Contenu |
|---|---|
| Markets | Prix live, graphiques candlestick, RSI / MACD |
| News | Actualités financières mondiales en temps réel |
| Macro | Taux directeurs, inflation, PIB, courbe des taux |
| Signals | Signaux trading, alertes Telegram |
| Portfolio | Suivi P&L, répartition, performance |
""")

st.divider()
st.markdown("<p class='caption'>AlphaDesk v1.0 &nbsp;·&nbsp; Yahoo Finance · Alpha Vantage · NewsAPI · FRED · Finnhub</p>", unsafe_allow_html=True)

