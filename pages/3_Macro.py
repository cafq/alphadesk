import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from dotenv import load_dotenv
from fredapi import Fred

load_dotenv(override=True)

FRED_KEY = os.getenv("FRED_KEY")
if not FRED_KEY:
    st.error("Clé FRED manquante — ajoute FRED_KEY dans ton fichier .env")
    st.stop()

fred = Fred(api_key=FRED_KEY)

st.set_page_config(page_title="Macro — AlphaDesk", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    section[data-testid="stSidebar"] { background-color: #13161d; border-right: 1px solid #2a2d35; }
    h1, h2, h3 { color: #ffffff !important; font-weight: 600 !important; }
    .stMetric { background-color: #1c1f26; padding: 14px; border-radius: 8px; border: 1px solid #2a2d35; }
    .stMetric label { color: #8b9ab0 !important; font-size: 0.75rem !important; text-transform: uppercase; }
    </style>
""", unsafe_allow_html=True)

st.markdown("## Macro")
st.markdown("<p style='color:#8b9ab0; font-size:0.85rem; margin-top:-10px;'>Taux · Inflation · PIB · Courbe des taux · Emploi</p>", unsafe_allow_html=True)
st.divider()

@st.cache_data(ttl=86400, show_spinner=False)
def get_fred(series_id, start="2005-01-01"):
    try:
        return fred.get_series(series_id, observation_start=start).dropna()
    except:
        return pd.Series(dtype=float)

def last(s):
    try: return float(s.iloc[-1])
    except: return None

def delta(s):
    try: return float(s.iloc[-1]) - float(s.iloc[-2])
    except: return None

def fmt(v, suffix="", dec=2):
    if v is None: return "—"
    return f"{v:.{dec}f}{suffix}"

def base_layout(h=300):
    return dict(
        height=h,
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        font=dict(family="Inter", color="#8b9ab0"),
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(gridcolor="#1e2228"),
        yaxis=dict(gridcolor="#1e2228"),
        legend=dict(bgcolor="rgba(0,0,0,0)")
    )

# ── Chargement initial ───────────────────────────────────────────────
with st.spinner("Chargement FRED..."):
    fed   = get_fred("FEDFUNDS")
    cpi   = get_fred("CPIAUCSL")
    unemp = get_fred("UNRATE")
    vix   = get_fred("VIXCLS")
    gdp   = get_fred("GDP")
    m2    = get_fred("M2SL")

# ── Métriques ────────────────────────────────────────────────────────
st.markdown("### Indicateurs clés")
c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.metric("Fed Funds",  fmt(last(fed),   "%"), fmt(delta(fed)))
c2.metric("CPI",        fmt(last(cpi)),        "—")
c3.metric("Chômage",    fmt(last(unemp), "%"), fmt(delta(unemp)))
c4.metric("VIX",        fmt(last(vix)),        fmt(delta(vix)))
c5.metric("PIB US",     fmt(last(gdp)),        "—")
c6.metric("M2 (Mds$)",  fmt(last(m2)),         "—")
st.divider()

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Taux & Inflation", "PIB & Conso", "Courbe des taux", "Emploi", "Banques centrales"])

# ── Tab 1 : Taux & Inflation ─────────────────────────────────────────
with tab1:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Fed Funds Rate")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=fed.index, y=fed.values, name="Fed Funds",
                                 line=dict(color="#4fc3f7", width=2),
                                 fill="tozeroy", fillcolor="rgba(79,195,247,0.05)"))
        L = base_layout()
        L["yaxis"]["ticksuffix"] = "%"
        fig.update_layout(**L)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Inflation US YoY (CPI)")
        cpi_yoy = cpi.pct_change(12).dropna() * 100
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=cpi_yoy.index, y=cpi_yoy.values, name="CPI YoY",
                                  line=dict(color="#f0b429", width=2),
                                  fill="tozeroy", fillcolor="rgba(240,180,41,0.05)"))
        fig2.add_hline(y=2, line_dash="dash", line_color="#26a69a", line_width=1, opacity=0.6)
        L2 = base_layout()
        L2["yaxis"]["ticksuffix"] = "%"
        fig2.update_layout(**L2)
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("#### PCE Core YoY")
        pce = get_fred("PCEPILFE")
        pce_yoy = pce.pct_change(12).dropna() * 100
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=pce_yoy.index, y=pce_yoy.values, name="PCE Core",
                                  line=dict(color="#ce93d8", width=2)))
        fig3.add_hline(y=2, line_dash="dash", line_color="#26a69a", line_width=1, opacity=0.6)
        L3 = base_layout()
        L3["yaxis"]["ticksuffix"] = "%"
        fig3.update_layout(**L3)
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.markdown("#### M2 Money Supply")
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(x=m2.index, y=m2.values, name="M2",
                                  line=dict(color="#ff7043", width=2),
                                  fill="tozeroy", fillcolor="rgba(255,112,67,0.05)"))
        fig4.update_layout(**base_layout())
        st.plotly_chart(fig4, use_container_width=True)

# ── Tab 2 : PIB & Conso ──────────────────────────────────────────────
with tab2:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Croissance PIB YoY")
        gdp_yoy = gdp.pct_change(4).dropna() * 100
        colors  = ["#26a69a" if v >= 0 else "#ef5350" for v in gdp_yoy.values]
        fig5 = go.Figure()
        fig5.add_trace(go.Bar(x=gdp_yoy.index, y=gdp_yoy.values,
                              marker_color=colors, name="PIB YoY"))
        L5 = base_layout()
        L5["yaxis"]["ticksuffix"] = "%"
        fig5.update_layout(**L5)
        st.plotly_chart(fig5, use_container_width=True)

    with col2:
        st.markdown("#### Confiance consommateurs (UMich)")
        umcs = get_fred("UMCSENT")
        fig6 = go.Figure()
        fig6.add_trace(go.Scatter(x=umcs.index, y=umcs.values, name="UMich",
                                  line=dict(color="#4fc3f7", width=2)))
        fig6.update_layout(**base_layout())
        st.plotly_chart(fig6, use_container_width=True)

# ── Tab 3 : Courbe des taux ──────────────────────────────────────────
with tab3:
    st.markdown("#### Courbe des taux US (snapshot actuel)")
    MATS = {"3M": "DTB3", "2Y": "DGS2", "5Y": "DGS5", "10Y": "DGS10", "30Y": "DGS30"}
    yields = {}
    for label, code in MATS.items():
        s = get_fred(code, start="2020-01-01")
        if not s.empty:
            yields[label] = float(s.iloc[-1])

    if yields:
        fig7 = go.Figure()
        fig7.add_trace(go.Scatter(
            x=list(yields.keys()), y=list(yields.values()),
            mode="lines+markers",
            line=dict(color="#4fc3f7", width=2),
            marker=dict(size=9, color="#4fc3f7"),
            fill="tozeroy", fillcolor="rgba(79,195,247,0.05)"
        ))
        L7 = base_layout(h=350)
        L7["xaxis"]["title"] = "Maturité"
        L7["yaxis"]["ticksuffix"] = "%"
        L7["yaxis"]["title"] = "Rendement"
        fig7.update_layout(**L7)
        st.plotly_chart(fig7, use_container_width=True)

        spread = yields.get("10Y", 0) - yields.get("2Y", 0)
        ca, cb, cc = st.columns(3)
        ca.metric("Spread 10Y-2Y", f"{spread:.2f}%")
        cb.metric("10Y", f"{yields.get('10Y', 0):.2f}%")
        cc.metric("2Y",  f"{yields.get('2Y',  0):.2f}%")
        if spread < 0:
            st.warning("⚠️ Courbe inversée — signal historique de récession.")

# ── Tab 4 : Emploi ───────────────────────────────────────────────────
with tab4:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Taux de chômage US")
        fig8 = go.Figure()
        fig8.add_trace(go.Scatter(x=unemp.index, y=unemp.values, name="Chômage",
                                  line=dict(color="#ef5350", width=2),
                                  fill="tozeroy", fillcolor="rgba(239,83,80,0.05)"))
        L8 = base_layout()
        L8["yaxis"]["ticksuffix"] = "%"
        fig8.update_layout(**L8)
        st.plotly_chart(fig8, use_container_width=True)

    with col2:
        st.markdown("#### NFP — Créations d'emplois (60 mois)")
        nfp     = get_fred("PAYEMS")
        nfp_chg = nfp.diff().dropna().iloc[-60:]
        colors  = ["#26a69a" if v >= 0 else "#ef5350" for v in nfp_chg.values]
        fig9 = go.Figure()
        fig9.add_trace(go.Bar(x=nfp_chg.index, y=nfp_chg.values,
                              marker_color=colors, name="NFP MoM"))
        fig9.update_layout(**base_layout())
        st.plotly_chart(fig9, use_container_width=True)

# ── Tab 5 : Banques centrales ────────────────────────────────────────
with tab5:
    st.markdown("#### Taux directeurs — Fed / BoE / SNB")
    CB = {
        "Fed (US)": ("FEDFUNDS",        "#4fc3f7"),
        "BoE (UK)": ("IUDSOIA",         "#f0b429"),
        "SNB (CH)": ("IRSTCB01CHM156N", "#26a69a"),
    }
    fig10 = go.Figure()
    for name, (code, color) in CB.items():
        s = get_fred(code, start="2000-01-01")
        if not s.empty:
            fig10.add_trace(go.Scatter(x=s.index, y=s.values, name=name,
                                       line=dict(color=color, width=2)))
    L10 = base_layout(h=400)
    L10["yaxis"]["ticksuffix"] = "%"
    fig10.update_layout(**L10)
    st.plotly_chart(fig10, use_container_width=True)
    st.info("BCE : données disponibles sur data.ecb.europa.eu")
