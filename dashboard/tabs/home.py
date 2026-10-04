from textwrap import dedent

import pandas as pd
import streamlit as st


HERO_CSS = """
<style>
/* Content area — sits on top of the app's existing bubbles background */
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
    border-radius: 30px;
    color: #1f4e79;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 5px;
    margin-bottom: 32px;
    text-transform: uppercase;
    box-shadow: 0 2px 10px rgba(31,78,121,0.06);
}

.home-title {
    font-size: 4.4rem;
    color: #0d2a47;
    font-weight: 900;
    letter-spacing: -2.5px;
    line-height: 1.02;
    margin: 0 0 26px 0;
    text-shadow: 0 2px 20px rgba(31,78,121,0.08);
}
.home-title .accent {
    background: linear-gradient(90deg, #3a8fb7 0%, #1f4e79 100%);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
}

.home-divider {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 14px;
    margin: 4px 0 26px 0;
}
.home-divider .line {
    width: 80px;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(31,78,121,0.4), transparent);
}
.home-divider .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #1f4e79;
    box-shadow: 0 0 0 5px rgba(31,78,121,0.10);
}

.home-tagline {
    font-size: 1.25rem;
    color: #374151;
    font-weight: 500;
    line-height: 1.8;
    max-width: 720px;
    margin: 0 auto 40px auto;
}

.home-timeline {
    display: flex;
    gap: 18px;
    align-items: center;
    margin: 6px 0 44px 0;
    flex-wrap: wrap;
    justify-content: center;
}
.year-pill {
    padding: 12px 30px;
    background: rgba(255,255,255,0.85);
    border: 1px solid rgba(31,78,121,0.20);
    border-radius: 16px;
    color: #1f4e79;
    font-weight: 700;
    font-size: 1.05rem;
    letter-spacing: 2px;
    box-shadow: 0 4px 14px rgba(31,78,121,0.08);
    backdrop-filter: blur(6px);
    -webkit-backdrop-filter: blur(6px);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.year-pill:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 20px rgba(31,78,121,0.16);
}
.year-sep {
    color: rgba(31,78,121,0.35);
    font-size: 0.95rem;
}

/* KPI stat cards — glass morphism row */
.home-stats {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 18px;
    width: 100%;
    max-width: 820px;
    margin: 4px 0 40px 0;
}
.stat-card {
    position: relative;
    overflow: hidden;
    background: rgba(255,255,255,0.85);
    border: 1px solid rgba(31,78,121,0.12);
    border-radius: 16px;
    padding: 22px 14px 20px 14px;
    text-align: center;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    box-shadow: 0 6px 20px rgba(31,78,121,0.08);
    transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
}
.stat-card::before {
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #1f4e79, #3a8fb7);
    opacity: 0.9;
}
.stat-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 30px rgba(31,78,121,0.18);
    border-color: rgba(31,78,121,0.25);
}
.stat-icon {
    font-size: 1.8rem;
    margin-bottom: 4px;
    filter: drop-shadow(0 2px 6px rgba(31,78,121,0.18));
}
.stat-value {
    font-size: 2rem;
    font-weight: 900;
    letter-spacing: -1px;
    line-height: 1.1;
    background: linear-gradient(135deg, #1f4e79, #3a8fb7);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 4px;
}
.stat-label {
    color: #6b7280;
    font-size: 0.9rem;
    font-weight: 600;
}

/* Credits panel — glass card on top of bubbles */
.credits-panel {
    margin-top: 20px;
    padding: 26px 40px;
    background: rgba(255,255,255,0.75);
    border: 1px solid rgba(31,78,121,0.12);
    border-radius: 20px;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    box-shadow: 0 10px 32px rgba(31,78,121,0.10);
    max-width: 780px;
    width: 100%;
}
.credits-label {
    text-align: center;
    color: #94a3b8;
    font-size: 0.74rem;
    font-weight: 700;
    letter-spacing: 6px;
    margin-bottom: 22px;
    text-transform: uppercase;
}
.credits-label::before, .credits-label::after {
    content: "";
    display: inline-block;
    width: 44px; height: 1px;
    background: rgba(148,163,184,0.5);
    vertical-align: middle;
    margin: 0 14px;
}
.credits-list {
    display: flex;
    gap: 56px;
    justify-content: center;
    flex-wrap: wrap;
}
.credit-item {
    display: flex;
    align-items: center;
    gap: 15px;
    direction: rtl;
}
.credit-avatar {
    width: 56px; height: 56px;
    border-radius: 50%;
    background: linear-gradient(135deg, #1f4e79 0%, #3a8fb7 100%);
    color: #ffffff;
    font-weight: 900;
    font-size: 1.5rem;
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 6px 18px rgba(31,78,121,0.30),
                inset 0 1px 0 rgba(255,255,255,0.25);
    flex-shrink: 0;
}
.credit-info { text-align: right; }
.credit-name {
    color: #1f4e79;
    font-size: 1.22rem;
    font-weight: 700;
    letter-spacing: -0.3px;
    line-height: 1.2;
    margin-bottom: 3px;
}
.credit-role {
    color: #6b7280;
    font-size: 0.86rem;
    font-weight: 500;
}

@media (max-width: 760px) {
    .home-title { font-size: 2.8rem; letter-spacing: -1.2px; }
    .home-tagline { font-size: 1.05rem; }
    .home-eyebrow { font-size: 0.72rem; letter-spacing: 3px; padding: 7px 16px; }
    .credits-list { gap: 26px; }
    .credits-panel { padding: 20px 22px; }
    .home-content { padding: 30px 16px 12px 16px; min-height: calc(100vh - 220px); }
    .home-stats { grid-template-columns: repeat(2, 1fr); gap: 12px; }
    .stat-value { font-size: 1.6rem; }
}
</style>
"""


