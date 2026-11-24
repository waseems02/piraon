import streamlit as st
import pandas as pd


# Anonymous identifiers — shown first so each row can be traced back
# (via the private טבלת התממה) without exposing any real identifier.
ID_COLS_DISPLAY = {
    "tik_code": "קוד תיק (T)",
    "hayav_code": "קוד חייב (H)",
    "neeman": "נאמן משויך (P)",
    "neeman_1": "נאמן 1 (P)",
    "neeman_2": "נאמן 2 (P)",
}

CASE_COLS_DISPLAY = {
    **ID_COLS_DISPLAY,
    "year": "שנת פתיחה",
    "d_tzav_ptichat_halichim": "תאריך צו פתיחה",
    "d_tzav_shikum": "תאריך צו שיקום",
    "age_ptichat_hlichim": "גיל בפתיחה",
    "num_children_minor": "ילדים קטינים",
    "income_salery": "הכנסה (₪)",
    "first_payment": "תשלום ראשון (₪)",
    "last_payment": "תשלום אחרון (₪)",
    "duration_stage1_months": "משך שלב ביניים (חודשים)",
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
        dur_range = st.slider("טווח משך שלב ביניים (חודשים)", 0, max_dur, (0, max_dur), key="dt_dur")

    sub = df.copy()
    if sel_out != "הכל":
        sub = sub[sub["outcome"] == sel_out]
    if sel_mahoz != "הכל":
        sub = sub[sub["mahoz"] == sel_mahoz]
    sub = sub[(sub["duration_stage1_months"].fillna(-1).between(dur_range[0], dur_range[1])) |
              sub["duration_stage1_months"].isna()]

    q = st.text_input(
        "חיפוש חופשי (קוד תיק T / קוד חייב H / נאמן P / סטטוס / תוצאה)",
        key="dt_q")
    if q:
        search_cols = list(ID_COLS_DISPLAY) + ["status_d_15032026", "outcome"]
        mask = pd.Series(False, index=sub.index)
        for c in search_cols:
            mask |= sub[c].astype("string").fillna("").str.contains(q, case=False, regex=False)
        sub = sub[mask]

    show_all = st.toggle("הצג את כל העמודות בקובץ", value=True, key="dt_all_cols")

    st.caption(f"מציג {len(sub):,} תיקים")

    cols = list(CASE_COLS_DISPLAY)
    if show_all:
        # Everything in the frame is already anonymized; "num_tik" is just an
        # alias of tik_code, so skip it to avoid a duplicate column.
        cols += [c for c in sub.columns if c not in CASE_COLS_DISPLAY and c != "num_tik"]
    display = sub[cols].rename(columns=CASE_COLS_DISPLAY)
    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        height=420,
        column_config={
            "משך שלב ביניים (חודשים)": st.column_config.NumberColumn(
                "משך שלב ביניים (חודשים)", format="%.1f"),
            "גיל בפתיחה": st.column_config.NumberColumn("גיל בפתיחה", format="%d"),
            "הכנסה (₪)": st.column_config.NumberColumn("הכנסה (₪)", format="localized"),
            "תאריך צו פתיחה": st.column_config.DateColumn("תאריך צו פתיחה", format="DD/MM/YYYY"),
            "תאריך צו שיקום": st.column_config.DateColumn("תאריך צו שיקום", format="DD/MM/YYYY"),
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
        drop_range = st.slider("טווח שיעור נשירה (%)", 0, 100, (0, 100), key="dt_n_drop")

    sub = df_n[df_n["total_valid_cases"] >= min_cases].copy()
    sub = sub[(sub["dropout_rate_full"] * 100).between(drop_range[0], drop_range[1])]

    q = st.text_input("חיפוש קוד נאמן (P)", key="dt_n_q")
    if q:
        sub = sub[sub["full_name_neeman"].fillna("").str.contains(q, case=False, regex=False)]

    st.caption(f"מציג {len(sub):,} נאמנים")

    # Every column of the trustees table (df_neemanim_anon_211026.xlsx);
    # columns missing from the computed fallback table are skipped.
    show = sub[[c for c in NEEMANIM_COLS_DISPLAY if c in sub.columns]].copy()
    for c in NEEMANIM_PCT_COLS:
        if c in show.columns:
            show[c] = (show[c] * 100).round(1)
    if "notable_shift" in show.columns:
        show["notable_shift"] = show["notable_shift"].map({1: "כן", 0: "לא"})
    show = show.rename(columns=NEEMANIM_COLS_DISPLAY)

    st.dataframe(
        show, use_container_width=True, hide_index=True, height=420,
        column_config={
            "% נשירה כללי": st.column_config.ProgressColumn(
                "% נשירה כללי", format="%.1f%%", min_value=0, max_value=100),
            "% נשירה 2020": st.column_config.ProgressColumn(
                "% נשירה 2020", format="%.1f%%", min_value=0, max_value=100),
            "תיקים": st.column_config.NumberColumn("תיקים", format="%d"),
            "z נשירה כללי": st.column_config.NumberColumn("z נשירה כללי", format="%.2f"),
            "z נשירה 2020": st.column_config.NumberColumn("z נשירה 2020", format="%.2f"),
            "הפרש z": st.column_config.NumberColumn("הפרש z", format="%.2f"),
            "דירוג כללי": st.column_config.NumberColumn("דירוג כללי", format="%d"),
            "דירוג 2020": st.column_config.NumberColumn("דירוג 2020", format="%d"),
            "שינוי בדירוג": st.column_config.NumberColumn("שינוי בדירוג", format="%d"),
        },
    )


NEEMANIM_COLS_DISPLAY = {
    "full_name_neeman": "נאמן (P)",
    "gender": "מגדר נאמן",
    "total_valid_cases": "תיקים",
    "dropout_rate_full": "% נשירה כללי",
    "dropout_rate_2020": "% נשירה 2020",
    "bitul_2020": "ביטולים 2020",
    "z_dropout_full": "z נשירה כללי",
    "z_dropout_2020": "z נשירה 2020",
    "z_diff": "הפרש z",
    "rank_full": "דירוג כללי",
    "rank_2020": "דירוג 2020",
    "rank_change": "שינוי בדירוג",
    "notable_shift": "שינוי בולט",
    "pct_150": "% תשלום 150",
    "pct_siyua": "% סיוע",
    "pct_arab": "% ערבי",
    "mahoz_באר שבע": "% ב\"ש",
    "mahoz_חיפה": "% חיפה",
    "mahoz_ירושלים": "% ירושלים",
    "mahoz_תל אביב": "% ת\"א",
}
NEEMANIM_PCT_COLS = ["dropout_rate_full", "dropout_rate_2020", "pct_150", "pct_siyua",
                     "pct_arab", "mahoz_באר שבע", "mahoz_חיפה", "mahoz_ירושלים", "mahoz_תל אביב"]