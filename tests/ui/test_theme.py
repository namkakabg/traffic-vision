import tomllib
from pathlib import Path
from unittest.mock import MagicMock

from trafficvision.ui.theme import CUSTOM_CSS, apply_theme, clean_html


def test_theme_css_contains_input_contrast_rules():
    """Verify that CUSTOM_CSS includes high-contrast rules for inputs, selectboxes, and buttons."""
    # Check input background & text color
    assert 'div[data-testid="stTextInput"] input' in CUSTOM_CSS
    assert 'div[data-testid="stNumberInput"] input' in CUSTOM_CSS
    assert 'div[data-testid="stSelectbox"]' in CUSTOM_CSS
    assert "background-color: #ffffff !important;" in CUSTOM_CSS
    assert "-webkit-text-fill-color: #0f172a !important;" in CUSTOM_CSS
    assert "caret-color: #2563eb !important;" in CUSTOM_CSS
    assert "border: 1.5px solid #cbd5e1 !important;" in CUSTOM_CSS

    # Check button styling
    assert '.stButton > button[kind="primary"]' in CUSTOM_CSS
    assert 'button[kind="primaryFormSubmit"]' in CUSTOM_CSS
    assert ".stDownloadButton > button" in CUSTOM_CSS

    # Check dropdown menu popover styling
    assert 'div[data-baseweb="popover"]' in CUSTOM_CSS
    assert 'li[role="option"]' in CUSTOM_CSS


def test_streamlit_config_theme():
    """Verify that .streamlit/config.toml uses proper light theme colors without dark input conflict."""
    config_path = Path(__file__).parents[2] / ".streamlit" / "config.toml"
    assert config_path.is_file()

    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    theme = data.get("theme", {})
    assert theme.get("secondaryBackgroundColor") == "#ffffff"
    assert theme.get("primaryColor") == "#2563eb"
    assert theme.get("backgroundColor") == "#f8fafc"
    assert theme.get("textColor") == "#0f172a"


def test_apply_theme_calls_markdown():
    """Verify apply_theme properly calls st.markdown with unsafe_allow_html."""
    mock_st = MagicMock()
    apply_theme(mock_st)
    mock_st.markdown.assert_called_once_with(CUSTOM_CSS, unsafe_allow_html=True)


def test_clean_html():
    raw_html = """
        <div>
            <span>Hello</span>
        </div>
    """
    cleaned = clean_html(raw_html)
    assert cleaned == "<div>\n<span>Hello</span>\n</div>"
