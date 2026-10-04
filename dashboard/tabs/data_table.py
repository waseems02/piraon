import streamlit as st
import pandas as pd


CASE_COLS_DISPLAY = {
    "neeman_2": "נאמן",
    "duration_stage1_months": "משך שלב א' (חודשים)",
    "mahoz": "מחוז",
    "gender_label": "מגדר",
    "age_bin": "קבוצת גיל",
    "sector_label": "מגזר",
    "siyua_label": "סיוע משפטי",
    "nechut_label": "נכות כללית",
    "status_d_15032026": "סטטוס",
    "outcome": "תוצאה",
    "sibat_sgira_kidud_c": "סיבת סגירה",
    "income_salery_bin": "קבוצת שכר",
}


def render(df: pd.DataFrame, df_neemanim: pd.DataFrame):
    st.subheader("טבלת נתונים — גישה ישירה")
    st.caption(
        "הפילטרים הגלובליים כבר הופעלו. כאן ניתן לחפש, למיין, לצנן ולהוריד CSV. "
        "מסך זה משמש כמסד־נתונים אינטראקטיבי לצד הגרפים."
    )

    view = st.radio(
        "בחר טבלה", ["תיקים", "נאמנים"], horizontal=True, key="dt_view"
    )

    if view == "תיקים":
        _render_cases(df)
    else:
        _render_neemanim(df_neemanim)


def _render_cases(df: pd.DataFrame):
    if df.empty:
        st.info("אין תיקים לפי הפילטרים הגלובליים.")
        return

    st.markdown("**פילטרים ייעודיים לטבלה**")
    col1, col2, col3 = st.columns(3)

    with col1:
        outcomes = ["הכל"] + sorted(df["outcome"].dropna().unique().tolist())
        sel_out = st.selectbox("תוצאה", outcomes, key="dt_out")
    with col2:
        mahozot = ["הכל"] + sorted(df["mahoz"].dropna().unique().tolist())
        sel_mahoz = st.selectbox("מחוז", mahozot, key="dt_mahoz")
    with col3:
        min_dur, max_dur = 0, 100
        if df["duration_stage1_months"].notna().any():
            max_dur = int(df["duration_stage1_months"].max()) + 1
        dur_range = st.slider("טווח משך שלב א' (חודשים)", 0, max_dur, (0, max_dur), key="dt_dur")

    sub = df.copy()
    if sel_out != "הכל":
        sub = sub[sub["outcome"] == sel_out]
    if sel_mahoz != "הכל":
        sub = sub[sub["mahoz"] == sel_mahoz]
    sub = sub[(sub["duration_stage1_months"].fillna(-1).between(dur_range[0], dur_range[1])) |
              sub["duration_stage1_months"].isna()]

    q = st.text_input("חיפוש חופשי (נאמן / סטטוס / תוצאה)", key="dt_q")
    if q:
        mask = (
            sub["neeman_2"].fillna("").str.contains(q, na=False)
            | sub["status_d_15032026"].fillna("").str.contains(q, na=False)
            | sub["outcome"].fillna("").str.contains(q, na=False)
        )
        sub = sub[mask]

    st.caption(f"מציג {len(sub):,} תיקים")

    display = sub[list(CASE_COLS_DISPLAY.keys())].rename(columns=CASE_COLS_DISPLAY)
    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        height=360,
        column_config={
            "משך שלב א' (חודשים)": st.column_config.NumberColumn(
                "משך שלב א' (חודשים)", format="%.1f"),
        },
    )


def _render_neemanim(df_n: pd.DataFrame):
    if df_n.empty:
        st.info("קובץ הנאמנים ריק.")
        return

    col1, col2 = st.columns(2)
    with col1:
        max_cases = int(df_n["total_valid_cases"].max())
        min_cases = st.slider("מינימום תיקים", 1, max_cases, 1, key="dt_n_min")
    with col2:
        drop_range = st.slider("טווח שיעור ביטול (%)", 0, 100, (0, 100), key="dt_n_drop")

    sub = df_n[df_n["total_valid_cases"] >= min_cases].copy()
    sub = sub[(sub["dropout_rate_full"] * 100).between(drop_range[0], drop_range[1])]

    q = st.text_input("חיפוש שם נאמן", key="dt_n_q")
    if q:
        sub = sub[sub["full_name_neeman"].fillna("").str.contains(q, na=False)]

    st.caption(f"מציג {len(sub):,} נאמנים")

    display_cols = [
        "full_name_neeman", "total_valid_cases", "dropout_rate_full", "dropout_rate_2020",
        "pct_150", "pct_siyua", "pct_arab",
        "mahoz_באר שבע", "mahoz_חיפה", "mahoz_ירושלים", "mahoz_תל אביב",
    ]
    show = sub[display_cols].copy()
    for c in ["dropout_rate_full", "dropout_rate_2020", "pct_150", "pct_siyua", "pct_arab",
              "mahoz_באר שבע", "mahoz_חיפה", "mahoz_ירושלים", "mahoz_תל אביב"]:
        show[c] = (show[c] * 100).round(1)

    show.columns = [
        "נאמן", "תיקים", "% ביטול כללי", "% ביטול 2020",
        "% תשלום 150", "% סיוע", "% ערבי",
        "% ב\"ש", "% חיפה", "% ירושלים", "% ת\"א",
    ]

    st.dataframe(
        show, use_container_width=True, hide_index=True, height=360,
        column_config={
            "% ביטול כללי": st.column_config.ProgressColumn(
                "% ביטול כללי", format="%.1f%%", min_value=0, max_value=100),
            "% ביטול 2020": st.column_config.ProgressColumn(
                "% ביטול 2020", format="%.1f%%", min_value=0, max_value=100),
            "תיקים": st.column_config.NumberColumn("תיקים", format="%d"),
        },
    )
