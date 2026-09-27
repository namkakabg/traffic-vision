"""Approved theme styling for TrafficVision."""

NAVY = "#0f172a"
BLUE_PRIMARY = "#0284c7"
TEAL_ACCENT = "#0d9488"
BG_LIGHT = "#f8fafc"
TEXT_DARK = "#0f172a"
BORDER_COLOR = "#e2e8f0"

CUSTOM_CSS = f"""
<style>
    /* Global font and background adjustments */
    .stApp {{
        background-color: {BG_LIGHT};
        color: {TEXT_DARK};
    }}

    /* Sidebar custom styling */
    [data-testid="stSidebar"] {{
        background-color: {NAVY} !important;
        color: #f8fafc !important;
    }}
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label {{
        color: #e2e8f0 !important;
    }}

    /* Card styling */
    .tv-card {{
        background: #ffffff;
        border-radius: 8px;
        padding: 1.25rem;
        border: 1px solid {BORDER_COLOR};
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
    }}

    /* Metric card */
    .tv-stat-card {{
        background: #ffffff;
        border-left: 4px solid {BLUE_PRIMARY};
        border-radius: 6px;
        padding: 1rem;
        border-top: 1px solid {BORDER_COLOR};
        border-right: 1px solid {BORDER_COLOR};
        border-bottom: 1px solid {BORDER_COLOR};
    }}

    .tv-badge {{
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: 600;
    }}
    .tv-badge-baseline {{
        background-color: #fef3c7;
        color: #92400e;
        border: 1px solid #fde68a;
    }}
    .tv-badge-production {{
        background-color: #d1fae5;
        color: #065f46;
        border: 1px solid #a7f3d0;
    }}
</style>
"""


def apply_theme(st) -> None:
    """Inject CSS styling into Streamlit page."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
