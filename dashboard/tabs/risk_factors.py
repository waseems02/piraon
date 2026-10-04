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
    "קבוצת שכר": "income_salery_bin",
}


def render(df: pd.DataFrame, df_neemanim: pd.DataFrame):
    st.subheader("גורמי סיכון — מי בסיכון גבוה מלכתחילה")
    st.caption(
        "המימדים במצגת (גיל, מגזר, סיוע, נכות, גובה תשלום) זמינים כאן ומופיעים בכל הפילוחים. "
        "למודלי הרגרסיה המלאים (Logistic, Cox) ולפרשנות המקדמים — עמודים 9–10 ו־15–16 במצגת."
    )

    if df.empty:
        empty_state()
        return

    baseline = df["is_dropout"].mean() * 100
    st.metric("שיעור ביטול בסיס (בפילטר הנוכחי)", f"{baseline:.1f}%")

    st.markdown("---")

    with section("Cross-tab דו־מימדי — שיעור ביטול בכל שילוב", key="rf_cross") as (side, main, view):
        with side:
            d1_label = st.selectbox("מימד ראשון", list(DIMENSIONS.keys()), index=0, key="rf_d1")
            d2_label = st.selectbox("מימד שני", list(DIMENSIONS.keys()), index=1, key="rf_d2")
            min_n = st.slider("מינימום תיקים בקבוצה", 1, 100, 5, key="rf_minn")
        with main:
            if d1_label == d2_label:
                st.caption("בחר שני מימדים שונים.")
            else:
                d1, d2 = DIMENSIONS[d1_label], DIMENSIONS[d2_label]
                agg = (
                    df.groupby([d1, d2])
                    .agg(תיקים=("num_tik", "count"), ביטולים=("is_dropout", "sum"))
                    .reset_index()
                    .rename(columns={d1: d1_label, d2: d2_label})
                )
                agg["שיעור ביטול %"] = (agg["ביטולים"] / agg["תיקים"] * 100).round(1)
                agg = agg[agg["תיקים"] >= min_n]
                agg["פרופיל"] = agg[d1_label].astype(str) + " · " + agg[d2_label].astype(str)
                agg = agg.sort_values("שיעור ביטול %", ascending=False)
                if view == "chart":
                    fig = px.bar(agg, x="שיעור ביטול %", y="פרופיל", orientation="h",
                                 color="שיעור ביטול %", color_continuous_scale="Reds",
                                 text="שיעור ביטול %", hover_data=["תיקים", "ביטולים"])
                    fig.add_vline(x=baseline, line_dash="dash", line_color="#1f4e79",
                                  annotation_text=f"בסיס {baseline:.1f}%")
                    fig.update_layout(height=max(260, 20 * len(agg)),
                                      coloraxis_showscale=False, yaxis_title="")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    table = agg[[d1_label, d2_label, "תיקים", "ביטולים", "שיעור ביטול %"]]
                    styled_dataframe(table, column_config={
                        "שיעור ביטול %": st.column_config.ProgressColumn(
                            "שיעור ביטול %", format="%.1f%%", min_value=0, max_value=100),
                    })

    st.markdown("---")

    with section("סימולציית פרופיל", key="rf_sim") as (side, main, view):
        with side:
            sel_mahoz = st.selectbox("מחוז", ["כל המחוזות"] + sorted(df["mahoz"].dropna().unique()), key="rf_sim_m")
            sel_gender = st.selectbox("מגדר", ["הכל"] + sorted(df["gender_label"].dropna().unique()), key="rf_sim_g")
            sel_sector = st.selectbox("מגזר", ["הכל"] + sorted(df["sector_label"].dropna().unique()), key="rf_sim_s")
            sel_siyua = st.selectbox("סיוע משפטי", ["הכל"] + sorted(df["siyua_label"].dropna().unique()), key="rf_sim_sy")
        subset = df
        if sel_mahoz != "כל המחוזות":
            subset = subset[subset["mahoz"] == sel_mahoz]
        if sel_gender != "הכל":
            subset = subset[subset["gender_label"] == sel_gender]
        if sel_sector != "הכל":
            subset = subset[subset["sector_label"] == sel_sector]
        if sel_siyua != "הכל":
            subset = subset[subset["siyua_label"] == sel_siyua]
        with main:
            if subset.empty:
                st.info("אין תיקים לפרופיל שנבחר.")
            else:
                prof_rate = subset["is_dropout"].mean() * 100
                delta = prof_rate - baseline
                c1, c2, c3 = st.columns(3)
                c1.metric("תיקים בפרופיל", f"{len(subset):,}")
                c2.metric("שיעור ביטול בפרופיל", f"{prof_rate:.1f}%",
                          f"{delta:+.1f}pp מול בסיס")
                c3.metric("בסיס (כל הפילטר)", f"{baseline:.1f}%")
                if view == "chart":
                    comp_df = pd.DataFrame({
                        "קבוצה": ["בסיס", "פרופיל שנבחר"],
                        "% ביטול": [round(baseline, 1), round(prof_rate, 1)],
                    })
                    fig = px.bar(comp_df, x="קבוצה", y="% ביטול", text="% ביטול",
                                 color="קבוצה")
                    fig.update_layout(showlegend=False, height=250, xaxis_title="")
                    wrap_x_labels(fig)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.dataframe(pd.DataFrame({
                        "מדד": ["תיקים", "ביטולים", "% ביטול פרופיל", "% ביטול בסיס", "פער (pp)"],
                        "ערך": [len(subset), int(subset["is_dropout"].sum()),
                                round(prof_rate, 1), round(baseline, 1), round(delta, 1)],
                    }), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.info(
        "**ציטוט מהמצגת:** פרופיל הסיכון הגבוה — **ערבי + לקוח סיוע + נדחה בעבר + חיפה = 54% נשירה**. "
        "מנבאים חזקים במודל הלוגיסטי: מגדר (נשים מוגנות פי 2.25), לקוח סיוע (סיכון פי 0.60), "
        "קצבת נכות (סיכון פי 1.42), גיל 60+ (סיכון פי 1.26)."
    )
