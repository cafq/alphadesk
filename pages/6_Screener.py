import os
import sys
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)
from utils.ai_assistant import render_chat_widget, build_context

render_chat_widget("screener")

# pages/6_Screener.py

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import io

# ───────────────────────────────────────
# CONFIG
# ───────────────────────────────────────
st.set_page_config(
    page_title="AlphaDesk · Screener",
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
    .stSelectbox label, .stSlider label, .stMultiSelect label {
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
        <span style='font-size:1.1rem; font-weight:500; color:#8b9ab0; margin-left:12px;'>/ Screener</span>
    </div>
    <p style='color:#8b9ab0; font-size:0.88rem; margin-top:8px;'>
        Filtre les actifs par performance · volatilité · RSI · volume · Sharpe
    </p>
</div>
""", unsafe_allow_html=True)

st.divider()


# ───────────────────────────────────────
# UNIVERS
# ───────────────────────────────────────
UNIVERSES = {
    "S&P 500 — Top 30": [
        "AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","BRK-B","JPM","V",
        "UNH","XOM","LLY","JNJ","MA","PG","HD","MRK","ABBV","CVX",
        "PEP","KO","COST","WMT","BAC","CRM","ORCL","NFLX","AMD","INTC",
    ],
    "CAC 40 — Top 20": [
        "MC.PA","TTE.PA","SAN.PA","BNP.PA","AIR.PA","RI.PA","DG.PA","SU.PA",
        "AI.PA","OR.PA","CS.PA","BN.PA","ACA.PA","SGO.PA","VIE.PA",
        "STM.PA","SAF.PA","KER.PA","CAP.PA","DSY.PA",
    ],
    "Crypto — Top 15": [
        "BTC-USD","ETH-USD","BNB-USD","SOL-USD","XRP-USD",
        "ADA-USD","AVAX-USD","DOGE-USD","DOT-USD","MATIC-USD",
        "LINK-USD","LTC-USD","ATOM-USD","UNI-USD","APT-USD",
    ],
    "ETF Majeurs": [
        "SPY","QQQ","IWM","DIA","GLD","SLV","TLT","HYG",
        "EEM","VNQ","XLK","XLF","XLE","XLV","ARKK",
    ],
    "Tech US — Growth": [
        "NVDA","AMD","TSLA","PLTR","SNOW","CRWD","NET","DDOG",
        "ZS","MDB","SMCI","ARM","AVGO","QCOM","TXN",
    ],
    "Dividendes US": [
        "JNJ","PG","KO","PEP","MCD","MMM","T","VZ",
        "IBM","CVX","XOM","WBA","O","MAIN","JEPI",
    ],
    "Personnalisé": [],
}


# ───────────────────────────────────────
# SIDEBAR
# ───────────────────────────────────────
with st.sidebar:
    st.markdown("<p class='section-label'>Univers</p>", unsafe_allow_html=True)
    universe = st.selectbox("UNIVERS", list(UNIVERSES.keys()), label_visibility="collapsed")

    # Tickers personnalisés
    if universe == "Personnalisé":
        custom_tickers = st.text_area(
            "TICKERS (virgule ou espace)",
            placeholder="AAPL, TSLA, BTC-USD...",
            height=120,
        )
        tickers = [t.strip().upper() for t in custom_tickers.replace(",", " ").split() if t.strip()]
    else:
        tickers = UNIVERSES[universe]

    st.markdown("<p class='section-label' style='margin-top:16px;'>Période</p>", unsafe_allow_html=True)
    period = st.selectbox("PÉRIODE", ["1mo", "3mo", "6mo", "1y", "2y"], index=2, label_visibility="collapsed")

    st.divider()
    st.markdown("<p class='section-label'>Filtres techniques</p>", unsafe_allow_html=True)

    rsi_range = st.slider("RSI", 0, 100, (0, 100))
    ret_min   = st.slider("Rendement min (%)", -50, 200, -100)
    vol_max   = st.slider("Volatilité max (%)", 0, 300, 300)
    sharpe_min= st.slider("Sharpe min", -5.0, 5.0, -5.0, step=0.1)

    st.divider()
    st.markdown("<p class='section-label'>Tri</p>", unsafe_allow_html=True)
    sort_by  = st.selectbox("TRIER PAR", ["Rendement %", "Volatilité %", "Sharpe", "RSI", "1J %", "Volume moyen"], label_visibility="collapsed")
    sort_asc = st.checkbox("Ordre croissant", value=False)

    st.divider()
    run = st.button("🔍 LANCER LE SCREENER", use_container_width=True, type="primary")


# ───────────────────────────────────────
# INDICATEURS
# ───────────────────────────────────────
def compute_rsi(s, n=14) -> float:
    d = s.diff()
    g = d.clip(lower=0).rolling(n).mean()
    l = (-d.clip(upper=0)).rolling(n).mean()
    rsi = 100 - (100 / (1 + g / l.replace(0, np.nan)))
    try:    return float(rsi.dropna().iloc[-1])
    except: return 50.0

def compute_macd_signal(s) -> str:
    ef  = s.ewm(span=12, adjust=False).mean()
    es  = s.ewm(span=26, adjust=False).mean()
    m   = ef - es
    sig = m.ewm(span=9, adjust=False).mean()
    if float(m.iloc[-1]) > float(sig.iloc[-1]):  return "🟢 BULL"
    if float(m.iloc[-1]) < float(sig.iloc[-1]):  return "🔴 BEAR"
    return "🟡 NEUT"

def compute_bb_position(s, n=20, k=2) -> str:
    sma = s.rolling(n).mean()
    std = s.rolling(n).std()
    up  = sma + k * std
    lo  = sma - k * std
    lc  = float(s.iloc[-1])
    if lc >= float(up.iloc[-1]):  return "↑ Haute"
    if lc <= float(lo.iloc[-1]):  return "↓ Basse"
    return "— Milieu"

def compute_trend(s) -> str:
    ema20 = float(s.ewm(span=20, adjust=False).mean().iloc[-1])
    ema50 = float(s.ewm(span=50, adjust=False).mean().iloc[-1])
    lc    = float(s.iloc[-1])
    if lc > ema20 > ema50: return "🟢 Haussière"
    if lc < ema20 < ema50: return "🔴 Baissière"
    return "🟡 Mixte"


# ───────────────────────────────────────
# SCREENER PRINCIPAL
# ───────────────────────────────────────
if run:
    if not tickers:
        st.warning("⚠️ Aucun ticker sélectionné.")
        st.stop()

    results  = []
    errors   = []
    progress = st.progress(0, text="Analyse en cours...")

    for i, ticker in enumerate(tickers):
        try:
            df = yf.download(ticker, period=period, auto_adjust=True,
                             progress=False, timeout=12)
            if df.empty or len(df) < 20:
                errors.append(ticker)
                continue

            df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
            close  = df["Close"].squeeze()
            volume = df["Volume"].squeeze() if "Volume" in df else pd.Series(dtype=float)

            daily_r = close.pct_change().dropna()
            ret     = float(close.iloc[-1] / close.iloc[0] - 1) * 100
            volatil = float(daily_r.std() * np.sqrt(252)) * 100
            sharpe  = float(daily_r.mean() * 252 / (daily_r.std() * np.sqrt(252))) if daily_r.std() > 0 else 0
            rsi     = compute_rsi(close)
            chg_1d  = float(daily_r.iloc[-1]) * 100
            price   = float(close.iloc[-1])
            avg_vol = float(volume.mean()) if not volume.empty and volume.sum() > 0 else 0

            macd_sig  = compute_macd_signal(close)
            bb_pos    = compute_bb_position(close)
            trend     = compute_trend(close)

            results.append({
                "Ticker":       ticker,
                "Prix":         round(price, 2),
                "1J %":         round(chg_1d, 2),
                "Rendement %":  round(ret, 2),
                "Volatilité %": round(volatil, 2),
                "Sharpe":       round(sharpe, 2),
                "RSI":          round(rsi, 1),
                "MACD":         macd_sig,
                "BB Position":  bb_pos,
                "Tendance":     trend,
                "Volume moyen": int(avg_vol),
            })

        except Exception:
            errors.append(ticker)

        progress.progress((i + 1) / len(tickers), text=f"Analyse de {ticker}...")

    progress.empty()

    if not results:
        st.error("Aucune donnée récupérée. Vérifie ta connexion ou les tickers.")
        st.stop()

    df_res = pd.DataFrame(results)

    # ── Application des filtres ──
    df_res = df_res[
        (df_res["RSI"]          >= rsi_range[0]) &
        (df_res["RSI"]          <= rsi_range[1]) &
        (df_res["Rendement %"]  >= ret_min)      &
        (df_res["Volatilité %"] <= vol_max)      &
        (df_res["Sharpe"]       >= sharpe_min)
    ].sort_values(sort_by, ascending=sort_asc).reset_index(drop=True)

    # ───────────────────────────────────────
    # MÉTRIQUES RÉSUMÉ
    # ───────────────────────────────────────
    n_total  = len(results)
    n_shown  = len(df_res)
    n_bull   = len(df_res[df_res["Tendance"] == "🟢 Haussière"])
    n_bear   = len(df_res[df_res["Tendance"] == "🔴 Baissière"])
    avg_rsi  = df_res["RSI"].mean() if not df_res.empty else 0
    avg_ret  = df_res["Rendement %"].mean() if not df_res.empty else 0

    m1,m2,m3,m4,m5,m6 = st.columns(6)
    m1.metric("Actifs analysés",  n_total)
    m2.metric("Résultats filtrés",n_shown)
    m3.metric("🟢 Haussiers",     n_bull)
    m4.metric("🔴 Baissiers",     n_bear)
    m5.metric("RSI moyen",        f"{avg_rsi:.1f}")
    m6.metric("Rdt moyen",        f"{avg_ret:.2f}%")

    if errors:
        st.caption(f"⚠️ Tickers ignorés (données insuffisantes) : {', '.join(errors)}")

    st.divider()

    if df_res.empty:
        st.warning("Aucun actif ne correspond aux filtres. Élargis les critères.")
        st.stop()

    # ───────────────────────────────────────
    # ONGLETS RÉSULTATS
    # ───────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["📋 Tableau", "📊 Visualisations", "🗺️ Heatmap"])

    # ── Tab 1 : Tableau ──
    with tab1:
        st.markdown(f"<p class='section-label'>{n_shown} actifs trouvés</p>", unsafe_allow_html=True)

        st.dataframe(
            df_res,
            use_container_width=True,
            hide_index=True,
            column_config={
                "RSI": st.column_config.ProgressColumn(
                    "RSI", min_value=0, max_value=100, format="%.1f"
                ),
                "1J %": st.column_config.NumberColumn(
                    "1J %", format="%.2f%%"
                ),
                "Rendement %": st.column_config.NumberColumn(
                    "Rendement %", format="%.2f%%"
                ),
                "Volatilité %": st.column_config.NumberColumn(
                    "Volatilité %", format="%.2f%%"
                ),
                "Sharpe": st.column_config.NumberColumn(
                    "Sharpe", format="%.2f"
                ),
                "Prix": st.column_config.NumberColumn(
                    "Prix", format="%.2f"
                ),
                "Volume moyen": st.column_config.NumberColumn(
                    "Volume moyen", format="%d"
                ),
            },
            height=500,
        )

        # Export CSV
        col_dl1, col_dl2, _ = st.columns([1, 1, 4])
        with col_dl1:
            csv = df_res.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Exporter CSV",
                data=csv,
                file_name=f"screener_{universe.split('—')[0].strip().replace(' ', '_')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with col_dl2:
            # Export vers Portfolio (session_state)
            if st.button("📁 Envoyer vers Portfolio", use_container_width=True):
                st.session_state["csv_tickers"] = df_res["Ticker"].tolist()
                st.session_state["csv_weights"]  = [1/n_shown] * n_shown
                st.success("✅ Tickers envoyés vers le module Portfolio !")

    # ── Tab 2 : Visualisations ──
    with tab2:
        col1, col2 = st.columns(2)

        with col1:
            # Scatter Rendement vs Volatilité
            st.markdown("<p class='section-label'>Rendement vs Volatilité</p>", unsafe_allow_html=True)
            fig_sc = go.Figure()
            colors_sc = df_res["Rendement %"].apply(lambda v: "#26a69a" if v >= 0 else "#ef5350")
            fig_sc.add_trace(go.Scatter(
                x=df_res["Volatilité %"],
                y=df_res["Rendement %"],
                mode="markers+text",
                text=df_res["Ticker"],
                textposition="top center",
                textfont=dict(size=9, color="#8b9ab0"),
                marker=dict(
                    size=df_res["RSI"].apply(lambda r: max(8, r / 5)),
                    color=df_res["Sharpe"],
                    colorscale="RdYlGn",
                    showscale=True,
                    colorbar=dict(title="Sharpe", tickfont=dict(color="#8b9ab0")),
                    line=dict(color="#2a2d35", width=0.5),
                ),
                name="",
            ))
            fig_sc.add_hline(y=0, line_color="#2a2d35", line_width=1)
            fig_sc.update_layout(
                height=380, paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                font=dict(family="Inter", color="#8b9ab0"),
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(gridcolor="#1e2228", title="Volatilité %", ticksuffix="%"),
                yaxis=dict(gridcolor="#1e2228", title="Rendement %",  ticksuffix="%"),
                showlegend=False,
            )
            st.plotly_chart(fig_sc, use_container_width=True)

        with col2:
            # Barres Rendement
            st.markdown("<p class='section-label'>Rendements classés</p>", unsafe_allow_html=True)
            df_sorted = df_res.sort_values("Rendement %")
            colors_bar = ["#26a69a" if v >= 0 else "#ef5350" for v in df_sorted["Rendement %"]]
            fig_bar = go.Figure(go.Bar(
                x=df_sorted["Rendement %"],
                y=df_sorted["Ticker"],
                orientation="h",
                marker_color=colors_bar,
                text=[f"{v:.1f}%" for v in df_sorted["Rendement %"]],
                textposition="outside",
            ))
            fig_bar.update_layout(
                height=380, paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                font=dict(family="Inter", color="#8b9ab0"),
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(gridcolor="#1e2228", ticksuffix="%"),
                yaxis=dict(gridcolor="#1e2228", tickfont=dict(size=9)),
                showlegend=False,
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        col3, col4 = st.columns(2)

        with col3:
            # RSI distribution
            st.markdown("<p class='section-label'>Distribution RSI</p>", unsafe_allow_html=True)
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Histogram(
                x=df_res["RSI"], nbinsx=20,
                marker_color="#4F46E5", opacity=0.8, name="RSI",
            ))
            fig_rsi.add_vline(x=70, line_dash="dash", line_color="#ef5350", line_width=1,
                              annotation_text="Surachat", annotation_font_color="#ef5350")
            fig_rsi.add_vline(x=30, line_dash="dash", line_color="#26a69a", line_width=1,
                              annotation_text="Survente", annotation_font_color="#26a69a")
            fig_rsi.update_layout(
                height=280, paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                font=dict(family="Inter", color="#8b9ab0"),
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(gridcolor="#1e2228", range=[0, 100]),
                yaxis=dict(gridcolor="#1e2228"),
                showlegend=False,
            )
            st.plotly_chart(fig_rsi, use_container_width=True)

        with col4:
            # Répartition Tendance
            st.markdown("<p class='section-label'>Répartition des tendances</p>", unsafe_allow_html=True)
            trend_counts = df_res["Tendance"].value_counts()
            fig_pie = go.Figure(go.Pie(
                labels=trend_counts.index,
                values=trend_counts.values,
                hole=0.55,
                marker=dict(colors=["#26a69a", "#ef5350", "#f0b429"]),
                textinfo="label+percent",
            ))
            fig_pie.update_layout(
                height=280, paper_bgcolor="#0e1117",
                font=dict(family="Inter", color="#8b9ab0"),
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(bgcolor="rgba(0,0,0,0)"),
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    # ── Tab 3 : Heatmap ──
    with tab3:
        st.markdown("<p class='section-label'>Heatmap — Rendement par actif</p>", unsafe_allow_html=True)

        if len(df_res) >= 2:
            # Heatmap Rendement × RSI
            fig_heat = go.Figure(go.Heatmap(
                z=[df_res["Rendement %"].values, df_res["RSI"].values,
                   df_res["Volatilité %"].values, df_res["Sharpe"].values],
                x=df_res["Ticker"].values,
                y=["Rendement %", "RSI", "Volatilité %", "Sharpe"],
                colorscale="RdYlGn",
                text=np.round([
                    df_res["Rendement %"].values,
                    df_res["RSI"].values,
                    df_res["Volatilité %"].values,
                    df_res["Sharpe"].values,
                ], 2),
                texttemplate="%{text}",
                textfont=dict(size=9),
                colorbar=dict(tickfont=dict(color="#8b9ab0")),
            ))
            fig_heat.update_layout(
                height=320, paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                font=dict(family="Inter", color="#8b9ab0"),
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(tickfont=dict(size=9, color="#e0e0e0")),
                yaxis=dict(tickfont=dict(color="#e0e0e0")),
            )
            st.plotly_chart(fig_heat, use_container_width=True)

            # Bubble chart Sharpe vs RSI
            st.markdown("<p class='section-label'>Sharpe vs RSI (taille = volatilité)</p>", unsafe_allow_html=True)
            fig_bub = go.Figure(go.Scatter(
                x=df_res["RSI"],
                y=df_res["Sharpe"],
                mode="markers+text",
                text=df_res["Ticker"],
                textposition="top center",
                textfont=dict(size=9, color="#8b9ab0"),
                marker=dict(
                    size=df_res["Volatilité %"].apply(lambda v: max(8, v / 3)),
                    color=df_res["Rendement %"],
                    colorscale="RdYlGn",
                    showscale=True,
                    colorbar=dict(title="Rdt %", tickfont=dict(color="#8b9ab0")),
                    line=dict(color="#2a2d35", width=0.5),
                ),
            ))
            fig_bub.add_vline(x=70, line_dash="dash", line_color="#ef5350", line_width=1, opacity=0.5)
            fig_bub.add_vline(x=30, line_dash="dash", line_color="#26a69a", line_width=1, opacity=0.5)
            fig_bub.add_hline(y=0,  line_dash="dash", line_color="#f0b429", line_width=1, opacity=0.5)
            fig_bub.update_layout(
                height=380, paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                font=dict(family="Inter", color="#8b9ab0"),
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(gridcolor="#1e2228", title="RSI", range=[0, 100]),
                yaxis=dict(gridcolor="#1e2228", title="Sharpe"),
                showlegend=False,
            )
            st.plotly_chart(fig_bub, use_container_width=True)
        else:
            st.info("Besoin d'au moins 2 actifs pour la heatmap.")

else:
    st.info("⚙️ Configure les filtres dans la sidebar et clique sur **LANCER LE SCREENER**.")


st.divider()
st.markdown(
    "<p class='caption' style='text-align:center;'>AlphaDesk v1.0 &nbsp;·&nbsp; Screener · Yahoo Finance</p>",
    unsafe_allow_html=True,
)
