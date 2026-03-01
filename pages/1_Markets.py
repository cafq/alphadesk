# pages/1_Markets.py

import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from dotenv import load_dotenv

load_dotenv()

# ───────────────────────────────────────
# CONFIG
# ───────────────────────────────────────
st.set_page_config(
    page_title="AlphaDesk · Markets",
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
        color: #4F46E5 !important; font-weight: 600 !important;
    }
    .stMetric {
        background-color: #1c1f26;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #2a2d35;
    }
    .stMetric label {
        color: #8b9ab0 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    h1, h2, h3 { color: #ffffff !important; font-weight: 600 !important; }
    .stSelectbox label, .stTextInput label {
        color: #8b9ab0 !important;
        font-size: 0.8rem !important;
        text-transform: uppercase;
    }
    .caption { color: #555e6e !important; font-size: 0.75rem; }
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
    .section-label {
        color: #8b9ab0;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 12px;
    }
    </style>
""", unsafe_allow_html=True)


# ───────────────────────────────────────
# HEADER
# ───────────────────────────────────────
st.markdown("""
<div style='padding: 30px 0 10px 0; text-align: center;'>
    <div style='font-size:2.2rem; font-weight:800; color:#ffffff; letter-spacing:-0.04em;'>
        Alpha<span style='color:#4F46E5;'>Desk</span>
        <span style='font-size:1.1rem; font-weight:500; color:#8b9ab0; margin-left:12px;'>/ Markets</span>
    </div>
    <p style='color:#8b9ab0; font-size:0.88rem; margin-top:8px;'>
        Graphiques avancés · Indicateurs · Données fondamentales
    </p>
</div>
""", unsafe_allow_html=True)

st.divider()


# ───────────────────────────────────────
# INDICATEURS TECHNIQUES
# ───────────────────────────────────────
def compute_rsi(s, n=14):
    d = s.diff()
    g = d.clip(lower=0).rolling(n).mean()
    l = (-d.clip(upper=0)).rolling(n).mean()
    rs = g / l.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def compute_macd(s, fast=12, slow=26, sig=9):
    ef = s.ewm(span=fast, adjust=False).mean()
    es = s.ewm(span=slow, adjust=False).mean()
    m = ef - es
    signal = m.ewm(span=sig, adjust=False).mean()
    return m, signal, m - signal

def compute_bollinger(s, n=20, k=2):
    sma = s.rolling(n).mean()
    std = s.rolling(n).std()
    return sma + k*std, sma, sma - k*std

def compute_stoch(high, low, close, n=14, d=3):
    lo = low.rolling(n).min()
    hi = high.rolling(n).max()
    k = 100 * (close - lo) / (hi - lo).replace(0, np.nan)
    return k, k.rolling(d).mean()

def compute_stoch_rsi(s, rsi_period=14, stoch_period=14, k_smooth=3, d_smooth=3):
    rsi = compute_rsi(s, rsi_period)
    lo = rsi.rolling(stoch_period).min()
    hi = rsi.rolling(stoch_period).max()
    k = 100 * (rsi - lo) / (hi - lo).replace(0, np.nan)
    k_s = k.rolling(k_smooth).mean()
    d_s = k_s.rolling(d_smooth).mean()
    return k_s, d_s

def compute_atr(high, low, close, n=14):
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(n).mean()

def compute_obv(close, volume):
    direction = np.sign(close.diff()).fillna(0)
    return (direction * volume).cumsum()

def compute_ema(s, n):
    return s.ewm(span=n, adjust=False).mean()

def compute_vwap(df):
    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    return (tp * df["Volume"]).cumsum() / df["Volume"].cumsum()

def compute_williams_r(high, low, close, n=14):
    hi = high.rolling(n).max()
    lo = low.rolling(n).min()
    return -100 * (hi - close) / (hi - lo).replace(0, np.nan)


# ───────────────────────────────────────
# WATCHLIST RAPIDE
# ───────────────────────────────────────
st.markdown("<p class='section-label'>Watchlist rapide</p>", unsafe_allow_html=True)

watchlist = ["BTC-USD", "ETH-USD", "AAPL", "MSFT", "GOOGL", "EURUSD=X", "GC=F"]
cols = st.columns(len(watchlist))
for col, t in zip(cols, watchlist):
    try:
        info = yf.Ticker(t).fast_info
        price = info["last_price"]
        prev  = info["previous_close"]
        chg   = (price - prev) / prev * 100
        col.metric(
            t.replace("-USD","").replace("=X","").replace("=F",""),
            f"{price:,.2f}",
            f"{chg:+.2f}%"
        )
    except:
        col.metric(t, "N/A", "—")

st.divider()


# ───────────────────────────────────────
# SÉLECTION TICKER / PÉRIODE
# ───────────────────────────────────────
col_left, col_right = st.columns([3, 1])
with col_left:
    ticker_input = st.text_input(
        "TICKER",
        value="BTC-USD",
        placeholder="Ex: AAPL, BTC-USD, EURUSD=X..."
    )
with col_right:
    period = st.selectbox("PÉRIODE", ["1d","5d","1mo","3mo","6mo","1y","2y","5y"], index=5)

interval_map = {
    "1d": "5m", "5d": "15m", "1mo": "1h",
    "3mo": "1d", "6mo": "1d", "1y": "1d",
    "2y": "1wk", "5y": "1wk"
}
interval = interval_map[period]


# ───────────────────────────────────────
# SÉLECTION INDICATEURS
# ───────────────────────────────────────
st.markdown("<p class='section-label'>Indicateurs</p>", unsafe_allow_html=True)

c1,c2,c3,c4,c5,c6,c7,c8,c9,c10 = st.columns(10)
show_ema20   = c1.checkbox("EMA 20",    value=True)
show_ema50   = c2.checkbox("EMA 50",    value=True)
show_ema200  = c3.checkbox("EMA 200",   value=False)
show_bb      = c4.checkbox("Bollinger", value=True)
show_vwap    = c5.checkbox("VWAP",      value=False)
show_rsi     = c6.checkbox("RSI",       value=True)
show_macd    = c7.checkbox("MACD",      value=True)
show_stoch   = c8.checkbox("Stoch",     value=False)
show_stochrsi= c9.checkbox("StochRSI",  value=False)
show_obv     = c10.checkbox("OBV",      value=False)

st.divider()


# ───────────────────────────────────────
# CHARGEMENT DONNÉES
# ───────────────────────────────────────
@st.cache_data(ttl=60)
def get_data(ticker, period, interval):
    df = yf.download(ticker, period=period, interval=interval, auto_adjust=True, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

try:
    df = get_data(ticker_input.upper(), period, interval)
    if df.empty:
        st.error("Ticker introuvable. Vérifie le symbole.")
        st.stop()
except:
    st.error("Erreur lors du chargement des données.")
    st.stop()

close  = df["Close"]
high   = df["High"]
low    = df["Low"]
volume = df["Volume"]

# Calcul des indicateurs
rsi              = compute_rsi(close)
macd, macd_sig, macd_hist = compute_macd(close)
bb_up, bb_mid, bb_lo = compute_bollinger(close)
ema20            = compute_ema(close, 20)
ema50            = compute_ema(close, 50)
ema200           = compute_ema(close, 200)
stoch_k, stoch_d = compute_stoch(high, low, close)
stochrsi_k, stochrsi_d = compute_stoch_rsi(close)
atr              = compute_atr(high, low, close)
obv              = compute_obv(close, volume)
vwap             = compute_vwap(df)
williams_r       = compute_williams_r(high, low, close)


# ───────────────────────────────────────
# MÉTRIQUES HEADER
# ───────────────────────────────────────
current   = float(close.iloc[-1])
prev_c    = float(close.iloc[-2]) if len(close) > 1 else current
change    = (current - prev_c) / prev_c * 100
high_val  = float(high.max())
low_val   = float(low.min())
rsi_val   = float(rsi.dropna().iloc[-1]) if not rsi.dropna().empty else 0
atr_val   = float(atr.dropna().iloc[-1]) if not atr.dropna().empty else 0
vol_val   = float(volume.sum())

m1,m2,m3,m4,m5,m6 = st.columns(6)
m1.metric("PRIX ACTUEL",  f"{current:,.2f}",  f"{change:+.2f}%")
m2.metric("PLUS HAUT",    f"{high_val:,.2f}")
m3.metric("PLUS BAS",     f"{low_val:,.2f}")
m4.metric(f"RSI 14",      f"{rsi_val:.1f}")
m5.metric("ATR 14",       f"{atr_val:.2f}")
m6.metric("WILLIAMS %R",  f"{float(williams_r.dropna().iloc[-1]):.1f}")

st.divider()


# ───────────────────────────────────────
# CONSTRUCTION DU GRAPHIQUE
# ───────────────────────────────────────
subplot_titles = ["", "Volume"]
row_heights    = [0.50, 0.12]
nrows          = 2

if show_rsi:      nrows += 1; subplot_titles.append("RSI 14");     row_heights.append(0.11)
if show_macd:     nrows += 1; subplot_titles.append("MACD");       row_heights.append(0.12)
if show_stoch:    nrows += 1; subplot_titles.append("Stochastique"); row_heights.append(0.11)
if show_stochrsi: nrows += 1; subplot_titles.append("Stoch RSI");  row_heights.append(0.11)
if show_obv:      nrows += 1; subplot_titles.append("OBV");        row_heights.append(0.11)

# Normaliser row_heights
total = sum(row_heights)
row_heights = [h/total for h in row_heights]

fig = make_subplots(
    rows=nrows, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.02,
    row_heights=row_heights,
    subplot_titles=subplot_titles,
)

# ── Candlestick ──
fig.add_trace(go.Candlestick(
    x=df.index, open=df["Open"], high=high, low=low, close=close,
    name="Prix",
    increasing_line_color="#26a69a", decreasing_line_color="#ef5350",
    increasing_fillcolor="#26a69a", decreasing_fillcolor="#ef5350",
), row=1, col=1)

# ── Bollinger ──
if show_bb:
    for y, name, dash in [(bb_up,"BB Up","dash"),(bb_mid,"BB Mid","dot"),(bb_lo,"BB Low","dash")]:
        fig.add_trace(go.Scatter(
            x=df.index, y=y, name=name,
            line=dict(color="#7b8fa1", width=1, dash=dash), opacity=0.6
        ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=df.index, y=bb_up, fill=None, mode="lines",
        line=dict(color="rgba(123,143,161,0)"), showlegend=False
    ), row=1, col=1)

# ── EMAs ──
emas = [
    (show_ema20,  ema20,  "EMA 20",  "#f0b429"),
    (show_ema50,  ema50,  "EMA 50",  "#4fc3f7"),
    (show_ema200, ema200, "EMA 200", "#ce93d8"),
]
for show, data, name, color in emas:
    if show:
        fig.add_trace(go.Scatter(
            x=df.index, y=data, name=name,
            line=dict(color=color, width=1.5)
        ), row=1, col=1)

# ── VWAP ──
if show_vwap:
    fig.add_trace(go.Scatter(
        x=df.index, y=vwap, name="VWAP",
        line=dict(color="#ff7043", width=1.5, dash="dot")
    ), row=1, col=1)

# ── Volume ──
colors_vol = ["#26a69a" if float(close.iloc[i]) >= float(df["Open"].iloc[i]) else "#ef5350"
              for i in range(len(df))]
fig.add_trace(go.Bar(
    x=df.index, y=volume, name="Volume",
    marker_color=colors_vol, opacity=0.6
), row=2, col=1)

# ── Indicateurs oscillateurs ──
current_row = 3

if show_rsi:
    fig.add_trace(go.Scatter(
        x=df.index, y=rsi, name="RSI",
        line=dict(color="#f0b429", width=1.5)
    ), row=current_row, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="#ef5350", line_width=1, opacity=0.5, row=current_row, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="#26a69a", line_width=1, opacity=0.5, row=current_row, col=1)
    fig.add_hrect(y0=70, y1=100, fillcolor="#ef5350", opacity=0.04, row=current_row, col=1)
    fig.add_hrect(y0=0,  y1=30,  fillcolor="#26a69a", opacity=0.04, row=current_row, col=1)
    current_row += 1

if show_macd:
    colors_macd = ["#26a69a" if v >= 0 else "#ef5350" for v in macd_hist.fillna(0)]
    fig.add_trace(go.Bar(
        x=df.index, y=macd_hist, name="Histogramme",
        marker_color=colors_macd, opacity=0.7
    ), row=current_row, col=1)
    fig.add_trace(go.Scatter(
        x=df.index, y=macd, name="MACD",
        line=dict(color="#4fc3f7", width=1.5)
    ), row=current_row, col=1)
    fig.add_trace(go.Scatter(
        x=df.index, y=macd_sig, name="Signal",
        line=dict(color="#f48fb1", width=1.5)
    ), row=current_row, col=1)
    current_row += 1

if show_stoch:
    fig.add_trace(go.Scatter(
        x=df.index, y=stoch_k, name="Stoch %K",
        line=dict(color="#4fc3f7", width=1.5)
    ), row=current_row, col=1)
    fig.add_trace(go.Scatter(
        x=df.index, y=stoch_d, name="Stoch %D",
        line=dict(color="#f0b429", width=1.5)
    ), row=current_row, col=1)
    fig.add_hline(y=80, line_dash="dash", line_color="#ef5350", line_width=1, opacity=0.5, row=current_row, col=1)
    fig.add_hline(y=20, line_dash="dash", line_color="#26a69a", line_width=1, opacity=0.5, row=current_row, col=1)
    current_row += 1

if show_stochrsi:
    fig.add_trace(go.Scatter(
        x=df.index, y=stochrsi_k, name="StochRSI %K",
        line=dict(color="#ce93d8", width=1.5)
    ), row=current_row, col=1)
    fig.add_trace(go.Scatter(
        x=df.index, y=stochrsi_d, name="StochRSI %D",
        line=dict(color="#ff7043", width=1.5)
    ), row=current_row, col=1)
    fig.add_hline(y=80, line_dash="dash", line_color="#ef5350", line_width=1, opacity=0.5, row=current_row, col=1)
    fig.add_hline(y=20, line_dash="dash", line_color="#26a69a", line_width=1, opacity=0.5, row=current_row, col=1)
    current_row += 1

if show_obv:
    fig.add_trace(go.Scatter(
        x=df.index, y=obv, name="OBV",
        line=dict(color="#26a69a", width=1.5),
        fill="tozeroy", fillcolor="rgba(38,166,154,0.05)"
    ), row=current_row, col=1)
    current_row += 1

# ── Layout global ──
fig.update_layout(
    height=780,
    paper_bgcolor="#0e1117",
    plot_bgcolor="#0e1117",
    font=dict(family="Inter", color="#8b9ab0", size=11),
    xaxis_rangeslider_visible=False,
    legend=dict(
        orientation="h", yanchor="bottom", y=1.01,
        xanchor="right", x=1, bgcolor="rgba(0,0,0,0)",
        font=dict(size=10)
    ),
    margin=dict(l=10, r=10, t=30, b=10),
    hovermode="x unified",
)
fig.update_xaxes(gridcolor="#1e2228", showgrid=True, zeroline=False)
fig.update_yaxes(gridcolor="#1e2228", showgrid=True, zeroline=False)

st.plotly_chart(fig, use_container_width=True)


# ───────────────────────────────────────
# DONNÉES FONDAMENTALES
# ───────────────────────────────────────
st.divider()
st.markdown("<p class='section-label'>Données fondamentales</p>", unsafe_allow_html=True)

try:
    info = yf.Ticker(ticker_input.upper()).info
    f1, f2, f3, f4, f5, f6 = st.columns(6)
    f1.metric("Market Cap",  f"{info.get('marketCap',0)/1e9:.2f}B" if info.get('marketCap') else "—")
    f2.metric("PE Ratio",    f"{info.get('trailingPE','—'):.2f}"   if isinstance(info.get('trailingPE'), float) else "—")
    f3.metric("52W High",    f"{info.get('fiftyTwoWeekHigh','—')}")
    f4.metric("52W Low",     f"{info.get('fiftyTwoWeekLow','—')}")
    f5.metric("Dividend",    f"{info.get('dividendYield',0)*100:.2f}%" if info.get('dividendYield') else "—")
    f6.metric("Beta",        f"{info.get('beta','—'):.2f}"             if isinstance(info.get('beta'), float) else "—")
except:
    st.info("Données fondamentales non disponibles pour ce ticker.")

st.divider()
st.markdown(
    "<p class='caption' style='text-align:center;'>AlphaDesk v1.0 &nbsp;·&nbsp; Yahoo Finance · Markets</p>",
    unsafe_allow_html=True,
)
