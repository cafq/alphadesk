# pages/8_ESG.py

import streamlit as st
import sqlite3
import pandas as pd


TITLE = "🌍 Ethique & ESG"
st.markdown(f"<h1 style='font-size:1.8rem;color:#e0e0e0;'>{TITLE}</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#8b9ab0; font-size:0.8rem;'>Explore les impacts éthiques de tes actifs et investis selon tes valeurs.</p>", unsafe_allow_html=True)

st.divider()



# ───────────────────────────────────────
# Helpers : connexion base + chargement ESG
# ───────────────────────────────────────

def get_esg_db():
    return sqlite3.connect("data/esg_data.db", check_same_thread=False)

def load_esg_profiles():
    conn = get_esg_db()
    df = pd.read_sql("SELECT * FROM esg_profiles ORDER BY total_esg_score DESC", conn)
    conn.close()
    return df


# ───────────────────────────────────────
# Sections de valeurs (exemples)
# ───────────────────────────────────────

st.markdown("### 🔍 Sélection de valeurs")

# Exemple de secteurs à éviter
SECTORS_TO_AVOID = st.multiselect(
    "Secteurs que tu veux éviter",
    options=["fossil_fuel", "defense", "tobacco", "alcohol", "gaming", "others"],
    default=[],
    help="Les actifs appartenant à ces secteurs seront mis en évidence ou cachés."
)

NO_AVOID = st.checkbox("Montrer tous les actifs", value=True)
show_only_non_avoid = st.checkbox("Montrer seulement ceux qui NE sont PAS dans les secteurs à éviter", value=False)


# ───────────────────────────────────────
# Chargement et affichage
# ───────────────────────────────────────

df = load_esg_profiles()

if show_only_non_avoid and SECTORS_TO_AVOID:
    mask = ~df["sector"].isin(SECTORS_TO_AVOID)
    df_filtered = df[mask]
else:
    df_filtered = df

if df_filtered.empty:
    st.info("Aucun actif ne correspond à ces filtres.")
else:
    st.markdown("### 📊 Profils ESG des actifs")

    for _, row in df_filtered.iterrows():
        with st.container():
            col1, col2, col3 = st.columns([4, 2, 2])

            with col1:
                st.markdown(
                    f"<div style='font-weight:700; font-size:1.05rem;'>{row['ticker']}</div>",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"<span style='color:#8b9ab0; font-size:0.8rem;'>Secteur : {row['sector']}</span>",
                    unsafe_allow_html=True
                )

            with col2:
                st.markdown(
                    f"<span style='font-size:0.7rem; color:#555e6e;'>🌍 Env</span>",
                    unsafe_allow_html=True
                )
                st.metric(label="", value=f"{row['environment_score']:.1f}/100")

            with col3:
                st.markdown(
                    f"<span style='font-size:0.7rem; color:#555e6e;'>👥 Social</span>",
                    unsafe_allow_html=True
                )
                st.metric(label="", value=f"{row['social_score']:.1f}/100")


        # Barre de score global
        st.progress(float(row["total_esg_score"]) / 100.0)
        st.markdown(
            f"<span style='color:#8b9ab0; font-size:0.8rem;'>✨ Score ESG global : {row['total_esg_score']:.1f}/100</span>",
            unsafe_allow_html=True
        )

        st.markdown("---")


# ───────────────────────────────────────
# Petites infos pédagogiques
# ───────────────────────────────────────

st.markdown("### 📚 Pourquoi l'ESG ?")

st.markdown(
    """
    - **Environnement (E)** : impact sur l’eau, l’air, l’énergie, le climat, etc.  
    - **Social (S)** : conditions de travail, droits humains, relations communautaires.  
    - **Governance (G)** : qualité de la gouvernance, transparence, conformité.  

    En choisissant des actifs avec des scores ESG plus élevés, tu peux **aligner tes investissements avec tes valeurs** et limiter ton exposition à certains secteurs controversés.
    """
)


# ──────────────────────────────────────────
# Optionnel : proposer d’ajouter des tickers
# ──────────────────────────────────────────

st.divider()
st.markdown("### 🧩 Ajouter un actif à la base ESG")

with st.form("add_esg_ticker"):
    ticker = st.text_input("Ticker", help="ex: TSLA, XOM, JNJ")
    env_score = st.slider("Score Environnement (0–100)", 0, 100, 50)
    social_score = st.slider("Score Social (0–100)", 0, 100, 50)
    gov_score = st.slider("Score Gouvernance (0–100)", 0, 100, 50)
    sector = st.text_input("Secteur", help="ex: tech, fossil_fuel, defense, clean_energy, etc.")

    submitted = st.form_submit_button("Ajouter / Mettre à jour")

    if submitted and ticker and sector:
        total = (env_score + social_score + gov_score) / 3.

        conn = get_esg_db()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO esg_profiles
                (ticker, environment_score, social_score, governance_score, total_esg_score, sector)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
            (ticker.upper(), env_score, social_score, gov_score, total, sector.lower())
        )
        conn.commit()
        conn.close()
        st.success(f"✅ {ticker.upper()} ajouté dans la base ESG.")
        st.rerun()
