import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta

st.set_page_config(page_title="Portfolio — AlphaDesk", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    section[data-testid="stSidebar"] { background-color: #13161d; border-right: 1px solid #2a2d35; }
    h1, h2, h3 { color: #ffffff !important; font-weight: 600 !important; }
    .stMetric { background-color: #1c1f26; padding: 14px; border-radius: 8px; border: 1px solid #2a2d35; }
    .stMetric label { color: #8b9ab0 !important; font-size: 0.75rem !important; text-transform: uppercase; }
    .stTextArea label, .stSelectbox label { color: #8b9ab0 !important; font-size: 0.8rem !important; text-transform: uppercase; }
    .pos-row { color: #26a69a; font-weight: 600; }
    .neg-row { color: #ef5350; font-weight: 600; }
    </style>
""", unsafe_allow_html=True)

st.markdown("## Portfolio")
st.markdown("<p style='color:#8b9ab0; font-size:0.85rem; margin-top:-10px;'>Analyse & optimisation de portefeuille — Markowitz · Sharpe · VaR · Corrélations</p>", unsafe_allow_html=True)
st.divider()

# ── Sidebar input ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    tickers_input = st.text_area(
        "TICKERS (un par ligne)",
        value="AAPL\nMSFT\nGOOGL\nAMZN\nTSLA\nBTC-USD\nGLD",
        height=200
    )
    weights_input = st.text_area(
        "POIDS % (un par ligne, laisser vide = équipondéré)",
        value="",
        height=150,
        placeholder="Ex:\n20\n20\n15\n15\n10\n10\n10"
    )
    period = st.selectbox("PÉRIODE", ["6mo", "1y", "2y", "3y", "5y"], index=2)
    risk_free = st.number_input("TAUX SANS RISQUE (%)", value=4.5, step=0.1) / 100
    capital = st.number_input("CAPITAL (€)", value=10000, step=500)

tickers = [t.strip().upper() for t in tickers_input.strip().split("\n") if t.strip()]

# Poids
if weights_input.strip():
    try:
        w_raw = [float(x.strip()) for x in weights_input.strip().split("\n") if x.strip()]
        weights = np.array(w_raw) / sum(w_raw)
    except:
        weights = np.ones(len(tickers)) / len(tickers)
else:
    weights = np.ones(len(tickers)) / len(tickers)

if len(weights) != len(tickers):
    weights = np.ones(len(tickers)) / len(tickers)

# ── Chargement données ───────────────────────────────────────────────
@st.cache_data(ttl=900)
def load_prices(tickers, period):
    raw = yf.download(tickers, period=period, auto_adjust=True, progress=False)["Close"]
    if isinstance(raw, pd.Series):
        raw = raw.to_frame(name=tickers[0])
    return raw.dropna(how="all")

with st.spinner("Chargement des données..."):
    prices = load_prices(tickers, period)

available = [t for t in tickers if t in prices.columns]
if not available:
    st.error("Aucun ticker valide.")
    st.stop()

prices = prices[available]
weights = weights[:len(available)]
weights = weights / weights.sum()

returns = prices.pct_change().dropna()

# ── Métriques portefeuille ───────────────────────────────────────────
port_returns = returns @ weights
cum_returns  = (1 + port_returns).cumprod()

annual_ret   = float(port_returns.mean() * 252)
annual_vol   = float(port_returns.std() * np.sqrt(252))
sharpe       = (annual_ret - risk_free) / annual_vol if annual_vol > 0 else 0
max_dd       = float(((cum_returns / cum_returns.cummax()) - 1).min())
var_95       = float(np.percentile(port_returns, 5))
cvar_95      = float(port_returns[port_returns <= var_95].mean())
total_ret    = float(cum_returns.iloc[-1] - 1)

st.markdown("### Métriques du portefeuille")
m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
m1.metric("Rendement Total",  f"{total_ret*100:.2f}%")
m2.metric("Rendement Annuel", f"{annual_ret*100:.2f}%")
m3.metric("Volatilité Ann.",  f"{annual_vol*100:.2f}%")
m4.metric("Sharpe Ratio",     f"{sharpe:.2f}")
m5.metric("Max Drawdown",     f"{max_dd*100:.2f}%")
m6.metric("VaR 95%",          f"{var_95*100:.2f}%")
m7.metric("CVaR 95%",         f"{cvar_95*100:.2f}%")

st.divider()

# ── Tabs ─────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Performance", "Allocation", "Corrélations", "Risque", "Optimisation"])

# ── Tab 1 : Performance ──────────────────────────────────────────────
with tab1:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("#### Performance cumulée du portefeuille")
        fig = go.Figure()
        # Portefeuille global
        fig.add_trace(go.Scatter(
            x=cum_returns.index, y=(cum_returns - 1) * 100,
            name="Portefeuille", line=dict(color="#4fc3f7", width=2.5),
            fill='tozeroy', fillcolor='rgba(79,195,247,0.05)'
        ))
        # Chaque actif
        for ticker in available:
            cum_t = (1 + returns[ticker]).cumprod()
            fig.add_trace(go.Scatter(
                x=cum_t.index, y=(cum_t - 1) * 100,
                name=ticker, line=dict(width=1), opacity=0.5
            ))
        fig.add_hline(y=0, line_color="#2a2d35", line_width=1)
        fig.update_layout(height=380, paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                          font=dict(family="Inter", color="#8b9ab0"),
                          margin=dict(l=10, r=10, t=10, b=10),
                          xaxis=dict(gridcolor="#1e2228"),
                          yaxis=dict(gridcolor="#1e2228", ticksuffix="%"),
                          legend=dict(bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Résumé par actif")
        rows = []
        for t in available:
            s = returns[t]
            ret_t = float((1 + s).cumprod().iloc[-1] - 1) * 100
            vol_t = float(s.std() * np.sqrt(252)) * 100
            sr_t  = (s.mean() * 252 - risk_free) / (s.std() * np.sqrt(252))
            rows.append({"Ticker": t, "Rdt %": f"{ret_t:.2f}%", "Vol %": f"{vol_t:.2f}%", "Sharpe": f"{sr_t:.2f}", "Poids %": f"{weights[available.index(t)]*100:.1f}%"})

        df_sum = pd.DataFrame(rows)
        st.dataframe(df_sum, use_container_width=True, hide_index=True,
                     column_config={
                         "Rdt %": st.column_config.TextColumn("Rdt %"),
                         "Vol %": st.column_config.TextColumn("Vol %"),
                     })

    # Drawdown
    st.markdown("#### Drawdown")
    dd_series = (cum_returns / cum_returns.cummax()) - 1
    fig_dd = go.Figure()
    fig_dd.add_trace(go.Scatter(x=dd_series.index, y=dd_series * 100, name="Drawdown",
                                line=dict(color="#ef5350", width=1.5),
                                fill='tozeroy', fillcolor='rgba(239,83,80,0.1)'))
    fig_dd.update_layout(height=200, paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                         font=dict(family="Inter", color="#8b9ab0"),
                         margin=dict(l=10, r=10, t=10, b=10),
                         xaxis=dict(gridcolor="#1e2228"),
                         yaxis=dict(gridcolor="#1e2228", ticksuffix="%"))
    st.plotly_chart(fig_dd, use_container_width=True)

# ── Tab 2 : Allocation ───────────────────────────────────────────────
with tab2:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Répartition du portefeuille")
        fig_pie = go.Figure(go.Pie(
            labels=available,
            values=weights * capital,
            hole=0.55,
            textinfo='label+percent',
            marker=dict(colors=px.colors.qualitative.Set3)
        ))
        fig_pie.update_layout(height=380, paper_bgcolor="#0e1117",
                              font=dict(family="Inter", color="#8b9ab0"),
                              margin=dict(l=10, r=10, t=10, b=10),
                              legend=dict(bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.markdown("#### Capital alloué par actif")
        alloc_df = pd.DataFrame({
            "Actif": available,
            "Poids %": [f"{w*100:.1f}%" for w in weights],
            "Capital (€)": [f"{w*capital:,.0f} €" for w in weights],
            "Prix actuel": [f"{float(prices[t].iloc[-1]):.2f}" for t in available]
        })
        st.dataframe(alloc_df, use_container_width=True, hide_index=True)

        st.markdown("<br>", unsafe_allow_html=True)
        total_invested = capital
        current_value = capital * float(cum_returns.iloc[-1])
        pnl = current_value - total_invested
        pnl_color = "#26a69a" if pnl >= 0 else "#ef5350"
        st.markdown(f"""
        <div style='background:#1c1f26; border:1px solid #2a2d35; border-radius:10px; padding:16px;'>
            <div style='color:#8b9ab0; font-size:0.75rem; text-transform:uppercase;'>Capital initial</div>
            <div style='color:#e0e0e0; font-size:1.3rem; font-weight:700;'>{total_invested:,.0f} €</div>
            <div style='color:#8b9ab0; font-size:0.75rem; text-transform:uppercase; margin-top:10px;'>Valeur actuelle</div>
            <div style='color:#e0e0e0; font-size:1.3rem; font-weight:700;'>{current_value:,.0f} €</div>
            <div style='color:#8b9ab0; font-size:0.75rem; text-transform:uppercase; margin-top:10px;'>P&L</div>
            <div style='color:{pnl_color}; font-size:1.3rem; font-weight:700;'>{pnl:+,.0f} €</div>
        </div>
        """, unsafe_allow_html=True)

# ── Tab 3 : Corrélations ─────────────────────────────────────────────
with tab3:
    st.markdown("#### Matrice de corrélation")
    corr = returns.corr()
    fig_corr = go.Figure(go.Heatmap(
        z=corr.values, x=corr.columns, y=corr.index,
        colorscale="RdBu_r", zmid=0, zmin=-1, zmax=1,
        text=np.round(corr.values, 2),
        texttemplate="%{text}",
        colorbar=dict(tickfont=dict(color="#8b9ab0"))
    ))
    fig_corr.update_layout(height=450, paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                           font=dict(family="Inter", color="#8b9ab0"),
                           margin=dict(l=10, r=10, t=10, b=10),
                           xaxis=dict(tickfont=dict(color="#e0e0e0")),
                           yaxis=dict(tickfont=dict(color="#e0e0e0")))
    st.plotly_chart(fig_corr, use_container_width=True)

# ── Tab 4 : Risque ───────────────────────────────────────────────────
with tab4:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Distribution des rendements journaliers")
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Histogram(
            x=port_returns * 100, nbinsx=60,
            marker_color="#4fc3f7", opacity=0.7, name="Rendements"
        ))
        fig_hist.add_vline(x=var_95 * 100, line_dash="dash", line_color="#ef5350",
                           annotation_text=f"VaR 95%: {var_95*100:.2f}%",
                           annotation_font_color="#ef5350")
        fig_hist.update_layout(height=320, paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                               font=dict(family="Inter", color="#8b9ab0"),
                               margin=dict(l=10, r=10, t=10, b=10),
                               xaxis=dict(gridcolor="#1e2228", ticksuffix="%"),
                               yaxis=dict(gridcolor="#1e2228"))
        st.plotly_chart(fig_hist, use_container_width=True)

    with col2:
        st.markdown("#### Volatilité glissante (21j)")
        roll_vol = port_returns.rolling(21).std() * np.sqrt(252) * 100
        fig_vol = go.Figure()
        fig_vol.add_trace(go.Scatter(x=roll_vol.index, y=roll_vol,
                                     name="Vol 21j", line=dict(color="#f0b429", width=2),
                                     fill='tozeroy', fillcolor='rgba(240,180,41,0.05)'))
        fig_vol.update_layout(height=320, paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                              font=dict(family="Inter", color="#8b9ab0"),
                              margin=dict(l=10, r=10, t=10, b=10),
                              xaxis=dict(gridcolor="#1e2228"),
                              yaxis=dict(gridcolor="#1e2228", ticksuffix="%"))
        st.plotly_chart(fig_vol, use_container_width=True)

# ── Tab 5 : Optimisation Markowitz ──────────────────────────────────
with tab5:
    st.markdown("#### Frontière efficiente de Markowitz")
    n_portfolios = 3000
    n_assets = len(available)
    results = np.zeros((3, n_portfolios))
    weights_store = []

    with st.spinner("Simulation Monte Carlo des portefeuilles..."):
        mu = returns.mean() * 252
        cov = returns.cov() * 252
        for i in range(n_portfolios):
            w = np.random.dirichlet(np.ones(n_assets))
            weights_store.append(w)
            r = float(w @ mu)
            v = float(np.sqrt(w @ cov @ w))
            s = (r - risk_free) / v
            results[0, i] = v * 100
            results[1, i] = r * 100
            results[2, i] = s

    max_sharpe_idx = results[2].argmax()
    min_vol_idx    = results[0].argmin()

    fig_ef = go.Figure()
    fig_ef.add_trace(go.Scatter(
        x=results[0], y=results[1],
        mode='markers',
        marker=dict(color=results[2], colorscale='Viridis', size=3, opacity=0.5,
                    colorbar=dict(title="Sharpe", tickfont=dict(color="#8b9ab0"))),
        name="Portefeuilles simulés"
    ))
    fig_ef.add_trace(go.Scatter(
        x=[results[0, max_sharpe_idx]], y=[results[1, max_sharpe_idx]],
        mode='markers', marker=dict(color="#f0b429", size=14, symbol="star"),
        name=f"Max Sharpe ({results[2, max_sharpe_idx]:.2f})"
    ))
    fig_ef.add_trace(go.Scatter(
        x=[results[0, min_vol_idx]], y=[results[1, min_vol_idx]],
        mode='markers', marker=dict(color="#26a69a", size=14, symbol="diamond"),
        name=f"Min Volatilité ({results[0, min_vol_idx]:.2f}%)"
    ))
    # Portefeuille actuel
    curr_v = float(np.sqrt(weights @ cov @ weights)) * 100
    curr_r = float(weights @ mu) * 100
    fig_ef.add_trace(go.Scatter(
        x=[curr_v], y=[curr_r],
        mode='markers', marker=dict(color="#4fc3f7", size=14, symbol="circle"),
        name="Portefeuille actuel"
    ))
    fig_ef.update_layout(height=430, paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                         font=dict(family="Inter", color="#8b9ab0"),
                         margin=dict(l=10, r=10, t=10, b=10),
                         xaxis=dict(gridcolor="#1e2228", title="Volatilité (%)", ticksuffix="%"),
                         yaxis=dict(gridcolor="#1e2228", title="Rendement (%)", ticksuffix="%"),
                         legend=dict(bgcolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig_ef, use_container_width=True)

    # Poids optimaux
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### Poids — Max Sharpe ⭐")
        w_sharpe = weights_store[max_sharpe_idx]
        df_s = pd.DataFrame({"Actif": available, "Poids %": [f"{w*100:.1f}%" for w in w_sharpe]})
        st.dataframe(df_s, use_container_width=True, hide_index=True)
    with col2:
        st.markdown("##### Poids — Min Volatilité 💎")
        w_minvol = weights_store[min_vol_idx]
        df_v = pd.DataFrame({"Actif": available, "Poids %": [f"{w*100:.1f}%" for w in w_minvol]})
        st.dataframe(df_v, use_container_width=True, hide_index=True)
