import streamlit as st
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv(override=True)

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
FINNHUB_KEY  = os.getenv("FINNHUB_KEY")

st.set_page_config(page_title="News — AlphaDesk", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    section[data-testid="stSidebar"] { background-color: #13161d; border-right: 1px solid #2a2d35; }
    h1, h2, h3 { color: #ffffff !important; font-weight: 600 !important; }
    .stSelectbox label, .stTextInput label, .stRadio label {
        color: #8b9ab0 !important; font-size: 0.8rem !important; text-transform: uppercase;
    }
    .news-card { background-color: #1c1f26; border: 1px solid #2a2d35; border-radius: 10px; padding: 16px 20px; margin-bottom: 12px; }
    .news-title { color: #e0e0e0; font-size: 0.95rem; font-weight: 600; margin-bottom: 6px; }
    .news-meta  { color: #8b9ab0; font-size: 0.75rem; }
    .news-desc  { color: #a0aab8; font-size: 0.85rem; margin-top: 8px; }
    .badge-pos  { background:#1a3a2a; color:#26a69a; padding:2px 8px; border-radius:4px; font-size:0.7rem; font-weight:600; }
    .badge-neg  { background:#3a1a1a; color:#ef5350; padding:2px 8px; border-radius:4px; font-size:0.7rem; font-weight:600; }
    .badge-neu  { background:#1e2228; color:#8b9ab0; padding:2px 8px; border-radius:4px; font-size:0.7rem; font-weight:600; }
    .source-badge { background:#1c2333; color:#4fc3f7; padding:2px 8px; border-radius:4px; font-size:0.7rem; font-weight:600; margin-right:6px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("## News")
st.markdown("<p style='color:#8b9ab0; font-size:0.85rem; margin-top:-10px;'>Actualités financières mondiales en temps réel</p>", unsafe_allow_html=True)
st.divider()

# ── Sentiment ────────────────────────────────────────────────────────
POS = ["surge","rally","gain","rise","beat","growth","profit","up","high","bull","boost","hausse","bénéfice"]
NEG = ["crash","drop","fall","loss","miss","recession","debt","down","bear","crisis","baisse","chute","perte"]

def sentiment(text):
    t = text.lower()
    p = sum(1 for w in POS if w in t)
    n = sum(1 for w in NEG if w in t)
    if p > n: return "positive"
    if n > p: return "negative"
    return "neutral"

def badge(s):
    if s == "positive": return "<span class='badge-pos'>POSITIF</span>"
    if s == "negative": return "<span class='badge-neg'>NÉGATIF</span>"
    return "<span class='badge-neu'>NEUTRE</span>"

def news_card(title, source, date, url, desc, sent, origin="NewsAPI"):
    st.markdown(f"""
    <div class='news-card'>
        <div class='news-title'>
            <a href='{url}' target='_blank' style='color:#e0e0e0;text-decoration:none;'>{title}</a>
        </div>
        <div class='news-meta'>
            <span class='source-badge'>{origin}</span>
            {source} &nbsp;·&nbsp; {date} &nbsp;·&nbsp; {badge(sent)}
        </div>
        {"<div class='news-desc'>" + str(desc)[:200] + "...</div>" if desc else ""}
    </div>
    """, unsafe_allow_html=True)

# ── Fetch NewsAPI ────────────────────────────────────────────────────
def fetch_newsapi(q, nb):
    try:
        r = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q":        q,
                "apiKey":   NEWS_API_KEY,
                "sortBy":   "publishedAt",
                "pageSize": nb,
                "language": "en",
                "from":     (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
            },
            timeout=15
        )
        data = r.json()
        if data.get("status") != "ok":
            return []
        return [
            {
                "title":   a.get("title", ""),
                "source":  a.get("source", {}).get("name", ""),
                "date":    a.get("publishedAt", "")[:10],
                "url":     a.get("url", "#"),
                "desc":    a.get("description", ""),
                "origin":  "NewsAPI"
            }
            for a in data.get("articles", [])
            if a.get("title") and a["title"] != "[Removed]"
        ]
    except:
        return []

# ── Fetch Finnhub ────────────────────────────────────────────────────
def fetch_finnhub(ticker, nb):
    try:
        today    = datetime.now().strftime("%Y-%m-%d")
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        r = requests.get(
            "https://finnhub.io/api/v1/company-news",
            params={
                "symbol": ticker.upper(),
                "from":   week_ago,
                "to":     today,
                "token":  FINNHUB_KEY
            },
            timeout=15
        )
        data = r.json()
        if not isinstance(data, list):
            return []
        result = []
        for a in data[:nb]:
            try:
                date = datetime.fromtimestamp(a.get("datetime", 0)).strftime("%Y-%m-%d")
            except:
                date = "—"
            result.append({
                "title":  a.get("headline", ""),
                "source": a.get("source", ""),
                "date":   date,
                "url":    a.get("url", "#"),
                "desc":   a.get("summary", ""),
                "origin": "Finnhub"
            })
        return result
    except:
        return []

# ── Barre de recherche unifiée ───────────────────────────────────────
st.markdown("### 🔍 Recherche")
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    query = st.text_input(
        "MOT-CLÉ OU TICKER",
        value="",
        placeholder="Ex: Bitcoin, inflation, AAPL, Fed, CAC 40..."
    )
with col2:
    nb = st.selectbox("NOMBRE", [10, 20, 30, 50], index=1)
with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    search = st.button("🔍 RECHERCHER", use_container_width=True, type="primary")

st.divider()

# ── Logique de recherche ─────────────────────────────────────────────
# Requête par défaut si vide
default_query = "finance OR stock OR market OR economy OR crypto"
q = query.strip() if query.strip() else default_query

# On cherche sur les DEUX sources simultanément
with st.spinner("Chargement des actualités..."):
    all_articles = []

    # NewsAPI
    if NEWS_API_KEY:
        news_articles = fetch_newsapi(q, nb)
        all_articles.extend(news_articles)
    else:
        st.warning("⚠️ NEWS_API_KEY manquante")

    # Finnhub — si le mot-clé ressemble à un ticker (court, majuscules)
    if FINNHUB_KEY:
        # Détecte si c'est un ticker (1-5 lettres) ou un mot-clé
        is_ticker = len(q.split()) == 1 and len(q) <= 6
        finnhub_q = q if is_ticker else "AAPL"  # fallback AAPL si mot-clé générique
        fh_articles = fetch_finnhub(finnhub_q, nb // 2)
        all_articles.extend(fh_articles)
    else:
        st.warning("⚠️ FINNHUB_KEY manquante")

# ── Tri par date ─────────────────────────────────────────────────────
all_articles = sorted(all_articles, key=lambda x: x.get("date", ""), reverse=True)

# ── Stats ─────────────────────────────────────────────────────────────
if all_articles:
    n_news    = sum(1 for a in all_articles if a["origin"] == "NewsAPI")
    n_finnhub = sum(1 for a in all_articles if a["origin"] == "Finnhub")
    sentiments = [sentiment((a.get("title") or "") + " " + (a.get("desc") or "")) for a in all_articles]
    n_pos = sentiments.count("positive")
    n_neg = sentiments.count("negative")
    n_neu = sentiments.count("neutral")

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total articles",  len(all_articles))
    m2.metric("NewsAPI",         n_news)
    m3.metric("Finnhub",         n_finnhub)
    m4.metric("😊 Positifs",     n_pos)
    m5.metric("😟 Négatifs",     n_neg)

    st.divider()

    # Filtre sentiment
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        filter_sent = st.multiselect(
            "FILTRER PAR SENTIMENT",
            ["positive", "negative", "neutral"],
            default=["positive", "negative", "neutral"]
        )
    with col_f2:
        filter_source = st.multiselect(
            "FILTRER PAR SOURCE",
            ["NewsAPI", "Finnhub"],
            default=["NewsAPI", "Finnhub"]
        )

    # Affichage
    shown = 0
    for a, s in zip(all_articles, sentiments):
        if s in filter_sent and a["origin"] in filter_source:
            news_card(
                a["title"], a["source"], a["date"],
                a["url"], a["desc"], s, a["origin"]
            )
            shown += 1

    if shown == 0:
        st.info("Aucun article avec ces filtres.")

else:
    st.warning("Aucun article trouvé. Vérifie tes clés API ou ta connexion.")
