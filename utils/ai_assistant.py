import os
from typing import Dict, List, Optional

import streamlit as st
from groq import Groq


MODEL_NAME = "llama-3.3-70b-versatile"

DEFAULT_PAGE_PROMPTS = {
    "home": "Tu es l'assistant IA d'AlphaDesk. Aide l'utilisateur à comprendre la plateforme, ses modules et comment l'utiliser.",
    "markets": "Tu es l'assistant Markets d'AlphaDesk. Aide à interpréter les prix, tendances, momentum, RSI, MACD, moyennes mobiles et contexte de marché.",
    "news": "Tu es l'assistant News d'AlphaDesk. Résume les actualités, identifie les catalyseurs et explique l'impact potentiel sur les marchés.",
    "macro": "Tu es l'assistant Macro d'AlphaDesk. Explique les indicateurs macro, taux, inflation, croissance, politique monétaire et implications marchés.",
    "signals": "Tu es l'assistant Signals d'AlphaDesk. Aide à lire les signaux techniques, la confluence des indicateurs et les scénarios haussier/baissier.",
    "portfolio": "Tu es l'assistant Portfolio d'AlphaDesk. Aide à analyser allocation, performance, volatilité, diversification, drawdown et risque.",
    "screener": "Tu es l'assistant Screener d'AlphaDesk. Aide à lire les filtres, interpréter les résultats et trouver des idées d'actions.",
    "backtest": "Tu es l'assistant Backtest d'AlphaDesk. Aide à comprendre les résultats d'une stratégie, le Sharpe, win rate, drawdown et biais éventuels.",
    "esg": "Tu es l'assistant ESG d'AlphaDesk. Aide à interpréter les scores ESG, controverses, profil durable et limites méthodologiques.",
}

SUGGESTIONS = {
    "home": [
        "Que puis-je faire sur cette page ?",
        "Explique rapidement AlphaDesk",
        "Comment utiliser les autres modules ?",
    ],
    "markets": [
        "Résume la situation de ce marché",
        "Interprète les indicateurs affichés",
        "Quels signaux surveiller maintenant ?",
    ],
    "news": [
        "Résume les news importantes",
        "Quel impact potentiel sur le marché ?",
        "Quelles entreprises sont concernées ?",
    ],
    "macro": [
        "Explique les indicateurs affichés",
        "Quel est le message macro principal ?",
        "Quel impact pour les actifs risqués ?",
    ],
    "signals": [
        "Que disent les signaux actuels ?",
        "Y a-t-il un biais haussier ou baissier ?",
        "Quels indicateurs confirment le setup ?",
    ],
    "portfolio": [
        "Analyse mon portefeuille",
        "Quels sont les principaux risques ?",
        "Comment améliorer la diversification ?",
    ],
    "screener": [
        "Que penser des résultats du screener ?",
        "Comment prioriser les actions trouvées ?",
        "Quels filtres ajuster ?",
    ],
    "backtest": [
        "Interprète les résultats du backtest",
        "La stratégie semble-t-elle robuste ?",
        "Quels biais ou limites vois-tu ?",
    ],
    "esg": [
        "Explique les scores ESG affichés",
        "Quels sont les points faibles ESG ?",
        "Que retenir rapidement ?",
    ],
}


def _get_api_key() -> Optional[str]:
    try:
        if "GROQ_API_KEY" in st.secrets:
            return st.secrets["GROQ_API_KEY"]
    except Exception:
        pass
    return os.getenv("GROQ_API_KEY")


def _get_client() -> Groq:
    api_key = _get_api_key()
    if not api_key:
        raise ValueError(
            "Clé API Groq introuvable. Ajoute GROQ_API_KEY dans ton .env ou dans st.secrets."
        )
    return Groq(api_key=api_key)


def build_context(page: str, **kwargs) -> Dict:
    clean_data = {}
    for k, v in kwargs.items():
        if v is None:
            continue
        if isinstance(v, str) and not v.strip():
            continue
        clean_data[k] = v

    return {
        "page": page,
        "data": clean_data,
    }


def _context_to_text(context: Optional[Dict]) -> str:
    if not context:
        return "Aucun contexte additionnel fourni."

    page = context.get("page", "unknown")
    data = context.get("data", {})

    if not data:
        return f"Page courante: {page}\nAucune donnée dynamique disponible."

    lines = [f"Page courante: {page}", "Contexte dynamique :"]
    for key, value in data.items():
        pretty_key = str(key).replace("_", " ").capitalize()
        lines.append(f"- {pretty_key}: {value}")
    return "\n".join(lines)


