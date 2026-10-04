import base64
from pathlib import Path

import streamlit as st
import plotly.io as pio

from data_loader import load_flat, load_neemanim, apply_filters
from tabs import home, overview, dropouts, completions, risk_factors, durations, trustees, data_table, crosstab


ISRAEL_IMAGE_PATH = Path(__file__).resolve().parent / "Israel_image.jpg"


def _israel_image_data_uri() -> str:
    data = ISRAEL_IMAGE_PATH.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


st.set_page_config(
    page_title="דאשבורד חדלות פירעון",
    layout="wide",
    initial_sidebar_state="expanded",
)


CUSTOM_CSS = """
<style>
:root {
    --brand: #1f4e79;
    --brand-2: #3a8fb7;
    --brand-light: #e8eef5;
    --ink: #1a1a1a;
    --muted: #6b7280;
    --line: #e5e7eb;
    --bg: #ffffff;
    --card-shadow: 0 2px 8px rgba(31, 78, 121, 0.06);
    --card-shadow-hover: 0 4px 14px rgba(31, 78, 121, 0.12);
}
html, body, [class*="css"] {
    direction: rtl;
    text-align: right;
    color: var(--ink) !important;
    font-family: "Assistant", "Rubik", "Segoe UI", sans-serif;
}
section[data-testid="stSidebar"] {
    direction: rtl;
    text-align: right;
    background: rgba(255,255,255,0.35) !important;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border-left: 1px solid rgba(31,78,121,0.12);
    box-shadow: -2px 0 12px rgba(0,0,0,0.04);
}
section[data-testid="stSidebar"] > div { background: transparent !important; }
/* Roomier sidebar */
section[data-testid="stSidebar"] {
    width: 290px !important;
    min-width: 290px !important;
}
section[data-testid="stSidebar"] > div:first-child {
    padding: 1.4rem 1.1rem 1.8rem 1.1rem !important;
}
section[data-testid="stSidebar"] [data-testid="stHeading"] {
    margin-top: 0.4rem !important;
    margin-bottom: 1rem !important;
}
section[data-testid="stSidebar"] hr {
    margin: 1.4rem 0 !important;
}
/* Breathing room between filter widgets */
section[data-testid="stSidebar"] [data-testid="stMultiSelect"],
section[data-testid="stSidebar"] [data-testid="stSelectbox"] {
    margin-bottom: 0.75rem !important;
}
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] {
    margin-bottom: 0.35rem !important;
    font-weight: 600 !important;
}
h1 {
    color: var(--brand);
    font-weight: 700;
    letter-spacing: -0.5px;
    border-bottom: 3px solid var(--brand);
    padding-bottom: 8px;
    display: inline-block;
}
h2, h3 { color: var(--ink); font-weight: 600; }
h2, h3, h4, h5, h6, p, li, label { direction: rtl; text-align: right; }
h1 { direction: rtl; text-align: center; }
/* Center the app title block (Streamlit wraps h1 in a markdown container) */
.main .block-container > div:first-child [data-testid="stMarkdownContainer"]:has(h1),
[data-testid="stHeading"]:has(h1) {
    text-align: center !important;
}
[data-testid="stHeading"] h1,
[data-testid="stMarkdownContainer"] h1 {
    display: inline-block;
    margin-left: auto;
    margin-right: auto;
}
[data-testid="stMetricLabel"] {
    direction: rtl; text-align: right;
    color: var(--muted); font-size: 0.85rem; font-weight: 500;
}
[data-testid="stMetricValue"] {
    direction: rtl; text-align: right;
    color: var(--brand); font-weight: 700; font-size: 1.6rem;
}
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.85);
    backdrop-filter: blur(6px);
    -webkit-backdrop-filter: blur(6px);
    border: 1px solid var(--line);
    border-right: 3px solid var(--brand);
    border-radius: 10px;
    padding: 14px 18px;
    box-shadow: var(--card-shadow);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: var(--card-shadow-hover);
}
div[data-baseweb="tab-list"] {
    direction: rtl;
    background: linear-gradient(180deg, rgba(255,255,255,0.95), rgba(248,250,252,0.9));
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border: 1px solid var(--line);
    border-bottom: 2px solid var(--brand);
    border-radius: 12px 12px 0 0;
    gap: 6px;
    padding: 8px 10px 0 10px;
    box-shadow: var(--card-shadow);
}
button[data-baseweb="tab"] {
    font-weight: 600;
    font-size: 0.98rem;
    color: var(--muted);
    padding: 12px 22px;
    border-radius: 10px 10px 0 0;
    border: 1px solid transparent;
    border-bottom: none;
    transition: background 0.18s ease, color 0.18s ease, transform 0.18s ease, border-color 0.18s ease;
    position: relative;
    top: 1px;
}
button[data-baseweb="tab"]:hover {
    background: var(--brand-light);
    color: var(--brand);
    transform: translateY(-1px);
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: var(--brand) !important;
    background: #ffffff !important;
    border: 1px solid var(--line) !important;
    border-bottom: 3px solid var(--brand) !important;
    font-weight: 700;
    box-shadow: 0 -2px 8px rgba(31,78,121,0.08);
}
button[data-baseweb="tab"] > div[data-testid="stMarkdownContainer"] p {
    margin: 0 !important;
    line-height: 1.2 !important;
}
.stDataFrame, [data-testid="stDataFrame"] {
    direction: rtl;
    border: 1px solid var(--line);
    border-radius: 10px;
    overflow: hidden;
    background: rgba(255,255,255,0.95);
    box-shadow: var(--card-shadow);
}
.stAlert {
    direction: rtl; text-align: right;
    border-radius: 10px;
    background: rgba(255,255,255,0.9) !important;
    backdrop-filter: blur(4px);
    -webkit-backdrop-filter: blur(4px);
    box-shadow: var(--card-shadow);
}
div[data-testid="stMarkdownContainer"] p { line-height: 1.6; }
hr {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--line) 20%, var(--line) 80%, transparent);
    margin: 1.75rem 0;
}
.stSelectbox, .stMultiSelect { direction: rtl; }
.stSlider { direction: ltr; }
.js-plotly-plot, .plot-container {
    border-radius: 10px;
    background: rgba(255,255,255,0.85) !important;
    padding: 8px 8px 8px 8px;
    box-shadow: var(--card-shadow);
    overflow: visible !important;
    position: relative;
}
/* Ensure Plotly modebar (zoom, pan, download, fullscreen icons) is always visible */
.js-plotly-plot .plotly .modebar,
.js-plotly-plot .modebar,
.modebar-container {
    opacity: 1 !important;
    visibility: visible !important;
    z-index: 100 !important;
    position: absolute !important;
    top: 6px !important;
    right: 10px !important;
    left: auto !important;
    background: rgba(255,255,255,0.92) !important;
    border-radius: 6px !important;
    padding: 2px 4px !important;
    box-shadow: 0 1px 4px rgba(31,78,121,0.10);
    display: flex !important;
    flex-direction: row !important;
    gap: 2px;
}
.js-plotly-plot .modebar-group {
    background: transparent !important;
    display: inline-flex !important;
}
.js-plotly-plot .modebar-btn {
    color: #1f4e79 !important;
    opacity: 0.85 !important;
    display: inline-block !important;
}
.js-plotly-plot .modebar-btn:hover {
    opacity: 1 !important;
    color: #3a8fb7 !important;
}
.js-plotly-plot .modebar-btn path {
    fill: currentColor !important;
}
/* Chart/table toggle segmented control — fit in narrow side column */
div[data-testid="stSegmentedControl"] {
    direction: ltr;
    width: 100% !important;
    overflow: visible !important;
}
div[data-testid="stSegmentedControl"] > div {
    flex-wrap: nowrap !important;
    justify-content: flex-start !important;
    gap: 4px !important;
}
div[data-testid="stSegmentedControl"] button,
div[data-testid="stSegmentedControl"] label {
    min-width: 42px !important;
    padding: 6px 10px !important;
    white-space: nowrap !important;
    border: 2px solid var(--brand) !important;
    background: #ffffff !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 3px rgba(31,78,121,0.12) !important;
    transition: background 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease, border-color 0.15s ease !important;
    outline: none !important;
}
div[data-testid="stSegmentedControl"] button:hover,
div[data-testid="stSegmentedControl"] label:hover {
    background: var(--brand-light) !important;
    transform: translateY(-1px);
    box-shadow: 0 2px 6px rgba(31,78,121,0.20) !important;
}
/* Streamlit uses kind="segmented_controlActive" on the active button */
div[data-testid="stSegmentedControl"] button[kind="segmented_controlActive"],
div[data-testid="stSegmentedControl"] button[aria-checked="true"],
div[data-testid="stSegmentedControl"] button[aria-selected="true"],
div[data-testid="stSegmentedControl"] button[data-selected="true"],
div[data-testid="stSegmentedControl"] label[data-selected="true"],
div[data-testid="stSegmentedControl"] label:has(input:checked) {
    background: var(--brand) !important;
    border: 2px solid var(--brand) !important;
    box-shadow: 0 0 0 3px rgba(31,78,121,0.20), 0 2px 8px rgba(31,78,121,0.28) !important;
}
div[data-testid="stSegmentedControl"] button[kind="segmented_controlActive"] span[data-testid="stIconMaterial"],
div[data-testid="stSegmentedControl"] button[kind="segmented_controlActive"] span.material-symbols-rounded,
div[data-testid="stSegmentedControl"] button[aria-checked="true"] span[data-testid="stIconMaterial"],
div[data-testid="stSegmentedControl"] button[aria-checked="true"] span.material-symbols-rounded,
div[data-testid="stSegmentedControl"] label:has(input:checked) span[data-testid="stIconMaterial"],
div[data-testid="stSegmentedControl"] label:has(input:checked) span.material-symbols-rounded {
    color: #ffffff !important;
}
div[data-testid="stSegmentedControl"] button span[data-testid="stIconMaterial"],
div[data-testid="stSegmentedControl"] button span.material-symbols-rounded,
div[data-testid="stSegmentedControl"] label span[data-testid="stIconMaterial"],
div[data-testid="stSegmentedControl"] label span.material-symbols-rounded {
    font-size: 20px !important;
    color: var(--brand) !important;
    display: inline-flex !important;
    align-items: center;
    justify-content: center;
    line-height: 1 !important;
}
[data-testid="stSubheader"] {
    color: var(--brand);
    font-weight: 700;
    margin-top: 8px;
}
/* Sidebar category radio — rendered as pill buttons (no circles) */
section[data-testid="stSidebar"] div[data-testid="stRadio"] > div {
    gap: 10px !important;
    display: flex !important;
    flex-direction: column !important;
}
section[data-testid="stSidebar"] label[data-baseweb="radio"] {
    width: 100% !important;
    padding: 11px 14px !important;
    background: #ffffff !important;
    border: 1px solid var(--line) !important;
    border-radius: 12px !important;
    cursor: pointer !important;
    transition: background 0.18s ease, border-color 0.18s ease, transform 0.18s ease, box-shadow 0.18s ease !important;
    box-shadow: 0 1px 3px rgba(31,78,121,0.06) !important;
    margin: 0 !important;
    display: flex !important;
    align-items: center !important;
    direction: rtl !important;
}
section[data-testid="stSidebar"] label[data-baseweb="radio"]:hover {
    background: var(--brand-light) !important;
    border-color: var(--brand-2) !important;
    transform: translateX(-3px);
    box-shadow: 0 4px 12px rgba(31,78,121,0.14) !important;
}
/* Hide the radio circle + native input */
section[data-testid="stSidebar"] label[data-baseweb="radio"] > div:first-child,
section[data-testid="stSidebar"] label[data-baseweb="radio"] input {
    display: none !important;
}
/* Label text */
section[data-testid="stSidebar"] label[data-baseweb="radio"] > div {
    width: 100% !important;
    font-weight: 600 !important;
    color: var(--ink) !important;
    font-size: 1.03rem !important;
    direction: rtl !important;
    text-align: right !important;
    line-height: 1.4 !important;
}
section[data-testid="stSidebar"] label[data-baseweb="radio"] p {
    margin: 0 !important;
    color: var(--ink) !important;
    font-weight: 600 !important;
}
/* Selected state */
section[data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked) {
    background: linear-gradient(135deg, var(--brand), var(--brand-2)) !important;
    border-color: var(--brand) !important;
    box-shadow: 0 4px 14px rgba(31,78,121,0.30) !important;
}
section[data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked) > div,
section[data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked) p {
    color: #ffffff !important;
    font-weight: 700 !important;
}
/* Prevent tab / column content from clipping absolute-positioned icons */
[data-testid="stHorizontalBlock"],
[data-testid="stVerticalBlock"],
[data-testid="column"],
[data-testid="stTabsContent"] {
    overflow: visible !important;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


ISRAEL_FLAG_HTML = f"""
<div class="israel-corner">
  <img src="{_israel_image_data_uri()}" alt="Israel">
