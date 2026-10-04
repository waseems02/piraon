import streamlit as st
import pandas as pd
import plotly.express as px

from data_loader import empty_state
from ui import section, styled_dataframe, wrap_x_labels


DIMENSIONS = {
    "מחוז": "mahoz",
    "מגדר": "gender_label",
    "שנת פתיחה": "year",
    "תוצאה": "outcome",
    "סטטוס": "status_d_15032026",
    "קבוצת גיל": "age_bin",
    "מגזר": "sector_label",
    "סיוע משפטי": "siyua_label",
    "נכות כללית": "nechut_label",
    "קבוצת תשלום ראשון": "first_payment_bin",
    "קבוצת שכר": "income_salery_bin",
}


def render(df: pd.DataFrame, df_neemanim: pd.DataFrame):
    st.subheader("סקירה — מי מתחיל את ההליך")
    st.caption(
        "פרופיל דמוגרפי מלא זמין כאן: גיל, מגזר, סיוע משפטי, נכות, שכר וגובה תשלום. "
        "לניתוח מעמיק ומודלים סטטיסטיים — עמוד 5 במצגת."
    )

    if df.empty:
        empty_state()
        return

    total = len(df)
    closed = df["is_closed"].sum()
    immediate = df["is_immediate_discharge"].sum()
    dropouts = df["is_dropout"].sum()
    median_stage1 = df["duration_stage1_months"].median()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("סך תיקים", f"{total:,}")
    c2.metric("סגורים", f"{closed / total * 100:.1f}%" if total else "—")
    c3.metric("הפטר לאלתר", f"{immediate / total * 100:.1f}%" if total else "—")
    c4.metric("ביטול לאחר צו שיקום", f"{dropouts / total * 100:.1f}%" if total else "—")
    c5.metric("חציון משך שלב א' (חודשים)",
              f"{median_stage1:.1f}" if pd.notna(median_stage1) else "—")

    st.markdown("---")

    with section("פילוח כללי — לפי מימד לבחירה", key="ov_dist") as (side, main, view):
        with side:
            dim_label = st.selectbox("פילוח לפי", list(DIMENSIONS.keys()), key="ov_dim")
            chart_type = st.radio("סוג גרף", ["עמודות", "עוגה"], key="ov_chart")
        dim = DIMENSIONS[dim_label]
        counts = df[dim].value_counts(dropna=False).reset_index()
        counts.columns = [dim_label, "תיקים"]
        counts["אחוז %"] = (counts["תיקים"] / counts["תיקים"].sum() * 100).round(1)
        with main:
            if view == "chart":
                if chart_type == "עמודות":
                    fig = px.bar(counts, x=dim_label, y="תיקים", text="תיקים", color=dim_label)
                    fig.update_layout(showlegend=False, height=300)
                    wrap_x_labels(fig)
                else:
                    fig = px.pie(counts, names=dim_label, values="תיקים", hole=0.4)
                    fig.update_traces(textposition="inside", textinfo="percent+label")
                    fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            else:
                styled_dataframe(counts, column_config={
                    "אחוז %": st.column_config.ProgressColumn(
                        "אחוז %", format="%.1f%%", min_value=0, max_value=100),
                })

    st.markdown("---")

    with section("פתיחת תיקים לפי שנה ומחוז", key="ov_time") as (side, main, view):
        with side:
            mahoz_filter = st.multiselect(
                "מחוזות בגרף", sorted(df["mahoz"].dropna().unique()),
                default=sorted(df["mahoz"].dropna().unique()), key="ov_time_m")
        y = df[df["mahoz"].isin(mahoz_filter)].groupby(["year", "mahoz"]).size().reset_index(name="תיקים")
        with main:
            if view == "chart":
                fig = px.line(y, x="year", y="תיקים", color="mahoz", markers=True)
                fig.update_layout(height=280, xaxis_title="שנה", legend_title="מחוז")
                st.plotly_chart(fig, use_container_width=True)
            else:
                pivot = y.pivot(index="year", columns="mahoz", values="תיקים").fillna(0).astype(int)
                pivot["סה\"כ"] = pivot.sum(axis=1)
                st.dataframe(pivot, use_container_width=True)

    st.markdown("---")

    with section("ערים עם הכי הרבה תיקים", key="ov_cities") as (side, main, view):
        with side:
            top_n = st.slider("Top N ערים", 5, 30, 15, key="ov_topn")
        c = df["city"].value_counts().head(top_n).reset_index()
        c.columns = ["עיר", "תיקים"]
        c["אחוז %"] = (c["תיקים"] / len(df) * 100).round(1)
        with main:
            if view == "chart":
                fig = px.bar(c, y="עיר", x="תיקים", orientation="h", text="תיקים",
                             color="תיקים", color_continuous_scale="Blues")
                fig.update_layout(height=max(260, 18 * top_n),
                                  yaxis={"categoryorder": "total ascending"},
                                  coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                styled_dataframe(c, column_config={
                    "אחוז %": st.column_config.ProgressColumn(
                        "אחוז %", format="%.1f%%", min_value=0, max_value=100),
                })

    st.markdown("---")

    with section("התפלגות תוצאה בסוף התהליך", key="ov_outcome") as (side, main, view):
        o = df["outcome"].value_counts().reset_index()
        o.columns = ["תוצאה", "תיקים"]
        o["אחוז %"] = (o["תיקים"] / o["תיקים"].sum() * 100).round(1)
        with main:
            if view == "chart":
                fig = px.bar(o, x="תוצאה", y="תיקים",
                             text=o["אחוז %"].astype(str) + "%", color="תוצאה")
                fig.update_layout(showlegend=False, height=290)
                wrap_x_labels(fig)
                st.plotly_chart(fig, use_container_width=True)
            else:
                styled_dataframe(o, column_config={
                    "אחוז %": st.column_config.ProgressColumn(
                        "אחוז %", format="%.1f%%", min_value=0, max_value=100),
                })
