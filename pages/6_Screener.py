import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

st.set_page_config(page_title="Screener — AlphaDesk", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    section[data-testid="stSidebar"] { background-color: #13161d; border-right: 1px solid #2a2d35; }
    h1, h2, h3 { color: #ffffff !important; font-weight: 600 !important; }
    .stSelectbox label, .stSlider label { color: #8b9ab0 !important; font-size: 0.8rem !important; text-transform: uppercase; }
    </style>
""", unsafe_allow_html=True)

st.markdown("## Screener")
st.markdown("<p style='color:#8b9ab0; font-size:0.85rem; margin-top:-10px;'>Filtre les actifs par performance, volatilité, RSI et volume</p>", unsafe_allow_html=True)
st.divider()

UNIVERSES = {
    "S&P 500 — Top 30": ["AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","BRK-B","JPM","V",
                          "UNH","XOM","LLY","JNJ","MA","PG","HD","MRK","ABBV","CVX",
                          "PEP","KO","COST","WMT","BAC","CRM","ORCL","NFLX","AMD","INTC"],
    "CAC 40 — Top 20":  ["MC.PA","TTE.PA","SAN.PA","BNP.PA","AIR.PA","RI.PA","DG.PA","SU.PA",
                          "AI.PA","OR.PA","CS.PA","BN.PA","ACA.PA","SGO.PA","VIE.PA",
                          "STM.PA","SAF.PA","KER.PA","CAP.PA","DSY.PA"],
    "Crypto — Top 10":  ["BTC-USD","ETH-USD","BNB-USD","SOL-USD","XRP-USD",
                          "ADA-USD","AVAX-USD","DOGE-USD","DOT-USD","MATIC-USD"],
    "ETF Majeurs":      ["SPY","QQQ","IWM","DIA","GLD","SLV","TLT","HYG","EEM","VNQ"],
}

# ── Sidebar ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Filtres")
    universe = st.selectbox("UNIVERS", list(UNIVERSES.keys()))
    period   = st.selectbox("PÉRIODE", ["1mo","3mo","6mo","1y"], index=1)
    min_ret  = st.slider("Rendement min (%)",   -50, 100, -100)
    max_vol  = st.slider("Volatilité max (%)",    0, 150,  150)
    min_rsi  = st.slider("RSI min",               0, 100,    0)
    max_rsi  = st.slider("RSI max",               0, 100,  100)
    sort_by  = st.selectbox("TRIER PAR", ["Rendement %","Volatilité %","Sharpe","RSI"])
    sort_asc = st.checkbox("Ordre croissant", value=False)
    run      = st.button("🔍 LANCER", use_container_width=True, type="primary")

# ── RSI ──────────────────────────────────────────────────────────────
def compute_rsi(s, n=14):
    d = s.diff()
    g = d.clip(lower=0).rolling(n).mean()
    l = -d.clip(upper=0).rolling(n).mean()
    rs = g / l.replace(0, np.nan)
    return float((100 - 100 / (1 + rs)).dropna().iloc[-1])

# ── Main ─────────────────────────────────────────────────────────────
if run:
    tickers = UNIVERSES[universe]
    results = []
    progress = st.progress(0, text="Analyse en cours...")

    for i, ticker in enumerate(tickers):
        try:
            df = yf.download(ticker, period=period, auto_adjust=True, progress=False, timeout=10)
            if df.empty or len(df) < 20:
                continue
            df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
            close = df["Close"].squeeze()
            vol   = df["Volume"].squeeze()

            daily_r = close.pct_change().dropna()
            ret     = float((close.iloc[-1] / close.iloc[0] - 1) * 100)
            volatil = float(daily_r.std() * np.sqrt(252) * 100)
            sharpe  = float((daily_r.mean() * 252) / (daily_r.std() * np.sqrt(252))) if daily_r.std() > 0 else 0
            rsi     = compute_rsi(close)
            chg1d   = float(daily_r.iloc[-1] * 100)
            price   = float(close.iloc[-1])
            avg_vol = float(vol.mean()) if vol.sum() > 0 else 0

            results.append({
                "Ticker":       ticker,
                "Prix":         round(price, 2),
                "1J %":         round(chg1d, 2),
                "Rendement %":  round(ret, 2),
                "Volatilité %": round(volatil, 2),
                "Sharpe":       round(sharpe, 2),
                "RSI":          round(rsi, 1),
                "Vol. moyen":   int(avg_vol),
            })
        except:
            pass
        progress.progress((i + 1) / len(tickers), text=f"Analyse {ticker}...")

    progress.empty()

    if not results:
        st.error("Aucune donnée récupérée.")
    else:
        df_res = pd.DataFrame(results)
        df_res = df_res[
            (df_res["Rendement %"]  >= min_ret) &
            (df_res["Volatilité %"] <= max_vol) &
            (df_res["RSI"]          >= min_rsi) &
            (df_res["RSI"]          <= max_rsi)
        ].sort_values(sort_by, ascending=sort_asc).reset_index(drop=True)

        st.markdown(f"### {len(df_res)} actif(s) trouvé(s)")

        st.dataframe(
            df_res,
            use_container_width=True,
            hide_index=True,
            column_config={
                "RSI": st.column_config.ProgressColumn("RSI", min_value=0, max_value=100, format="%.1f"),
                "1J %": st.column_config.NumberColumn("1J %", format="%.2f%%"),
                "Rendement %": st.column_config.NumberColumn("Rendement %", format="%.2f%%"),
                "Volatilité %": st.column_config.NumberColumn("Volatilité %", format="%.2f%%"),
                "Sharpe": st.column_config.NumberColumn("Sharpe", format="%.2f"),
            }
        )
        csv = df_res.to_csv(index=False)
        st.download_button("⬇️ Exporter CSV", csv, "screener.csv", "text/csv")
else:
    st.info("👈 Configure les filtres dans la sidebar et clique sur **LANCER**")