</div>
"""
CORNER_CSS = """
<style>
.israel-corner {
    position: fixed;
    top: 72px;
    left: 24px;
    width: 108px;
    height: 108px;
    z-index: 9999;
    border: 1px solid rgba(31,78,121,0.15);
    border-radius: 14px;
    overflow: hidden;
    background: #ffffff;
    box-shadow: 0 6px 18px rgba(31,78,121,0.18), 0 0 0 4px rgba(255,255,255,0.6);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.israel-corner:hover {
    transform: translateY(-2px) scale(1.03);
    box-shadow: 0 6px 20px rgba(31,78,121,0.22), 0 0 0 4px rgba(255,255,255,0.7);
}
.israel-corner img { width: 100%; height: 100%; object-fit: cover; display: block; }

@keyframes float-a {
    0%, 100% { transform: translate(0, 0); }
    50% { transform: translate(20px, -18px); }
}
@keyframes float-b {
    0%, 100% { transform: translate(0, 0); }
    50% { transform: translate(-16px, 22px); }
}
@keyframes float-c {
    0%, 100% { transform: translate(0, 0); }
    50% { transform: translate(14px, 14px); }
}

.bubbles-bg {
    position: fixed;
    inset: 0;
    z-index: 0;
    pointer-events: none;
    overflow: hidden;
    background:
        radial-gradient(circle 120px at 8% 12%, rgba(31,78,121,0.09), transparent 70%),
        radial-gradient(circle 160px at 82% 18%, rgba(58,143,183,0.08), transparent 70%),
        radial-gradient(circle 200px at 91% 62%, rgba(58,143,183,0.07), transparent 70%),
        radial-gradient(circle 130px at 45% 92%, rgba(31,78,121,0.07), transparent 70%),
        radial-gradient(circle 140px at 15% 45%, rgba(31,78,121,0.06), transparent 70%),
        radial-gradient(circle 100px at 55% 65%, rgba(58,143,183,0.07), transparent 70%),
        radial-gradient(circle 130px at 30% 30%, rgba(58,143,183,0.06), transparent 70%),
        linear-gradient(135deg, #ffffff 0%, #f7fbff 50%, #ffffff 100%);
}
.bubble {
    position: absolute;
    border-radius: 50%;
    filter: blur(1px);
    opacity: 0.55;
    background: radial-gradient(circle at 30% 30%,
        rgba(58,143,183,0.28), rgba(31,78,121,0.14) 55%, rgba(31,78,121,0) 75%);
    box-shadow: inset 0 0 20px rgba(255,255,255,0.4);
}
.bubble.b1 { width: 70px; height: 70px; top: 8%; left: 4%; animation: float-a 22s ease-in-out infinite; }
.bubble.b2 { width: 110px; height: 110px; top: 22%; left: 78%; animation: float-b 28s ease-in-out infinite; }
.bubble.b3 { width: 55px; height: 55px; top: 78%; left: 12%; animation: float-c 20s ease-in-out infinite; }
.bubble.b4 { width: 140px; height: 140px; top: 62%; left: 88%; animation: float-a 32s ease-in-out infinite; }
.bubble.b5 { width: 45px; height: 45px; top: 35%; left: 60%; animation: float-b 18s ease-in-out infinite; }
.bubble.b6 { width: 90px; height: 90px; top: 90%; left: 42%; animation: float-c 26s ease-in-out infinite; }
.bubble.b7 { width: 60px; height: 60px; top: 6%; left: 55%; animation: float-a 24s ease-in-out infinite; }
.bubble.b8 { width: 80px; height: 80px; top: 48%; left: 2%; animation: float-b 30s ease-in-out infinite; }
.bubble.b9 { width: 40px; height: 40px; top: 88%; left: 72%; animation: float-c 19s ease-in-out infinite; }
.bubble.b10 { width: 100px; height: 100px; top: 30%; left: 35%; animation: float-a 34s ease-in-out infinite; }

.stApp > header,
header[data-testid="stHeader"] {
    background: transparent !important;
    backdrop-filter: blur(6px);
    -webkit-backdrop-filter: blur(6px);
}
[data-testid="stDecoration"] { display: none !important; }
/* Ensure the sidebar expand/collapse chevrons stay visible and tinted */
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"] {
    visibility: visible !important;
    display: flex !important;
    opacity: 1 !important;
    z-index: 1000 !important;
}
[data-testid="stSidebarCollapsedControl"] button,
[data-testid="collapsedControl"] button,
[data-testid="stSidebarCollapseButton"] button {
    color: var(--brand) !important;
    opacity: 1 !important;
}
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
section.main { background: transparent !important; }
.main .block-container,
[data-testid="stAppViewContainer"] .main .block-container,
section.main > div.block-container {
    position: relative;
    z-index: 1;
    padding-top: 0.5rem !important;
    margin-top: 0 !important;
}
</style>
<div class="bubbles-bg">
  <div class="bubble b1"></div>
  <div class="bubble b2"></div>
  <div class="bubble b3"></div>
  <div class="bubble b4"></div>
  <div class="bubble b5"></div>
  <div class="bubble b6"></div>
  <div class="bubble b7"></div>
  <div class="bubble b8"></div>
  <div class="bubble b9"></div>
  <div class="bubble b10"></div>
</div>
"""
st.markdown(CORNER_CSS, unsafe_allow_html=True)


PLOTLY_TEMPLATE = pio.templates["plotly_white"]
PLOTLY_TEMPLATE.layout.colorway = [
    "#1f4e79", "#e07b39", "#4a8b3f", "#c94f4f",
    "#8a5cb8", "#3a8fb7", "#d4a017", "#6b7280",
]
PLOTLY_TEMPLATE.layout.font = dict(family="Assistant, Rubik, sans-serif", size=13, color="#1a1a1a")
PLOTLY_TEMPLATE.layout.paper_bgcolor = "#ffffff"
PLOTLY_TEMPLATE.layout.plot_bgcolor = "#ffffff"
PLOTLY_TEMPLATE.layout.margin = dict(t=50, r=30, l=30, b=60, pad=6)
PLOTLY_TEMPLATE.layout.autosize = True
PLOTLY_TEMPLATE.layout.uniformtext = dict(mode="hide", minsize=10)
PLOTLY_TEMPLATE.layout.xaxis = dict(automargin=True, tickfont=dict(size=12), tickangle=0)
PLOTLY_TEMPLATE.layout.yaxis = dict(automargin=True, tickfont=dict(size=12))
PLOTLY_TEMPLATE.layout.legend = dict(font=dict(size=12))
pio.templates.default = "plotly_white"


df_flat = load_flat()
df_neemanim = load_neemanim()


TAB_ITEMS = [
    ("🏠", "בית"),
    ("📊", "סקירה ופרופיל"),
    ("📉", "נשירה"),
    ("✅", "מסיימים"),
    ("⚠️", "גורמי סיכון"),
    ("⏱️", "משך ותשלומים"),
    ("👥", "נאמנים"),
    ("🔀", "טבלת הצלבה"),
    ("📋", "טבלת נתונים"),
]
tab_labels = [f"{icon}  {name}" for icon, name in TAB_ITEMS]
_tab_name_by_label = {f"{icon}  {name}": name for icon, name in TAB_ITEMS}

st.sidebar.header("קטגוריות")
_selected_label = st.sidebar.radio(
    "בחירת קטגוריה",
    tab_labels,
    label_visibility="collapsed",
)
selected_tab = _tab_name_by_label[_selected_label]

st.sidebar.markdown("---")
st.sidebar.header("סינון גלובלי")

years = sorted(df_flat["year"].dropna().unique().tolist())
selected_years = st.sidebar.multiselect("שנת פתיחה", years, default=years)

mahozot = sorted(df_flat["mahoz"].dropna().unique().tolist())
selected_mahoz = st.sidebar.multiselect("מחוז", mahozot, default=mahozot)

genders = sorted(df_flat["gender_label"].dropna().unique().tolist())
selected_genders = st.sidebar.multiselect("מגדר", genders, default=genders)

statuses = sorted(df_flat["status_d_15032026"].dropna().unique().tolist())
selected_statuses = st.sidebar.multiselect("סטטוס תיק", statuses, default=statuses)

sectors = sorted(df_flat["sector_label"].dropna().unique().tolist())
selected_sectors = st.sidebar.multiselect("מגזר", sectors, default=sectors)

siyua_opts = sorted(df_flat["siyua_label"].dropna().unique().tolist())
selected_siyua = st.sidebar.multiselect("סיוע משפטי", siyua_opts, default=siyua_opts)

# Age bins are ordered manually (Hebrew sort is not natural here)
AGE_ORDER = ["19-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"]
age_bins_all = [b for b in AGE_ORDER if b in df_flat["age_bin"].dropna().unique().tolist()]
selected_age_bins = st.sidebar.multiselect("קבוצת גיל", age_bins_all, default=age_bins_all)

filters = {
    "years": selected_years,
    "mahoz": selected_mahoz,
    "gender_labels": selected_genders,
    "statuses": selected_statuses,
    "sectors": selected_sectors,
    "siyua": selected_siyua,
    "age_bins": selected_age_bins,
}

df_filtered = apply_filters(df_flat, filters)

st.sidebar.markdown("---")
st.sidebar.metric("תיקים לאחר סינון", f"{len(df_filtered):,}")
st.sidebar.caption(f"מתוך {len(df_flat):,} תיקים בקובץ")

def _show_common_header():
    st.caption(
        f"הדאשבורד מציג את הדאטה המלא; נתונים כאן , {len(df_flat):,} תיקים (2020–2022) כל שלבי ההליך"
    )
    st.info(
        "🔒 שמות הנאמנים והחייבים חסויים. לצורכי פרטיות הוחלפו בכל התצוגות "
        "במזהים אנונימיים (P001, P002, …). כל הזיהויים בטבלאות, בתרשימים "
        "ובחיפוש מתייחסים למזהים אלה בלבד — לא לשמות אמיתיים."
    )


if selected_tab == "בית":
    home.render(df_flat, df_neemanim)
elif selected_tab == "סקירה ופרופיל":
    _show_common_header()
    overview.render(df_filtered, df_neemanim)
elif selected_tab == "נשירה":
    _show_common_header()
    dropouts.render(df_filtered, df_neemanim)
elif selected_tab == "מסיימים":
    _show_common_header()
    completions.render(df_filtered, df_neemanim)
elif selected_tab == "גורמי סיכון":
    _show_common_header()
    risk_factors.render(df_filtered, df_neemanim)
elif selected_tab == "משך ותשלומים":
    _show_common_header()
    durations.render(df_filtered, df_neemanim)
elif selected_tab == "נאמנים":
    _show_common_header()
    trustees.render(df_filtered, df_neemanim)
elif selected_tab == "טבלת הצלבה":
    _show_common_header()
    crosstab.render(df_filtered, df_neemanim)
elif selected_tab == "טבלת נתונים":
    _show_common_header()
    data_table.render(df_filtered, df_neemanim)
