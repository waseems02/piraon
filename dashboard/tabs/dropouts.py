import streamlit as st
import pandas as pd
import plotly.express as px

from data_loader import empty_state
from ui import section, styled_dataframe, wrap_x_labels


DIMENSIONS = {
    "מחוז": "mahoz",
    "מגדר": "gender_label",
    "שנת פתיחה": "year",
    "עיר": "city",
    "קבוצת גיל": "age_bin",
    "מגזר": "sector_label",
    "סיוע משפטי": "siyua_label",
    "נכות כללית": "nechut_label",
    "קבוצת תשלום ראשון": "first_payment_bin",
    "קבוצת שכר": "income_salery_bin",
}


def render(df: pd.DataFrame, df_neemanim: pd.DataFrame):
    st.subheader("נשירה — מי יוצא מההליך לפני צו שיקום")
    st.caption(
        "נשירה מוגדרת כתיקים שלא הגיעו לצו שיקום (got_2shikum = 0 בקובץ המקראה). "
        "התיקים כוללים ביטול לפני צו שיקום ולא נגישים לצו תשלומים ארוך־טווח."
    )

    if df.empty:
        empty_state()
        return

    n_total = len(df)
    n_drop = int(df["is_dropout"].sum())
    rate_all = (n_drop / n_total * 100) if n_total else 0
    n_post = int(df["is_post_shikum_cancel"].sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("סך תיקים (בפילטר)", f"{n_total:,}")
    c2.metric("נשירה (ביטול לפני צו שיקום)", f"{n_drop:,}")
    c3.metric("שיעור נשירה", f"{rate_all:.1f}%")
    c4.metric("ביטול לאחר צו שיקום (לייחוס)", f"{n_post:,}")

    st.markdown("---")

    with section("שיעור נשירה לפי חתך", key="dr_by_dim") as (side, main, view):
        with side:
            dim_label = st.selectbox("פילוח לפי", list(DIMENSIONS.keys()), key="dr_dim")
            min_n = st.slider("מינימום תיקים בקבוצה", 5, 200, 10, key="dr_minn")
        dim = DIMENSIONS[dim_label]
        agg = (
            df.groupby(dim)
            .agg(תיקים=("num_tik", "count"), נשירות=("is_dropout", "sum"))
            .reset_index()
            .rename(columns={dim: dim_label})
        )
        agg["שיעור נשירה %"] = (agg["נשירות"] / agg["תיקים"] * 100).round(1)
        agg = agg[agg["תיקים"] >= min_n].sort_values("שיעור נשירה %", ascending=False)
        with main:
            if agg.empty:
                st.caption("אין קבוצות שעומדות במינימום התיקים.")
            elif view == "chart":
                fig = px.bar(agg.head(25), x=dim_label, y="שיעור נשירה %",
                             text="שיעור נשירה %", color="שיעור נשירה %",
                             hover_data=["תיקים", "נשירות"],
                             color_continuous_scale="Reds")
                fig.update_layout(height=300, xaxis_title="", coloraxis_showscale=False)
                wrap_x_labels(fig)
                st.plotly_chart(fig, use_container_width=True)
            else:
                styled_dataframe(agg, column_config={
                    "שיעור נשירה %": st.column_config.ProgressColumn(
                        "שיעור נשירה %", format="%.1f%%", min_value=0, max_value=100),
                })

    st.markdown("---")

    with section("Heatmap דו־מימדי — שיעור נשירה", key="dr_hm") as (side, main, view):
        with side:
            d1 = st.selectbox("ציר Y", list(DIMENSIONS.keys()), index=0, key="dr_hm1")
            d2 = st.selectbox("ציר X", list(DIMENSIONS.keys()), index=1, key="dr_hm2")
        with main:
            if d1 == d2:
                st.caption("בחר שני מימדים שונים.")
            else:
                pivot = (
                    df.groupby([DIMENSIONS[d1], DIMENSIONS[d2]])["is_dropout"]
                    .mean().mul(100).round(1).reset_index()
                    .pivot(index=DIMENSIONS[d1], columns=DIMENSIONS[d2], values="is_dropout")
                )
                if pivot.empty:
                    st.caption("אין נתונים.")
                elif view == "chart":
                    fig = px.imshow(pivot, text_auto=True, aspect="auto",
                                    color_continuous_scale="Reds",
                                    labels=dict(x=d2, y=d1, color="שיעור נשירה %"))
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.dataframe(pivot, use_container_width=True)

    st.markdown("---")

    with section("נאמנים — כמות ושיעור נשירה בקבוצה זו", key="dr_neem") as (side, main, view):
        with side:
            q = st.text_input("חיפוש נאמן", key="dr_search")
            min_cases = st.slider("מינימום תיקים", 1, 200, 5, key="dr_neeman_min")
        top = (
            df.groupby("neeman")
            .agg(תיקים=("num_tik", "count"), נשירות=("is_dropout", "sum"))
            .reset_index()
            .rename(columns={"neeman": "נאמן"})
        )
        top["שיעור נשירה %"] = (top["נשירות"] / top["תיקים"] * 100).round(1)
        if q:
            top = top[top["נאמן"].fillna("").str.contains(q, na=False)]
        top = top[top["תיקים"] >= min_cases].sort_values("שיעור נשירה %", ascending=False)
        with main:
            if top.empty:
                st.caption("אין נאמנים לפי הפילטרים.")
            elif view == "chart":
                fig = px.bar(top.head(20), x="נאמן", y="שיעור נשירה %",
                             text="שיעור נשירה %", color="שיעור נשירה %",
                             hover_data=["תיקים", "נשירות"],
                             color_continuous_scale="Reds")
                fig.update_layout(height=300, xaxis_title="", coloraxis_showscale=False,
                                  xaxis_tickangle=0)
                st.plotly_chart(fig, use_container_width=True)
            else:
                styled_dataframe(top, column_config={
                    "שיעור נשירה %": st.column_config.ProgressColumn(
                        "שיעור נשירה %", format="%.1f%%", min_value=0, max_value=100),
                    "תיקים": st.column_config.NumberColumn("תיקים", format="%d"),
                    "נשירות": st.column_config.NumberColumn("נשירות", format="%d"),
                })
