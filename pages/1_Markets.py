import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Markets — AlphaDesk", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    section[data-testid="stSidebar"] { background-color: #13161d; border-right: 1px solid #2a2d35; }
    .stMetric { background-color: #1c1f26; padding: 15px; border-radius: 8px; border: 1px solid #2a2d35; }
    .stMetric label { color: #8b9ab0 !important; font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 0.08em; }
    h1, h2, h3 { color: #ffffff !important; font-weight: 600 !important; }
    .stSelectbox label, .stTextInput label { color: #8b9ab0 !important; font-size: 0.8rem !important; text-transform: uppercase; }
    </style>
""", unsafe_allow_html=True)

# ── Indicateurs techniques ──────────────────────────────────────────
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = -delta.where(delta < 0, 0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def compute_macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast).mean()
    ema_slow = series.ewm(span=slow).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal).mean()
    histogram = macd - signal_line
    return macd, signal_line, histogram

def compute_bollinger(series, period=20, std=2):
    sma = series.rolling(period).mean()
    stddev = series.rolling(period).std()
    return sma + std * stddev, sma, sma - std * stddev

def compute_stoch(high, low, close, period=14):
    lowest = low.rolling(period).min()
    highest = high.rolling(period).max()
    k = 100 * (close - lowest) / (highest - lowest)
    d = k.rolling(3).mean()
    return k, d

def compute_atr(high, low, close, period=14):
    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def compute_ema(series, period):
    return series.ewm(span=period).mean()

def compute_vwap(df):
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    return (tp * df['Volume']).cumsum() / df['Volume'].cumsum()

# ── Header ──────────────────────────────────────────────────────────
st.markdown("## Markets")
st.markdown("<p style='color:#8b9ab0; font-size:0.85rem; margin-top:-10px;'>Graphiques avancés · Indicateurs · Données fondamentales</p>", unsafe_allow_html=True)
st.divider()

# ── Watchlist rapide ────────────────────────────────────────────────
watchlist = ["BTC-USD", "ETH-USD", "AAPL", "MSFT", "GOOGL", "EURUSD=X", "GC=F", "^GSPC", "^FCHI"]
cols = st.columns(len(watchlist))
for col, t in zip(cols, watchlist):
    try:
        info = yf.Ticker(t).fast_info
        price = info['last_price']
        prev = info['previous_close']
        chg = ((price - prev) / prev) * 100
        col.metric(t.replace("-USD","").replace("=X","").replace("^",""), f"{price:,.2f}", f"{chg:+.2f}%")
    except:
        col.metric(t, "—", "—")

st.divider()

# ── Sélection ticker ────────────────────────────────────────────────
col_left, col_right = st.columns([3, 1])
with col_left:
    ticker_input = st.text_input("TICKER", value="BTC-USD", placeholder="Ex: AAPL, BTC-USD, EURUSD=X...")
with col_right:
    period = st.selectbox("PÉRIODE", ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"], index=5)

interval_map = {"1d": "5m", "5d": "15m", "1mo": "1h", "3mo": "1d", "6mo": "1d", "1y": "1d", "2y": "1wk", "5y": "1wk"}
interval = interval_map[period]

# ── Indicateurs à afficher ──────────────────────────────────────────
st.markdown("**INDICATEURS**")
c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
show_ema20 = c1.checkbox("EMA 20", value=True)
show_ema50 = c2.checkbox("EMA 50", value=True)
show_ema200 = c3.checkbox("EMA 200", value=False)
show_bb = c4.checkbox("Bollinger", value=True)
show_vwap = c5.checkbox("VWAP", value=False)
show_rsi = c6.checkbox("RSI", value=True)
show_macd = c7.checkbox("MACD", value=True)

@st.cache_data(ttl=60)
def get_data(ticker, period, interval):
    return yf.download(ticker, period=period, interval=interval, auto_adjust=True)

try:
    df = get_data(ticker_input.upper(), period, interval)

    if df.empty:
        st.error("Ticker introuvable. Vérifie le symbole.")
        st.stop()

    # Flatten colonnes si MultiIndex
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    close = df['Close']

    # Calcul indicateurs
    rsi = compute_rsi(close)
    macd, macd_signal, macd_hist = compute_macd(close)
    bb_upper, bb_mid, bb_lower = compute_bollinger(close)
    ema20 = compute_ema(close, 20)
    ema50 = compute_ema(close, 50)
    ema200 = compute_ema(close, 200)
    stoch_k, stoch_d = compute_stoch(df['High'], df['Low'], close)
    atr = compute_atr(df['High'], df['Low'], close)
    vwap = compute_vwap(df)

    # ── Métriques clés ──────────────────────────────────────────────
    current = float(close.iloc[-1])
    prev_close = float(close.iloc[-2]) if len(close) > 1 else current
    change = ((current - prev_close) / prev_close) * 100
    high = float(df['High'].max())
    low = float(df['Low'].min())
    vol = float(df['Volume'].sum()) if 'Volume' in df else 0

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("PRIX ACTUEL", f"{current:,.2f}", f"{change:+.2f}%")
    m2.metric("PLUS HAUT", f"{high:,.2f}")
    m3.metric("PLUS BAS", f"{low:,.2f}")
    m4.metric(f"RSI (14)", f"{float(rsi.iloc[-1]):.1f}")
    m5.metric("ATR (14)", f"{float(atr.iloc[-1]):.2f}")

    # ── Nombre de sous-graphes ──────────────────────────────────────
    n_rows = 2
    row_heights = [0.6, 0.15]
    if show_rsi:
        n_rows += 1
        row_heights.append(0.12)
    if show_macd:
        n_rows += 1
        row_heights.append(0.13)

    subplot_titles = ["", "Volume"]
    if show_rsi: subplot_titles.append("RSI (14)")
    if show_macd: subplot_titles.append("MACD")

    fig = make_subplots(
        rows=n_rows, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
        subplot_titles=subplot_titles
    )

    # ── Candlestick ─────────────────────────────────────────────────
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'],
        name="Prix",
        increasing_line_color="#26a69a",
        decreasing_line_color="#ef5350",
        increasing_fillcolor="#26a69a",
        decreasing_fillcolor="#ef5350"
    ), row=1, col=1)

    # Bollinger Bands
    if show_bb:
        fig.add_trace(go.Scatter(x=df.index, y=bb_upper, name="BB Upper", line=dict(color="#7b8fa1", width=1, dash="dash"), opacity=0.6), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=bb_mid, name="BB Mid", line=dict(color="#7b8fa1", width=1), opacity=0.4, fill=None), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=bb_lower, name="BB Lower", line=dict(color="#7b8fa1", width=1, dash="dash"), opacity=0.6, fill='tonexty', fillcolor='rgba(123,143,161,0.05)'), row=1, col=1)

    # EMAs
    if show_ema20:
        fig.add_trace(go.Scatter(x=df.index, y=ema20, name="EMA 20", line=dict(color="#f0b429", width=1.5)), row=1, col=1)
    if show_ema50:
        fig.add_trace(go.Scatter(x=df.index, y=ema50, name="EMA 50", line=dict(color="#4fc3f7", width=1.5)), row=1, col=1)
    if show_ema200:
        fig.add_trace(go.Scatter(x=df.index, y=ema200, name="EMA 200", line=dict(color="#ce93d8", width=1.5)), row=1, col=1)

    # VWAP
    if show_vwap:
        fig.add_trace(go.Scatter(x=df.index, y=vwap, name="VWAP", line=dict(color="#ff7043", width=1.5, dash="dot")), row=1, col=1)

    # ── Volume ──────────────────────────────────────────────────────
    colors_vol = ["#26a69a" if float(df['Close'].iloc[i]) >= float(df['Open'].iloc[i]) else "#ef5350" for i in range(len(df))]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Volume", marker_color=colors_vol, opacity=0.6), row=2, col=1)

    current_row = 3

    # ── RSI ─────────────────────────────────────────────────────────
    if show_rsi:
        fig.add_trace(go.Scatter(x=df.index, y=rsi, name="RSI", line=dict(color="#f0b429", width=1.5)), row=current_row, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="#ef5350", line_width=1, opacity=0.5, row=current_row, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#26a69a", line_width=1, opacity=0.5, row=current_row, col=1)
        fig.add_hrect(y0=70, y1=100, fillcolor="#ef5350", opacity=0.05, row=current_row, col=1)
        fig.add_hrect(y0=0, y1=30, fillcolor="#26a69a", opacity=0.05, row=current_row, col=1)
        current_row += 1

    # ── MACD ────────────────────────────────────────────────────────
    if show_macd:
        colors_macd = ["#26a69a" if v >= 0 else "#ef5350" for v in macd_hist]
        fig.add_trace(go.Bar(x=df.index, y=macd_hist, name="Histogramme", marker_color=colors_macd, opacity=0.7), row=current_row, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=macd, name="MACD", line=dict(color="#4fc3f7", width=1.5)), row=current_row, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=macd_signal, name="Signal", line=dict(color="#f48fb1", width=1.5)), row=current_row, col=1)

    # ── Layout ──────────────────────────────────────────────────────
    fig.update_layout(
        height=750,
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        font=dict(family="Inter", color="#8b9ab0", size=11),
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1, bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
        margin=dict(l=10, r=10, t=30, b=10),
        hovermode="x unified"
    )
    fig.update_xaxes(gridcolor="#1e2228", showgrid=True, zeroline=False)
    fig.update_yaxes(gridcolor="#1e2228", showgrid=True, zeroline=False)

    st.plotly_chart(fig, use_container_width=True)

    # ── Données fondamentales ────────────────────────────────────────
    st.divider()
    st.markdown("### Données fondamentales")
    try:
        info = yf.Ticker(ticker_input.upper()).info
        f1, f2, f3, f4 = st.columns(4)
        f1.metric("Market Cap", f"{info.get('marketCap', 0)/1e9:.2f}B" if info.get('marketCap') else "—")
        f2.metric("P/E Ratio", f"{info.get('trailingPE', '—'):.2f}" if isinstance(info.get('trailingPE'), float) else "—")
        f3.metric("52W High", f"{info.get('fiftyTwoWeekHigh', '—')}")
        f4.metric("52W Low", f"{info.get('fiftyTwoWeekLow', '—')}")
    except:
        st.info("Données fondamentales non disponibles pour ce ticker.")

except Exception as e:
    st.error(f"Erreur : {e}")
