import os
import sys
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)
from utils.ai_assistant import render_chat_widget, build_context

render_chat_widget("backtest")

# pages/7_Backtest.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf

# ───────────────────────────────────────
# CONFIG
# ───────────────────────────────────────
st.set_page_config(
    page_title="AlphaDesk · Backtest",
    page_icon="▲",
    layout="wide",
    initial_sidebar_state="expanded",
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
    .stSelectbox label, .stTextInput label, .stSlider label, .stNumberInput label {
        color: #8b9ab0 !important;
        font-size: 0.8rem !important;
        text-transform: uppercase;
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
    .trade-win  { color: #26a69a; font-weight: 600; }
    .trade-loss { color: #ef5350; font-weight: 600; }

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
# HEADER
# ───────────────────────────────────────
st.markdown("""
<div style='padding: 30px 0 10px 0; text-align: center;'>
    <div style='font-size:2.2rem; font-weight:800; color:#ffffff; letter-spacing:-0.04em;'>
        Alpha<span style='color:#4F46E5;'>Desk</span>
        <span style='font-size:1.1rem; font-weight:500; color:#8b9ab0; margin-left:12px;'>/ Backtest</span>
    </div>
    <p style='color:#8b9ab0; font-size:0.88rem; margin-top:8px;'>
        Teste tes stratégies · SL/TP · Comparaison multi-stratégies · Monte Carlo
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
    m  = s.ewm(span=f, adjust=False).mean() - s.ewm(span=sl, adjust=False).mean()
    sg = m.ewm(span=sig, adjust=False).mean()
    return m, sg

def compute_bb(s, n=20, k=2):
    sma = s.rolling(n).mean()
    std = s.rolling(n).std()
    return sma + k * std, sma - k * std

def compute_stoch(h, l, c, n=14):
    lo = l.rolling(n).min()
    hi = h.rolling(n).max()
    return 100 * (c - lo) / (hi - lo).replace(0, np.nan)

def base_layout(h=350):
    return dict(
        height=h, paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
        font=dict(family="Inter", color="#8b9ab0"),
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(gridcolor="#1e2228"),
        yaxis=dict(gridcolor="#1e2228"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        hovermode="x unified",
    )


# ───────────────────────────────────────
# SIDEBAR
# ───────────────────────────────────────
with st.sidebar:
    st.markdown("<p class='section-label'>Configuration</p>", unsafe_allow_html=True)
    ticker   = st.text_input("TICKER", value="AAPL")
    period   = st.selectbox("PÉRIODE", ["1y","2y","3y","5y","10y"], index=2)
    capital  = st.number_input("CAPITAL INITIAL (€)", value=10000, step=500)
    fees     = st.number_input("FRAIS PAR TRADE (%)", value=0.1, step=0.05) / 100
    strategy = st.selectbox("STRATÉGIE", [
        "SMA Crossover",
        "RSI Mean Reversion",
        "MACD Signal",
        "Bollinger Breakout",
        "Stochastique",
    ])

    st.divider()
    st.markdown("<p class='section-label'>Risk Management</p>", unsafe_allow_html=True)
    use_sl = st.checkbox("Stop Loss", value=False)
    sl_pct = st.slider("Stop Loss (%)", 1, 30, 5) / 100 if use_sl else None
    use_tp = st.checkbox("Take Profit", value=False)
    tp_pct = st.slider("Take Profit (%)", 1, 50, 10) / 100 if use_tp else None

    st.divider()
    st.markdown("<p class='section-label'>Paramètres stratégie</p>", unsafe_allow_html=True)

    if strategy == "SMA Crossover":
        sma_fast = st.slider("SMA Rapide", 5, 50, 20)
        sma_slow = st.slider("SMA Lente", 20, 200, 50)
    elif strategy == "RSI Mean Reversion":
        rsi_period     = st.slider("Période RSI", 5, 30, 14)
        rsi_oversold   = st.slider("Seuil Survente (BUY)", 10, 45, 30)
        rsi_overbought = st.slider("Seuil Surachat (SELL)", 55, 90, 70)
    elif strategy == "MACD Signal":
        macd_fast   = st.slider("MACD Fast", 5, 20, 12)
        macd_slow   = st.slider("MACD Slow", 15, 50, 26)
        macd_signal = st.slider("MACD Signal", 5, 20, 9)
    elif strategy == "Bollinger Breakout":
        bb_period = st.slider("Période BB", 10, 50, 20)
        bb_std    = st.slider("Écart-type BB", 1, 3, 2)
    elif strategy == "Stochastique":
        stoch_period    = st.slider("Période Stoch", 5, 30, 14)
        stoch_oversold  = st.slider("Seuil BUY", 10, 40, 20)
        stoch_overbought= st.slider("Seuil SELL", 60, 90, 80)

    st.divider()
    run      = st.button("🚀 LANCER LE BACKTEST", use_container_width=True, type="primary")
    run_comp = st.button("📊 COMPARER TOUTES LES STRATÉGIES", use_container_width=True)


# ───────────────────────────────────────
# CHARGEMENT DONNÉES
# ───────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def load_data(t, p):
    df = yf.download(t, period=p, auto_adjust=True, progress=False, timeout=15)
    if not df.empty:
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    return df


# ───────────────────────────────────────
# GÉNÉRATION DES SIGNAUX
# ───────────────────────────────────────
def generate_signals(df, strategy, **params) -> pd.Series:
    close = df["Close"].squeeze()
    high  = df["High"].squeeze()  if "High"  in df else close
    low   = df["Low"].squeeze()   if "Low"   in df else close
    signals = pd.Series(0, index=close.index)

    if strategy == "SMA Crossover":
        fast = close.rolling(params["sma_fast"]).mean()
        slow = close.rolling(params["sma_slow"]).mean()
        cross = (fast > slow).astype(int).diff()
        signals[cross > 0]  =  1
        signals[cross < 0]  = -1

    elif strategy == "RSI Mean Reversion":
        rsi = compute_rsi(close, params["rsi_period"])
        signals[rsi < params["rsi_oversold"]]   =  1
        signals[rsi > params["rsi_overbought"]] = -1

    elif strategy == "MACD Signal":
        m, sg = compute_macd(close, params["macd_fast"], params["macd_slow"], params["macd_signal"])
        cross = (m > sg).astype(int).diff()
        signals[cross > 0]  =  1
        signals[cross < 0]  = -1

    elif strategy == "Bollinger Breakout":
        bb_up, bb_lo = compute_bb(close, params["bb_period"], params["bb_std"])
        signals[close < bb_lo] =  1
        signals[close > bb_up] = -1

    elif strategy == "Stochastique":
        stk = compute_stoch(high, low, close, params["stoch_period"])
        signals[stk < params["stoch_oversold"]]   =  1
        signals[stk > params["stoch_overbought"]]  = -1

    return signals


# ───────────────────────────────────────
# MOTEUR DE BACKTEST
# ───────────────────────────────────────
def run_backtest(df, signals, capital, fees, sl_pct=None, tp_pct=None):
    close    = df["Close"].squeeze()
    position = 0
    cash     = float(capital)
    shares   = 0.0
    equity   = []
    trades   = []
    entry_price = 0.0

    for i in range(len(signals)):
        price = float(close.iloc[i])
        sig   = int(signals.iloc[i])

        # Stop Loss / Take Profit
        if position > 0 and entry_price > 0:
            if sl_pct and price <= entry_price * (1 - sl_pct):
                # Stop Loss déclenché
                cash = shares * price * (1 - fees)
                pnl  = cash - (shares * entry_price)
                trades.append({
                    "Date": close.index[i], "Type": "SL",
                    "Prix": round(price, 2), "Shares": round(shares, 4),
                    "Valeur": round(cash, 2), "P&L": round(pnl, 2),
                })
                position = 0; shares = 0.0; entry_price = 0.0

            elif tp_pct and price >= entry_price * (1 + tp_pct):
                # Take Profit déclenché
                cash = shares * price * (1 - fees)
                pnl  = cash - (shares * entry_price)
                trades.append({
                    "Date": close.index[i], "Type": "TP",
                    "Prix": round(price, 2), "Shares": round(shares, 4),
                    "Valeur": round(cash, 2), "P&L": round(pnl, 2),
                })
                position = 0; shares = 0.0; entry_price = 0.0

        # Signaux
        if sig == 1 and position == 0:
            shares      = cash * (1 - fees) / price
            cash        = 0.0
            position    = 1
            entry_price = price
            trades.append({
                "Date": close.index[i], "Type": "BUY",
                "Prix": round(price, 2), "Shares": round(shares, 4),
                "Valeur": round(shares * price, 2), "P&L": None,
            })

        elif sig == -1 and position > 0:
            cash = shares * price * (1 - fees)
            pnl  = cash - (shares * entry_price)
            trades.append({
                "Date": close.index[i], "Type": "SELL",
                "Prix": round(price, 2), "Shares": round(shares, 4),
                "Valeur": round(cash, 2), "P&L": round(pnl, 2),
            })
            position = 0; shares = 0.0; entry_price = 0.0

        val = cash + shares * price
        equity.append(val)

    # Fermeture position ouverte
    if position > 0:
        cash     = shares * float(close.iloc[-1]) * (1 - fees)
        equity[-1] = cash

    equity_s = pd.Series(equity, index=close.index)
    trades_df = pd.DataFrame(trades)
    return equity_s, trades_df


# ───────────────────────────────────────
# MÉTRIQUES
# ───────────────────────────────────────
def compute_metrics(equity: pd.Series, capital: float, trades_df: pd.DataFrame) -> dict:
    daily_ret  = equity.pct_change().dropna()
    final_val  = float(equity.iloc[-1])
    total_ret  = (final_val / capital - 1) * 100
    annual_ret = float(daily_ret.mean() * 252) * 100
    annual_vol = float(daily_ret.std() * np.sqrt(252)) * 100
    sharpe     = (daily_ret.mean() * 252) / (daily_ret.std() * np.sqrt(252)) if daily_ret.std() > 0 else 0
    sortino_d  = daily_ret[daily_ret < 0].std() * np.sqrt(252)
    sortino    = (daily_ret.mean() * 252) / sortino_d if sortino_d > 0 else 0
    drawdown   = equity / equity.cummax() - 1
    max_dd     = float(drawdown.min()) * 100
    calmar     = (annual_ret / 100) / abs(max_dd / 100) if max_dd != 0 else 0

    sells = trades_df[trades_df["Type"].isin(["SELL","SL","TP"])] if not trades_df.empty else pd.DataFrame()
    n_trades  = len(sells)
    win_rate  = 0.0
    avg_win   = 0.0
    avg_loss  = 0.0
    profit_factor = 0.0

    if not sells.empty and "P&L" in sells.columns:
        pnl_series = sells["P&L"].dropna()
        wins  = pnl_series[pnl_series > 0]
        losses= pnl_series[pnl_series < 0]
        win_rate = len(wins) / len(pnl_series) * 100 if len(pnl_series) > 0 else 0
        avg_win  = float(wins.mean())  if not wins.empty  else 0
        avg_loss = float(losses.mean()) if not losses.empty else 0
        total_wins  = wins.sum()
        total_losses= abs(losses.sum())
        profit_factor = total_wins / total_losses if total_losses > 0 else float("inf")

    return {
        "final_val": final_val, "total_ret": total_ret,
        "annual_ret": annual_ret, "annual_vol": annual_vol,
        "sharpe": sharpe, "sortino": sortino,
        "calmar": calmar, "max_dd": max_dd,
        "n_trades": n_trades, "win_rate": win_rate,
        "avg_win": avg_win, "avg_loss": avg_loss,
        "profit_factor": profit_factor,
        "drawdown": drawdown,
    }


# ═══════════════════════════════════════
# BACKTEST SIMPLE
# ═══════════════════════════════════════
if run:
    with st.spinner(f"Chargement de {ticker.upper()}..."):
        df = load_data(ticker.upper(), period)

    if df is None or df.empty or len(df) < 50:
        st.error("Données insuffisantes pour ce ticker/période.")
        st.stop()

    close = df["Close"].squeeze()

    # Paramètres selon stratégie
    params = {}
    if strategy == "SMA Crossover":
        params = {"sma_fast": sma_fast, "sma_slow": sma_slow}
    elif strategy == "RSI Mean Reversion":
        params = {"rsi_period": rsi_period, "rsi_oversold": rsi_oversold, "rsi_overbought": rsi_overbought}
    elif strategy == "MACD Signal":
        params = {"macd_fast": macd_fast, "macd_slow": macd_slow, "macd_signal": macd_signal}
    elif strategy == "Bollinger Breakout":
        params = {"bb_period": bb_period, "bb_std": bb_std}
    elif strategy == "Stochastique":
        params = {"stoch_period": stoch_period, "stoch_oversold": stoch_oversold, "stoch_overbought": stoch_overbought}

    with st.spinner("Calcul du backtest..."):
        signals = generate_signals(df, strategy, **params)
        equity, trades_df = run_backtest(df, signals, capital, fees, sl_pct, tp_pct)

    # Buy & Hold
    bh = close / float(close.iloc[0]) * capital

    m = compute_metrics(equity, capital, trades_df)
    bh_ret = float(bh.iloc[-1] / capital - 1) * 100

    # ── Métriques ──
    st.markdown(f"<p class='section-label'>{ticker.upper()} — {strategy}</p>", unsafe_allow_html=True)

    c1,c2,c3,c4,c5,c6,c7,c8 = st.columns(8)
    c1.metric("Rendement Total",  f"{m['total_ret']:.2f}%",   f"vs B&H {bh_ret:.2f}%")
    c2.metric("Rendement Annuel", f"{m['annual_ret']:.2f}%")
    c3.metric("Volatilité Ann.",  f"{m['annual_vol']:.2f}%")
    c4.metric("Sharpe",          f"{m['sharpe']:.2f}")
    c5.metric("Sortino",         f"{m['sortino']:.2f}")
    c6.metric("Max Drawdown",    f"{m['max_dd']:.2f}%")
    c7.metric("Win Rate",        f"{m['win_rate']:.1f}%",  f"{m['n_trades']} trades")
    c8.metric("Profit Factor",   f"{m['profit_factor']:.2f}" if m['profit_factor'] != float('inf') else "∞")

    st.divider()

    # ── Onglets résultats ──
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Performance", "📉 Drawdown & Risque", "🔄 Trades", "🎲 Monte Carlo"
    ])

    # ── Tab 1 : Performance ──
    with tab1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=equity.index, y=equity,
            name=strategy, line=dict(color="#4fc3f7", width=2.5),
            fill="tozeroy", fillcolor="rgba(79,195,247,0.05)",
        ))
        fig.add_trace(go.Scatter(
            x=bh.index, y=bh,
            name="Buy & Hold", line=dict(color="#f0b429", width=1.5, dash="dash"),
        ))

        # Marqueurs BUY / SELL / SL / TP
        if not trades_df.empty:
            for trade_type, color, symbol, size in [
                ("BUY",  "#26a69a", "triangle-up",   10),
                ("SELL", "#ef5350", "triangle-down",  10),
                ("SL",   "#ff7043", "x",               9),
                ("TP",   "#ce93d8", "star",             9),
            ]:
                t_sub = trades_df[trades_df["Type"] == trade_type]
                if not t_sub.empty:
                    y_vals = [float(equity.loc[d]) if d in equity.index else None for d in t_sub["Date"]]
                    fig.add_trace(go.Scatter(
                        x=t_sub["Date"], y=y_vals,
                        mode="markers", name=trade_type,
                        marker=dict(color=color, size=size, symbol=symbol),
                    ))

        L = base_layout(460)
        L["yaxis"]["tickprefix"] = "€"
        fig.update_layout(L)
        st.plotly_chart(fig, use_container_width=True)

        # Rendements mensuels
        st.markdown("<p class='section-label'>Rendements mensuels</p>", unsafe_allow_html=True)
        monthly = equity.resample("ME").last().pct_change().dropna() * 100
        colors_m = ["#26a69a" if v >= 0 else "#ef5350" for v in monthly]
        fig_m = go.Figure(go.Bar(
            x=monthly.index, y=monthly,
            marker_color=colors_m,
            text=[f"{v:.1f}%" for v in monthly], textposition="outside",
        ))
        L_m = base_layout(250)
        L_m["yaxis"]["ticksuffix"] = "%"
        fig_m.update_layout(L_m)
        st.plotly_chart(fig_m, use_container_width=True)

    # ── Tab 2 : Drawdown & Risque ──
    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("<p class='section-label'>Drawdown</p>", unsafe_allow_html=True)
            fig2 = go.Figure(go.Scatter(
                x=m["drawdown"].index, y=m["drawdown"] * 100,
                name="Drawdown", line=dict(color="#ef5350", width=1.5),
                fill="tozeroy", fillcolor="rgba(239,83,80,0.1)",
            ))
            L2 = base_layout(300)
            L2["yaxis"]["ticksuffix"] = "%"
            fig2.update_layout(L2)
            st.plotly_chart(fig2, use_container_width=True)

        with col2:
            st.markdown("<p class='section-label'>Distribution des P&L</p>", unsafe_allow_html=True)
            if not trades_df.empty and "P&L" in trades_df.columns:
                pnl_vals = trades_df["P&L"].dropna()
                if not pnl_vals.empty:
                    fig3 = go.Figure()
                    fig3.add_trace(go.Histogram(
                        x=pnl_vals, nbinsx=20,
                        marker_color=["#26a69a" if v >= 0 else "#ef5350" for v in pnl_vals],
                        opacity=0.8, name="P&L",
                    ))
                    fig3.add_vline(x=0, line_color="#ffffff", line_width=1, opacity=0.3)
                    L3 = base_layout(300)
                    L3["xaxis"]["tickprefix"] = "€"
                    fig3.update_layout(L3)
                    st.plotly_chart(fig3, use_container_width=True)
                else:
                    st.info("Pas de P&L à afficher.")
            else:
                st.info("Pas de trades fermés.")

        # Stats détaillées
        st.markdown("<p class='section-label'>Statistiques détaillées</p>", unsafe_allow_html=True)
        details = {
            "Calmar Ratio":    f"{m['calmar']:.2f}",
            "Gain moyen/trade":f"€{m['avg_win']:.2f}" if m['avg_win'] else "—",
            "Perte moy/trade": f"€{m['avg_loss']:.2f}" if m['avg_loss'] else "—",
            "Profit Factor":   f"{m['profit_factor']:.2f}" if m['profit_factor'] != float('inf') else "∞",
            "Capital final":   f"€{m['final_val']:,.2f}",
        }
        d_cols = st.columns(len(details))
        for col, (label, val) in zip(d_cols, details.items()):
            col.metric(label, val)

    # ── Tab 3 : Trades ──
    with tab3:
        if trades_df.empty:
            st.info("Aucun trade généré avec cette stratégie sur cette période.")
        else:
            n_buy  = len(trades_df[trades_df["Type"] == "BUY"])
            n_sell = len(trades_df[trades_df["Type"] == "SELL"])
            n_sl   = len(trades_df[trades_df["Type"] == "SL"])
            n_tp   = len(trades_df[trades_df["Type"] == "TP"])

            mc1, mc2, mc3, mc4 = st.columns(4)
            mc1.metric("BUY",  n_buy)
            mc2.metric("SELL", n_sell)
            mc3.metric("Stop Loss", n_sl)
            mc4.metric("Take Profit", n_tp)

            st.markdown(f"<p class='section-label'>{len(trades_df)} ordres exécutés</p>", unsafe_allow_html=True)
            st.dataframe(
                trades_df.round(2),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Prix":   st.column_config.NumberColumn("Prix",   format="%.2f"),
                    "Valeur": st.column_config.NumberColumn("Valeur", format="€%.2f"),
                    "P&L":    st.column_config.NumberColumn("P&L",    format="€%.2f"),
                },
                height=400,
            )

            csv = trades_df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Exporter trades CSV", csv, "trades.csv", "text/csv")

    # ── Tab 4 : Monte Carlo ──
    with tab4:
        st.markdown("<p class='section-label'>Simulation Monte Carlo — 500 trajectoires</p>", unsafe_allow_html=True)

        daily_ret = equity.pct_change().dropna()
        mu_d  = float(daily_ret.mean())
        sig_d = float(daily_ret.std())
        n_sim = 500
        n_days = len(equity)

        np.random.seed(42)
        sims = np.zeros((n_sim, n_days))
        for s in range(n_sim):
            r = np.random.normal(mu_d, sig_d, n_days)
            sims[s, 0] = capital
            for d in range(1, n_days):
                sims[s, d] = sims[s, d-1] * (1 + r[d])

        p5   = np.percentile(sims, 5,  axis=0)
        p25  = np.percentile(sims, 25, axis=0)
        p50  = np.percentile(sims, 50, axis=0)
        p75  = np.percentile(sims, 75, axis=0)
        p95  = np.percentile(sims, 95, axis=0)

        fig_mc = go.Figure()
        # Quelques trajectoires aléatoires (fond)
        for s in range(0, min(100, n_sim), 5):
            fig_mc.add_trace(go.Scatter(
                x=list(range(n_days)), y=sims[s],
                line=dict(color="rgba(79,195,247,0.05)", width=0.8),
                showlegend=False,
            ))
        # Percentiles
        fig_mc.add_trace(go.Scatter(
            x=list(range(n_days)), y=p95,
            name="P95", line=dict(color="#26a69a", width=1.5, dash="dash"),
        ))
        fig_mc.add_trace(go.Scatter(
            x=list(range(n_days)), y=p50,
            name="Médiane", line=dict(color="#4fc3f7", width=2.5),
        ))
        fig_mc.add_trace(go.Scatter(
            x=list(range(n_days)), y=p5,
            name="P5", line=dict(color="#ef5350", width=1.5, dash="dash"),
            fill="tonexty", fillcolor="rgba(239,83,80,0.05)",
        ))
        fig_mc.add_hline(y=capital, line_color="#f0b429", line_dash="dot", line_width=1,
                         annotation_text="Capital initial", annotation_font_color="#f0b429")

        L_mc = base_layout(420)
        L_mc["yaxis"]["tickprefix"] = "€"
        L_mc["xaxis"]["title"] = "Jours"
        fig_mc.update_layout(L_mc)
        st.plotly_chart(fig_mc, use_container_width=True)

        # Résultats finaux Monte Carlo
        finals = sims[:, -1]
        mc1, mc2, mc3, mc4, mc5 = st.columns(5)
        mc1.metric("Médiane finale",  f"€{np.median(finals):,.0f}")
        mc2.metric("P95 (best)",      f"€{np.percentile(finals,95):,.0f}")
        mc3.metric("P5 (worst)",      f"€{np.percentile(finals,5):,.0f}")
        mc4.metric("Prob. profit",    f"{(finals > capital).mean()*100:.1f}%")
        mc5.metric("Perte max sim.",  f"€{(finals.min() - capital):,.0f}")


# ═══════════════════════════════════════
# COMPARAISON MULTI-STRATÉGIES
# ═══════════════════════════════════════
elif run_comp:
    with st.spinner(f"Chargement de {ticker.upper()}..."):
        df = load_data(ticker.upper(), period)

    if df is None or df.empty or len(df) < 50:
        st.error("Données insuffisantes.")
        st.stop()

    close = df["Close"].squeeze()
    bh    = close / float(close.iloc[0]) * capital

    ALL_STRATEGIES = {
        "SMA Crossover":       {"sma_fast": 20, "sma_slow": 50},
        "RSI Mean Reversion":  {"rsi_period": 14, "rsi_oversold": 30, "rsi_overbought": 70},
        "MACD Signal":         {"macd_fast": 12, "macd_slow": 26, "macd_signal": 9},
        "Bollinger Breakout":  {"bb_period": 20, "bb_std": 2},
        "Stochastique":        {"stoch_period": 14, "stoch_oversold": 20, "stoch_overbought": 80},
    }

    COLORS = ["#4fc3f7", "#f0b429", "#26a69a", "#ce93d8", "#ff7043"]

    st.markdown(f"<p class='section-label'>{ticker.upper()} — Comparaison toutes stratégies (paramètres par défaut)</p>",
                unsafe_allow_html=True)

    fig_comp = go.Figure()
    fig_comp.add_trace(go.Scatter(
        x=bh.index, y=bh, name="Buy & Hold",
        line=dict(color="#ffffff", width=1.5, dash="dot"),
    ))

    rows = []
    for (strat_name, params), color in zip(ALL_STRATEGIES.items(), COLORS):
        sigs   = generate_signals(df, strat_name, **params)
        eq, tr = run_backtest(df, sigs, capital, fees)
        m      = compute_metrics(eq, capital, tr)

        fig_comp.add_trace(go.Scatter(
            x=eq.index, y=eq, name=strat_name,
            line=dict(color=color, width=2),
        ))
        rows.append({
            "Stratégie":     strat_name,
            "Rendement %":   f"{m['total_ret']:.2f}",
            "Annualisé %":   f"{m['annual_ret']:.2f}",
            "Sharpe":        f"{m['sharpe']:.2f}",
            "Max DD %":      f"{m['max_dd']:.2f}",
            "Win Rate %":    f"{m['win_rate']:.1f}",
            "Nb Trades":     m['n_trades'],
            "Capital final": f"€{m['final_val']:,.0f}",
        })

    L_comp = base_layout(460)
    L_comp["yaxis"]["tickprefix"] = "€"
    fig_comp.update_layout(L_comp)
    st.plotly_chart(fig_comp, use_container_width=True)

    st.markdown("<p class='section-label'>Tableau comparatif</p>", unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Meilleure stratégie
    best = max(rows, key=lambda r: float(r["Rendement %"]))
    st.success(f"🏆 Meilleure stratégie sur cette période : **{best['Stratégie']}** "
               f"({best['Rendement %']}% | Sharpe {best['Sharpe']})")

else:
    st.info("⚙️ Configure la stratégie dans la sidebar et clique sur **LANCER LE BACKTEST**.")


st.divider()
st.markdown(
    "<p class='caption' style='text-align:center;'>AlphaDesk v1.0 &nbsp;·&nbsp; Backtest · Yahoo Finance</p>",
    unsafe_allow_html=True,
)
