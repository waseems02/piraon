import streamlit as st
import pandas as pd
import plotly.express as px

from data_loader import empty_state
from ui import section, styled_dataframe


DIMENSIONS = {
    "מחוז": "mahoz",
    "מגדר": "gender_label",
    "שנת פתיחה": "year",
    "תוצאה": "outcome",
    "קבוצת גיל": "age_bin",
    "מגזר": "sector_label",
    "סיוע משפטי": "siyua_label",
    "נכות כללית": "nechut_label",
    "קבוצת תשלום ראשון": "first_payment_bin",
}


def render(df: pd.DataFrame, df_neemanim: pd.DataFrame):
    st.subheader("משך זמן ותשלומים")
    st.caption(
        "יעד בחוק: שלב א' — 12 חודשים; שלב ב' — 36 חודשים. "
        "המצגת מצאה: חציון בפועל לצו שיקום — 22 חודשים; להפטר — 52."
    )

    if df.empty:
        empty_state()
        return

    have = df[df["duration_stage1_months"].notna() & (df["duration_stage1_months"] >= 0)]
    n_have = len(have)
    median_d = have["duration_stage1_months"].median() if n_have else float("nan")
    mean_d = have["duration_stage1_months"].mean() if n_have else float("nan")
    over_12 = (have["duration_stage1_months"] > 12).mean() * 100 if n_have else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("תיקים עם משך מדיד", f"{n_have:,}")
    c2.metric("חציון שלב א' (חודשים)", f"{median_d:.1f}" if n_have else "—")
    c3.metric("ממוצע שלב א' (חודשים)", f"{mean_d:.1f}" if n_have else "—")
    c4.metric("% מעל 12 חודשים", f"{over_12:.1f}%")

    if n_have == 0:
        st.warning("אין מספיק תאריכים לחישוב משך בפילטר הנוכחי.")
        return

    st.markdown("---")

    with section("התפלגות משך שלב א'", key="du_dist") as (side, main, view):
        with side:
            dim_label = st.selectbox("פילוח לפי", ["ללא"] + list(DIMENSIONS.keys()), key="du_dim")
            chart_type = st.radio("סוג גרף", ["היסטוגרמה", "Boxplot", "Violin"], key="du_ct")
        with main:
            if view == "chart":
                if dim_label == "ללא":
                    if chart_type == "היסטוגרמה":
                        fig = px.histogram(have, x="duration_stage1_months", nbins=40)
                        fig.add_vline(x=12, line_dash="dash", line_color="red",
                                      annotation_text="יעד החוק (12 חודשים)")
                        fig.update_layout(bargap=0.05)
                    elif chart_type == "Boxplot":
                        fig = px.box(have, y="duration_stage1_months", points="outliers")
                    else:
                        fig = px.violin(have, y="duration_stage1_months",
                                        box=True, points="outliers")
                else:
                    dim = DIMENSIONS[dim_label]
                    if chart_type == "היסטוגרמה":
                        fig = px.histogram(have, x="duration_stage1_months", color=dim,
                                           nbins=40, barmode="overlay", opacity=0.6)
                        fig.add_vline(x=12, line_dash="dash", line_color="red",
                                      annotation_text="יעד החוק")
                    elif chart_type == "Boxplot":
                        fig = px.box(have, x=dim, y="duration_stage1_months",
                                     color=dim, points="outliers")
                    else:
                        fig = px.violin(have, x=dim, y="duration_stage1_months",
                                        color=dim, box=True, points="outliers")
                fig.update_layout(height=320, xaxis_title="", yaxis_title="חודשים")
                st.plotly_chart(fig, use_container_width=True)
            else:
                if dim_label == "ללא":
                    stats = pd.DataFrame({
                        "מדד": ["תיקים", "חציון", "ממוצע", "מינימום", "מקסימום",
                                "% מעל 12 חודשים", "% מעל 24 חודשים"],
                        "ערך": [
                            n_have,
                            round(have["duration_stage1_months"].median(), 1),
                            round(have["duration_stage1_months"].mean(), 1),
                            round(have["duration_stage1_months"].min(), 1),
                            round(have["duration_stage1_months"].max(), 1),
                            round((have["duration_stage1_months"] > 12).mean() * 100, 1),
                            round((have["duration_stage1_months"] > 24).mean() * 100, 1),
                        ],
                    })
                    styled_dataframe(stats)
                else:
                    dim = DIMENSIONS[dim_label]
                    agg = (
                        have.groupby(dim)["duration_stage1_months"]
                        .agg(["count", "median", "mean", "min", "max"])
                        .round(1).reset_index()
                        .rename(columns={dim: dim_label, "count": "תיקים", "median": "חציון",
                                         "mean": "ממוצע", "min": "מינימום", "max": "מקסימום"})
                    )
                    styled_dataframe(agg)

    st.markdown("---")

    with section("מסלול מהיר — מה מייחד תיקים שסיימו מתחת לחציון?", key="du_fast") as (side, main, view):
        with side:
            dim_label = st.selectbox("השווה לפי", list(DIMENSIONS.keys()), key="du_cmp")
        dim = DIMENSIONS[dim_label]
        fast = have[have["duration_stage1_months"] <= median_d]
        slow = have[have["duration_stage1_months"] > median_d]

        def dist(sub, name):
            if sub.empty:
                return pd.DataFrame(columns=[dim_label, "%", "קבוצה"])
            s = (sub[dim].value_counts(normalize=True) * 100).round(1)
            return pd.DataFrame({dim_label: s.index.astype(str),
                                 "%": s.values, "קבוצה": name})

        comp = pd.concat([dist(fast, "מהיר (≤ חציון)"), dist(slow, "איטי (> חציון)")])
        with main:
            if comp.empty:
                st.caption("אין נתונים.")
            elif view == "chart":
                fig = px.bar(comp, x=dim_label, y="%", color="קבוצה", barmode="group", text="%")
                fig.update_layout(height=290)
                st.plotly_chart(fig, use_container_width=True)
            else:
                pivot = comp.pivot(index=dim_label, columns="קבוצה", values="%").fillna(0)
                st.dataframe(pivot, use_container_width=True)

    st.markdown("---")

    with section("תשלום ראשון — התפלגות בקבוצות", key="du_pay") as (side, main, view):
        st.caption(
            "המצגת מנתחת קבוצות תשלום 0 / 150 / 151–500 / 501–1,000 / 1,001+ (עמודים 6, 9–10)."
        )
        fp_nonzero = df[df["first_payment"] > 0]["first_payment"]
        zero_share = (df["first_payment"] == 0).mean() * 100

        c1, c2, c3 = st.columns(3)
        c1.metric("% תשלום 0", f"{zero_share:.1f}%")
        c2.metric("חציון (בלא 0)", f"{fp_nonzero.median():,.0f} ₪" if len(fp_nonzero) else "—")
        c3.metric("ממוצע (בלא 0)", f"{fp_nonzero.mean():,.0f} ₪" if len(fp_nonzero) else "—")

        with main:
            if len(fp_nonzero) == 0:
                st.caption("אין תשלומים > 0 בפילטר.")
            else:
                bins = [-1, 0, 150, 500, 1000, 2000, 100000]
                labels = ["₪0", "₪1–150", "₪151–500", "₪501–1,000",
                          "₪1,001–2,000", "₪2,001+"]
                buckets = pd.cut(df["first_payment"], bins=bins, labels=labels, right=True)
                bucket_df = buckets.value_counts().reindex(labels).reset_index()
                bucket_df.columns = ["קבוצת תשלום", "תיקים"]
                bucket_df["אחוז %"] = (bucket_df["תיקים"] / bucket_df["תיקים"].sum() * 100).round(1)
                if view == "chart":
                    fig = px.bar(bucket_df, x="קבוצת תשלום", y="תיקים",
                                 text="תיקים", color="קבוצת תשלום")
                    fig.update_layout(height=260, showlegend=False, xaxis_title="")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    styled_dataframe(bucket_df, column_config={
                        "אחוז %": st.column_config.ProgressColumn(
                            "אחוז %", format="%.1f%%", min_value=0, max_value=100),
                    })
