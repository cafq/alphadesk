# pages/4_Signals.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import json
import os

# ───────────────────────────────────────
# CONFIG
# ───────────────────────────────────────
st.set_page_config(
    page_title="AlphaDesk · Signals",
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
    h1, h2, h3 { color: #ffffff !important; font-weight: 600 !important; }
    .stSelectbox label, .stTextInput label, .stSlider label {
        color: #8b9ab0 !important;
        font-size: 0.8rem !important;
        text-transform: uppercase;
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
    .stMetric {
        background-color: #1c1f26;
        padding: 14px;
        border-radius: 8px;
        border: 1px solid #2a2d35;
    }
    .stMetric label {
        color: #8b9ab0 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .caption { color: #555e6e !important; font-size: 0.75rem; }
    .section-label {
        color: #8b9ab0;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 12px;
    }
    .signal-card {
        background-color: #1c1f26;
        border-radius: 10px;
        padding: 18px 22px;
        border: 1px solid #2a2d35;
        text-align: center;
        margin-bottom: 12px;
    }
    .signal-buy  { border-left: 4px solid #26a69a !important; }
    .signal-sell { border-left: 4px solid #ef5350 !important; }
    .signal-hold { border-left: 4px solid #f0b429 !important; }
    .sig-label { font-size: 0.68rem; color: #8b9ab0; text-transform: uppercase; letter-spacing: 0.1em; }
    .sig-value { font-size: 1.4rem; font-weight: 700; margin: 4px 0; }
    .buy-color  { color: #26a69a; }
    .sell-color { color: #ef5350; }
    .hold-color { color: #f0b429; }
    .strategy-card {
        background: #1c1f26;
        border: 1px solid #2a2d35;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 8px;
        cursor: pointer;
        transition: border-color 0.2s;
    }
    .strategy-card:hover { border-color: #4F46E5; }
    .strategy-active { border-color: #4F46E5 !important; border-left: 4px solid #4F46E5 !important; }
    .strat-name { font-size: 0.95rem; font-weight: 700; color: #ffffff; }
    .strat-desc { font-size: 0.78rem; color: #8b9ab0; margin-top: 4px; }
    .strat-tag  {
        display: inline-block;
        font-size: 0.62rem; font-weight: 700;
        padding: 2px 8px; border-radius: 20px;
        text-transform: uppercase; letter-spacing: 0.08em;
        margin-right: 4px; margin-top: 6px;
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
        <span style='font-size:1.1rem; font-weight:500; color:#8b9ab0; margin-left:12px;'>/ Signaux</span>
    </div>
    <p style='color:#8b9ab0; font-size:0.88rem; margin-top:8px;'>
        Analyse technique · Stratégies prêtes à l'emploi · Constructeur personnalisé
    </p>
</div>
""", unsafe_allow_html=True)

st.divider()


# ───────────────────────────────────────
# INDICATEURS
# ───────────────────────────────────────
def compute_rsi(s, n=14):
    d = s.diff()
    g = d.clip(lower=0).rolling(n).mean()
    l = (-d.clip(upper=0)).rolling(n).mean()
    return 100 - (100 / (1 + g / l.replace(0, np.nan)))

def compute_macd(s, f=12, sl=26, sig=9):
    ef = s.ewm(span=f, adjust=False).mean()
    es = s.ewm(span=sl, adjust=False).mean()
    m  = ef - es
    sg = m.ewm(span=sig, adjust=False).mean()
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

def compute_stoch_rsi(s, rsi_n=14, stoch_n=14, k_s=3, d_s=3):
    rsi = compute_rsi(s, rsi_n)
    lo  = rsi.rolling(stoch_n).min()
    hi  = rsi.rolling(stoch_n).max()
    k   = 100 * (rsi - lo) / (hi - lo).replace(0, np.nan)
    ks  = k.rolling(k_s).mean()
    return ks, ks.rolling(d_s).mean()

def compute_atr(h, l, c, n=14):
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()

def compute_obv(c, v):
    return (np.sign(c.diff()).fillna(0) * v).cumsum()

def compute_ema(s, n):
    return s.ewm(span=n, adjust=False).mean()

def compute_williams_r(h, l, c, n=14):
    return -100 * (h.rolling(n).max() - c) / (h.rolling(n).max() - l.rolling(n).min()).replace(0, np.nan)

def safe_last(s):
    try:    return float(s.dropna().iloc[-1])
    except: return 0.0

def get_signal_val(val, low, high):
    if val <= low:  return "BUY",  "buy-color",  "signal-buy"
    if val >= high: return "SELL", "sell-color", "signal-sell"
    return "HOLD", "hold-color", "signal-hold"

def get_signal_cross(a, b):
    if a > b: return "BUY",  "buy-color",  "signal-buy"
    if a < b: return "SELL", "sell-color", "signal-sell"
    return "HOLD", "hold-color", "signal-hold"

def signal_card(col, label, value, sig, color, cls):
    with col:
        st.markdown(f"""
        <div class='signal-card {cls}'>
            <div class='sig-label'>{label}</div>
            <div class='sig-value {color}'>{value}</div>
            <div class='sig-label'>{sig}</div>
        </div>
        """, unsafe_allow_html=True)

def base_layout(h=300):
    return dict(
        height=h, paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
        font=dict(family="Inter", color="#8b9ab0"),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(gridcolor="#1e2228"), yaxis=dict(gridcolor="#1e2228"),
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h"),
        hovermode="x unified",
    )


# ───────────────────────────────────────
# STRATÉGIES PAR DÉFAUT
# ───────────────────────────────────────
DEFAULT_STRATEGIES = {
    "RSI Mean Reversion": {
        "desc": "Achète quand RSI < 30 (survente), vend quand RSI > 70 (surachat).",
        "tags": ["RSI", "Mean Reversion", "Contrarian"],
        "color": "#f0b429",
        "rules": {"rsi_low": 30, "rsi_high": 70},
        "type": "rsi",
    },
    "EMA Crossover": {
        "desc": "BUY quand EMA 20 croise EMA 50 à la hausse. SELL à la baisse.",
        "tags": ["EMA", "Trend Following", "Crossover"],
        "color": "#4fc3f7",
        "rules": {"ema_fast": 20, "ema_slow": 50},
        "type": "ema_cross",
    },
    "Bollinger Breakout": {
        "desc": "BUY quand le prix touche la bande basse. SELL quand il touche la bande haute.",
        "tags": ["Bollinger", "Breakout", "Volatilité"],
        "color": "#ce93d8",
        "rules": {"bb_period": 20, "bb_std": 2},
        "type": "bollinger",
    },
    "MACD Signal": {
        "desc": "BUY quand MACD croise la signal line à la hausse. SELL inversement.",
        "tags": ["MACD", "Momentum", "Trend"],
        "color": "#26a69a",
        "rules": {"macd_fast": 12, "macd_slow": 26, "macd_sig": 9},
        "type": "macd",
    },
    "Stochastique": {
        "desc": "BUY quand Stoch %K < 20, SELL quand > 80.",
        "tags": ["Stochastique", "Oscillateur", "Overbought"],
        "color": "#ff7043",
        "rules": {"stoch_low": 20, "stoch_high": 80, "stoch_n": 14},
        "type": "stoch",
    },
    "StochRSI Momentum": {
        "desc": "Combine RSI et Stochastique pour un signal de momentum précis.",
        "tags": ["StochRSI", "Momentum", "Avancé"],
        "color": "#ec4899",
        "rules": {"srsi_low": 20, "srsi_high": 80},
        "type": "stochrsi",
    },
    "ATR Volatility Filter": {
        "desc": "Filtre les signaux RSI quand la volatilité (ATR) est trop faible.",
        "tags": ["ATR", "Volatilité", "Filtre"],
        "color": "#8b5cf6",
        "rules": {"rsi_low": 35, "rsi_high": 65, "atr_period": 14},
        "type": "atr_filter",
    },
    "Triple EMA Trend": {
        "desc": "BUY quand EMA20 > EMA50 > EMA200 (tendance haussière forte).",
        "tags": ["EMA", "Trend", "Multi-période"],
        "color": "#22c55e",
        "rules": {"ema1": 20, "ema2": 50, "ema3": 200},
        "type": "triple_ema",
    },
}


# ───────────────────────────────────────
# PERSISTANCE STRATÉGIES CUSTOM
# ───────────────────────────────────────
CUSTOM_FILE = "data/custom_strategies.json"
os.makedirs("data", exist_ok=True)

def load_custom_strategies() -> dict:
    if os.path.exists(CUSTOM_FILE):
        try:
            with open(CUSTOM_FILE) as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_custom_strategies(strategies: dict):
    with open(CUSTOM_FILE, "w") as f:
        json.dump(strategies, f, indent=2)


# ───────────────────────────────────────
# APPLICATION D'UNE STRATÉGIE
# ───────────────────────────────────────
def apply_strategy(strat: dict, close, high, low) -> tuple[str, str, str]:
    """Retourne (signal, color, card_class) pour une stratégie donnée."""
    t = strat.get("type", "rsi")
    r = strat.get("rules", {})

    if t == "rsi":
        rsi = compute_rsi(close)
        return get_signal_val(safe_last(rsi), r.get("rsi_low", 30), r.get("rsi_high", 70))

    elif t == "ema_cross":
        e_fast = compute_ema(close, r.get("ema_fast", 20))
        e_slow = compute_ema(close, r.get("ema_slow", 50))
        return get_signal_cross(safe_last(e_fast), safe_last(e_slow))

    elif t == "bollinger":
        bb_up, _, bb_lo = compute_bb(close, r.get("bb_period", 20), r.get("bb_std", 2))
        lc = safe_last(close)
        if lc <= safe_last(bb_lo):  return "BUY",  "buy-color",  "signal-buy"
        if lc >= safe_last(bb_up):  return "SELL", "sell-color", "signal-sell"
        return "HOLD", "hold-color", "signal-hold"

    elif t == "macd":
        m, sg, _ = compute_macd(close, r.get("macd_fast", 12), r.get("macd_slow", 26), r.get("macd_sig", 9))
        return get_signal_cross(safe_last(m), safe_last(sg))

    elif t == "stoch":
        k, _ = compute_stoch(high, low, close, r.get("stoch_n", 14))
        return get_signal_val(safe_last(k), r.get("stoch_low", 20), r.get("stoch_high", 80))

    elif t == "stochrsi":
        ks, _ = compute_stoch_rsi(close)
        return get_signal_val(safe_last(ks), r.get("srsi_low", 20), r.get("srsi_high", 80))

    elif t == "atr_filter":
        rsi = compute_rsi(close)
        atr = compute_atr(high, low, close, r.get("atr_period", 14))
        atr_mean = float(atr.mean()) if not atr.empty else 0
        if safe_last(atr) < atr_mean * 0.7:
            return "HOLD", "hold-color", "signal-hold"
        return get_signal_val(safe_last(rsi), r.get("rsi_low", 35), r.get("rsi_high", 65))

    elif t == "triple_ema":
        e1 = safe_last(compute_ema(close, r.get("ema1", 20)))
        e2 = safe_last(compute_ema(close, r.get("ema2", 50)))
        e3 = safe_last(compute_ema(close, r.get("ema3", 200)))
        if e1 > e2 > e3: return "BUY",  "buy-color",  "signal-buy"
        if e1 < e2 < e3: return "SELL", "sell-color", "signal-sell"
        return "HOLD", "hold-color", "signal-hold"

    elif t == "custom":
        return apply_custom_strategy(strat, close, high, low)

    return "HOLD", "hold-color", "signal-hold"

def apply_custom_strategy(strat: dict, close, high, low) -> tuple[str, str, str]:
    """Applique une stratégie personnalisée avec conditions AND/OR."""
    conditions = strat.get("conditions", [])
    logic      = strat.get("logic", "AND")
    signals    = []

    for cond in conditions:
        ind = cond.get("indicator", "RSI")
        op  = cond.get("operator", "<")
        val = float(cond.get("value", 50))
        action = cond.get("action", "BUY")

        if ind == "RSI":
            cur = safe_last(compute_rsi(close))
        elif ind == "MACD":
            m, sg, _ = compute_macd(close)
            cur = safe_last(m) - safe_last(sg)
        elif ind == "Stochastique %K":
            k, _ = compute_stoch(high, low, close)
            cur = safe_last(k)
        elif ind == "StochRSI %K":
            ks, _ = compute_stoch_rsi(close)
            cur = safe_last(ks)
        elif ind == "ATR":
            cur = safe_last(compute_atr(high, low, close))
        elif ind == "Williams %R":
            cur = safe_last(compute_williams_r(high, low, close))
        elif ind == "EMA20 - EMA50":
            cur = safe_last(compute_ema(close, 20)) - safe_last(compute_ema(close, 50))
        else:
            continue

        triggered = (op == "<" and cur < val) or (op == ">" and cur > val) or \
                    (op == "<=" and cur <= val) or (op == ">=" and cur >= val)

        if triggered:
            signals.append(action)

    if not signals:
        return "HOLD", "hold-color", "signal-hold"

    if logic == "AND" and len(signals) == len(conditions):
        final = signals[0]
    elif logic == "OR" and signals:
        final = signals[0]
    else:
        return "HOLD", "hold-color", "signal-hold"

    if final == "BUY":  return "BUY",  "buy-color",  "signal-buy"
    if final == "SELL": return "SELL", "sell-color", "signal-sell"
    return "HOLD", "hold-color", "signal-hold"


# ───────────────────────────────────────
# CHARGEMENT DONNÉES
# ───────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_data(ticker, period, interval):
    try:
        df = yf.download(ticker, period=period, interval=interval,
                         auto_adjust=True, progress=False, timeout=20)
        if df.empty: return None
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        return df
    except:
        return None


# ───────────────────────────────────────
# INTERFACE PRINCIPALE
# ───────────────────────────────────────
c1, c2, c3, c4 = st.columns([2, 1.5, 1.5, 1])
with c1:
    ticker = st.text_input("TICKER", value="AAPL", placeholder="AAPL, BTC-USD...")
with c2:
    period = st.selectbox("PÉRIODE", ["3mo", "6mo", "1y", "2y"], index=2)
with c3:
    interval = st.selectbox("INTERVALLE", ["1d", "1wk"], index=0)
with c4:
    st.markdown("<br>", unsafe_allow_html=True)
    run = st.button("ANALYSER", use_container_width=True, type="primary")

st.divider()

# ───────────────────────────────────────
# ONGLETS
# ───────────────────────────────────────
tab_analysis, tab_strategies, tab_custom = st.tabs([
    "📊 Analyse technique",
    "🎯 Stratégies prêtes à l'emploi",
    "🛠️ Constructeur personnalisé",
])


# ══════════════════════════════════════════════
# TAB 1 — ANALYSE TECHNIQUE
# ══════════════════════════════════════════════
with tab_analysis:
    if run:
        if not ticker.strip():
            st.warning("Entre un ticker valide.")
            st.stop()

        with st.spinner(f"Chargement de {ticker.upper()}..."):
            df = load_data(ticker.upper(), period, interval)

        if df is None:
            st.error(f"Impossible de charger {ticker.upper()}. Vérifie le ticker.")
            st.stop()
        if len(df) < 30:
            st.error("Pas assez de données (minimum 30 bougies).")
            st.stop()

        close  = df["Close"].squeeze()
        high   = df["High"].squeeze()
        low    = df["Low"].squeeze()
        volume = df["Volume"].squeeze()

        # Calculs
        rsi              = compute_rsi(close)
        macd_l, sig_l, hist = compute_macd(close)
        bb_up, bb_mid, bb_lo = compute_bb(close)
        ema20            = compute_ema(close, 20)
        ema50            = compute_ema(close, 50)
        ema200           = compute_ema(close, 200)
        stk, std         = compute_stoch(high, low, close)
        srsi_k, srsi_d   = compute_stoch_rsi(close)
        atr              = compute_atr(high, low, close)
        obv              = compute_obv(close, volume)
        wr               = compute_williams_r(high, low, close)

        # Signaux
        sr  = get_signal_val(safe_last(rsi), 30, 70)
        sm  = get_signal_cross(safe_last(macd_l), safe_last(sig_l))
        sb  = ("BUY","buy-color","signal-buy") if safe_last(close) <= safe_last(bb_lo) \
              else ("SELL","sell-color","signal-sell") if safe_last(close) >= safe_last(bb_up) \
              else ("HOLD","hold-color","signal-hold")
        se  = get_signal_cross(safe_last(ema20), safe_last(ema50))
        ss  = get_signal_val(safe_last(stk), 20, 80)
        ssr = get_signal_val(safe_last(srsi_k), 20, 80)
        swr = get_signal_val(safe_last(wr), -80, -20)

        all_sigs = [sr, sm, sb, se, ss, ssr, swr]
        buys  = sum(1 for s in all_sigs if s[0] == "BUY")
        sells = sum(1 for s in all_sigs if s[0] == "SELL")
        score = buys - sells
        if   score >= 2:  glob = ("BUY",  "buy-color",  "signal-buy")
        elif score <= -2: glob = ("SELL", "sell-color", "signal-sell")
        else:             glob = ("HOLD", "hold-color", "signal-hold")

        # ── Score cards ──
        st.markdown(f"<p class='section-label'>{ticker.upper()} — Score Technique</p>", unsafe_allow_html=True)
        cols = st.columns(8)
        signal_card(cols[0], "RSI 14",       f"{safe_last(rsi):.1f}",    sr[0],  sr[1],  sr[2])
        signal_card(cols[1], "MACD",         f"{safe_last(macd_l):.3f}", sm[0],  sm[1],  sm[2])
        signal_card(cols[2], "Bollinger",    f"{safe_last(close):.2f}",  sb[0],  sb[1],  sb[2])
        signal_card(cols[3], "EMA 20/50",    f"{safe_last(ema20):.2f}",  se[0],  se[1],  se[2])
        signal_card(cols[4], "Stoch %K",     f"{safe_last(stk):.1f}",    ss[0],  ss[1],  ss[2])
        signal_card(cols[5], "StochRSI",     f"{safe_last(srsi_k):.1f}", ssr[0], ssr[1], ssr[2])
        signal_card(cols[6], "Williams %R",  f"{safe_last(wr):.1f}",     swr[0], swr[1], swr[2])
        signal_card(cols[7], "SCORE GLOBAL", f"{buys}↑ {sells}↓",        glob[0], glob[1], glob[2])

        st.divider()

        # ── Graphiques ──
        t1, t2, t3, t4, t5 = st.tabs(["Prix & EMA", "RSI", "MACD", "Stochastique", "OBV & ATR"])

        with t1:
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                row_heights=[0.75, 0.25], vertical_spacing=0.03)
            fig.add_trace(go.Candlestick(
                x=df.index, open=df["Open"].squeeze(), high=high, low=low, close=close,
                name="Prix", increasing_line_color="#26a69a", decreasing_line_color="#ef5350",
                increasing_fillcolor="#26a69a", decreasing_fillcolor="#ef5350",
            ), row=1, col=1)
            for y, name, color, dash in [
                (ema20, "EMA 20", "#f0b429", "solid"),
                (ema50, "EMA 50", "#4fc3f7", "solid"),
                (ema200, "EMA 200", "#ce93d8", "dot"),
                (bb_up, "BB Up", "#7b8fa1", "dash"),
                (bb_lo, "BB Low", "#7b8fa1", "dash"),
            ]:
                fig.add_trace(go.Scatter(
                    x=df.index, y=y, name=name,
                    line=dict(color=color, width=1.2, dash=dash), opacity=0.85
                ), row=1, col=1)
            c_vol = ["#26a69a" if float(c) >= float(o) else "#ef5350"
                     for c, o in zip(df["Close"].squeeze(), df["Open"].squeeze())]
            fig.add_trace(go.Bar(x=df.index, y=volume, marker_color=c_vol, opacity=0.5, name="Volume"), row=2, col=1)
            L = base_layout(500)
            L["xaxis_rangeslider_visible"] = False
            L["xaxis2"] = dict(gridcolor="#1e2228")
            L["yaxis2"] = dict(gridcolor="#1e2228")
            fig.update_layout(L)
            st.plotly_chart(fig, use_container_width=True)

        with t2:
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=df.index, y=rsi, line=dict(color="#f0b429", width=2), name="RSI"))
            fig2.add_hline(y=70, line_dash="dash", line_color="#ef5350", line_width=1, opacity=0.7)
            fig2.add_hline(y=30, line_dash="dash", line_color="#26a69a", line_width=1, opacity=0.7)
            fig2.add_hrect(y0=70, y1=100, fillcolor="rgba(239,83,80,0.04)",  line_width=0)
            fig2.add_hrect(y0=0,  y1=30,  fillcolor="rgba(38,166,154,0.04)", line_width=0)
            L2 = base_layout(300); L2["yaxis"]["range"] = [0, 100]
            fig2.update_layout(L2)
            st.plotly_chart(fig2, use_container_width=True)

        with t3:
            fig3 = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                  row_heights=[0.6, 0.4], vertical_spacing=0.05)
            fig3.add_trace(go.Scatter(x=df.index, y=macd_l, line=dict(color="#4fc3f7", width=2), name="MACD"), row=1, col=1)
            fig3.add_trace(go.Scatter(x=df.index, y=sig_l,  line=dict(color="#f0b429", width=1.5), name="Signal"), row=1, col=1)
            hcols = ["#26a69a" if v >= 0 else "#ef5350" for v in hist.fillna(0)]
            fig3.add_trace(go.Bar(x=df.index, y=hist, marker_color=hcols, opacity=0.8, name="Histo"), row=2, col=1)
            L3 = base_layout(350)
            L3["xaxis2"] = dict(gridcolor="#1e2228")
            L3["yaxis2"] = dict(gridcolor="#1e2228")
            fig3.update_layout(L3)
            st.plotly_chart(fig3, use_container_width=True)

        with t4:
            fig4 = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                  row_heights=[0.5, 0.5], vertical_spacing=0.05)
            fig4.add_trace(go.Scatter(x=df.index, y=stk, line=dict(color="#4fc3f7", width=2), name="Stoch %K"), row=1, col=1)
            fig4.add_trace(go.Scatter(x=df.index, y=std, line=dict(color="#f0b429", width=1.5), name="Stoch %D"), row=1, col=1)
            fig4.add_hline(y=80, line_dash="dash", line_color="#ef5350", line_width=1, opacity=0.7, row=1, col=1)
            fig4.add_hline(y=20, line_dash="dash", line_color="#26a69a", line_width=1, opacity=0.7, row=1, col=1)
            fig4.add_trace(go.Scatter(x=df.index, y=srsi_k, line=dict(color="#ce93d8", width=2), name="StochRSI %K"), row=2, col=1)
            fig4.add_trace(go.Scatter(x=df.index, y=srsi_d, line=dict(color="#ff7043", width=1.5), name="StochRSI %D"), row=2, col=1)
            fig4.add_hline(y=80, line_dash="dash", line_color="#ef5350", line_width=1, opacity=0.5, row=2, col=1)
            fig4.add_hline(y=20, line_dash="dash", line_color="#26a69a", line_width=1, opacity=0.5, row=2, col=1)
            L4 = base_layout(380)
            L4["xaxis2"] = dict(gridcolor="#1e2228")
            L4["yaxis2"] = dict(gridcolor="#1e2228", range=[0, 100])
            L4["yaxis"]["range"] = [0, 100]
            fig4.update_layout(L4)
            st.plotly_chart(fig4, use_container_width=True)

        with t5:
            fig5 = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                  row_heights=[0.5, 0.5], vertical_spacing=0.05)
            fig5.add_trace(go.Scatter(
                x=df.index, y=obv, name="OBV",
                line=dict(color="#26a69a", width=2),
                fill="tozeroy", fillcolor="rgba(38,166,154,0.05)"
            ), row=1, col=1)
            fig5.add_trace(go.Scatter(
                x=df.index, y=atr, name="ATR 14",
                line=dict(color="#f0b429", width=2),
                fill="tozeroy", fillcolor="rgba(240,180,41,0.05)"
            ), row=2, col=1)
            L5 = base_layout(380)
            L5["xaxis2"] = dict(gridcolor="#1e2228")
            L5["yaxis2"] = dict(gridcolor="#1e2228")
            fig5.update_layout(L5)
            st.plotly_chart(fig5, use_container_width=True)

    else:
        st.info("Entre un ticker et clique sur **ANALYSER**.")


# ══════════════════════════════════════════════
# TAB 2 — STRATÉGIES PRÊTES À L'EMPLOI
# ══════════════════════════════════════════════
with tab_strategies:
    st.markdown("<p class='section-label'>Choisir une stratégie</p>", unsafe_allow_html=True)

    all_strats = {**DEFAULT_STRATEGIES, **load_custom_strategies()}

    selected_strat = st.selectbox(
        "Stratégie",
        list(all_strats.keys()),
        label_visibility="collapsed",
    )

    strat = all_strats[selected_strat]
    strat_color = strat.get("color", "#4F46E5")
    tags_html = "".join([
        f"<span class='strat-tag' style='background:{strat_color}22; color:{strat_color}; border:1px solid {strat_color}44;'>{t}</span>"
        for t in strat.get("tags", [])
    ])

    st.markdown(f"""
    <div class='strategy-card strategy-active'>
        <div class='strat-name' style='color:{strat_color};'>{selected_strat}</div>
        <div class='strat-desc'>{strat.get("desc","")}</div>
        <div style='margin-top:8px;'>{tags_html}</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Tickers à analyser
    st.markdown("<p class='section-label'>Appliquer sur</p>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([3, 1, 1])
    with c1:
        strat_tickers = st.text_input(
            "Tickers",
            value="AAPL, MSFT, GOOGL, TSLA, BTC-USD",
            placeholder="Ex: AAPL, MSFT, BTC-USD...",
            label_visibility="collapsed",
        )
    with c2:
        strat_period = st.selectbox("Période", ["3mo", "6mo", "1y"], index=1, label_visibility="collapsed")
    with c3:
        run_strat = st.button("LANCER", use_container_width=True, type="primary")

    if run_strat:
        tickers_list = [t.strip().upper() for t in strat_tickers.split(",") if t.strip()]
        results = []

        progress = st.progress(0, text="Analyse en cours...")
        for i, t in enumerate(tickers_list):
            df_t = load_data(t, strat_period, "1d")
            if df_t is not None and len(df_t) >= 30:
                c_s = df_t["Close"].squeeze()
                h_s = df_t["High"].squeeze()
                l_s = df_t["Low"].squeeze()
                sig, color, _ = apply_strategy(strat, c_s, h_s, l_s)
                price = safe_last(c_s)
                rsi_v = safe_last(compute_rsi(c_s))
                results.append({"Ticker": t, "Signal": sig, "Prix": f"{price:.2f}", "RSI": f"{rsi_v:.1f}"})
            progress.progress((i+1)/len(tickers_list), text=f"Analyse de {t}...")
        progress.empty()

        if results:
            st.markdown("<p class='section-label'>Résultats</p>", unsafe_allow_html=True)
            for r in results:
                sig_color = "#26a69a" if r["Signal"] == "BUY" else "#ef5350" if r["Signal"] == "SELL" else "#f0b429"
                sig_icon  = "🟢" if r["Signal"] == "BUY" else "🔴" if r["Signal"] == "SELL" else "🟡"
                st.markdown(f"""
                <div style='display:flex; justify-content:space-between; align-items:center;
                            background:#1c1f26; border:1px solid #2a2d35; border-left:4px solid {sig_color};
                            border-radius:8px; padding:12px 18px; margin-bottom:6px;'>
                    <div style='font-size:1rem; font-weight:700; color:#ffffff;'>{r["Ticker"]}</div>
                    <div style='display:flex; gap:24px; align-items:center;'>
                        <div style='text-align:center;'>
                            <div style='font-size:0.65rem; color:#8b9ab0; text-transform:uppercase;'>Prix</div>
                            <div style='color:#e0e0e0; font-weight:600;'>{r["Prix"]}</div>
                        </div>
                        <div style='text-align:center;'>
                            <div style='font-size:0.65rem; color:#8b9ab0; text-transform:uppercase;'>RSI</div>
                            <div style='color:#e0e0e0; font-weight:600;'>{r["RSI"]}</div>
                        </div>
                        <div style='font-size:1rem; font-weight:800; color:{sig_color};'>
                            {sig_icon} {r["Signal"]}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)


# ══════════════════════════════════════════════
# TAB 3 — CONSTRUCTEUR PERSONNALISÉ
# ══════════════════════════════════════════════
with tab_custom:
    st.markdown("<p class='section-label'>Créer ta stratégie</p>", unsafe_allow_html=True)

    custom_strategies = load_custom_strategies()

    with st.form("create_strategy"):
        f1, f2 = st.columns([3, 1])
        with f1:
            strat_name = st.text_input("NOM DE LA STRATÉGIE", placeholder="Ex: My RSI + MACD Strategy")
        with f2:
            strat_logic = st.selectbox("LOGIQUE", ["AND", "OR"])

        strat_desc_input = st.text_input("DESCRIPTION", placeholder="Ex: Achète quand RSI < 30 ET MACD haussier")

        st.markdown("<p class='section-label'>Conditions</p>", unsafe_allow_html=True)

        n_conditions = st.number_input("Nombre de conditions", min_value=1, max_value=5, value=2)

        INDICATORS = ["RSI", "MACD", "Stochastique %K", "StochRSI %K",
                      "ATR", "Williams %R", "EMA20 - EMA50"]
        OPERATORS  = ["<", ">", "<=", ">="]
        ACTIONS    = ["BUY", "SELL", "HOLD"]

        conditions = []
        for i in range(int(n_conditions)):
            cc1, cc2, cc3, cc4 = st.columns([2, 1, 1, 1])
            with cc1: ind    = st.selectbox(f"Indicateur {i+1}", INDICATORS, key=f"ind_{i}")
            with cc2: op     = st.selectbox(f"Opérateur {i+1}", OPERATORS,  key=f"op_{i}")
            with cc3: val    = st.number_input(f"Valeur {i+1}", value=30.0, key=f"val_{i}")
            with cc4: action = st.selectbox(f"→ Signal {i+1}", ACTIONS, key=f"act_{i}")
            conditions.append({"indicator": ind, "operator": op, "value": val, "action": action})

        submitted = st.form_submit_button("💾 Sauvegarder la stratégie", use_container_width=True)

        if submitted:
            if strat_name.strip():
                custom_strategies[strat_name] = {
                    "desc":       strat_desc_input or "Stratégie personnalisée",
                    "tags":       ["Custom", strat_logic],
                    "color":      "#4F46E5",
                    "type":       "custom",
                    "logic":      strat_logic,
                    "conditions": conditions,
                }
                save_custom_strategies(custom_strategies)
                st.success(f"✅ Stratégie **{strat_name}** sauvegardée ! Disponible dans l'onglet Stratégies.")
                st.rerun()
            else:
                st.error("⚠️ Donne un nom à ta stratégie.")

    # Stratégies custom existantes
    if custom_strategies:
        st.divider()
        st.markdown("<p class='section-label'>Mes stratégies</p>", unsafe_allow_html=True)
        for name, s in custom_strategies.items():
            col_name, col_del = st.columns([5, 1])
            with col_name:
                tags_h = "".join([
                    f"<span class='strat-tag' style='background:#4F46E522; color:#4F46E5; border:1px solid #4F46E544;'>{t}</span>"
                    for t in s.get("tags", [])
                ])
                st.markdown(f"""
                <div class='strategy-card'>
                    <div class='strat-name'>{name}</div>
                    <div class='strat-desc'>{s.get("desc","")}</div>
                    <div>{tags_h}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_del:
                st.markdown("<br><br>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_{name}"):
                    del custom_strategies[name]
                    save_custom_strategies(custom_strategies)
                    st.rerun()


st.divider()
st.markdown(
    "<p class='caption' style='text-align:center;'>AlphaDesk v1.0 &nbsp;·&nbsp; Signals · Yahoo Finance</p>",
    unsafe_allow_html=True,
)