def _build_system_prompt(page_key: str, context: Optional[Dict]) -> str:
    base_prompt = DEFAULT_PAGE_PROMPTS.get(
        page_key,
        "Tu es l'assistant IA d'AlphaDesk. Aide l'utilisateur de façon claire, structurée et utile.",
    )

    rules = """
Règles :
- Réponds en français sauf si l'utilisateur demande une autre langue.
- Base-toi d'abord sur le contexte fourni dans la page.
- Si une donnée manque, dis-le clairement au lieu d'inventer.
- Donne des réponses concrètes, orientées usage produit et finance.
- Tu n'exécutes pas d'ordres de trading et tu ne garantis aucun résultat.
- Tu peux expliquer, synthétiser, comparer et interpréter.
- Reste clair, court et utile.
""".strip()

    context_text = _context_to_text(context)

    return f"{base_prompt}\n\n{rules}\n\nContexte de la page:\n{context_text}"


def ask_groq(
    user_message: str,
    page_key: str = "home",
    context: Optional[Dict] = None,
    history: Optional[List[Dict[str, str]]] = None,
    model_name: str = MODEL_NAME,
) -> str:
    client = _get_client()
    system_prompt = _build_system_prompt(page_key, context)

    messages = [{"role": "system", "content": system_prompt}]

    if history:
        for msg in history[-8:]:
            role = msg.get("role")
            content = msg.get("content", "")
            if role in {"user", "assistant"} and content:
                messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_message})

    completion = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=0.3,
        max_tokens=700,
    )

    return completion.choices[0].message.content.strip()


def render_chat_widget(
    page_key: str = "home",
    context=None,
    title: str = "Alpha Assistant AI",
):
    history_key = f"alpha_ai_history_{page_key}"
    input_key = f"alpha_ai_input_{page_key}"
    open_key = f"alpha_ai_open_{page_key}"

    if history_key not in st.session_state:
        st.session_state[history_key] = []
    if open_key not in st.session_state:
        st.session_state[open_key] = False

    # Injection CSS floating
    st.markdown("""
    <style>
    #alpha-ai-float-anchor + div [data-testid="stVerticalBlock"] > div:last-child {
        position: fixed !important;
        bottom: 24px !important;
        right: 24px !important;
        z-index: 9999 !important;
        width: 380px !important;
        max-height: 80vh !important;
        overflow-y: auto !important;
        border-radius: 16px !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.18) !important;
        background: white !important;
    }
    [data-theme="dark"] #alpha-ai-float-anchor + div [data-testid="stVerticalBlock"] > div:last-child {
        background: #1c1b19 !important;
    }
    </style>
    <div id="alpha-ai-float-anchor"></div>
    """, unsafe_allow_html=True)

    with st.container():
        with st.expander(title, expanded=st.session_state[open_key]):
            st.session_state[open_key] = True
            st.caption("Pose une question sur cette page ou ses données.")

            cols = st.columns([1, 1, 1])
            page_suggestions = SUGGESTIONS.get(page_key, ["Explique cette page"])
            for i, suggestion in enumerate(page_suggestions[:3]):
                if cols[i].button(suggestion, key=f"{page_key}_sug_{i}"):
                    try:
                        st.session_state[history_key].append({"role": "user", "content": suggestion})
                        answer = ask_groq(
                            user_message=suggestion,
                            page_key=page_key,
                            context=context,
                            history=st.session_state[history_key][:-1],
                        )
                        st.session_state[history_key].append({"role": "assistant", "content": answer})
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur : {e}")

            st.markdown("---")

            for msg in st.session_state[history_key]:
                if msg["role"] == "user":
                    st.markdown(f"**🧑 Toi :** {msg['content']}")
                else:
                    st.markdown(f"**🤖 Alpha :** {msg['content']}")

            if st.session_state[history_key]:
                st.markdown("---")

            user_text = st.text_area(
                "Ton message",
                key=input_key,
                placeholder="Ex: interprète les indicateurs affichés, explique les news, analyse mon portefeuille...",
                height=80,
            )

            col_send, col_clear = st.columns([1, 1])
            if col_send.button("Envoyer", use_container_width=True, key=f"{page_key}_send"):
                if user_text and user_text.strip():
                    try:
                        st.session_state[history_key].append({"role": "user", "content": user_text.strip()})
                        answer = ask_groq(
                            user_message=user_text.strip(),
                            page_key=page_key,
                            context=context,
                            history=st.session_state[history_key][:-1],
                        )
                        st.session_state[history_key].append({"role": "assistant", "content": answer})
                        st.session_state[input_key] = ""
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur : {e}")
                else:
                    st.warning("Écris un message avant d'envoyer.")

            if col_clear.button("Effacer", use_container_width=True, key=f"{page_key}_clear"):
                st.session_state[history_key] = []
                st.session_state[input_key] = ""
                st.rerun()