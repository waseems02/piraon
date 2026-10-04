import streamlit as st
import pandas as pd
import plotly.express as px

from data_loader import empty_state
from ui import section, styled_dataframe, wrap_x_labels


DIMENSIONS = {
    "מחוז": "mahoz",
    "מגדר": "gender_label",
    "שנת פתיחה": "year",
    "קבוצת גיל": "age_bin",
    "מגזר": "sector_label",
    "סיוע משפטי": "siyua_label",
    "נכות כללית": "nechut_label",
    "קבוצת תשלום ראשון": "first_payment_bin",
}


def render(df: pd.DataFrame, df_neemanim: pd.DataFrame):
    st.subheader("מסיימים בהצלחה — מסלולי סיום")
    st.caption(
        "3 מסלולים: הפטר לאלתר (מהיר, ללא יכולת תשלום), "
        "הפטר (בסוף תכנית שיקום), ביטול (נשירה)."
    )

    if df.empty:
        empty_state()
        return

    imm_rate = df["is_immediate_discharge"].mean() * 100
    hef_rate = df["is_hefter"].mean() * 100
    drop_rate = df["is_dropout"].mean() * 100

    c1, c2, c3 = st.columns(3)
    c1.metric("% הפטר לאלתר", f"{imm_rate:.1f}%")
    c2.metric("% הפטר בסוף תכנית", f"{hef_rate:.1f}%")
    c3.metric("% ביטול לאחר צו שיקום", f"{drop_rate:.1f}%")

    st.markdown("---")

    with section("התפלגות תוצאות לפי מימד", key="cp_dist") as (side, main, view):
        with side:
            dim_label = st.selectbox("פילוח לפי", list(DIMENSIONS.keys()), key="cp_dim")
            norm = st.radio("תצוגה", ["מספרים", "אחוזים"], key="cp_norm")
        dim = DIMENSIONS[dim_label]
        ct = df.groupby([dim, "outcome"]).size().reset_index(name="תיקים")
        if norm == "אחוזים":
            totals = ct.groupby(dim)["תיקים"].transform("sum")
            ct["ערך"] = (ct["תיקים"] / totals * 100).round(1)
            y_title = "%"
        else:
            ct["ערך"] = ct["תיקים"]
            y_title = "תיקים"
        with main:
            if view == "chart":
                fig = px.bar(ct, x=dim, y="ערך", color="outcome", barmode="stack",
                             text="ערך", hover_data=["תיקים"])
                fig.update_layout(height=300, xaxis_title="", yaxis_title=y_title,
                                  legend_title="תוצאה")
                wrap_x_labels(fig)
                st.plotly_chart(fig, use_container_width=True)
            else:
                pivot = ct.pivot(index=dim, columns="outcome", values="ערך").fillna(0)
                if norm == "אחוזים":
                    pivot = pivot.round(1)
                else:
                    pivot = pivot.astype(int)
                    pivot["סה\"כ"] = pivot.sum(axis=1)
                st.dataframe(pivot, use_container_width=True)

    st.markdown("---")

    imm = df[df["is_immediate_discharge"]]
    hef = df[df["is_hefter"]]

    with section("הפטר לאלתר מול הפטר רגיל — פרופיל", key="cp_cmp") as (side, main, view):
        with side:
            compare_dim_label = st.selectbox("מימד השוואה", list(DIMENSIONS.keys()), key="cp_cmp_dim")
        compare_dim = DIMENSIONS[compare_dim_label]

        def dist(sub, name):
            if sub.empty:
                return pd.DataFrame(columns=[compare_dim_label, "%", "תוצאה"])
            s = (sub[compare_dim].value_counts(normalize=True) * 100).round(1)
            return pd.DataFrame({compare_dim_label: s.index.astype(str),
                                 "%": s.values, "תוצאה": name})

        comp = pd.concat([dist(imm, "הפטר לאלתר"), dist(hef, "הפטר")])
        with main:
            if comp.empty:
                st.caption("אין נתונים מ־2 הקטגוריות בפילטר הנוכחי.")
            elif view == "chart":
                fig = px.bar(comp, x=compare_dim_label, y="%", color="תוצאה",
                             barmode="group", text="%")
                fig.update_layout(height=280)
                wrap_x_labels(fig)
                st.plotly_chart(fig, use_container_width=True)
            else:
                pivot = comp.pivot(index=compare_dim_label, columns="תוצאה", values="%").fillna(0)
                st.dataframe(pivot, use_container_width=True)

    st.markdown("---")

    with section("חציוני משך עד סיום", key="cp_dur") as (side, main, view):
        st.caption("מפתיחה עד 15/03/2026 (בהיעדר תאריך סגירה בקובץ).")
        dur = df[df["outcome"].isin(["הפטר לאלתר", "הפטר", "ביטול לאחר צו שיקום"])]
        dur = dur[dur["months_since_opening"].notna()]
        with main:
            if dur.empty:
                st.caption("אין תאריכי פתיחה לחישוב.")
            else:
                agg = (
                    dur.groupby("outcome")["months_since_opening"]
                    .agg(["median", "mean", "count"])
                    .reset_index()
                    .rename(columns={"outcome": "תוצאה", "median": "חציון",
                                     "mean": "ממוצע", "count": "תיקים"})
                )
                agg["חציון"] = agg["חציון"].round(1)
                agg["ממוצע"] = agg["ממוצע"].round(1)
                if view == "chart":
                    fig = px.bar(agg, x="תוצאה", y="חציון", text="חציון", color="תוצאה")
                    fig.update_layout(showlegend=False, height=250,
                                      yaxis_title="חודשים", xaxis_title="")
                    wrap_x_labels(fig)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    styled_dataframe(agg)
