import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf

st.set_page_config(page_title="Signals — AlphaDesk", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    section[data-testid="stSidebar"] { background-color: #13161d; border-right: 1px solid #2a2d35; }
    h1, h2, h3 { color: #ffffff !important; font-weight: 600 !important; }
    .stSelectbox label, .stTextInput label { color: #8b9ab0 !important; font-size: 0.8rem !important; text-transform: uppercase; }
    .signal-card { background-color: #1c1f26; border-radius: 10px; padding: 18px 22px; border: 1px solid #2a2d35; text-align: center; margin-bottom: 12px; }
    .signal-buy  { border-left: 4px solid #26a69a !important; }
    .signal-sell { border-left: 4px solid #ef5350 !important; }
    .signal-hold { border-left: 4px solid #f0b429 !important; }
    .sig-label { font-size: 0.7rem; color: #8b9ab0; text-transform: uppercase; letter-spacing: 0.1em; }
    .sig-value { font-size: 1.5rem; font-weight: 700; margin: 4px 0; }
    .buy-color  { color: #26a69a; }
    .sell-color { color: #ef5350; }
    .hold-color { color: #f0b429; }
    </style>
""", unsafe_allow_html=True)

st.markdown("## Signaux Techniques")
st.markdown("<p style='color:#8b9ab0; font-size:0.85rem; margin-top:-10px;'>RSI · MACD · Bollinger · EMA · Stochastique · Score global</p>", unsafe_allow_html=True)
st.divider()

# ── Indicateurs ──────────────────────────────────────────────────────
def compute_rsi(s, n=14):
    d = s.diff()
    g = d.clip(lower=0).rolling(n).mean()
    l = -d.clip(upper=0).rolling(n).mean()
    rs = g / l.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def compute_macd(s, f=12, sl=26, sig=9):
    ef  = s.ewm(span=f,   adjust=False).mean()
    es  = s.ewm(span=sl,  adjust=False).mean()
    m   = ef - es
    sg  = m.ewm(span=sig, adjust=False).mean()
    return m, sg, m - sg

def compute_bb(s, n=20, k=2):
    sma = s.rolling(n).mean()
    std = s.rolling(n).std()
    return sma + k*std, sma, sma - k*std

def compute_stoch(h, l, c, n=14, d=3):
    lo = l.rolling(n).min()
    hi = h.rolling(n).max()
    k  = 100 * (c - lo) / (hi - lo).replace(0, np.nan)
    return k, k.rolling(d).mean()

def get_signal(val, low, high):
    if val <= low:  return "BUY",  "buy-color",  "signal-buy"
    if val >= high: return "SELL", "sell-color", "signal-sell"
    return "HOLD", "hold-color", "signal-hold"

def get_signal_cross(a, b):
    if a > b: return "BUY",  "buy-color",  "signal-buy"
    if a < b: return "SELL", "sell-color", "signal-sell"
    return "HOLD", "hold-color", "signal-hold"

def card(col, label, value, sig, color, cls):
    with col:
        st.markdown(f"""
        <div class='signal-card {cls}'>
            <div class='sig-label'>{label}</div>
            <div class='sig-value {color}'>{value}</div>
            <div class='sig-label'>{sig}</div>
        </div>""", unsafe_allow_html=True)

def base_layout(h=300):
    return dict(
        height=h, paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
        font=dict(family="Inter", color="#8b9ab0"),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(gridcolor="#1e2228"),
        yaxis=dict(gridcolor="#1e2228"),
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h")
    )

# ── Interface ────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns([2, 1.5, 1.5, 1])
with c1: ticker   = st.text_input("TICKER", value="AAPL")
with c2: period   = st.selectbox("PÉRIODE",    ["3mo","6mo","1y","2y"], index=2)
with c3: interval = st.selectbox("INTERVALLE", ["1d","1wk"], index=0)
with c4:
    st.markdown("<br>", unsafe_allow_html=True)
    run = st.button("ANALYSER", use_container_width=True, type="primary")

# ── Chargement ───────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_data(ticker, period, interval):
    try:
        df = yf.download(
            ticker, period=period, interval=interval,
            auto_adjust=True, progress=False, timeout=20
        )
        if df.empty:
            return None
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        return df
    except Exception as e:
        return None

# ── Analyse ──────────────────────────────────────────────────────────
if run:
    if not ticker.strip():
        st.warning("Entre un ticker valide.")
        st.stop()

    with st.spinner(f"Chargement de {ticker.upper()}..."):
        df = load_data(ticker.upper(), period, interval)

    if df is None:
        st.error(f"Impossible de charger les données pour **{ticker.upper()}**. Vérifie le ticker ou ta connexion.")
        st.stop()

    if len(df) < 30:
        st.error("Pas assez de données pour calculer les indicateurs (minimum 30 bougies).")
        st.stop()

    # Séries
    close = df["Close"].squeeze()
    high  = df["High"].squeeze()
    low   = df["Low"].squeeze()
    vol   = df["Volume"].squeeze()

    # Calcul
    rsi_s             = compute_rsi(close)
    macd_l, sig_l, his = compute_macd(close)
    bb_up, bb_mid, bb_lo = compute_bb(close)
    ema20  = close.ewm(span=20,  adjust=False).mean()
    ema50  = close.ewm(span=50,  adjust=False).mean()
    ema200 = close.ewm(span=200, adjust=False).mean()
    stk, std_ = compute_stoch(high, low, close)

    # Dernières valeurs
    def safe_last(s):
        try: return float(s.dropna().iloc[-1])
        except: return 0.0

    lc   = safe_last(close)
    lr   = safe_last(rsi_s)
    lm   = safe_last(macd_l)
    ls   = safe_last(sig_l)
    lbu  = safe_last(bb_up)
    lbl  = safe_last(bb_lo)
    le20 = safe_last(ema20)
    le50 = safe_last(ema50)
    lsk  = safe_last(stk)
    lsd  = safe_last(std_)

    # Signaux
    sr = get_signal(lr, 30, 70)
    sm = get_signal_cross(lm, ls)
    sb = get_signal(lc, lbl, lbu)
    se = get_signal_cross(le20, le50)
    ss = get_signal(lsk, 20, 80)

    all_sigs = [sr, sm, sb, se, ss]
    buys  = sum(1 for s in all_sigs if s[0] == "BUY")
    sells = sum(1 for s in all_sigs if s[0] == "SELL")
    if buys > sells:   glob = ("BUY",  "buy-color",  "signal-buy")
    elif sells > buys: glob = ("SELL", "sell-color", "signal-sell")
    else:              glob = ("HOLD", "hold-color", "signal-hold")

    # ── Score cards ──────────────────────────────────────────────────
    st.markdown(f"### {ticker.upper()} — Score Technique")
    cols = st.columns(6)
    card(cols[0], "RSI 14",       f"{lr:.1f}",   sr[0],   sr[1],   sr[2])
    card(cols[1], "MACD",         f"{lm:.3f}",   sm[0],   sm[1],   sm[2])
    card(cols[2], "Bollinger",    f"{lc:.2f}",   sb[0],   sb[1],   sb[2])
    card(cols[3], "EMA 20/50",    f"{le20:.2f}", se[0],   se[1],   se[2])
    card(cols[4], "Stochastique", f"{lsk:.1f}",  ss[0],   ss[1],   ss[2])
    card(cols[5], "SCORE GLOBAL", glob[0],       glob[0], glob[1], glob[2])

    st.divider()

    # ── Graphiques ────────────────────────────────────────────────────
    t1, t2, t3, t4 = st.tabs(["Prix & EMA", "RSI", "MACD", "Stochastique"])

    with t1:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                            row_heights=[0.75, 0.25], vertical_spacing=0.03)
        fig.add_trace(go.Candlestick(
            x=df.index, open=df["Open"].squeeze(),
            high=high, low=low, close=close, name="Prix",
            increasing_line_color="#26a69a", decreasing_line_color="#ef5350"
        ), row=1, col=1)
        for y, name, color, dash in [
            (ema20,  "EMA 20",  "#4fc3f7", "solid"),
            (ema50,  "EMA 50",  "#f0b429", "solid"),
            (ema200, "EMA 200", "#ce93d8", "dot"),
            (bb_up,  "BB Up",   "#8b9ab0", "dash"),
            (bb_lo,  "BB Low",  "#8b9ab0", "dash"),
        ]:
            fig.add_trace(go.Scatter(
                x=df.index, y=y, name=name,
                line=dict(color=color, width=1.2, dash=dash), opacity=0.8
            ), row=1, col=1)
        c_vol = ["#26a69a" if float(c) >= float(o) else "#ef5350"
                 for c, o in zip(df["Close"].squeeze(), df["Open"].squeeze())]
        fig.add_trace(go.Bar(x=df.index, y=vol, marker_color=c_vol,
                             opacity=0.5, name="Volume"), row=2, col=1)
        L = base_layout(h=500)
        fig.update_layout(
            height=500, paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
            font=dict(family="Inter", color="#8b9ab0"),
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis_rangeslider_visible=False,
            legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h"),
            xaxis=dict(gridcolor="#1e2228"),
            yaxis=dict(gridcolor="#1e2228"),
            xaxis2=dict(gridcolor="#1e2228"),
            yaxis2=dict(gridcolor="#1e2228")
        )
        st.plotly_chart(fig, use_container_width=True)

    with t2:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=df.index, y=rsi_s,
                                  line=dict(color="#4fc3f7", width=2), name="RSI"))
        fig2.add_hline(y=70, line_dash="dash", line_color="#ef5350", line_width=1, opacity=0.7)
        fig2.add_hline(y=30, line_dash="dash", line_color="#26a69a", line_width=1, opacity=0.7)
        fig2.add_hrect(y0=30, y1=70, fillcolor="rgba(79,195,247,0.03)", line_width=0)
        fig2.update_layout(
            height=300, paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
            font=dict(family="Inter", color="#8b9ab0"),
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(gridcolor="#1e2228"),
            yaxis=dict(gridcolor="#1e2228", range=[0, 100])
        )
        st.plotly_chart(fig2, use_container_width=True)

    with t3:
        histo_colors = ["#26a69a" if v >= 0 else "#ef5350" for v in his.fillna(0)]
        fig3 = make_subplots(rows=2, cols=1, shared_xaxes=True,
                             row_heights=[0.6, 0.4], vertical_spacing=0.05)
        fig3.add_trace(go.Scatter(x=df.index, y=macd_l,
                                  line=dict(color="#4fc3f7", width=2), name="MACD"), row=1, col=1)
        fig3.add_trace(go.Scatter(x=df.index, y=sig_l,
                                  line=dict(color="#f0b429", width=1.5), name="Signal"), row=1, col=1)
        fig3.add_trace(go.Bar(x=df.index, y=his, marker_color=histo_colors,
                              name="Histo", opacity=0.8), row=2, col=1)
        fig3.update_layout(
            height=350, paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
            font=dict(family="Inter", color="#8b9ab0"),
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(gridcolor="#1e2228"),  yaxis=dict(gridcolor="#1e2228"),
            xaxis2=dict(gridcolor="#1e2228"), yaxis2=dict(gridcolor="#1e2228")
        )
        st.plotly_chart(fig3, use_container_width=True)

    with t4:
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(x=df.index, y=stk,
                                  line=dict(color="#4fc3f7", width=2), name="%K"))
        fig4.add_trace(go.Scatter(x=df.index, y=std_,
                                  line=dict(color="#f0b429", width=1.5), name="%D"))
        fig4.add_hline(y=80, line_dash="dash", line_color="#ef5350", line_width=1, opacity=0.7)
        fig4.add_hline(y=20, line_dash="dash", line_color="#26a69a", line_width=1, opacity=0.7)
        fig4.update_layout(
            height=300, paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
            font=dict(family="Inter", color="#8b9ab0"),
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(gridcolor="#1e2228"),
            yaxis=dict(gridcolor="#1e2228", range=[0, 100])
        )
        st.plotly_chart(fig4, use_container_width=True)

else:
    st.info("👆 Entre un ticker et clique sur **ANALYSER**")
