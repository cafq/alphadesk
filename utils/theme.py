import streamlit as st


GLOBAL_THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    color-scheme: dark;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at top left, rgba(79, 124, 255, 0.08), transparent 28%),
        radial-gradient(circle at top right, rgba(38, 166, 154, 0.05), transparent 24%),
        linear-gradient(180deg, #061019 0%, #090f16 100%);
    color: #e5edf7;
}

[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background: transparent;
    color: #e5edf7;
}

header[data-testid="stHeader"] {
    background: rgba(5, 10, 18, 0.94);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid rgba(148, 163, 184, 0.18);
    min-height: 3.25rem;
}

header[data-testid="stHeader"] > div {
    background: transparent;
}

[data-testid="stToolbar"] {
    background: transparent;
    opacity: 1;
    visibility: visible;
}

[data-testid="stToolbar"] button,
[data-testid="stToolbar"] [role="button"] {
    color: #e5edf7;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #08111a 0%, #0c1520 100%);
    border-right: 1px solid rgba(148, 163, 184, 0.18);
}

[data-testid="stSidebar"] * {
    color: #e5edf7;
}

[data-testid="stSidebar"] [aria-selected="true"] span {
    color: #8fb3ff !important;
    font-weight: 700 !important;
}

[data-testid="stExpandSidebarButton"] span,
[data-testid="stExpandSidebarButton"] svg {
    color: white !important;
    fill: white !important;
}

[data-testid="collapsedControl"] span,
[data-testid="collapsedControl"] svg {
    color: white !important;
    fill: white !important;
}

.stButton > button,
button {
    border-radius: 8px;
}

[data-testid="stMetric"] {
    background: linear-gradient(180deg, rgba(15, 24, 36, 0.95), rgba(10, 18, 28, 0.95));
    border: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 12px;
}

hr {
    border-color: rgba(148, 163, 184, 0.18);
}

</style>
"""


def apply_global_theme(page_title: str | None = None, page_icon: str = "▲") -> None:
    try:
        st.set_page_config(
            page_title=page_title or "AlphaDesk",
            page_icon=page_icon,
            layout="wide",
            initial_sidebar_state="expanded",
        )
    except Exception:
        pass

    st.markdown(GLOBAL_THEME_CSS, unsafe_allow_html=True)