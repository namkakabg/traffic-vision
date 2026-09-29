"""Approved theme styling for TrafficVision matching design mockups."""

NAVY = "#0b1730"
NAVY_GRADIENT = "linear-gradient(180deg, #0b1730, #101f3c)"
BLUE_PRIMARY = "#2563eb"
BLUE_GRADIENT = "linear-gradient(135deg, #2563eb, #2876ef)"
TEAL_CYAN = "#17b6b1"
MARK_GRADIENT = "linear-gradient(135deg, #29d2c8, #3182ff)"
BG_LIGHT = "#f5f7fb"
TEXT_DARK = "#132238"
MUTED = "#6d7c91"
BORDER_COLOR = "#e4eaf1"

CUSTOM_CSS = f"""
<style>
    /* Global base settings */
    html, body, [class*="css"], .stApp {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        background-color: {BG_LIGHT};
        color: {TEXT_DARK};
    }}

    /* Main container padding */
    .block-container {{
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 1400px;
    }}

    /* Sidebar custom styling */
    [data-testid="stSidebar"] {{
        background: {NAVY_GRADIENT} !important;
        color: #d8e5f7 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }}
    [data-testid="stSidebar"] .block-container {{
        padding: 1.5rem 1rem !important;
    }}
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label {{
        color: #9fb0c8 !important;
    }}

    /* Radio navigation in sidebar */
    [data-testid="stSidebar"] [data-testid="stRadio"] {{
        background: transparent;
    }}
    [data-testid="stSidebar"] [data-testid="stRadio"] > div {{
        gap: 4px;
    }}
    [data-testid="stSidebar"] [data-testid="stRadio"] label {{
        padding: 8px 12px !important;
        border-radius: 9px !important;
        margin: 2px 0 !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        color: #9fb0c8 !important;
        transition: all 0.15s ease-in-out;
        cursor: pointer;
    }}
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {{
        background: rgba(255, 255, 255, 0.05);
        color: #ffffff !important;
    }}
    [data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"],
    [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {{
        background: rgba(65, 129, 255, 0.18) !important;
        color: #ffffff !important;
        box-shadow: inset 3px 0 #48cfc7 !important;
        font-weight: 700 !important;
    }}
    [data-testid="stSidebar"] [data-testid="stRadio"] input {{
        display: none !important;
    }}

    /* Brand Logo in sidebar */
    [data-testid="stSidebar"] [data-testid="stHeadingWithActionElements"] h1,
    [data-testid="stSidebar"] h1 {{
        font-size: 19px !important;
        font-weight: 850 !important;
        color: #ffffff !important;
        padding: 0 4px 14px 4px !important;
        margin: 0 !important;
        letter-spacing: -0.02em !important;
    }}
    .tv-brand {{
        display: flex;
        align-items: center;
        gap: 10px;
        color: #ffffff;
        font-weight: 800;
        font-size: 18px;
        padding: 0 4px 20px 4px;
        letter-spacing: -0.02em;
    }}
    .tv-mark {{
        display: grid;
        place-items: center;
        width: 34px;
        height: 34px;
        border-radius: 10px;
        background: {MARK_GRADIENT};
        box-shadow: 0 7px 20px rgba(37, 99, 235, 0.35);
        color: #ffffff;
        font-size: 18px;
        font-weight: 900;
    }}
    .tv-navlabel {{
        padding: 12px 8px 6px;
        font-size: 10px;
        color: #7f94b3;
        letter-spacing: 0.13em;
        text-transform: uppercase;
        font-weight: 700;
    }}

    /* Sidebar Model Card */
    .tv-modelcard {{
        margin-top: 2rem;
        padding: 12px 14px;
        border: 1px solid rgba(255, 255, 255, 0.09);
        background: rgba(255, 255, 255, 0.045);
        border-radius: 12px;
    }}
    .tv-online {{
        display: flex;
        gap: 7px;
        align-items: center;
        color: #8fe8c2;
        font-size: 11px;
        font-weight: 600;
    }}
    .tv-pulse {{
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #38d996;
        box-shadow: 0 0 0 4px rgba(56, 217, 150, 0.15);
        display: inline-block;
    }}
    .tv-pulse-amber {{
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #f59e0b;
        box-shadow: 0 0 0 4px rgba(245, 158, 11, 0.15);
        display: inline-block;
    }}
    .tv-modelname {{
        color: #ffffff;
        font-weight: 700;
        font-size: 13px;
        margin-top: 8px;
    }}
    .tv-modelmeta {{
        color: #7f94b3;
        font-size: 10px;
        margin-top: 3px;
    }}

    /* Top Page Header */
    .tv-top {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 20px;
        padding-bottom: 4px;
    }}
    .tv-eyebrow {{
        color: {BLUE_PRIMARY};
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        margin-bottom: 4px;
    }}
    .tv-title {{
        font-size: 24px;
        font-weight: 850;
        letter-spacing: -0.035em;
        color: {TEXT_DARK};
        margin: 2px 0 4px 0;
        line-height: 1.2;
    }}
    .tv-desc {{
        color: {MUTED};
        font-size: 12px;
        margin: 0;
    }}
    .tv-top-actions {{
        display: flex;
        align-items: center;
        gap: 10px;
    }}
    .tv-pill {{
        padding: 6px 12px;
        background: #ffffff;
        border: 1px solid {BORDER_COLOR};
        border-radius: 99px;
        color: #5f6f84;
        font-size: 11px;
        font-weight: 600;
        box-shadow: 0 2px 6px rgba(33, 49, 75, 0.03);
    }}
    .tv-avatar {{
        display: grid;
        place-items: center;
        width: 34px;
        height: 34px;
        border-radius: 50%;
        color: #ffffff;
        font-size: 11px;
        font-weight: 800;
        background: {BLUE_GRADIENT};
        box-shadow: 0 4px 10px rgba(37, 99, 235, 0.25);
    }}

    /* Panels / Cards */
    .tv-panel {{
        border: 1px solid {BORDER_COLOR};
        background: #ffffff;
        border-radius: 16px;
        box-shadow: 0 6px 18px rgba(33, 49, 75, 0.045);
        overflow: hidden;
        margin-bottom: 1.25rem;
    }}
    .tv-panelhead {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 14px 18px;
        border-bottom: 1px solid {BORDER_COLOR};
        background: #ffffff;
    }}
    .tv-paneltitle {{
        font-size: 13px;
        font-weight: 800;
        color: {TEXT_DARK};
    }}
    .tv-panelcontent {{
        padding: 16px 18px;
    }}

    /* Modern Tabs inside panels */
    [data-testid="stTabs"] [data-baseweb="tab-list"] {{
        gap: 4px;
        padding: 4px;
        background: #eef2f7;
        border-radius: 10px;
        border: none;
    }}
    [data-testid="stTabs"] [data-baseweb="tab"] {{
        padding: 6px 14px !important;
        border-radius: 7px !important;
        color: #7b899b !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        border: none !important;
        background: transparent !important;
    }}
    [data-testid="stTabs"] [aria-selected="true"] {{
        background: #ffffff !important;
        color: {BLUE_PRIMARY} !important;
        box-shadow: 0 2px 7px rgba(33, 49, 75, 0.09) !important;
    }}

    /* Stats Grid */
    .tv-stats {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin-bottom: 14px;
    }}
    .tv-stat {{
        padding: 12px 14px;
        border-radius: 12px;
        background: #f6f8fb;
        border: 1px solid #edf1f6;
    }}
    .tv-statnum {{
        font-size: 22px;
        font-weight: 850;
        letter-spacing: -0.04em;
        color: {TEXT_DARK};
        line-height: 1.1;
    }}
    .tv-statlabel {{
        margin-top: 4px;
        color: #7a8798;
        font-size: 10px;
        font-weight: 600;
    }}

    /* Detection Results List */
    .tv-section-label {{
        padding: 2px 0 8px 0;
        font-size: 10px;
        font-weight: 850;
        color: #6c798a;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }}
    .tv-detect {{
        margin-bottom: 14px;
        overflow: hidden;
        border: 1px solid {BORDER_COLOR};
        border-radius: 11px;
        background: #ffffff;
    }}
    .tv-row {{
        display: grid;
        grid-template-columns: 32px 1fr auto;
        align-items: center;
        gap: 10px;
        padding: 10px 12px;
        border-bottom: 1px solid #edf0f4;
    }}
    .tv-row:last-child {{
        border-bottom: 0;
    }}
    .tv-mini {{
        display: grid;
        place-items: center;
        width: 30px;
        height: 30px;
        border: 2.5px solid #e74747;
        border-radius: 50%;
        color: #233248;
        font-size: 11px;
        font-weight: 900;
        background: #ffffff;
        line-height: 1;
    }}
    .tv-rname {{
        font-size: 11px;
        font-weight: 800;
        color: {TEXT_DARK};
    }}
    .tv-rcode {{
        color: #8995a5;
        font-size: 9px;
        margin-top: 2px;
    }}
    .tv-score {{
        padding: 4px 8px;
        border-radius: 6px;
        background: #eaf8f3;
        color: #178561;
        text-align: center;
        font-size: 10px;
        font-weight: 900;
    }}

    /* Notice Banner */
    .tv-notice {{
        display: flex;
        gap: 8px;
        align-items: flex-start;
        margin-bottom: 14px;
        padding: 10px 12px;
        border-radius: 10px;
        color: #656f7d;
        background: #fff8e8;
        font-size: 10px;
        line-height: 1.45;
        border: 1px solid #fae8c8;
    }}

    /* Buttons */
    .stButton > button {{
        border-radius: 9px !important;
        font-weight: 700 !important;
        font-size: 12.5px !important;
        padding: 8px 18px !important;
        transition: all 0.15s ease-in-out !important;
        cursor: pointer !important;
    }}
    .stButton > button[kind="primary"] {{
        background: {BLUE_GRADIENT} !important;
        border: none !important;
        color: #ffffff !important;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.28) !important;
    }}
    .stButton > button[kind="primary"]:hover {{
        box-shadow: 0 8px 22px rgba(37, 99, 235, 0.42) !important;
        transform: translateY(-1px);
        color: #ffffff !important;
    }}
    .stButton > button:not([kind="primary"]) {{
        background: #ffffff !important;
        border: 1.5px solid {BORDER_COLOR} !important;
        color: #1e293b !important;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04) !important;
    }}
    .stButton > button:not([kind="primary"]):hover {{
        background: #f8fafc !important;
        border-color: #94a3b8 !important;
        color: {BLUE_PRIMARY} !important;
        transform: translateY(-1px);
        box-shadow: 0 3px 8px rgba(15, 23, 42, 0.08) !important;
    }}

    /* Form Submit Button */
    button[kind="primaryFormSubmit"],
    .stFormSubmitButton > button {{
        background: {BLUE_GRADIENT} !important;
        border: none !important;
        color: #ffffff !important;
        font-weight: 750 !important;
        font-size: 13px !important;
        border-radius: 9px !important;
        padding: 9px 22px !important;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.28) !important;
        transition: all 0.15s ease-in-out !important;
    }}
    button[kind="primaryFormSubmit"]:hover,
    .stFormSubmitButton > button:hover {{
        box-shadow: 0 8px 22px rgba(37, 99, 235, 0.42) !important;
        transform: translateY(-1px);
        color: #ffffff !important;
    }}

    /* Download Buttons */
    .stDownloadButton > button {{
        border-radius: 9px !important;
        font-weight: 700 !important;
        font-size: 12px !important;
        padding: 8px 16px !important;
        background: #ffffff !important;
        border: 1.5px solid {BORDER_COLOR} !important;
        color: #1e293b !important;
        transition: all 0.15s ease-in-out !important;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04) !important;
    }}
    .stDownloadButton > button:hover {{
        background: #f8fafc !important;
        border-color: {BLUE_PRIMARY} !important;
        color: {BLUE_PRIMARY} !important;
        transform: translateY(-1px);
        box-shadow: 0 3px 8px rgba(37, 99, 235, 0.15) !important;
    }}

    /* Stepper for Training */
    .tv-steps {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 8px;
        margin-bottom: 16px;
    }}
    .tv-step {{
        padding: 11px 12px;
        border: 1px solid {BORDER_COLOR};
        border-radius: 11px;
        color: #8390a2;
        background: #ffffff;
        font-size: 11px;
        font-weight: 750;
        display: flex;
        align-items: center;
    }}
    .tv-step b {{
        display: inline-grid;
        place-items: center;
        width: 21px;
        height: 21px;
        margin-right: 8px;
        border-radius: 50%;
        color: #ffffff;
        background: #aeb9c8;
        font-size: 10px;
    }}
    .tv-step.done {{
        color: #177456;
        border-color: #bce5d3;
        background: #f3fcf8;
    }}
    .tv-step.done b {{
        background: #29b681;
    }}
    .tv-step.active {{
        color: #1f5ac6;
        border-color: #b9cdfa;
        background: #f3f7ff;
    }}
    .tv-step.active b {{
        background: #2e6ce2;
        box-shadow: 0 0 0 4px #dbe8ff;
    }}

    /* Training Lab Live Progress */
    .tv-metricrow {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 9px;
        margin-bottom: 14px;
    }}
    .tv-metric {{
        padding: 11px;
        border-radius: 10px;
        background: #f6f8fb;
        border: 1px solid #edf1f6;
    }}
    .tv-num {{
        font-size: 18px;
        font-weight: 900;
        letter-spacing: -0.04em;
        color: {TEXT_DARK};
    }}
    .tv-label {{
        margin-top: 3px;
        color: #7e8a9a;
        font-size: 10px;
        font-weight: 600;
    }}
    .tv-log {{
        margin-top: 12px;
        padding: 12px;
        border-radius: 9px;
        color: #97a9bd;
        background: #0c1930;
        font: 10px/1.65 ui-monospace, SFMono-Regular, Menlo, monospace;
        border: 1px solid #182844;
    }}
    .tv-log strong {{
        color: #62dfb2;
    }}
    .tv-gpu {{
        padding: 6px 12px;
        border: 1px solid #bfe6d4;
        border-radius: 99px;
        color: #157557;
        background: #edfaf4;
        font-size: 11px;
        font-weight: 800;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }}
    .tv-footergrid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 14px;
        margin-top: 14px;
    }}
    .tv-smallbox {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 16px;
        border: 1px solid {BORDER_COLOR};
        border-radius: 12px;
        background: #ffffff;
    }}
    .tv-smalltitle {{
        font-size: 11px;
        font-weight: 850;
        color: {TEXT_DARK};
    }}
    .tv-smalltext {{
        margin-top: 3px;
        color: #8591a1;
        font-size: 10px;
    }}
    .tv-tag {{
        padding: 5px 8px;
        border-radius: 6px;
        color: #225fbc;
        background: #edf4ff;
        font-size: 10px;
        font-weight: 850;
    }}

    /* ============================================================ */
    /* Form Inputs & Controls Styling (High Contrast & Modern UI)   */
    /* ============================================================ */

    /* Input Labels */
    [data-testid="stWidgetLabel"] label,
    [data-testid="stWidgetLabel"] p,
    label[data-testid="stWidgetLabel"] {{
        color: #0f172a !important;
        font-size: 13px !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em !important;
        margin-bottom: 5px !important;
    }}
    [data-testid="stWidgetLabel"] svg {{
        fill: #64748b !important;
    }}

    /* Text Inputs, Number Inputs, Text Areas */
    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input,
    div[data-testid="stTextArea"] textarea,
    div[data-baseweb="input"] input,
    div[data-baseweb="base-input"] input,
    div[data-baseweb="textarea"] textarea {{
        background-color: #ffffff !important;
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        caret-color: {BLUE_PRIMARY} !important;
        font-size: 13.5px !important;
        font-weight: 500 !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 9px !important;
        padding: 9px 13px !important;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04) !important;
        transition: border-color 0.15s ease, box-shadow 0.15s ease, background-color 0.15s ease !important;
    }}

    /* BaseWeb Input Wrappers */
    div[data-baseweb="input"],
    div[data-baseweb="base-input"] {{
        background-color: #ffffff !important;
        border-radius: 9px !important;
        border: none !important;
    }}

    /* Hover & Focus state for inputs */
    div[data-testid="stTextInput"] input:hover,
    div[data-testid="stNumberInput"] input:hover,
    div[data-testid="stTextArea"] textarea:hover,
    div[data-baseweb="input"]:hover input,
    div[data-baseweb="base-input"]:hover input {{
        border-color: #94a3b8 !important;
    }}

    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stNumberInput"] input:focus,
    div[data-testid="stTextArea"] textarea:focus,
    div[data-baseweb="input"]:focus-within input,
    div[data-baseweb="base-input"]:focus-within input {{
        border-color: {BLUE_PRIMARY} !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.18) !important;
        outline: none !important;
    }}

    /* Placeholders */
    input::placeholder,
    textarea::placeholder,
    [data-baseweb="input"] input::placeholder,
    [data-baseweb="base-input"] input::placeholder {{
        color: #94a3b8 !important;
        -webkit-text-fill-color: #94a3b8 !important;
        opacity: 1 !important;
        font-weight: 400 !important;
    }}

    /* Number Input Stepper (+ / -) Buttons */
    div[data-testid="stNumberInput"] button,
    div[data-testid="stNumberInputStepUp"],
    div[data-testid="stNumberInputStepDown"],
    div[data-testid="stNumberInputContainer"] button {{
        background-color: #f8fafc !important;
        border: 1px solid #cbd5e1 !important;
        color: #1e293b !important;
        border-radius: 6px !important;
        margin: 2px !important;
        transition: all 0.15s ease !important;
    }}
    div[data-testid="stNumberInput"] button:hover,
    div[data-testid="stNumberInputStepUp"]:hover,
    div[data-testid="stNumberInputStepDown"]:hover,
    div[data-testid="stNumberInputContainer"] button:hover {{
        background-color: #eff6ff !important;
        border-color: #93c5fd !important;
        color: {BLUE_PRIMARY} !important;
    }}
    div[data-testid="stNumberInput"] button svg,
    div[data-testid="stNumberInputStepUp"] svg,
    div[data-testid="stNumberInputStepDown"] svg {{
        fill: #334155 !important;
        stroke: #334155 !important;
    }}
    div[data-testid="stNumberInput"] button:hover svg,
    div[data-testid="stNumberInputStepUp"]:hover svg,
    div[data-testid="stNumberInputStepDown"]:hover svg {{
        fill: {BLUE_PRIMARY} !important;
        stroke: {BLUE_PRIMARY} !important;
    }}

    /* Selectbox & Dropdown Menus */
    div[data-testid="stSelectbox"] div[data-baseweb="select"],
    div[data-baseweb="select"] {{
        background-color: #ffffff !important;
        border-radius: 9px !important;
    }}
    div[data-baseweb="select"] > div {{
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 9px !important;
        color: #0f172a !important;
        font-size: 13.5px !important;
        font-weight: 500 !important;
        min-height: 40px !important;
        padding: 2px 6px !important;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04) !important;
        transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
    }}
    div[data-baseweb="select"] > div:hover {{
        border-color: #94a3b8 !important;
    }}
    div[data-baseweb="select"]:focus-within > div {{
        border-color: {BLUE_PRIMARY} !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.18) !important;
    }}
    div[data-baseweb="select"] div[role="combobox"] {{
        color: #0f172a !important;
        font-weight: 500 !important;
    }}
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] div {{
        color: #0f172a !important;
    }}
    div[data-baseweb="select"] svg {{
        fill: #475569 !important;
    }}

    /* Dropdown Popover List */
    div[data-baseweb="popover"] {{
        background-color: #ffffff !important;
        border-radius: 10px !important;
        box-shadow: 0 12px 28px -4px rgba(15, 23, 42, 0.12), 0 6px 12px -4px rgba(15, 23, 42, 0.06) !important;
        border: 1px solid #e2e8f0 !important;
    }}
    div[data-baseweb="popover"] ul[role="listbox"] {{
        background-color: #ffffff !important;
        padding: 6px !important;
    }}
    div[data-baseweb="popover"] li[role="option"] {{
        background-color: transparent !important;
        color: #0f172a !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        border-radius: 7px !important;
        padding: 8px 12px !important;
        margin: 2px 0 !important;
        transition: background-color 0.1s ease !important;
    }}
    div[data-baseweb="popover"] li[role="option"]:hover,
    div[data-baseweb="popover"] li[role="option"][aria-selected="true"] {{
        background-color: #eff6ff !important;
        color: {BLUE_PRIMARY} !important;
        font-weight: 650 !important;
    }}

    /* File Uploader */
    [data-testid="stFileUploader"] section {{
        background: #ffffff !important;
        border: 2px dashed #cbd5e1 !important;
        border-radius: 14px !important;
        padding: 24px 16px !important;
        text-align: center !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.02) !important;
    }}
    [data-testid="stFileUploader"] section:hover {{
        border-color: {BLUE_PRIMARY} !important;
        background: #f8faff !important;
    }}
    [data-testid="stFileUploader"] section div,
    [data-testid="stFileUploader"] section span,
    [data-testid="stFileUploader"] section small {{
        color: #475569 !important;
    }}
    [data-testid="stFileUploader"] button {{
        background: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        color: #1e293b !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        padding: 6px 16px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
    }}
    [data-testid="stFileUploader"] button:hover {{
        border-color: {BLUE_PRIMARY} !important;
        color: {BLUE_PRIMARY} !important;
        background: #eff6ff !important;
    }}
    [data-testid="stFileUploaderFile"] {{
        background: #f1f5f9 !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 9px !important;
        color: #0f172a !important;
        font-weight: 500 !important;
        padding: 8px 12px !important;
    }}
    [data-testid="stFileUploaderFile"] * {{
        color: #0f172a !important;
    }}

    /* Upload Bar */
    .tv-uploadbar {{
        margin: 10px 0 14px 0;
        padding: 10px 14px;
        background: #f8fafc;
        border: 1px solid {BORDER_COLOR};
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }}
    .tv-file {{
        display: flex;
        align-items: center;
        gap: 8px;
        color: {TEXT_DARK};
        font-size: 11px;
    }}

    /* Form Container */
    [data-testid="stForm"] {{
        background: #ffffff !important;
        border: 1px solid {BORDER_COLOR} !important;
        border-radius: 14px !important;
        padding: 20px 22px !important;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.03) !important;
    }}

    /* Sliders */
    [data-testid="stSlider"] div[data-baseweb="slider"] {{
        padding: 8px 0 !important;
    }}
    [data-testid="stSlider"] [role="slider"] {{
        background-color: {BLUE_PRIMARY} !important;
        border: 2px solid #ffffff !important;
        box-shadow: 0 2px 6px rgba(37, 99, 235, 0.45) !important;
        width: 18px !important;
        height: 18px !important;
    }}
    [data-testid="stSlider"] div[data-testid="stMarkdownContainer"] p {{
        color: #0f172a !important;
        font-weight: 650 !important;
    }}

    /* Checkbox */
    [data-testid="stCheckbox"] label span {{
        color: #1e293b !important;
        font-size: 13px !important;
        font-weight: 550 !important;
    }}
    [data-testid="stCheckbox"] [data-checked="true"] {{
        background-color: {BLUE_PRIMARY} !important;
    }}

    /* Expanders */
    [data-testid="stExpander"] {{
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03) !important;
        overflow: hidden !important;
        margin-bottom: 14px !important;
    }}
    [data-testid="stExpander"] summary {{
        color: #0f172a !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        padding: 12px 16px !important;
        background: #ffffff !important;
        border-radius: 12px !important;
        transition: color 0.15s ease, background 0.15s ease !important;
    }}
    [data-testid="stExpander"] summary:hover {{
        color: {BLUE_PRIMARY} !important;
        background: #f8fafc !important;
    }}
    [data-testid="stExpander"] summary svg {{
        fill: #64748b !important;
    }}
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] {{
        padding: 16px !important;
        border-top: 1px solid #edf1f6 !important;
    }}

    /* Metric Cards */
    [data-testid="stMetric"] {{
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        padding: 14px 18px !important;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.03) !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease !important;
    }}
    [data-testid="stMetric"]:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.06) !important;
    }}
    [data-testid="stMetricLabel"] p {{
        color: #64748b !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
    }}
    [data-testid="stMetricValue"] {{
        color: #0f172a !important;
        font-weight: 850 !important;
        font-size: 26px !important;
        letter-spacing: -0.04em !important;
    }}

    /* Alerts */
    [data-testid="stAlert"] {{
        border-radius: 11px !important;
        font-size: 12.5px !important;
        font-weight: 550 !important;
        border: 1px solid rgba(0, 0, 0, 0.06) !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02) !important;
        padding: 12px 16px !important;
    }}
    [data-testid="stAlert"] p {{
        font-size: 12.5px !important;
        line-height: 1.5 !important;
    }}

    /* Progress Bar */
    [data-testid="stProgress"] > div {{
        background-color: #e2e8f0 !important;
        border-radius: 99px !important;
        height: 8px !important;
        overflow: hidden !important;
    }}
    [data-testid="stProgress"] div[role="progressbar"] {{
        background: linear-gradient(90deg, #2563eb, #38bdf8) !important;
        border-radius: 99px !important;
    }}

    /* Dataframe / Tables */
    [data-testid="stDataFrame"] {{
        border: 1px solid #e2e8f0 !important;
        border-radius: 11px !important;
        overflow: hidden !important;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.02) !important;
    }}

    /* Sidebar specific input adjustments if placed in sidebar */
    [data-testid="stSidebar"] div[data-baseweb="input"] input,
    [data-testid="stSidebar"] div[data-baseweb="select"] > div {{
        background-color: rgba(255, 255, 255, 0.08) !important;
        color: #ffffff !important;
        border-color: rgba(255, 255, 255, 0.18) !important;
    }}

    /* Code elements */
    code {{
        background: #eef2f7 !important;
        color: #0f172a !important;
        padding: 2px 6px !important;
        border-radius: 5px !important;
        font-size: 88% !important;
        border: 1px solid #e2e8f0 !important;
    }}

    /* Sleek Custom Scrollbars */
    ::-webkit-scrollbar {{
        width: 7px;
        height: 7px;
    }}
    ::-webkit-scrollbar-track {{
        background: transparent;
    }}
    ::-webkit-scrollbar-thumb {{
        background: #cbd5e1;
        border-radius: 99px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: #94a3b8;
    }}

    /* Card styling for other pages */
    .tv-card {{
        background: #ffffff;
        border-radius: 14px;
        padding: 1.5rem;
        border: 1px solid {BORDER_COLOR};
        box-shadow: 0 4px 14px rgba(33, 49, 75, 0.04);
        margin-bottom: 1.2rem;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }}
    .tv-card:hover {{
        box-shadow: 0 8px 24px rgba(33, 49, 75, 0.07);
    }}

    .tv-badge {{
        display: inline-block;
        padding: 0.3rem 0.7rem;
        border-radius: 7px;
        font-size: 0.8rem;
        font-weight: 750;
        letter-spacing: 0.03em;
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


def clean_html(html_str: str) -> str:
    """Strip leading/trailing whitespace from each line so Markdown doesn't treat indented HTML as a code block."""
    return "\n".join(line.strip() for line in html_str.splitlines() if line.strip())
