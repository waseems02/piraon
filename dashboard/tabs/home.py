import base64
from pathlib import Path
from textwrap import dedent

import pandas as pd
import streamlit as st


ISRAEL_IMAGE_PATH = Path(__file__).resolve().parent.parent / "Israel_image.jpg"


def _israel_image_data_uri() -> str:
    data = ISRAEL_IMAGE_PATH.read_bytes()
    return f"data:image/jpeg;base64,{base64.b64encode(data).decode('ascii')}"


HERO_CSS = """
<style>
.home-content {
    position: relative;
    z-index: 2;
    min-height: calc(100vh - 260px);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 30px 20px 30px;
    direction: rtl;
    text-align: center;
}

.home-eyebrow {
    display: inline-block;
    padding: 9px 22px;
    background: linear-gradient(135deg, rgba(31,78,121,0.06), rgba(58,143,183,0.06));
    border: 1px solid rgba(31,78,121,0.25);
    color: #1f4e79;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 5px;
    margin-bottom: 32px;
    text-transform: uppercase;
}

.home-title {
    font-size: 4.4rem;
    color: #0d2a47;
    font-weight: 900;
    letter-spacing: -2.5px;
    line-height: 1.02;
    margin: 0 0 26px 0;
    text-shadow: 0 2px 20px rgba(31,78,121,0.08);
    border-bottom: none !important;
    padding-bottom: 0 !important;
}
.home-title .accent {
    background: linear-gradient(90deg, #3a8fb7 0%, #1f4e79 100%);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
}

.home-subtitle {
    font-size: 1rem;
    color: #6b7280;
    font-weight: 500;
    letter-spacing: 1.5px;
    margin: 0 0 20px 0;
}
.home-divider {
    width: 200px;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(31,78,121,0.45), transparent);
    margin: 4px auto 26px auto;
}

.home-tagline {
    font-size: 1.25rem;
    color: #374151;
    font-weight: 500;
    line-height: 1.8;
    max-width: 720px;
    margin: 0 auto 40px auto;
}

.home-years {
    font-size: 1.1rem;
    color: #1f4e79;
    font-weight: 700;
    letter-spacing: 6px;
    margin-bottom: 48px;
}

.home-credits {
    margin-top: 24px;
    font-size: 1.05rem;
    color: #1f4e79;
    font-weight: 600;
    letter-spacing: 0.5px;
}
.credits-dot {
    display: inline-block;
    margin: 0 10px;
    color: #3a8fb7;
    font-size: 1.5rem;
    line-height: 1;
    vertical-align: middle;
    transform: translateY(-2px);
}

@media (max-width: 760px) {
    .home-title { font-size: 2.8rem; letter-spacing: -1.2px; }
    .home-tagline { font-size: 1.05rem; }
    .home-eyebrow { font-size: 0.72rem; letter-spacing: 3px; padding: 7px 16px; }
    .home-content { padding: 30px 16px 12px 16px; min-height: calc(100vh - 220px); }
    .home-years { font-size: 0.95rem; letter-spacing: 4px; }
}
</style>
"""


def render(df_full: pd.DataFrame, df_neemanim: pd.DataFrame):
    st.markdown(HERO_CSS, unsafe_allow_html=True)
    st.markdown(
        f'<div class="israel-corner"><img src="{_israel_image_data_uri()}" alt="Israel"></div>',
        unsafe_allow_html=True,
    )

    html = dedent("""\
<div class="home-content">
<h1 class="home-title">חדלות פירעון <span class="accent">בישראל</span></h1>
<div class="home-subtitle">דאשבורד אינטרקטיבי חדל"פ</div>
<div class="home-divider"></div>
<p class="home-tagline">ניתוח מקיף של הליכי חדלות פירעון — מפתיחת התיק ועד לסגירתו, לאורך כל שלבי המערכת.</p>
<div class="home-years">2020 — 2021 — 2022</div>
<div class="home-credits">וסים סעדי <span class="credits-dot">·</span> שלומית כהן</div>
</div>
""")
    st.markdown(html, unsafe_allow_html=True)