def render(df_full: pd.DataFrame, df_neemanim: pd.DataFrame):
    st.markdown(HERO_CSS, unsafe_allow_html=True)

    total_cases = len(df_full)
    closed_count = int(df_full["is_closed"].sum()) if "is_closed" in df_full.columns else 0
    trustees_count = (
        df_full["neeman_2"].dropna().nunique() if "neeman_2" in df_full.columns else len(df_neemanim)
    )
    years_count = int(df_full["year"].dropna().nunique()) if "year" in df_full.columns else 3

    html = dedent(f"""\
<div class="home-content">
<div class="home-eyebrow">דוח נתונים · 2020–2022</div>
<h1 class="home-title">חדלות פירעון <span class="accent">בישראל</span></h1>
<div class="home-divider"><span class="line"></span><span class="dot"></span><span class="line"></span></div>
<p class="home-tagline">ניתוח מקיף של הליכי חדלות פירעון — מפתיחת התיק ועד לסגירתו, לאורך כל שלבי המערכת.</p>
<div class="home-timeline">
<span class="year-pill">2020</span>
<span class="year-sep">━━</span>
<span class="year-pill">2021</span>
<span class="year-sep">━━</span>
<span class="year-pill">2022</span>
</div>
<div class="home-stats">
<div class="stat-card">
<div class="stat-icon">📁</div>
<div class="stat-value">{total_cases:,}</div>
<div class="stat-label">תיקים בניתוח</div>
</div>
<div class="stat-card">
<div class="stat-icon">✅</div>
<div class="stat-value">{closed_count:,}</div>
<div class="stat-label">תיקים סגורים</div>
</div>
<div class="stat-card">
<div class="stat-icon">👥</div>
<div class="stat-value">{trustees_count:,}</div>
<div class="stat-label">נאמנים</div>
</div>
<div class="stat-card">
<div class="stat-icon">📅</div>
<div class="stat-value">{years_count}</div>
<div class="stat-label">שנות ניתוח</div>
</div>
</div>
<div class="credits-panel">
<div class="credits-label">Credits</div>
<div class="credits-list">
<div class="credit-item">
<div class="credit-avatar">ו</div>
<div class="credit-info">
<div class="credit-name">וסים סעדי</div>
<div class="credit-role">פיתוח וניתוח נתונים</div>
</div>
</div>
<div class="credit-item">
<div class="credit-avatar">ש</div>
<div class="credit-info">
<div class="credit-name">שלומית כהן</div>
<div class="credit-role">הובלה וייעוץ מקצועי</div>
</div>
</div>
</div>
</div>
</div>
""")
    st.markdown(html, unsafe_allow_html=True)
