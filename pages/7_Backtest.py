import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf

st.set_page_config(page_title="Backtest — AlphaDesk", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    section[data-testid="stSidebar"] { background-color: #13161d; border-right: 1px solid #2a2d35; }
    h1, h2, h3 { color: #ffffff !important; font-weight: 600 !important; }
    .stSelectbox label, .stTextInput label, .stSlider label, .stNumberInput label {
        color: #8b9ab0 !important; font-size: 0.8rem !important; text-transform: uppercase;
    }
    .stMetric { background-color: #1c1f26; padding: 14px; border-radius: 8px; border: 1px solid #2a2d35; }
    .stMetric label { color: #8b9ab0 !important; font-size: 0.75rem !important; text-transform: uppercase; }
    </style>
""", unsafe_allow_html=True)

st.markdown("## Backtest")
st.markdown("<p style='color:#8b9ab0; font-size:0.85rem; margin-top:-10px;'>Teste tes stratégies sur données historiques — SMA · RSI · MACD · Bollinger</p>", unsafe_allow_html=True)
st.divider()

# ── Sidebar config ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    ticker   = st.text_input("TICKER", value="AAPL")
    period   = st.selectbox("PÉRIODE", ["1y","2y","3y","5y","10y"], index=2)
    capital  = st.number_input("CAPITAL INITIAL (€)", value=10000, step=500)
    fees     = st.number_input("FRAIS PAR TRADE (%)", value=0.1, step=0.05) / 100
    strategy = st.selectbox("STRATÉGIE", [
        "SMA Crossover",
        "RSI Mean Reversion",
        "MACD Signal",
        "Bollinger Breakout",
    ])
    st.divider()

    # Paramètres selon stratégie
    if strategy == "SMA Crossover":
        sma_fast = st.slider("SMA Rapide", 5,  50,  20)
        sma_slow = st.slider("SMA Lente",  20, 200, 50)

    elif strategy == "RSI Mean Reversion":
        rsi_period   = st.slider("Période RSI",  5, 30, 14)
        rsi_oversold = st.slider("Seuil Survente (BUY)",  10, 40, 30)
        rsi_overbought = st.slider("Seuil Surachat (SELL)", 60, 90, 70)

    elif strategy == "MACD Signal":
        macd_fast   = st.slider("MACD Fast",   5,  20, 12)
        macd_slow   = st.slider("MACD Slow",  15,  50, 26)
        macd_signal = st.slider("MACD Signal", 5,  20,  9)

    elif strategy == "Bollinger Breakout":
        bb_period = st.slider("Période BB",  10, 50, 20)
        bb_std    = st.slider("Écart-type",   1,  3,  2)

    run = st.button("▶ LANCER LE BACKTEST", use_container_width=True, type="primary")

# ── Indicateurs ───────────────────────────────────────────────────────
def compute_rsi(s, n=14):
    d = s.diff()
    g = d.clip(lower=0).rolling(n).mean()
    l = -d.clip(upper=0).rolling(n).mean()
    return 100 - (100 / (1 + g / l.replace(0, np.nan)))

def compute_macd(s, f=12, sl=26, sig=9):
    m  = s.ewm(span=f,  adjust=False).mean() - s.ewm(span=sl, adjust=False).mean()
    sg = m.ewm(span=sig, adjust=False).mean()
    return m, sg

def compute_bb(s, n=20, k=2):
    sma = s.rolling(n).mean()
    std = s.rolling(n).std()
    return sma + k*std, sma - k*std

def base_layout(h=350):
    return dict(
        height=h, paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
        font=dict(family="Inter", color="#8b9ab0"),
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(gridcolor="#1e2228"),
        yaxis=dict(gridcolor="#1e2228"),
        legend=dict(bgcolor="rgba(0,0,0,0)")
    )

# ── Backtest engine ───────────────────────────────────────────────────
def run_backtest(df, signals, capital, fees):
    close    = df["Close"].squeeze()
    position = 0
    cash     = capital
    equity   = []
    trades   = []

    for i in range(len(signals)):
        price = float(close.iloc[i])
        sig   = signals.iloc[i]

        if sig == 1 and position == 0:        # BUY
            shares   = (cash * (1 - fees)) / price
            position = shares
            cash     = 0
            trades.append({"Date": close.index[i], "Type": "BUY", "Prix": price, "Shares": shares})

        elif sig == -1 and position > 0:       # SELL
            cash     = position * price * (1 - fees)
            trades.append({"Date": close.index[i], "Type": "SELL", "Prix": price,
                           "Valeur": cash, "P&L": cash - capital})
            position = 0

        val = cash + position * price
        equity.append(val)

    # Ferme position ouverte
    if position > 0:
        cash = position * float(close.iloc[-1]) * (1 - fees)
        equity[-1] = cash

    equity_series = pd.Series(equity, index=close.index)
    return equity_series, pd.DataFrame(trades)

# ── Main ──────────────────────────────────────────────────────────────
if run:
    @st.cache_data(ttl=3600, show_spinner=False)
    def load(t, p):
        df = yf.download(t, period=p, auto_adjust=True, progress=False, timeout=15)
        if not df.empty:
            df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        return df

    with st.spinner(f"Chargement {ticker.upper()}..."):
        df = load(ticker.upper(), period)

    if df is None or df.empty or len(df) < 50:
        st.error("Données insuffisantes pour ce ticker/période.")
        st.stop()

    close = df["Close"].squeeze()

    # ── Génération des signaux ────────────────────────────────────────
    signals = pd.Series(0, index=close.index)

    if strategy == "SMA Crossover":
        fast = close.rolling(sma_fast).mean()
        slow = close.rolling(sma_slow).mean()
        signals[fast > slow] =  1
        signals[fast < slow] = -1
        signals = signals.diff().fillna(0)
        signals[signals >  0] =  1
        signals[signals < -0] = -1

    elif strategy == "RSI Mean Reversion":
        rsi = compute_rsi(close, rsi_period)
        signals[rsi < rsi_oversold]   =  1
        signals[rsi > rsi_overbought] = -1

    elif strategy == "MACD Signal":
        macd_line, sig_line = compute_macd(close, macd_fast, macd_slow, macd_signal)
        cross = (macd_line > sig_line).astype(int).diff()
        signals[cross ==  1] =  1
        signals[cross == -1] = -1

    elif strategy == "Bollinger Breakout":
        bb_up, bb_lo = compute_bb(close, bb_period, bb_std)
        signals[close < bb_lo] =  1
        signals[close > bb_up] = -1

    # ── Run ────────────────────────────────────────────────────────────
    with st.spinner("Calcul du backtest..."):
        equity, trades_df = run_backtest(df, signals, capital, fees)

    # Buy & Hold
    bh = (close / float(close.iloc[0])) * capital

    # ── Métriques ──────────────────────────────────────────────────────
    final_val   = float(equity.iloc[-1])
    total_ret   = (final_val / capital - 1) * 100
    bh_ret      = (float(bh.iloc[-1]) / capital - 1) * 100
    daily_ret   = equity.pct_change().dropna()
    annual_ret  = float(daily_ret.mean() * 252 * 100)
    annual_vol  = float(daily_ret.std() * np.sqrt(252) * 100)
    sharpe      = (daily_ret.mean() * 252) / (daily_ret.std() * np.sqrt(252)) if daily_ret.std() > 0 else 0
    drawdown    = (equity / equity.cummax() - 1)
    max_dd      = float(drawdown.min() * 100)
    n_trades    = len(trades_df[trades_df["Type"] == "BUY"]) if not trades_df.empty else 0

    wins = 0
    if not trades_df.empty and "P&L" in trades_df.columns:
        win_trades = trades_df[trades_df["P&L"] > 0]
        sell_trades = trades_df[trades_df["Type"] == "SELL"]
        wins = len(win_trades) / len(sell_trades) * 100 if len(sell_trades) > 0 else 0

    st.markdown(f"### {ticker.upper()} — {strategy}")
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("Rendement Total",   f"{total_ret:.2f}%",  f"vs B&H: {bh_ret:.2f}%")
    c2.metric("Rendement Annuel",  f"{annual_ret:.2f}%")
    c3.metric("Volatilité Ann.",   f"{annual_vol:.2f}%")
    c4.metric("Sharpe Ratio",      f"{sharpe:.2f}")
    c5.metric("Max Drawdown",      f"{max_dd:.2f}%")
    c6.metric("Nb Trades",         f"{n_trades}",        f"Win Rate: {wins:.0f}%")

    st.divider()

    tab1, tab2, tab3 = st.tabs(["Performance", "Drawdown", "Trades"])

    # ── Tab 1 : Performance ────────────────────────────────────────────
    with tab1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=equity.index, y=equity,
                                 name=strategy, line=dict(color="#4fc3f7", width=2.5),
                                 fill="tozeroy", fillcolor="rgba(79,195,247,0.05)"))
        fig.add_trace(go.Scatter(x=bh.index, y=bh,
                                 name="Buy & Hold", line=dict(color="#f0b429", width=1.5, dash="dash")))

        # Signaux BUY/SELL
        if not trades_df.empty:
            buys  = trades_df[trades_df["Type"] == "BUY"]
            sells = trades_df[trades_df["Type"] == "SELL"]
            if not buys.empty:
                fig.add_trace(go.Scatter(
                    x=buys["Date"], y=[float(equity.loc[d]) if d in equity.index else None for d in buys["Date"]],
                    mode="markers", name="BUY",
                    marker=dict(color="#26a69a", size=10, symbol="triangle-up")
                ))
            if not sells.empty:
                fig.add_trace(go.Scatter(
                    x=sells["Date"], y=[float(equity.loc[d]) if d in equity.index else None for d in sells["Date"]],
                    mode="markers", name="SELL",
                    marker=dict(color="#ef5350", size=10, symbol="triangle-down")
                ))

        fig.update_layout(**{**base_layout(h=450),
                             "yaxis": dict(gridcolor="#1e2228", tickprefix="€")})
        st.plotly_chart(fig, use_container_width=True)

    # ── Tab 2 : Drawdown ───────────────────────────────────────────────
    with tab2:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=drawdown.index, y=drawdown * 100,
                                  name="Drawdown", line=dict(color="#ef5350", width=1.5),
                                  fill="tozeroy", fillcolor="rgba(239,83,80,0.1)"))
        L2 = base_layout(h=300)
        L2["yaxis"]["ticksuffix"] = "%"
        fig2.update_layout(**L2)
        st.plotly_chart(fig2, use_container_width=True)

    # ── Tab 3 : Trades ─────────────────────────────────────────────────
    with tab3:
        if trades_df.empty:
            st.info("Aucun trade généré avec cette stratégie sur cette période.")
        else:
            st.markdown(f"**{len(trades_df)} ordres exécutés**")
            st.dataframe(
                trades_df.round(2),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Prix":  st.column_config.NumberColumn("Prix",  format="%.2f €"),
                    "P&L":   st.column_config.NumberColumn("P&L",   format="%.2f €"),
                    "Valeur":st.column_config.NumberColumn("Valeur",format="%.2f €"),
                }
            )
            csv = trades_df.to_csv(index=False)
            st.download_button("⬇️ Exporter trades CSV", csv, "trades.csv", "text/csv")

else:
    st.info("👈 Configure la stratégie dans la sidebar et clique sur **LANCER LE BACKTEST**")
