import streamlit as st
import pandas as pd
import plotly.express as px

from data_loader import empty_state
from ui import section, styled_dataframe, download_button


COLOR_OPTIONS = {
    "שינוי מובהק בדירוג": "notable_shift",
    "% תשלום ₪150": "pct_150",
    "% ערבים": "pct_arab",
    "% סיוע משפטי": "pct_siyua",
}
X_OPTIONS = {
    "סה\"כ תיקים": "total_valid_cases",
    "% תשלום ₪150": "pct_150",
    "% ערבים": "pct_arab",
    "% סיוע משפטי": "pct_siyua",
}


def render(df: pd.DataFrame, df_neemanim: pd.DataFrame):
    st.subheader("נאמנים — האם הנאמן מסביר את הנשירה?")
    st.caption(
        "מבוסס על קובץ הנאמנים (225 נאמנים, 2015–2022, 153,714 תיקים). "
        "המצגת מצאה: R²=63% מהשונות מוסברת ע\"י הרכב הלקוחות; ~37% בלתי מוסברים."
    )

    if df_neemanim.empty:
        empty_state("קובץ הנאמנים ריק.")
        return

    max_cases = int(df_neemanim["total_valid_cases"].max())

    with section("Scatter — נאמנים לפי גודל תיקים ושיעור ביטול", key="tr_scatter") as (side, main, view):
        with side:
            min_cases = st.slider("מינימום תיקים", 1, max_cases, 30, step=5, key="tr_min")
            x_label = st.selectbox("ציר X", list(X_OPTIONS.keys()), key="tr_x")
            color_label = st.selectbox("צבע לפי", list(COLOR_OPTIONS.keys()), key="tr_color")
        x_axis = X_OPTIONS[x_label]
        color_by = COLOR_OPTIONS[color_label]
        dn = df_neemanim[df_neemanim["total_valid_cases"] >= min_cases].copy()

        c1, c2, c3 = st.columns(3)
        c1.metric("נאמנים בתצוגה", f"{len(dn):,}")
        c2.metric("חציון % ביטול (כללי)", f"{dn['dropout_rate_full'].median() * 100:.1f}%")
        c3.metric("חציון % ביטול (2020)", f"{dn['dropout_rate_2020'].median() * 100:.1f}%")

        with main:
            if view == "chart":
                fig = px.scatter(
                    dn, x=x_axis, y="dropout_rate_full",
                    size=dn["total_valid_cases"].clip(lower=1),
                    color=color_by,
                    hover_name="full_name_neeman",
                    hover_data={"total_valid_cases": True, "pct_150": ":.2f",
                                "pct_siyua": ":.2f", "pct_arab": ":.2f",
                                "rank_change": True},
                    color_continuous_scale="RdYlGn_r" if color_by != "notable_shift" else None,
                    labels={x_axis: x_label, "dropout_rate_full": "שיעור ביטול",
                            color_by: color_label},
                )
                fig.update_layout(height=360)
                st.plotly_chart(fig, use_container_width=True)
            else:
                cols_for_table = ["full_name_neeman", "total_valid_cases",
                                  "dropout_rate_full", x_axis, color_by, "rank_change"]
                cols_for_table = list(dict.fromkeys(cols_for_table))
                table = dn[cols_for_table].copy()
                pct_cols = [c for c in ["dropout_rate_full", "pct_150", "pct_siyua", "pct_arab"]
                            if c in table.columns]
                for c in pct_cols:
                    table[c] = (table[c] * 100).round(1)
                st.dataframe(table.sort_values("dropout_rate_full", ascending=False),
                             use_container_width=True, hide_index=True, height=330)

    st.markdown("---")

    with section("Top / Bottom נאמנים לפי z-score", key="tr_leader") as (side, main, view):
        with side:
            n_show = st.slider("כמה להציג בכל צד", 5, 30, 10, key="tr_n")
            min_cases2 = st.slider("מינימום תיקים", 1, max_cases, 30, step=5, key="tr_min2")
        dn2 = df_neemanim[df_neemanim["total_valid_cases"] >= min_cases2].copy()
        top = dn2.nlargest(n_show, "z_dropout_full")[[
            "full_name_neeman", "total_valid_cases", "dropout_rate_full", "z_dropout_full"]]
        top["dropout_rate_full"] = (top["dropout_rate_full"] * 100).round(1)
        top["z_dropout_full"] = top["z_dropout_full"].round(2)
        top.columns = ["נאמן", "תיקים", "% ביטול", "Z"]
        bot = dn2.nsmallest(n_show, "z_dropout_full")[[
            "full_name_neeman", "total_valid_cases", "dropout_rate_full", "z_dropout_full"]]
        bot["dropout_rate_full"] = (bot["dropout_rate_full"] * 100).round(1)
        bot["z_dropout_full"] = bot["z_dropout_full"].round(2)
        bot.columns = ["נאמן", "תיקים", "% ביטול", "Z"]

        with main:
            if view == "chart":
                combined = pd.concat([top.assign(קבוצה="גבוה מהממוצע"),
                                      bot.assign(קבוצה="נמוך מהממוצע")])
                fig = px.bar(combined, x="Z", y="נאמן", color="קבוצה",
                             orientation="h", hover_data=["תיקים", "% ביטול"])
                fig.update_layout(height=max(290, 17 * len(combined)),
                                  yaxis={"categoryorder": "total ascending"})
                st.plotly_chart(fig, use_container_width=True)
            else:
                col1, col2 = st.columns(2)
                with col1:
                    st.caption("סיכון גבוה מהממוצע")
                    st.dataframe(top, use_container_width=True, hide_index=True,
                                 column_config={
                                     "% ביטול": st.column_config.ProgressColumn(
                                         "% ביטול", format="%.1f%%", min_value=0, max_value=100),
                                 })
                with col2:
                    st.caption("נמוכים משמעותית")
                    st.dataframe(bot, use_container_width=True, hide_index=True,
                                 column_config={
                                     "% ביטול": st.column_config.ProgressColumn(
                                         "% ביטול", format="%.1f%%", min_value=0, max_value=100),
                                 })

    st.markdown("---")

    with section("המנבא החזק: % לקוחות ₪150 מול שיעור ביטול", key="tr_150") as (side, main, view):
        with side:
            min_cases3 = st.slider("מינימום תיקים", 1, max_cases, 30, step=5, key="tr_min3")
        dn3 = df_neemanim[df_neemanim["total_valid_cases"] >= min_cases3].copy()
        with main:
            if view == "chart":
                fig = px.scatter(
                    dn3, x="pct_150", y="dropout_rate_full",
                    size=dn3["total_valid_cases"].clip(lower=1),
                    hover_name="full_name_neeman",
                    trendline="ols",
                    labels={"pct_150": "% לקוחות ₪150",
                            "dropout_rate_full": "שיעור ביטול"},
                )
                fig.update_layout(height=330)
                st.plotly_chart(fig, use_container_width=True)
            else:
                tbl = dn3[["full_name_neeman", "total_valid_cases",
                           "pct_150", "dropout_rate_full"]].copy()
                tbl["pct_150"] = (tbl["pct_150"] * 100).round(1)
                tbl["dropout_rate_full"] = (tbl["dropout_rate_full"] * 100).round(1)
                tbl.columns = ["נאמן", "תיקים", "% ₪150", "% ביטול"]
                st.dataframe(
                    tbl.sort_values("% ₪150", ascending=False),
                    use_container_width=True, hide_index=True, height=330,
                    column_config={
                        "% ביטול": st.column_config.ProgressColumn(
                            "% ביטול", format="%.1f%%", min_value=0, max_value=100),
                        "% ₪150": st.column_config.ProgressColumn(
                            "% ₪150", format="%.1f%%", min_value=0, max_value=100),
                    })

    st.markdown("---")

    with section("טבלת נאמנים מלאה — חיפוש וסינון", key="tr_full") as (side, main, view):
        with side:
            q = st.text_input("חיפוש שם", key="tr_search")
            min_cases4 = st.slider("מינימום תיקים", 1, max_cases, 1, step=5, key="tr_min4")
        dn4 = df_neemanim[df_neemanim["total_valid_cases"] >= min_cases4].copy()
        if q:
            dn4 = dn4[dn4["full_name_neeman"].fillna("").str.contains(q, na=False)]

        display_cols = [
            "full_name_neeman", "total_valid_cases", "dropout_rate_full",
            "dropout_rate_2020", "pct_150", "pct_siyua", "pct_arab",
            "mahoz_באר שבע", "mahoz_חיפה", "mahoz_ירושלים", "mahoz_תל אביב",
            "rank_change", "notable_shift",
        ]
        show = dn4[display_cols].copy()
        for c in ["dropout_rate_full", "dropout_rate_2020", "pct_150", "pct_siyua", "pct_arab",
                  "mahoz_באר שבע", "mahoz_חיפה", "mahoz_ירושלים", "mahoz_תל אביב"]:
            show[c] = (show[c] * 100).round(1)
        show.columns = [
            "נאמן", "תיקים", "% ביטול כללי", "% ביטול 2020",
            "% תשלום 150", "% סיוע", "% ערבי",
            "% ב\"ש", "% חיפה", "% ירושלים", "% ת\"א",
            "Δ דירוג", "שינוי מובהק",
        ]

        with main:
            if view == "chart":
                dist = show[["% ביטול כללי"]].dropna()
                if not dist.empty:
                    fig = px.histogram(dist, x="% ביטול כללי", nbins=30)
                    fig.update_layout(height=280, bargap=0.05)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.caption("אין נתונים.")
            else:
                st.dataframe(
                    show, use_container_width=True, hide_index=True, height=330,
                    column_config={
                        "% ביטול כללי": st.column_config.ProgressColumn(
                            "% ביטול כללי", format="%.1f%%", min_value=0, max_value=100),
                        "% ביטול 2020": st.column_config.ProgressColumn(
                            "% ביטול 2020", format="%.1f%%", min_value=0, max_value=100),
                        "תיקים": st.column_config.NumberColumn("תיקים", format="%d"),
                    })
                download_button(show, "neemanim.csv", key="tr_dl")
