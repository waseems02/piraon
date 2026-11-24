import streamlit as st
import pandas as pd
import plotly.express as px

from data_loader import empty_state
from ui import section, styled_dataframe, wrap_x_labels


DIMENSIONS = {
    "מחוז": "mahoz",
    "מגדר": "gender_label",
    "שנת פתיחה": "year",
    "סטטוס": "outcome",
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
        "פרופיל דמוגרפי מלא זמין כאן: גיל, מגזר, סיוע משפטי, נכות, שכר וגובה תשלום."
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
    c4.metric("שיעור נשירה (לפני צו שיקום)", f"{dropouts / total * 100:.1f}%" if total else "—")
    c5.metric("חציון שלב ביניים (חודשים)",
              f"{median_stage1:.1f}" if pd.notna(median_stage1) else "—",
              help="מצו פתיחת הליכים ועד צו שיקום או הפטר. "
                   "לא כולל תיקים שבוטלו לפני צו שיקום ותיקים שעדיין בשלב הביניים.")

    st.markdown("---")

    with section("פילוח כללי — לפי מימד לבחירה", key="ov_dist") as (side, main, view):
        with side:
            dim_label = st.selectbox("פילוח לפי", list(DIMENSIONS.keys()), key="ov_dim")
            chart_type = st.radio("סוג גרף", ["עמודות", "עוגה"], key="ov_chart")
        dim = DIMENSIONS[dim_label]
        counts = df[dim].value_counts(dropna=False).reset_index()
        counts.columns = [dim_label, "תיקים"]
        if counts[dim_label].isna().any():
            counts[dim_label] = counts[dim_label].astype(object).fillna("לא ידוע")
        share = counts["תיקים"] / counts["תיקים"].sum() * 100
        counts["אחוז %"] = share.round(1)
        with main:
            if view == "chart":
                if chart_type == "עמודות":
                    # A tiny group (e.g. the 5 cases without age) must not read as "0.0%".
                    labels = ["<0.1%" if p < 0.1 else f"{p:.1f}%" for p in share]
                    fig = px.bar(counts.assign(**{"אחוז %": share}),
                                 x=dim_label, y="אחוז %", text=labels, color=dim_label,
                                 hover_data={"אחוז %": ":.1f", "תיקים": ":,"})
                    fig.update_layout(showlegend=False, height=300)
                    fig.update_yaxes(ticksuffix="%", title_text="")
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
                # Years as categories: a numeric axis drew half-year ticks (2020.5).
                bars = y.assign(year=y["year"].astype(int).astype(str))
                fig = px.bar(bars, x="year", y="תיקים", color="mahoz", barmode="group",
                             text=bars["תיקים"].map("{:,}".format))
                fig.update_traces(textposition="outside", cliponaxis=False)
                fig.update_layout(height=320, xaxis_title="שנה", yaxis_title="תיקים",
                                  legend_title="מחוז")
                fig.update_xaxes(type="category")
                st.plotly_chart(fig, use_container_width=True)
            else:
                pivot = y.pivot(index="year", columns="mahoz", values="תיקים").fillna(0).astype(int)
                pivot["סה\"כ"] = pivot.sum(axis=1)
                st.dataframe(pivot, use_container_width=True)

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
