# pages/8_ESG.py

import streamlit as st
import sqlite3
import pandas as pd
import os
import yfinance as yf

# ───────────────────────────────────────
# CONFIG
# ───────────────────────────────────────
st.set_page_config(
    page_title="AlphaDesk · ESG",
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
    .stMetric {
        background-color: #1c1f26;
        padding: 16px;
        border-radius: 8px;
        border: 1px solid #2a2d35;
    }
    .stMetric label {
        color: #8b9ab0 !important;
        font-size: 0.7rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
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
    .esg-card {
        background: #1c1f26;
        border: 1px solid #2a2d35;
        border-radius: 10px;
        padding: 20px 24px;
        margin-bottom: 10px;
    }
    .esg-ticker { font-size: 1.0rem; font-weight: 700; color: #ffffff; letter-spacing: -0.01em; }
    .esg-sector { font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 2px; }
    .esg-label { font-size: 0.68rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: #555e6e; margin-bottom: 4px; }
    .esg-score { font-size: 1.1rem; font-weight: 700; color: #e0e0e0; }
    .esg-bar-wrap { background: #2a2d35; border-radius: 4px; height: 5px; margin-top: 6px; overflow: hidden; }
    .esg-bar-fill { height: 5px; border-radius: 4px; }
    .section-label { color: #8b9ab0; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 14px; }
    .api-badge {
        display: inline-block;
        font-size: 0.62rem;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 20px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-left: 8px;
        vertical-align: middle;
    }
    .badge-auto { background: #1a3a2a; color: #22c55e; border: 1px solid #22c55e44; }
    .badge-manual { background: #1e1e2e; color: #8b9ab0; border: 1px solid #2a2d35; }
    </style>
""", unsafe_allow_html=True)


# ───────────────────────────────────────
# HEADER
# ───────────────────────────────────────
st.markdown("""
<div style='padding: 30px 0 10px 0; text-align: center;'>
    <div style='font-size:2.2rem; font-weight:800; color:#ffffff; letter-spacing:-0.04em;'>
        Alpha<span style='color:#4F46E5;'>Desk</span>
        <span style='font-size:1.1rem; font-weight:500; color:#8b9ab0; margin-left:12px;'>/ ESG & Éthique</span>
    </div>
    <p style='color:#8b9ab0; font-size:0.88rem; margin-top:8px;'>
        Investis selon tes valeurs — scores environnementaux, sociaux & gouvernance
    </p>
</div>
""", unsafe_allow_html=True)

st.divider()


# ───────────────────────────────────────
# BASE DE DONNÉES
# ───────────────────────────────────────
def get_esg_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect("data/esg_data.db", check_same_thread=False)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS esg_profiles (
            ticker              TEXT PRIMARY KEY,
            environment_score   REAL NOT NULL,
            social_score        REAL NOT NULL,
            governance_score    REAL NOT NULL,
            total_esg_score     REAL NOT NULL,
            sector              TEXT NOT NULL,
            source              TEXT DEFAULT 'manual'
        )
    """)

    # ── MIGRATION : ajoute 'source' si ancienne DB sans cette colonne ──
    existing_cols = [
        row[1] for row in conn.execute("PRAGMA table_info(esg_profiles)").fetchall()
    ]
    if "source" not in existing_cols:
        conn.execute("ALTER TABLE esg_profiles ADD COLUMN source TEXT DEFAULT 'manual'")
        conn.commit()

    conn.execute("""
        INSERT OR IGNORE INTO esg_profiles VALUES
        ('AAPL',  75, 80, 78, 77.7, 'tech',         'manual'),
        ('GOOGL', 78, 75, 80, 77.7, 'tech',         'manual'),
        ('MSFT',  82, 79, 85, 82.0, 'tech',         'manual'),
        ('TSLA',  65, 70, 68, 67.7, 'clean_energy', 'manual'),
        ('ENPH',  88, 76, 74, 79.3, 'clean_energy', 'manual'),
        ('XOM',   30, 40, 50, 40.0, 'fossil_fuel',  'manual'),
        ('CVX',   25, 35, 45, 35.0, 'fossil_fuel',  'manual'),
        ('BA',    35, 50, 60, 48.3, 'defense',      'manual'),
        ('RTX',   32, 48, 58, 46.0, 'defense',      'manual'),
        ('MO',    20, 38, 55, 37.7, 'tobacco',      'manual'),
        ('JNJ',   70, 72, 75, 72.3, 'healthcare',   'manual'),
        ('MC.PA', 55, 60, 65, 60.0, 'luxury',       'manual')
    """)
    conn.commit()
    return conn


def load_esg_profiles():
    conn = get_esg_db()
    df = pd.read_sql("SELECT * FROM esg_profiles ORDER BY total_esg_score DESC", conn)
    conn.close()
    return df

def save_esg(ticker, env, soc, gov, sector, source="manual"):
    total = round((env + soc + gov) / 3, 1)
    conn = get_esg_db()
    conn.execute(
        "INSERT OR REPLACE INTO esg_profiles VALUES (?, ?, ?, ?, ?, ?, ?)",
        (ticker.upper(), env, soc, gov, total, sector.lower(), source)
    )
    conn.commit()
    conn.close()
    return total

def score_color(score):
    if score >= 70: return "#22c55e"
    elif score >= 50: return "#f59e0b"
    else: return "#ef4444"

def sector_color(sector):
    return {
        "tech": "#4F46E5", "clean_energy": "#22c55e",
        "fossil_fuel": "#ef4444", "defense": "#f59e0b",
        "tobacco": "#f97316", "alcohol": "#a855f7",
        "healthcare": "#06b6d4", "luxury": "#ec4899",
        "gaming": "#8b5cf6", "others": "#8b9ab0",
    }.get(sector, "#8b9ab0")


# ───────────────────────────────────────
# FETCH ESG DEPUIS YFINANCE
# ───────────────────────────────────────
def fetch_esg_from_yfinance(ticker: str):
    """
    Récupère les données ESG via yfinance.sustainability
    Retourne un dict avec env/social/gov/total/sector ou None si indisponible.
    """
    try:
        t = yf.Ticker(ticker)
        sus = t.sustainability

        if sus is None or sus.empty:
            return None

        # yfinance renvoie un DataFrame avec des index comme
        # 'environmentScore', 'socialScore', 'governanceScore', 'totalEsg'
        def get_val(key):
            try:
                val = sus.loc[key].values[0]
                # yfinance donne des scores sur ~30 max, on normalise sur 100
                return round(float(val) * (100 / 30), 1) if val else None
            except:
                return None

        env   = get_val("environmentScore")
        soc   = get_val("socialScore")
        gov   = get_val("governanceScore")
        total = get_val("totalEsg")

        if not any([env, soc, gov]):
            return None

        env   = env   or 50.0
        soc   = soc   or 50.0
        gov   = gov   or 50.0
        total = total or round((env + soc + gov) / 3, 1)

        # Secteur via info
        info   = t.info
        sector_raw = info.get("sector", "others").lower()
        sector_map = {
            "technology": "tech",
            "energy": "fossil_fuel",
            "utilities": "clean_energy",
            "healthcare": "healthcare",
            "industrials": "defense",
            "consumer defensive": "others",
            "financial services": "others",
            "basic materials": "others",
            "communication services": "tech",
            "consumer cyclical": "luxury",
            "real estate": "others",
        }
        sector = sector_map.get(sector_raw, "others")

        return {
            "env": min(env, 100.0),
            "soc": min(soc, 100.0),
            "gov": min(gov, 100.0),
            "total": min(total, 100.0),
            "sector": sector,
        }
    except Exception:
        return None


# ───────────────────────────────────────
# RECHERCHE / AJOUT VIA API
# ───────────────────────────────────────
st.markdown("<p class='section-label'>🔎 Rechercher un actif</p>", unsafe_allow_html=True)

search_col1, search_col2 = st.columns([4, 1])
with search_col1:
    search_ticker = st.text_input(
        "search",
        placeholder="Ex: AAPL, MSFT, TTE.PA, JNJ...",
        label_visibility="collapsed",
    )
with search_col2:
    search_btn = st.button("Rechercher", use_container_width=True)

if search_btn and search_ticker:
    ticker_clean = search_ticker.upper().strip()
    with st.spinner(f"Récupération des données ESG pour {ticker_clean}..."):
        result = fetch_esg_from_yfinance(ticker_clean)

    if result:
        st.markdown(f"""
        <div class='esg-card' style='border-color:#4F46E5;'>
            <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;'>
                <div>
                    <span class='esg-ticker'>{ticker_clean}</span>
                    <span class='api-badge badge-auto'>✓ Yahoo Finance</span>
                </div>
                <div style='font-size:1.4rem; font-weight:800; color:{score_color(result["total"])};'>
                    {result["total"]:.0f}<span style='font-size:0.75rem; color:#555e6e;'>/100</span>
                </div>
            </div>
            <div style='display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px;'>
                <div>
                    <div class='esg-label'>🌍 Environnement</div>
                    <div class='esg-score' style='color:{score_color(result["env"])};'>{result["env"]:.0f}<span style='font-size:0.7rem; color:#555e6e;'>/100</span></div>
                    <div class='esg-bar-wrap'><div class='esg-bar-fill' style='width:{result["env"]}%; background:{score_color(result["env"])};'></div></div>
                </div>
                <div>
                    <div class='esg-label'>👥 Social</div>
                    <div class='esg-score' style='color:{score_color(result["soc"])};'>{result["soc"]:.0f}<span style='font-size:0.7rem; color:#555e6e;'>/100</span></div>
                    <div class='esg-bar-wrap'><div class='esg-bar-fill' style='width:{result["soc"]}%; background:{score_color(result["soc"])};'></div></div>
                </div>
                <div>
                    <div class='esg-label'>🏛️ Gouvernance</div>
                    <div class='esg-score' style='color:{score_color(result["gov"])};'>{result["gov"]:.0f}<span style='font-size:0.7rem; color:#555e6e;'>/100</span></div>
                    <div class='esg-bar-wrap'><div class='esg-bar-fill' style='width:{result["gov"]}%; background:{score_color(result["gov"])};'></div></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button(f"💾 Sauvegarder {ticker_clean} dans ma base ESG", use_container_width=True):
            save_esg(ticker_clean, result["env"], result["soc"], result["gov"], result["sector"], source="yahoo_finance")
            st.success(f"✅ {ticker_clean} sauvegardé !")
            st.rerun()
    else:
        st.warning(
            f"⚠️ Aucune donnée ESG disponible sur Yahoo Finance pour **{ticker_clean}**. "
            "Tu peux l'ajouter manuellement ci-dessous."
        )

st.divider()


# ───────────────────────────────────────
# FILTRES
# ───────────────────────────────────────
st.markdown("<p class='section-label'>Filtres par valeurs</p>", unsafe_allow_html=True)

col_f1, col_f2 = st.columns([3, 1])
with col_f1:
    sectors_to_avoid = st.multiselect(
        "Secteurs à éviter",
        options=["fossil_fuel", "defense", "tobacco", "alcohol", "gaming", "others"],
        default=[],
        label_visibility="collapsed",
        placeholder="Secteurs à éviter (ex: fossil_fuel, defense...)",
    )
with col_f2:
    show_only_clean = st.toggle("Filtrer", value=False)

st.divider()


# ───────────────────────────────────────
# LISTE ESG
# ───────────────────────────────────────
df = load_esg_profiles()

if show_only_clean and sectors_to_avoid:
    df = df[~df["sector"].isin(sectors_to_avoid)]

if df.empty:
    st.info("Aucun actif ne correspond à ces filtres.")
else:
    st.markdown("<p class='section-label'>Profils ESG sauvegardés</p>", unsafe_allow_html=True)

    for _, row in df.iterrows():
        env   = float(row["environment_score"])
        soc   = float(row["social_score"])
        gov   = float(row["governance_score"])
        total = float(row["total_esg_score"])
        sec   = row["sector"]
        tick  = row["ticker"]
        src   = row.get("source", "manual")
        badge = '<span class="api-badge badge-auto">✓ Yahoo Finance</span>' if src == "yahoo_finance" else '<span class="api-badge badge-manual">Manuel</span>'

        st.markdown(f"""
        <div class='esg-card'>
            <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;'>
                <div>
                    <span class='esg-ticker'>{tick}</span>{badge}
                    <div class='esg-sector' style='color:{sector_color(sec)};'>{sec.replace("_"," ").upper()}</div>
                </div>
                <div style='text-align:right;'>
                    <div class='esg-label'>Score global</div>
                    <div style='font-size:1.4rem; font-weight:800; color:{score_color(total)};'>{total:.0f}<span style='font-size:0.75rem; color:#555e6e;'>/100</span></div>
                </div>
            </div>
            <div style='display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px;'>
                <div>
                    <div class='esg-label'>🌍 Environnement</div>
                    <div class='esg-score' style='color:{score_color(env)};'>{env:.0f}<span style='font-size:0.7rem; color:#555e6e;'>/100</span></div>
                    <div class='esg-bar-wrap'><div class='esg-bar-fill' style='width:{env}%; background:{score_color(env)};'></div></div>
                </div>
                <div>
                    <div class='esg-label'>👥 Social</div>
                    <div class='esg-score' style='color:{score_color(soc)};'>{soc:.0f}<span style='font-size:0.7rem; color:#555e6e;'>/100</span></div>
                    <div class='esg-bar-wrap'><div class='esg-bar-fill' style='width:{soc}%; background:{score_color(soc)};'></div></div>
                </div>
                <div>
                    <div class='esg-label'>🏛️ Gouvernance</div>
                    <div class='esg-score' style='color:{score_color(gov)};'>{gov:.0f}<span style='font-size:0.7rem; color:#555e6e;'>/100</span></div>
                    <div class='esg-bar-wrap'><div class='esg-bar-fill' style='width:{gov}%; background:{score_color(gov)};'></div></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ───────────────────────────────────────
# SECTION PÉDAGOGIQUE
# ───────────────────────────────────────
st.divider()
st.markdown("<p class='section-label'>Qu'est-ce que l'ESG ?</p>", unsafe_allow_html=True)

col_e1, col_e2, col_e3 = st.columns(3)
with col_e1:
    st.markdown("""<div class='esg-card'>
        <div class='esg-sector' style='color:#22c55e;'>🌍 Environnement</div>
        <p style='color:#8b9ab0; font-size:0.82rem; margin-top:8px;'>
            Mesure l'impact sur le climat, l'eau, l'air et les émissions carbone. Un score élevé = pratiques respectueuses.
        </p></div>""", unsafe_allow_html=True)
with col_e2:
    st.markdown("""<div class='esg-card'>
        <div class='esg-sector' style='color:#4F46E5;'>👥 Social</div>
        <p style='color:#8b9ab0; font-size:0.82rem; margin-top:8px;'>
            Conditions de travail, droits humains, diversité. Un score élevé = entreprise responsable envers ses parties prenantes.
        </p></div>""", unsafe_allow_html=True)
with col_e3:
    st.markdown("""<div class='esg-card'>
        <div class='esg-sector' style='color:#f59e0b;'>🏛️ Gouvernance</div>
        <p style='color:#8b9ab0; font-size:0.82rem; margin-top:8px;'>
            Transparence, conformité, indépendance du CA. Un score élevé = gestion solide et éthique.
        </p></div>""", unsafe_allow_html=True)


# ───────────────────────────────────────
# AJOUT MANUEL
# ───────────────────────────────────────
st.divider()
st.markdown("<p class='section-label'>Ajouter manuellement un actif</p>", unsafe_allow_html=True)

with st.form("add_esg_ticker"):
    a1, a2 = st.columns([2, 2])
    with a1:
        ticker_input = st.text_input("Ticker", placeholder="ex: TSLA, XOM, JNJ")
    with a2:
        sector_input = st.text_input("Secteur", placeholder="ex: tech, fossil_fuel, clean_energy...")

    b1, b2, b3 = st.columns(3)
    with b1:
        env_score = st.slider("🌍 Environnement", 0, 100, 50)
    with b2:
        social_score = st.slider("👥 Social", 0, 100, 50)
    with b3:
        gov_score = st.slider("🏛️ Gouvernance", 0, 100, 50)

    submitted = st.form_submit_button("Ajouter / Mettre à jour", use_container_width=True)

    if submitted:
        if ticker_input and sector_input:
            total = save_esg(ticker_input, env_score, social_score, gov_score, sector_input, source="manual")
            st.success(f"✅ {ticker_input.upper()} ajouté — Score ESG global : {total}/100")
            st.rerun()
        else:
            st.error("⚠️ Remplis le ticker et le secteur")

st.divider()
st.markdown(
    "<p class='caption' style='text-align:center;'>AlphaDesk v1.0 &nbsp;·&nbsp; ESG Module · Yahoo Finance</p>",
    unsafe_allow_html=True,
)
