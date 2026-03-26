# pages/2_News.py

import streamlit as st
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv(override=True)

NEWSAPI_KEY  = os.getenv("NEWS_API_KEY")
FINNHUB_KEY  = os.getenv("FINNHUB_KEY")

# ───────────────────────────────────────
# CONFIG
# ───────────────────────────────────────
st.set_page_config(
    page_title="AlphaDesk · News",
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
    .stSelectbox label, .stTextInput label, .stRadio label {
        color: #8b9ab0 !important;
        font-size: 0.8rem !important;
        text-transform: uppercase;
    }
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

    /* News cards */
    .news-card {
        background-color: #1c1f26;
        border: 1px solid #2a2d35;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 10px;
        transition: border-color 0.2s;
    }
    .news-card:hover { border-color: #4F46E5; }
    .news-card-pos { border-left: 3px solid #26a69a !important; }
    .news-card-neg { border-left: 3px solid #ef5350 !important; }
    .news-card-neu { border-left: 3px solid #555e6e !important; }
    .news-title {
        color: #e0e0e0;
        font-size: 0.95rem;
        font-weight: 600;
        margin-bottom: 6px;
        line-height: 1.4;
    }
    .news-meta { color: #8b9ab0; font-size: 0.75rem; }
    .news-desc { color: #a0aab8; font-size: 0.85rem; margin-top: 8px; line-height: 1.5; }

    /* Badges */
    .badge-pos { background:#1a3a2a; color:#26a69a; padding:2px 8px; border-radius:4px; font-size:0.68rem; font-weight:700; }
    .badge-neg { background:#3a1a1a; color:#ef5350; padding:2px 8px; border-radius:4px; font-size:0.68rem; font-weight:700; }
    .badge-neu { background:#1e2228; color:#8b9ab0; padding:2px 8px; border-radius:4px; font-size:0.68rem; font-weight:700; }
    .badge-score-pos { background:#1a3a2a; color:#22c55e; padding:2px 8px; border-radius:4px; font-size:0.68rem; font-weight:700; }
    .badge-score-neg { background:#3a1a1a; color:#ef5350; padding:2px 8px; border-radius:4px; font-size:0.68rem; font-weight:700; }
    .badge-score-neu { background:#1e2228; color:#8b9ab0; padding:2px 8px; border-radius:4px; font-size:0.68rem; font-weight:700; }
    .source-badge { background:#1c2333; color:#4fc3f7; padding:2px 8px; border-radius:4px; font-size:0.68rem; font-weight:700; margin-right:6px; }

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
        <span style='font-size:1.1rem; font-weight:500; color:#8b9ab0; margin-left:12px;'>/ News</span>
    </div>
    <p style='color:#8b9ab0; font-size:0.88rem; margin-top:8px;'>
        Actualités financières mondiales · Analyse de sentiment en temps réel
    </p>
</div>
""", unsafe_allow_html=True)

st.divider()


# ───────────────────────────────────────
# SENTIMENT ENGINE (amélioré)
# ───────────────────────────────────────
POS_WORDS = [
    "surge","rally","gain","rise","beat","growth","profit","up","high","bull",
    "boost","hausse","bénéfice","record","strong","outperform","upgrade","buy",
    "recover","rebound","soar","jump","positive","exceed","expansion","momentum",
    "breakout","bullish","opportunity","dividend","acquisition","partnership"
]
NEG_WORDS = [
    "crash","drop","fall","loss","miss","recession","debt","down","bear","crisis",
    "baisse","chute","perte","weak","downgrade","sell","decline","default","risk",
    "inflation","fear","concern","warning","disappointing","layoff","bankruptcy",
    "lawsuit","investigation","fraud","correction","selloff","bearish","plunge"
]

def sentiment_score(text: str) -> tuple[str, int]:
    """Retourne (label, score_net) basé sur les mots clés."""
    t = text.lower()
    p = sum(1 for w in POS_WORDS if w in t)
    n = sum(1 for w in NEG_WORDS if w in t)
    score = p - n
    if score > 0:   return "positive", score
    if score < 0:   return "negative", score
    return "neutral", 0

def sentiment_badge(s: str) -> str:
    if s == "positive": return "<span class='badge-pos'>📈 POSITIF</span>"
    if s == "negative": return "<span class='badge-neg'>📉 NÉGATIF</span>"
    return "<span class='badge-neu'>➖ NEUTRE</span>"

def score_badge(score: int) -> str:
    if score > 0:  return f"<span class='badge-score-pos'>+{score}</span>"
    if score < 0:  return f"<span class='badge-score-neg'>{score}</span>"
    return f"<span class='badge-score-neu'>{score}</span>"

def card_class(s: str) -> str:
    if s == "positive": return "news-card news-card-pos"
    if s == "negative": return "news-card news-card-neg"
    return "news-card news-card-neu"


# ───────────────────────────────────────
# FETCH NEWS
# ───────────────────────────────────────
def fetch_newsapi(q: str, nb: int) -> list:
    if not NEWSAPI_KEY:
        return []
    try:
        r = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": q,
                "apiKey": NEWSAPI_KEY,
                "sortBy": "publishedAt",
                "pageSize": nb,
                "language": "en",
                "from": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
            },
            timeout=15,
        )
        data = r.json()
        if data.get("status") != "ok":
            return []
        return [
            {
                "title":  a.get("title", ""),
                "source": a.get("source", {}).get("name", ""),
                "date":   a.get("publishedAt", "")[:10],
                "url":    a.get("url", ""),
                "desc":   a.get("description", "") or "",
                "origin": "NewsAPI",
            }
            for a in data.get("articles", [])
            if a.get("title") and a.get("title") != "[Removed]"
        ]
    except:
        return []

def fetch_finnhub(ticker: str, nb: int) -> list:
    if not FINNHUB_KEY:
        return []
    try:
        today    = datetime.now().strftime("%Y-%m-%d")
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        r = requests.get(
            "https://finnhub.io/api/v1/company-news",
            params={
                "symbol": ticker.upper(),
                "from":   week_ago,
                "to":     today,
                "token":  FINNHUB_KEY,
            },
            timeout=15,
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
                "url":    a.get("url", ""),
                "desc":   a.get("summary", "") or "",
                "origin": "Finnhub",
            })
        return result
    except:
        return []


# ───────────────────────────────────────
# RECHERCHE
# ───────────────────────────────────────
st.markdown("<p class='section-label'>Recherche</p>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
with col1:
    query = st.text_input(
        "MOT-CLÉ OU TICKER",
        value="",
        placeholder="Ex: Bitcoin, inflation, AAPL, Fed, CAC 40, Nvidia..."
    )
with col2:
    nb = st.selectbox("NOMBRE", [10, 20, 30, 50], index=1)
with col3:
    days_filter = st.selectbox("PÉRIODE", ["7 jours", "3 jours", "1 jour"], index=0)
with col4:
    st.markdown("<br>", unsafe_allow_html=True)
    search = st.button("RECHERCHER", use_container_width=True, type="primary")

st.divider()


# ───────────────────────────────────────
# LOGIQUE RECHERCHE
# ───────────────────────────────────────
default_query = "finance OR stock OR market OR economy OR crypto"
q = query.strip() if query.strip() else default_query

days_map = {"7 jours": 7, "3 jours": 3, "1 jour": 1}
days_back = days_map[days_filter]

with st.spinner("Chargement des actualités..."):
    all_articles = []

    # NewsAPI
    if NEWSAPI_KEY:
        news_articles = fetch_newsapi(q, nb)
        all_articles.extend(news_articles)
    else:
        st.warning("⚠️ NEWSAPI_KEY manquante dans ton .env")

    # Finnhub
    if FINNHUB_KEY:
        is_ticker = len(q.split()) == 1 and len(q) <= 6
        fh_q = q if is_ticker else "AAPL"
        fh_articles = fetch_finnhub(fh_q, nb // 2)
        all_articles.extend(fh_articles)
    else:
        st.warning("⚠️ FINNHUB_KEY manquante dans ton .env")

# Tri par date
all_articles = sorted(all_articles, key=lambda x: x.get("date", ""), reverse=True)

# Filtre par période
cutoff = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
all_articles = [a for a in all_articles if a.get("date", "0000") >= cutoff]

# Analyse sentiment
sentiments = [sentiment_score(a.get("title","") + " " + a.get("desc","")) for a in all_articles]


# ───────────────────────────────────────
# MÉTRIQUES
# ───────────────────────────────────────
if all_articles:
    n_news    = sum(1 for a in all_articles if a["origin"] == "NewsAPI")
    n_finnhub = sum(1 for a in all_articles if a["origin"] == "Finnhub")
    n_pos     = sum(1 for s,_ in sentiments if s == "positive")
    n_neg     = sum(1 for s,_ in sentiments if s == "negative")
    n_neu     = sum(1 for s,_ in sentiments if s == "neutral")
    avg_score = sum(sc for _,sc in sentiments) / len(sentiments) if sentiments else 0

    m1,m2,m3,m4,m5,m6 = st.columns(6)
    m1.metric("Total articles",   len(all_articles))
    m2.metric("NewsAPI",          n_news)
    m3.metric("Finnhub",          n_finnhub)
    m4.metric("📈 Positifs",      n_pos)
    m5.metric("📉 Négatifs",      n_neg)
    m6.metric("Score moyen",      f"{avg_score:+.1f}")

    st.divider()

    # ── Filtres sentiment + source ──
    colf1, colf2 = st.columns([2, 1])
    with colf1:
        filter_sent = st.multiselect(
            "FILTRER PAR SENTIMENT",
            ["positive", "negative", "neutral"],
            default=["positive", "negative", "neutral"],
            label_visibility="collapsed",
            placeholder="Filtrer par sentiment...",
        )
    with colf2:
        filter_source = st.multiselect(
            "SOURCE",
            ["NewsAPI", "Finnhub"],
            default=["NewsAPI", "Finnhub"],
            label_visibility="collapsed",
            placeholder="Filtrer par source...",
        )

    st.divider()

    # ── Affichage articles ──
    st.markdown("<p class='section-label'>Actualités</p>", unsafe_allow_html=True)

    shown = 0
    for a, (sent, score) in zip(all_articles, sentiments):
        if sent not in filter_sent:
            continue
        if a["origin"] not in filter_source:
            continue

        desc_short = (a["desc"][:220] + "...") if len(a["desc"]) > 220 else a["desc"]
        cls = card_class(sent)

        st.markdown(f"""
        <div class='{cls}'>
            <div class='news-title'>
                <a href='{a["url"]}' target='_blank' style='color:#e0e0e0; text-decoration:none;'>
                    {a["title"]}
                </a>
            </div>
            <div class='news-meta'>
                <span class='source-badge'>{a["origin"]}</span>
                {a["source"]} &nbsp;·&nbsp; {a["date"]}
                &nbsp;&nbsp;
                {sentiment_badge(sent)}
                &nbsp;
                {score_badge(score)}
            </div>
            {f"<div class='news-desc'>{desc_short}</div>" if desc_short else ""}
        </div>
        """, unsafe_allow_html=True)
        shown += 1

    if shown == 0:
        st.info("Aucun article avec ces filtres.")

else:
    st.warning("Aucun article trouvé. Vérifie tes clés API ou ta connexion.")

st.divider()
st.markdown(
    "<p class='caption' style='text-align:center;'>AlphaDesk v1.0 &nbsp;·&nbsp; NewsAPI · Finnhub</p>",
    unsafe_allow_html=True,
)
