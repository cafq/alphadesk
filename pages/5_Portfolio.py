import sys
_os = __import__("os")
ROOT_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)
from utils.ai_assistant import render_chat_widget, build_context
from utils.theme import apply_global_theme

render_chat_widget("portfolio")

# pages/5_Portfolio.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta
import sqlite3
import os

# ───────────────────────────────────────
# CONFIG
# ───────────────────────────────────────
st.set_page_config(
    page_title="AlphaDesk · Portfolio",
    page_icon="▲",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ───────────────────────────────────────
# STYLE
# ───────────────────────────────────────
apply_global_theme()
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
    .stTextArea label, .stSelectbox label, .stNumberInput label {
        color: #8b9ab0 !important;
        font-size: 0.8rem !important;
        text-transform: uppercase;
    }
    .stTextInput input, .stTextArea textarea {
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
    .caption { color: #555e6e !important; font-size: 0.75rem; }
    .section-label {
        color: #8b9ab0;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 12px;
    }
    .pnl-card {
        background: #1c1f26;
        border: 1px solid #2a2d35;
        border-radius: 10px;
        padding: 18px 22px;
        margin-bottom: 10px;
    }
    .esg-bar-wrap { background: #2a2d35; border-radius: 4px; height: 6px; margin-top: 6px; overflow: hidden; }
    .esg-bar-fill { height: 6px; border-radius: 4px; }

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
        <span style='font-size:1.1rem; font-weight:500; color:#8b9ab0; margin-left:12px;'>/ Portfolio</span>
    </div>
    <p style='color:#8b9ab0; font-size:0.88rem; margin-top:8px;'>
        Analyse · Optimisation Markowitz · Sharpe · VaR · ESG Score
    </p>
</div>
""", unsafe_allow_html=True)

st.divider()


# ───────────────────────────────────────
# ESG DB HELPER
# ───────────────────────────────────────
def get_esg_scores(tickers: list) -> dict:
    """Récupère les scores ESG depuis la DB locale."""
    try:
        conn = sqlite3.connect("data/esg_data.db", check_same_thread=False)
        df = pd.read_sql("SELECT ticker, total_esg_score FROM esg_profiles", conn)
        conn.close()
        return dict(zip(df["ticker"], df["total_esg_score"]))
    except:
        return {}


# ───────────────────────────────────────
# SIDEBAR — CONFIG
# ───────────────────────────────────────
with st.sidebar:
    st.markdown("<p class='section-label'>Configuration</p>", unsafe_allow_html=True)

    tickers_input = st.text_area(
        "TICKERS (un par ligne)",
        value="AAPL\nMSFT\nGOOGL\nTSLA\nBTC-USD",
        height=180,
    )
    weights_input = st.text_area(
        "POIDS (un par ligne, laisser vide = équipondéré)",
        value="",
        height=120,
        placeholder="Ex:\n20\n20\n20\n20\n20",
    )
    period    = st.selectbox("PÉRIODE", ["6mo","1y","2y","3y","5y"], index=2)
    risk_free = st.number_input("TAUX SANS RISQUE (%)", value=4.5, step=0.1) / 100
    capital   = st.number_input("CAPITAL (€)", value=10000, step=500)

tickers = [t.strip().upper() for t in tickers_input.strip().split() if t.strip()]

# Poids
if weights_input.strip():
    try:
        w_raw   = [float(x.strip()) for x in weights_input.strip().split() if x.strip()]
        weights = np.array(w_raw) / sum(w_raw)
    except:
        weights = np.ones(len(tickers)) / len(tickers)
else:
    weights = np.ones(len(tickers)) / len(tickers)

if len(weights) != len(tickers):
    weights = np.ones(len(tickers)) / len(tickers)

# ───────────────────────────────────────
# IMPORT CSV (optionnel)
# ───────────────────────────────────────
st.markdown("<p class='section-label'>📂 Importer ton portefeuille réel (optionnel)</p>", unsafe_allow_html=True)

with st.expander("Importer un fichier CSV", expanded=False):
    st.markdown("""
    <div style='color:#8b9ab0; font-size:0.82rem; margin-bottom:12px;'>
        Format attendu : <code>ticker,poids</code> ou <code>ticker,quantite,prix_achat</code><br>
        Exemple : <code>AAPL,30</code> / <code>AAPL,10,150.5</code>
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader("Dépose ton CSV ici", type=["csv"], label_visibility="collapsed")

    if uploaded:
        try:
            df_csv = pd.read_csv(uploaded)
            df_csv.columns = [c.strip().lower() for c in df_csv.columns]

            # ── Mode 1 : ticker + poids ──
            if "ticker" in df_csv.columns and "poids" in df_csv.columns:
                tickers_csv = df_csv["ticker"].str.upper().tolist()
                weights_csv = df_csv["poids"].astype(float).tolist()
                weights_csv = [w / sum(weights_csv) for w in weights_csv]

                st.success(f"✅ {len(tickers_csv)} actifs importés (mode poids)")
                st.dataframe(df_csv, use_container_width=True, hide_index=True)

                if st.button("✅ Utiliser ce portefeuille", use_container_width=True):
                    st.session_state["csv_tickers"] = tickers_csv
                    st.session_state["csv_weights"] = weights_csv
                    st.rerun()

            # ── Mode 2 : ticker + quantite + prix_achat ──
            elif "ticker" in df_csv.columns and "quantite" in df_csv.columns and "prix_achat" in df_csv.columns:
                df_csv["valeur"] = df_csv["quantite"].astype(float) * df_csv["prix_achat"].astype(float)
                total_val = df_csv["valeur"].sum()
                tickers_csv = df_csv["ticker"].str.upper().tolist()
                weights_csv = (df_csv["valeur"] / total_val).tolist()

                st.success(f"✅ {len(tickers_csv)} actifs importés (mode quantité × prix)")
                st.dataframe(df_csv, use_container_width=True, hide_index=True)

                if st.button("✅ Utiliser ce portefeuille", use_container_width=True):
                    st.session_state["csv_tickers"] = tickers_csv
                    st.session_state["csv_weights"] = weights_csv
                    st.rerun()

            else:
                st.error("⚠️ Colonnes non reconnues. Utilise : `ticker,poids` ou `ticker,quantite,prix_achat`")

        except Exception as e:
            st.error(f"Erreur lors de la lecture du CSV : {e}")

st.divider()
# Priorité au CSV importé si disponible
if "csv_tickers" in st.session_state:
    tickers = st.session_state["csv_tickers"]
    weights = np.array(st.session_state["csv_weights"])
    st.info(f"📂 Portefeuille CSV actif : {', '.join(tickers)}")

# ───────────────────────────────────────
# CHARGEMENT DONNÉES
# ───────────────────────────────────────
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

prices  = prices[available]
weights = weights[:len(available)]
weights = weights / weights.sum()

returns     = prices.pct_change().dropna()
port_ret    = (returns * weights).sum(axis=1)
cum_returns = (1 + port_ret).cumprod()

annual_ret = float(port_ret.mean() * 252)
annual_vol = float(port_ret.std() * np.sqrt(252))
sharpe     = (annual_ret - risk_free) / annual_vol if annual_vol > 0 else 0
max_dd     = float((cum_returns / cum_returns.cummax() - 1).min())
var_95     = float(np.percentile(port_ret, 5))
cvar_95    = float(port_ret[port_ret <= var_95].mean())
total_ret  = float(cum_returns.iloc[-1] - 1)
calmar     = annual_ret / abs(max_dd) if max_dd != 0 else 0
sortino_den = float(port_ret[port_ret < 0].std() * np.sqrt(252))
sortino    = (annual_ret - risk_free) / sortino_den if sortino_den > 0 else 0


# ───────────────────────────────────────
# MÉTRIQUES HEADER
# ───────────────────────────────────────
st.markdown("<p class='section-label'>Métriques du portefeuille</p>", unsafe_allow_html=True)

m1,m2,m3,m4,m5,m6,m7,m8,m9 = st.columns(9)
m1.metric("Rendement Total",  f"{total_ret*100:.2f}%")
m2.metric("Rendement Annuel", f"{annual_ret*100:.2f}%")
m3.metric("Volatilité Ann.",  f"{annual_vol*100:.2f}%")
m4.metric("Sharpe Ratio",     f"{sharpe:.2f}")
m5.metric("Sortino Ratio",    f"{sortino:.2f}")
m6.metric("Calmar Ratio",     f"{calmar:.2f}")
m7.metric("Max Drawdown",     f"{max_dd*100:.2f}%")
m8.metric("VaR 95%",          f"{var_95*100:.2f}%")
m9.metric("CVaR 95%",         f"{cvar_95*100:.2f}%")

st.divider()


# ───────────────────────────────────────
# ONGLETS
# ───────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 Performance",
    "🥧 Allocation",
    "🔗 Corrélations",
    "⚠️ Risque",
    "🎯 Optimisation",
    "🌱 Score ESG",
])


# ── Tab 1 : Performance ──
with tab1:
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("<p class='section-label'>Performance cumulée</p>", unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=cum_returns.index, y=(cum_returns - 1) * 100,
            name="Portefeuille", line=dict(color="#4fc3f7", width=2.5),
            fill="tozeroy", fillcolor="rgba(79,195,247,0.05)",
        ))
        for t in available:
            cum_t = (1 + returns[t]).cumprod()
            fig.add_trace(go.Scatter(
                x=cum_t.index, y=(cum_t - 1) * 100,
                name=t, line=dict(width=1), opacity=0.5,
            ))
        fig.add_hline(y=0, line_color="#2a2d35", line_width=1)
        fig.update_layout(
            height=380, paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
            font=dict(family="Inter", color="#8b9ab0"),
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(gridcolor="#1e2228"),
            yaxis=dict(gridcolor="#1e2228", ticksuffix="%"),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)

        # Drawdown
        st.markdown("<p class='section-label'>Drawdown</p>", unsafe_allow_html=True)
        dd_series = (cum_returns / cum_returns.cummax() - 1)
        fig_dd = go.Figure(go.Scatter(
            x=dd_series.index, y=dd_series * 100,
            name="Drawdown", line=dict(color="#ef5350", width=1.5),
            fill="tozeroy", fillcolor="rgba(239,83,80,0.1)",
        ))
        fig_dd.update_layout(
            height=200, paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
            font=dict(family="Inter", color="#8b9ab0"),
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(gridcolor="#1e2228"),
            yaxis=dict(gridcolor="#1e2228", ticksuffix="%"),
        )
        st.plotly_chart(fig_dd, use_container_width=True)

    with col2:
        st.markdown("<p class='section-label'>Résumé par actif</p>", unsafe_allow_html=True)
        rows = []
        for t in available:
            s    = returns[t]
            ret  = float((1 + s).cumprod().iloc[-1] - 1) * 100
            vol  = float(s.std() * np.sqrt(252)) * 100
            shr  = (s.mean() * 252 - risk_free) / (s.std() * np.sqrt(252)) if s.std() > 0 else 0
            rows.append({
                "Ticker": t,
                "Rdt %":  f"{ret:.2f}",
                "Vol %":  f"{vol:.2f}",
                "Sharpe": f"{shr:.2f}",
                "Poids %": f"{weights[available.index(t)]*100:.1f}",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # PnL card
        current_value = capital * float(cum_returns.iloc[-1])
        pnl           = current_value - capital
        pnl_color     = "#26a69a" if pnl >= 0 else "#ef5350"
        st.markdown(f"""
        <div class='pnl-card' style='margin-top:16px;'>
            <div style='color:#8b9ab0; font-size:0.7rem; text-transform:uppercase; letter-spacing:0.1em;'>Capital initial</div>
            <div style='color:#e0e0e0; font-size:1.3rem; font-weight:700;'>{capital:,.0f} €</div>
            <div style='color:#8b9ab0; font-size:0.7rem; text-transform:uppercase; letter-spacing:0.1em; margin-top:10px;'>Valeur actuelle</div>
            <div style='color:#e0e0e0; font-size:1.3rem; font-weight:700;'>{current_value:,.0f} €</div>
            <div style='color:#8b9ab0; font-size:0.7rem; text-transform:uppercase; letter-spacing:0.1em; margin-top:10px;'>P&L</div>
            <div style='color:{pnl_color}; font-size:1.3rem; font-weight:700;'>{pnl:+,.0f} €</div>
        </div>
        """, unsafe_allow_html=True)


# ── Tab 2 : Allocation ──
with tab2:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<p class='section-label'>Répartition du portefeuille</p>", unsafe_allow_html=True)
        fig_pie = go.Figure(go.Pie(
            labels=available, values=weights * capital,
            hole=0.55, textinfo="label+percent",
            marker=dict(colors=px.colors.qualitative.Set3),
        ))
        fig_pie.update_layout(
            height=380, paper_bgcolor="#0e1117",
            font=dict(family="Inter", color="#8b9ab0"),
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.markdown("<p class='section-label'>Capital alloué par actif</p>", unsafe_allow_html=True)
        alloc_df = pd.DataFrame({
            "Actif":      available,
            "Poids %":    [f"{w*100:.1f}" for w in weights],
            "Capital €":  [f"{w*capital:,.0f}" for w in weights],
            "Prix actuel":[f"{float(prices[t].iloc[-1]):.2f}" for t in available],
        })
        st.dataframe(alloc_df, use_container_width=True, hide_index=True)

        # Volatilité par actif (barres)
        st.markdown("<p class='section-label'>Volatilité annualisée</p>", unsafe_allow_html=True)
        vols = [float(returns[t].std() * np.sqrt(252)) * 100 for t in available]
        fig_vol = go.Figure(go.Bar(
            x=available, y=vols,
            marker_color=["#4F46E5"] * len(available),
            text=[f"{v:.1f}%" for v in vols], textposition="outside",
        ))
        fig_vol.update_layout(
            height=250, paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
            font=dict(family="Inter", color="#8b9ab0"),
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(gridcolor="#1e2228"),
            yaxis=dict(gridcolor="#1e2228", ticksuffix="%"),
            showlegend=False,
        )
        st.plotly_chart(fig_vol, use_container_width=True)


# ── Tab 3 : Corrélations ──
with tab3:
    st.markdown("<p class='section-label'>Matrice de corrélation</p>", unsafe_allow_html=True)
    corr = returns.corr()
    fig_corr = go.Figure(go.Heatmap(
        z=corr.values, x=corr.columns, y=corr.index,
        colorscale="RdBu_r", zmid=0, zmin=-1, zmax=1,
        text=np.round(corr.values, 2), texttemplate="%{text}",
        colorbar=dict(tickfont=dict(color="#8b9ab0")),
    ))
    fig_corr.update_layout(
        height=450, paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
        font=dict(family="Inter", color="#8b9ab0"),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(tickfont=dict(color="#e0e0e0")),
        yaxis=dict(tickfont=dict(color="#e0e0e0")),
    )
    st.plotly_chart(fig_corr, use_container_width=True)

    # Insight diversification
    avg_corr = (corr.values.sum() - len(available)) / (len(available)**2 - len(available))
    if avg_corr > 0.7:
        st.warning(f"⚠️ Corrélation moyenne élevée ({avg_corr:.2f}) — portefeuille peu diversifié.")
    elif avg_corr > 0.4:
        st.info(f"ℹ️ Corrélation moyenne modérée ({avg_corr:.2f}) — diversification partielle.")
    else:
        st.success(f"✅ Corrélation moyenne faible ({avg_corr:.2f}) — bon niveau de diversification.")


# ── Tab 4 : Risque ──
with tab4:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<p class='section-label'>Distribution des rendements journaliers</p>", unsafe_allow_html=True)
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Histogram(
            x=port_ret * 100, nbinsx=60,
            marker_color="#4fc3f7", opacity=0.7, name="Rendements",
        ))
        fig_hist.add_vline(
            x=var_95 * 100, line_dash="dash", line_color="#ef5350",
            annotation_text=f"VaR 95% {var_95*100:.2f}%",
            annotation_font_color="#ef5350",
        )
        fig_hist.add_vline(
            x=cvar_95 * 100, line_dash="dash", line_color="#f0b429",
            annotation_text=f"CVaR {cvar_95*100:.2f}%",
            annotation_font_color="#f0b429",
        )
        fig_hist.update_layout(
            height=320, paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
            font=dict(family="Inter", color="#8b9ab0"),
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(gridcolor="#1e2228", ticksuffix="%"),
            yaxis=dict(gridcolor="#1e2228"),
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    with col2:
        st.markdown("<p class='section-label'>Volatilité glissante 21j</p>", unsafe_allow_html=True)
        roll_vol = port_ret.rolling(21).std() * np.sqrt(252) * 100
        fig_rv = go.Figure(go.Scatter(
            x=roll_vol.index, y=roll_vol,
            name="Vol 21j", line=dict(color="#f0b429", width=2),
            fill="tozeroy", fillcolor="rgba(240,180,41,0.05)",
        ))
        fig_rv.update_layout(
            height=320, paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
            font=dict(family="Inter", color="#8b9ab0"),
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(gridcolor="#1e2228"),
            yaxis=dict(gridcolor="#1e2228", ticksuffix="%"),
        )
        st.plotly_chart(fig_rv, use_container_width=True)

    # Stress test
    st.markdown("<p class='section-label'>Stress Test — Scénarios de crise</p>", unsafe_allow_html=True)
    scenarios = {
        "Crash -10%":  -0.10,
        "Crash -20%":  -0.20,
        "Crash -30%":  -0.30,
        "Crash -50%":  -0.50,
        "Hausse +10%": +0.10,
        "Hausse +20%": +0.20,
    }
    sc_cols = st.columns(len(scenarios))
    for col, (name, shock) in zip(sc_cols, scenarios.items()):
        impact = capital * shock
        color  = "#26a69a" if shock > 0 else "#ef5350"
        col.metric(name, f"{impact:+,.0f} €", delta_color="off")


# ── Tab 5 : Optimisation Markowitz ──
with tab5:
    st.markdown("<p class='section-label'>Frontière efficiente de Markowitz</p>", unsafe_allow_html=True)

    n_portfolios = 3000
    n_assets     = len(available)
    results      = np.zeros((3, n_portfolios))
    weights_store = []

    with st.spinner("Simulation Monte Carlo..."):
        mu  = returns.mean() * 252
        cov = returns.cov() * 252
        for i in range(n_portfolios):
            w = np.random.dirichlet(np.ones(n_assets))
            weights_store.append(w)
            r = float(w @ mu)
            v = float(np.sqrt(w @ cov @ w))
            results[0, i] = v * 100
            results[1, i] = r * 100
            results[2, i] = (r - risk_free) / v if v > 0 else 0

    max_sharpe_idx = results[2].argmax()
    min_vol_idx    = results[0].argmin()

    fig_ef = go.Figure()
    fig_ef.add_trace(go.Scatter(
        x=results[0], y=results[1], mode="markers",
        marker=dict(color=results[2], colorscale="Viridis", size=3, opacity=0.5,
                    colorbar=dict(title="Sharpe", tickfont=dict(color="#8b9ab0"))),
        name="Portefeuilles simulés",
    ))
    fig_ef.add_trace(go.Scatter(
        x=[results[0, max_sharpe_idx]], y=[results[1, max_sharpe_idx]],
        mode="markers",
        marker=dict(color="#f0b429", size=14, symbol="star"),
        name=f"Max Sharpe {results[2, max_sharpe_idx]:.2f}",
    ))
    fig_ef.add_trace(go.Scatter(
        x=[results[0, min_vol_idx]], y=[results[1, min_vol_idx]],
        mode="markers",
        marker=dict(color="#26a69a", size=14, symbol="diamond"),
        name=f"Min Volatilité {results[0, min_vol_idx]:.2f}%",
    ))
    curr_v = float(np.sqrt(weights @ cov @ weights)) * 100
    curr_r = float(weights @ mu) * 100
    fig_ef.add_trace(go.Scatter(
        x=[curr_v], y=[curr_r], mode="markers",
        marker=dict(color="#4fc3f7", size=14, symbol="circle"),
        name="Portefeuille actuel",
    ))
    fig_ef.update_layout(
        height=430, paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
        font=dict(family="Inter", color="#8b9ab0"),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(gridcolor="#1e2228", title="Volatilité %", ticksuffix="%"),
        yaxis=dict(gridcolor="#1e2228", title="Rendement %", ticksuffix="%"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig_ef, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<p class='section-label'>Poids — Max Sharpe</p>", unsafe_allow_html=True)
        w_sharpe = weights_store[max_sharpe_idx]
        st.dataframe(
            pd.DataFrame({"Actif": available, "Poids %": [f"{w*100:.1f}" for w in w_sharpe]}),
            use_container_width=True, hide_index=True,
        )
    with col2:
        st.markdown("<p class='section-label'>Poids — Min Volatilité</p>", unsafe_allow_html=True)
        w_minvol = weights_store[min_vol_idx]
        st.dataframe(
            pd.DataFrame({"Actif": available, "Poids %": [f"{w*100:.1f}" for w in w_minvol]}),
            use_container_width=True, hide_index=True,
        )


# ── Tab 6 : Score ESG (NOUVEAU) ──
with tab6:
    st.markdown("<p class='section-label'>Score ESG du portefeuille</p>", unsafe_allow_html=True)

    esg_db = get_esg_scores(available)

    if not esg_db:
        st.warning("⚠️ Aucune donnée ESG trouvée. Ajoute tes actifs dans le module ESG d'abord.")
    else:
        matched    = {t: esg_db[t] for t in available if t in esg_db}
        unmatched  = [t for t in available if t not in esg_db]

        if matched:
            # Score global pondéré
            esg_weights = np.array([weights[available.index(t)] for t in matched])
            esg_weights = esg_weights / esg_weights.sum()
            esg_scores  = np.array([matched[t] for t in matched])
            global_esg  = float(np.dot(esg_weights, esg_scores))

            esg_color = "#22c55e" if global_esg >= 70 else "#f59e0b" if global_esg >= 50 else "#ef5350"
            esg_label = "EXCELLENT" if global_esg >= 70 else "MODÉRÉ" if global_esg >= 50 else "FAIBLE"

            # Carte score global
            st.markdown(f"""
            <div class='pnl-card' style='border-color:{esg_color}44; margin-bottom:20px;'>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <div>
                        <div style='color:#8b9ab0; font-size:0.7rem; text-transform:uppercase; letter-spacing:0.1em;'>
                            Score ESG global du portefeuille
                        </div>
                        <div style='color:{esg_color}; font-size:2rem; font-weight:800; margin-top:4px;'>
                            {global_esg:.1f}<span style='font-size:0.9rem; color:#555e6e;'>/100</span>
                        </div>
                        <div style='color:{esg_color}; font-size:0.75rem; font-weight:700; text-transform:uppercase;'>
                            {esg_label}
                        </div>
                    </div>
                    <div style='text-align:right; color:#8b9ab0; font-size:0.8rem;'>
                        {len(matched)}/{len(available)} actifs avec données ESG
                    </div>
                </div>
                <div class='esg-bar-wrap' style='margin-top:14px;'>
                    <div class='esg-bar-fill' style='width:{global_esg}%; background:{esg_color};'></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Scores par actif
            st.markdown("<p class='section-label'>Scores par actif</p>", unsafe_allow_html=True)
            for t in matched:
                score_t = matched[t]
                w_t     = weights[available.index(t)] * 100
                c_t     = "#22c55e" if score_t >= 70 else "#f59e0b" if score_t >= 50 else "#ef5350"
                contribution = score_t * (w_t / 100)
                st.markdown(f"""
                <div style='display:flex; justify-content:space-between; align-items:center;
                            background:#1c1f26; border:1px solid #2a2d35; border-radius:8px;
                            padding:12px 18px; margin-bottom:6px;'>
                    <div style='font-size:1rem; font-weight:700; color:#ffffff;'>{t}</div>
                    <div style='display:flex; gap:32px; align-items:center;'>
                        <div style='text-align:center;'>
                            <div style='font-size:0.65rem; color:#8b9ab0; text-transform:uppercase;'>Poids</div>
                            <div style='color:#e0e0e0; font-weight:600;'>{w_t:.1f}%</div>
                        </div>
                        <div style='text-align:center;'>
                            <div style='font-size:0.65rem; color:#8b9ab0; text-transform:uppercase;'>Score ESG</div>
                            <div style='color:{c_t}; font-weight:700; font-size:1.1rem;'>{score_t:.0f}/100</div>
                        </div>
                        <div style='text-align:center;'>
                            <div style='font-size:0.65rem; color:#8b9ab0; text-transform:uppercase;'>Contribution</div>
                            <div style='color:#e0e0e0; font-weight:600;'>{contribution:.1f} pts</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            if unmatched:
                st.info(f"ℹ️ Actifs sans données ESG : {', '.join(unmatched)} — ajoute-les dans le module ESG.")

            # Graphique ESG vs Poids
            st.markdown("<p class='section-label'>ESG Score vs Poids du portefeuille</p>", unsafe_allow_html=True)
            fig_esg = go.Figure()
            for t in matched:
                fig_esg.add_trace(go.Scatter(
                    x=[weights[available.index(t)] * 100],
                    y=[matched[t]],
                    mode="markers+text",
                    name=t,
                    text=[t],
                    textposition="top center",
                    marker=dict(size=14),
                ))
            fig_esg.add_hline(y=70, line_dash="dash", line_color="#26a69a", line_width=1, opacity=0.5,
                              annotation_text="Seuil ESG bon", annotation_font_color="#26a69a")
            fig_esg.update_layout(
                height=350, paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                font=dict(family="Inter", color="#8b9ab0"),
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(gridcolor="#1e2228", title="Poids %", ticksuffix="%"),
                yaxis=dict(gridcolor="#1e2228", title="Score ESG", range=[0, 100]),
                showlegend=False,
            )
            st.plotly_chart(fig_esg, use_container_width=True)


st.divider()
st.markdown(
    "<p class='caption' style='text-align:center;'>AlphaDesk v1.0 &nbsp;·&nbsp; Portfolio · Yahoo Finance · Markowitz</p>",
    unsafe_allow_html=True,
)
