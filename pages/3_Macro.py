import sys
_os = __import__("os")
ROOT_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)
from utils.ai_assistant import render_chat_widget, build_context

render_chat_widget("macro")

# pages/3_Macro.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from dotenv import load_dotenv
from fredapi import Fred

load_dotenv(override=True)

FRED_KEY = os.getenv("FRED_KEY")
if not FRED_KEY:
    st.error("⚠️ Clé FRED manquante — ajoute FRED_KEY dans ton fichier .env")
    st.stop()

fred = Fred(api_key=FRED_KEY)

# ───────────────────────────────────────
# CONFIG
# ───────────────────────────────────────
st.set_page_config(
    page_title="AlphaDesk · Macro",
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
    .recession-card {
        background: #1c1f26;
        border: 1px solid #2a2d35;
        border-radius: 10px;
        padding: 18px 22px;
        margin-bottom: 10px;
    }
    .indicator-label {
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #8b9ab0;
        margin-bottom: 4px;
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
    div.stButton > button {
        background-color: #4F46E5 !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
    }
    div.stButton > button:hover { background-color: #4338ca !important; }
    </style>
""", unsafe_allow_html=True)


# ───────────────────────────────────────
# HEADER
# ───────────────────────────────────────
st.markdown("""
<div style='padding: 30px 0 10px 0; text-align: center;'>
    <div style='font-size:2.2rem; font-weight:800; color:#ffffff; letter-spacing:-0.04em;'>
        Alpha<span style='color:#4F46E5;'>Desk</span>
        <span style='font-size:1.1rem; font-weight:500; color:#8b9ab0; margin-left:12px;'>/ Macro</span>
    </div>
    <p style='color:#8b9ab0; font-size:0.88rem; margin-top:8px;'>
        Taux · Inflation · PIB · Courbe des taux · Emploi · Banques centrales
    </p>
</div>
""", unsafe_allow_html=True)

st.divider()


# ───────────────────────────────────────
# HELPERS
# ───────────────────────────────────────
@st.cache_data(ttl=86400, show_spinner=False)
def get_fred(series_id: str, start: str = "2000-01-01") -> pd.Series:
    try:
        return fred.get_series(series_id, observation_start=start).dropna()
    except:
        return pd.Series(dtype=float)

def last(s):
    try:    return float(s.iloc[-1])
    except: return None

def delta(s):
    try:    return float(s.iloc[-1]) - float(s.iloc[-2])
    except: return None

def fmt(v, suffix="", dec=2):
    if v is None: return "—"
    return f"{v:.{dec}f}{suffix}"

def base_layout(h=350):
    return dict(
        height=h,
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        font=dict(family="Inter", color="#8b9ab0"),
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(gridcolor="#1e2228", showgrid=True, zeroline=False),
        yaxis=dict(gridcolor="#1e2228", showgrid=True, zeroline=False),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        hovermode="x unified",
    )

def line_chart(series_dict: dict, colors: list, h=320, tick_suffix="", fill=False) -> go.Figure:
    fig = go.Figure()
    for (name, s), color in zip(series_dict.items(), colors):
        if s.empty: continue
        fig.add_trace(go.Scatter(
            x=s.index, y=s.values, name=name,
            line=dict(color=color, width=2),
            fill="tozeroy" if fill else None,
            fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.05)" if fill else None,
        ))
    L = base_layout(h)
    L["yaxis"]["ticksuffix"] = tick_suffix
    fig.update_layout(L)
    return fig


# ───────────────────────────────────────
# CHARGEMENT FRED
# ───────────────────────────────────────
with st.spinner("Chargement des données FRED..."):
    fed   = get_fred("FEDFUNDS")
    cpi   = get_fred("CPIAUCSL")
    unemp = get_fred("UNRATE")
    vix   = get_fred("VIXCLS")
    gdp   = get_fred("GDP")
    m2    = get_fred("M2SL")
    pce   = get_fred("PCEPILFE")
    umcs  = get_fred("UMCSENT")
    nfp   = get_fred("PAYEMS")


# ───────────────────────────────────────
# MÉTRIQUES HEADER
# ───────────────────────────────────────
st.markdown("<p class='section-label'>Indicateurs clés</p>", unsafe_allow_html=True)

cpi_yoy = cpi.pct_change(12).dropna() * 100

c1,c2,c3,c4,c5,c6,c7 = st.columns(7)
c1.metric("Fed Funds",   fmt(last(fed),  "%"),    fmt(delta(fed),  "%", 2))
c2.metric("CPI YoY",     fmt(last(cpi_yoy), "%"), fmt(delta(cpi_yoy), "%", 2))
c3.metric("Chômage",     fmt(last(unemp), "%"),   fmt(delta(unemp), "%", 2))
c4.metric("VIX",         fmt(last(vix)),           fmt(delta(vix)))
c5.metric("PIB US",      f"${last(gdp)/1000:.1f}T" if last(gdp) else "—")
c6.metric("M2 (Mds)",    fmt(last(m2)))
c7.metric("UMich Conf.", fmt(last(umcs)))

st.divider()


# ───────────────────────────────────────
# ONGLETS
# ───────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 Taux & Inflation",
    "📊 PIB & Conso",
    "📉 Courbe des taux",
    "👷 Emploi",
    "🏦 Banques centrales",
    "⚠️ Récession",
])


# ── Tab 1 : Taux & Inflation ──
with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<p class='section-label'>Fed Funds Rate</p>", unsafe_allow_html=True)
        fig1 = line_chart({"Fed Funds": fed}, ["#4fc3f7"], fill=True, tick_suffix="%")
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.markdown("<p class='section-label'>Inflation US YoY (CPI)</p>", unsafe_allow_html=True)
        fig2 = line_chart({"CPI YoY": cpi_yoy}, ["#f0b429"], fill=True, tick_suffix="%")
        fig2.add_hline(y=2, line_dash="dash", line_color="#26a69a", line_width=1, opacity=0.6,
                       annotation_text="Cible 2%", annotation_font_color="#26a69a")
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("<p class='section-label'>PCE Core YoY</p>", unsafe_allow_html=True)
        pce_yoy = pce.pct_change(12).dropna() * 100
        fig3 = line_chart({"PCE Core": pce_yoy}, ["#ce93d8"], fill=True, tick_suffix="%")
        fig3.add_hline(y=2, line_dash="dash", line_color="#26a69a", line_width=1, opacity=0.6,
                       annotation_text="Cible 2%", annotation_font_color="#26a69a")
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.markdown("<p class='section-label'>M2 Money Supply</p>", unsafe_allow_html=True)
        fig4 = line_chart({"M2": m2}, ["#ff7043"], fill=True)
        st.plotly_chart(fig4, use_container_width=True)


# ── Tab 2 : PIB & Conso ──
with tab2:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<p class='section-label'>Croissance PIB YoY</p>", unsafe_allow_html=True)
        gdp_yoy = gdp.pct_change(4).dropna() * 100
        colors_gdp = ["#26a69a" if v >= 0 else "#ef5350" for v in gdp_yoy.values]
        fig5 = go.Figure(go.Bar(x=gdp_yoy.index, y=gdp_yoy.values, marker_color=colors_gdp, name="PIB YoY"))
        L5 = base_layout()
        L5["yaxis"]["ticksuffix"] = "%"
        fig5.update_layout(L5)
        st.plotly_chart(fig5, use_container_width=True)

    with col2:
        st.markdown("<p class='section-label'>Confiance consommateurs (UMich)</p>", unsafe_allow_html=True)
        fig6 = line_chart({"UMich": umcs}, ["#4fc3f7"])
        st.plotly_chart(fig6, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("<p class='section-label'>PIB nominal US (Mds $)</p>", unsafe_allow_html=True)
        fig7 = line_chart({"PIB": gdp}, ["#26a69a"], fill=True)
        st.plotly_chart(fig7, use_container_width=True)

    with col4:
        st.markdown("<p class='section-label'>M2 YoY (Masse monétaire)</p>", unsafe_allow_html=True)
        m2_yoy = m2.pct_change(12).dropna() * 100
        colors_m2 = ["#26a69a" if v >= 0 else "#ef5350" for v in m2_yoy.values]
        fig8 = go.Figure(go.Bar(x=m2_yoy.index, y=m2_yoy.values, marker_color=colors_m2, name="M2 YoY"))
        L8 = base_layout()
        L8["yaxis"]["ticksuffix"] = "%"
        fig8.update_layout(L8)
        st.plotly_chart(fig8, use_container_width=True)


# ── Tab 3 : Courbe des taux ──
with tab3:
    st.markdown("<p class='section-label'>Courbe des taux US — snapshot actuel</p>", unsafe_allow_html=True)

    MATS = {"3M": "DTB3", "6M": "DGS6MO", "1Y": "DGS1", "2Y": "DGS2",
            "5Y": "DGS5", "7Y": "DGS7", "10Y": "DGS10", "20Y": "DGS20", "30Y": "DGS30"}

    yields = {}
    for label, code in MATS.items():
        s = get_fred(code, start="2020-01-01")
        if not s.empty:
            yields[label] = float(s.iloc[-1])

    if yields:
        fig_yc = go.Figure()
        fig_yc.add_trace(go.Scatter(
            x=list(yields.keys()), y=list(yields.values()),
            mode="lines+markers",
            line=dict(color="#4fc3f7", width=2.5),
            marker=dict(size=9, color="#4fc3f7"),
            fill="tozeroy", fillcolor="rgba(79,195,247,0.05)",
            name="Taux actuels",
        ))
        L_yc = base_layout(h=380)
        L_yc["xaxis"]["title"] = "Maturité"
        L_yc["yaxis"]["ticksuffix"] = "%"
        L_yc["yaxis"]["title"] = "Rendement"
        fig_yc.update_layout(L_yc)
        st.plotly_chart(fig_yc, use_container_width=True)

        spread = yields.get("10Y", 0) - yields.get("2Y", 0)
        spread_3m = yields.get("10Y", 0) - yields.get("3M", 0)

        ca, cb, cc, cd = st.columns(4)
        ca.metric("Spread 10Y-2Y",  f"{spread:.2f}%",    delta_color="normal")
        cb.metric("Spread 10Y-3M",  f"{spread_3m:.2f}%", delta_color="normal")
        cc.metric("10Y",            f"{yields.get('10Y',0):.2f}%")
        cd.metric("2Y",             f"{yields.get('2Y',0):.2f}%")

        if spread < 0:
            st.warning("⚠️ **Courbe inversée** (10Y < 2Y) — signal historique de récession.")
        elif spread < 0.5:
            st.info("ℹ️ Spread très faible — courbe quasi plate, marché prudent.")
        else:
            st.success("✅ Courbe normale — spread positif.")


# ── Tab 4 : Emploi ──
with tab4:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<p class='section-label'>Taux de chômage US</p>", unsafe_allow_html=True)
        fig_u = line_chart({"Chômage": unemp}, ["#ef5350"], fill=True, tick_suffix="%")
        st.plotly_chart(fig_u, use_container_width=True)

    with col2:
        st.markdown("<p class='section-label'>NFP — Créations d'emplois (60 mois)</p>", unsafe_allow_html=True)
        nfp_chg = nfp.diff().dropna().iloc[-60:]
        colors_nfp = ["#26a69a" if v >= 0 else "#ef5350" for v in nfp_chg.values]
        fig_nfp = go.Figure(go.Bar(
            x=nfp_chg.index, y=nfp_chg.values,
            marker_color=colors_nfp, name="NFP MoM"
        ))
        fig_nfp.update_layout(base_layout())
        st.plotly_chart(fig_nfp, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("<p class='section-label'>Emploi total (PAYEMS)</p>", unsafe_allow_html=True)
        fig_pay = line_chart({"PAYEMS": nfp}, ["#4fc3f7"], fill=True)
        st.plotly_chart(fig_pay, use_container_width=True)

    with col4:
        st.markdown("<p class='section-label'>Taux de participation</p>", unsafe_allow_html=True)
        civpart = get_fred("CIVPART")
        fig_civ = line_chart({"Participation": civpart}, ["#f0b429"], tick_suffix="%")
        st.plotly_chart(fig_civ, use_container_width=True)


# ── Tab 5 : Banques centrales ──
with tab5:
    st.markdown("<p class='section-label'>Taux directeurs — Fed · BoE · SNB</p>", unsafe_allow_html=True)

    CB = {
        "Fed (US)": ("FEDFUNDS",            "#4fc3f7"),
        "BoE (UK)": ("IUDSOIA",             "#f0b429"),
        "SNB (CH)": ("IRSTCB01CHM156N",     "#26a69a"),
    }

    fig_cb = go.Figure()
    for name, (code, color) in CB.items():
        s = get_fred(code, start="2000-01-01")
        if not s.empty:
            fig_cb.add_trace(go.Scatter(
                x=s.index, y=s.values, name=name,
                line=dict(color=color, width=2)
            ))

    L_cb = base_layout(h=420)
    L_cb["yaxis"]["ticksuffix"] = "%"
    fig_cb.update_layout(L_cb)
    st.plotly_chart(fig_cb, use_container_width=True)

    st.info("ℹ️ BCE : données disponibles sur [data.ecb.europa.eu](https://data.ecb.europa.eu)")

    # Tableau comparatif
    st.markdown("<p class='section-label'>Comparatif actuel</p>", unsafe_allow_html=True)
    cb_rows = []
    for name, (code, _) in CB.items():
        s = get_fred(code)
        if not s.empty:
            cb_rows.append({
                "Banque": name,
                "Taux actuel": f"{float(s.iloc[-1]):.2f}%",
                "Précédent": f"{float(s.iloc[-2]):.2f}%" if len(s) > 1 else "—",
                "Variation": f"{float(s.iloc[-1]) - float(s.iloc[-2]):+.2f}%" if len(s) > 1 else "—",
            })
    if cb_rows:
        import pandas as pd
        st.dataframe(pd.DataFrame(cb_rows), use_container_width=True, hide_index=True)


# ── Tab 6 : Récession (NOUVEAU) ──
with tab6:
    st.markdown("<p class='section-label'>Indicateurs de récession</p>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        # Probabilité de récession FRED
        st.markdown("<p class='section-label'>Probabilité de récession (FRED)</p>", unsafe_allow_html=True)
        rec_prob = get_fred("RECPROUSM156N", start="2000-01-01")
        if not rec_prob.empty:
            fig_rec = go.Figure()
            fig_rec.add_trace(go.Scatter(
                x=rec_prob.index, y=rec_prob.values,
                name="Proba récession",
                line=dict(color="#ef5350", width=2),
                fill="tozeroy", fillcolor="rgba(239,83,80,0.1)",
            ))
            fig_rec.add_hline(y=50, line_dash="dash", line_color="#f0b429",
                              line_width=1, annotation_text="Seuil 50%",
                              annotation_font_color="#f0b429")
            L_r = base_layout()
            L_r["yaxis"]["ticksuffix"] = "%"
            fig_rec.update_layout(L_r)
            st.plotly_chart(fig_rec, use_container_width=True)

    with col2:
        # Spread 10Y-2Y historique
        st.markdown("<p class='section-label'>Spread 10Y - 2Y (historique)</p>", unsafe_allow_html=True)
        dgs10 = get_fred("DGS10", start="2000-01-01")
        dgs2  = get_fred("DGS2",  start="2000-01-01")
        if not dgs10.empty and not dgs2.empty:
            spread_hist = (dgs10 - dgs2).dropna()
            colors_sp = ["#26a69a" if v >= 0 else "#ef5350" for v in spread_hist.values]
            fig_sp = go.Figure(go.Bar(
                x=spread_hist.index, y=spread_hist.values,
                marker_color=colors_sp, name="Spread 10Y-2Y"
            ))
            fig_sp.add_hline(y=0, line_color="#ffffff", line_width=1, opacity=0.3)
            L_sp = base_layout()
            L_sp["yaxis"]["ticksuffix"] = "%"
            fig_sp.update_layout(L_sp)
            st.plotly_chart(fig_sp, use_container_width=True)

    # Score de récession
    st.markdown("<p class='section-label'>Score de risque macroéconomique</p>", unsafe_allow_html=True)

    score = 0
    signals_list = []

    spread_val = yields.get("10Y", 0) - yields.get("2Y", 0) if yields else 1
    if spread_val < 0:
        score += 2
        signals_list.append(("🔴", "Courbe inversée (10Y < 2Y)", "Signal fort de récession"))
    elif spread_val < 0.5:
        score += 1
        signals_list.append(("🟡", "Spread très faible", "Marché prudent"))
    else:
        signals_list.append(("🟢", "Courbe normale", "Pas de signal d'inversion"))

    unemp_delta = delta(unemp)
    if unemp_delta and unemp_delta > 0.3:
        score += 2
        signals_list.append(("🔴", "Chômage en hausse rapide", f"+{unemp_delta:.2f}% ce mois"))
    else:
        signals_list.append(("🟢", "Chômage stable", "Pas de signal"))

    cpi_val = last(cpi_yoy)
    if cpi_val and cpi_val > 5:
        score += 1
        signals_list.append(("🟡", f"Inflation élevée ({cpi_val:.1f}%)", "Risque de resserrement monétaire"))
    else:
        signals_list.append(("🟢", f"Inflation sous contrôle ({cpi_val:.1f}%)" if cpi_val else "Inflation N/A", ""))

    if not rec_prob.empty and float(rec_prob.iloc[-1]) > 30:
        score += 2
        signals_list.append(("🔴", f"Proba récession FRED élevée ({float(rec_prob.iloc[-1]):.0f}%)", "Signal fort"))
    elif not rec_prob.empty:
        signals_list.append(("🟢", f"Proba récession FRED faible ({float(rec_prob.iloc[-1]):.0f}%)", ""))

    # Affichage score global
    max_score = 7
    risk_pct = min(score / max_score * 100, 100)
    risk_color = "#26a69a" if score <= 2 else "#f0b429" if score <= 4 else "#ef5350"
    risk_label = "FAIBLE" if score <= 2 else "MODÉRÉ" if score <= 4 else "ÉLEVÉ"

    st.markdown(f"""
    <div class='recession-card'>
        <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;'>
            <div>
                <div class='indicator-label'>Risque macroéconomique global</div>
                <div style='font-size:1.6rem; font-weight:800; color:{risk_color};'>{risk_label}</div>
            </div>
            <div style='text-align:right;'>
                <div class='indicator-label'>Score</div>
                <div style='font-size:1.6rem; font-weight:800; color:{risk_color};'>{score}/{max_score}</div>
            </div>
        </div>
        <div style='background:#2a2d35; border-radius:4px; height:6px; overflow:hidden;'>
            <div style='width:{risk_pct}%; height:6px; background:{risk_color}; border-radius:4px;'></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    for icon, label, detail in signals_list:
        detail_html = f"<div style='color:#8b9ab0; font-size:0.75rem;'>{detail}</div>" if detail != "" else ""

        html_string = f"<div style='display:flex; align-items:center; gap:12px; padding:10px 16px; background:#1c1f26; border-radius:8px; margin-bottom:6px; border:1px solid #2a2d35;'><span style='font-size:1.1rem;'>{icon}</span><div><div style='color:#e0e0e0; font-size:0.88rem; font-weight:600;'>{label}</div>{detail_html}</div></div>"

        st.markdown(html_string, unsafe_allow_html=True)


st.divider()
st.markdown(
    "<p class='caption' style='text-align:center;'>AlphaDesk v1.0 &nbsp;·&nbsp; FRED API · Macro</p>",
    unsafe_allow_html=True,
)
