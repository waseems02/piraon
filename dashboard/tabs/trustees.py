import streamlit as st
import pandas as pd
import plotly.express as px

from data_loader import empty_state
from ui import section, wrap_text


X_OPTIONS = {
    "סה\"כ תיקים": "total_valid_cases",
    "% תשלום ₪150": "pct_150",
    "% ערבים": "pct_arab",
    "% סיוע משפטי": "pct_siyua",
}
COLOR_OPTIONS = {
    "% תשלום ₪150": "pct_150",
    "% ערבים": "pct_arab",
    "% סיוע משפטי": "pct_siyua",
}


def render(df: pd.DataFrame, df_neemanim: pd.DataFrame):
    st.subheader("נאמנים — שיעורי ביטול")
    st.caption(
        "דירוג נאמנים לפי שיעור הביטול בתיקיהם. ניתן לסנן לפי מינימום תיקים ולחפש לפי שם."
    )

    if df_neemanim.empty:
        empty_state("קובץ הנאמנים ריק.")
        return

    max_cases = int(df_neemanim["total_valid_cases"].max())

    overall_median = df_neemanim["dropout_rate_full"].median() * 100
    overall_mean = df_neemanim["dropout_rate_full"].mean() * 100
    overall_max = df_neemanim["dropout_rate_full"].max() * 100
    overall_cases = int(df_neemanim["total_valid_cases"].sum())

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("סך נאמנים", f"{len(df_neemanim):,}")
    k2.metric("סך תיקים", f"{overall_cases:,}")
    k3.metric("חציון % ביטול", f"{overall_median:.1f}%")
    k4.metric("ממוצע % ביטול", f"{overall_mean:.1f}%")
    k5.metric("% ביטול מקסימלי", f"{overall_max:.1f}%")

    st.markdown("---")

    with section("דירוג נאמנים לפי שיעור ביטול", key="tr_rank") as (side, main, view):
        with side:
            min_cases = st.slider("מינימום תיקים", 1, max_cases, 30, step=5, key="tr_min")
            top_n = st.slider("Top N להצגה", 10, 40, 20, step=5, key="tr_topn")
            q = st.text_input("חיפוש שם", key="tr_search")

        dn = df_neemanim[df_neemanim["total_valid_cases"] >= min_cases].copy()
        if q:
            dn = dn[dn["full_name_neeman"].fillna("").str.contains(q, na=False)]

        median_pct = dn["dropout_rate_full"].median() * 100 if len(dn) else 0

        top = dn.nlargest(top_n, "dropout_rate_full").copy()
        top["% ביטול"] = (top["dropout_rate_full"] * 100).round(1)
        top["תיקים"] = top["total_valid_cases"]
        top["נאמן"] = top["full_name_neeman"]
        top = top.sort_values("% ביטול", ascending=False)

        with main:
            if dn.empty:
                st.caption("אין נאמנים לפי הסינון.")
            elif view == "chart":
                fig = px.bar(
                    top, x="נאמן", y="% ביטול",
                    text="% ביטול", color="% ביטול",
                    color_continuous_scale=[
                        [0.0, "#3a8fb7"],
                        [0.5, "#e07b39"],
                        [1.0, "#c94f4f"],
                    ],
                    hover_data={"תיקים": True, "נאמן": False, "% ביטול": ":.1f"},
                )
                if len(dn) > 1 and median_pct > 0:
                    fig.add_hline(
                        y=median_pct, line_dash="dash", line_color="#1f4e79",
                        line_width=1.5,
                        annotation_text=f"חציון כולל: {median_pct:.1f}%",
                        annotation_position="top left",
                        annotation_font=dict(size=11, color="#1f4e79"),
                    )
                fig.update_traces(
                    textposition="outside",
                    textfont=dict(size=11, color="#1f4e79", family="Assistant, sans-serif"),
                    marker=dict(line=dict(width=0)),
                    cliponaxis=False,
                )
                fig.update_layout(
                    height=480,
                    coloraxis_showscale=False,
                    xaxis_title="",
                    yaxis_title="שיעור ביטול (%)",
                    bargap=0.28,
                    margin=dict(t=50, r=20, l=60, b=70),
                    plot_bgcolor="rgba(255,255,255,0.35)",
                )
                fig.update_xaxes(
                    tickangle=0,
                    tickfont=dict(size=11, color="#1f4e79"),
                    categoryorder="total descending",
                )
                fig.update_yaxes(
                    gridcolor="rgba(31,78,121,0.08)",
                    zerolinecolor="rgba(31,78,121,0.18)",
                    ticksuffix="%",
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                table = top[["נאמן", "תיקים", "% ביטול"]].copy()
                st.dataframe(
                    table, use_container_width=True, hide_index=True, height=420,
                    column_config={
                        "% ביטול": st.column_config.ProgressColumn(
                            "% ביטול", format="%.1f%%", min_value=0, max_value=100),
                        "תיקים": st.column_config.NumberColumn("תיקים", format="%d"),
                    },
                )

    st.markdown("---")

    with section("נאמנים לפי שיעור ביטול ומדדים נוספים", key="tr_scatter") as (side, main, view):
        with side:
            min_cases2 = st.slider("מינימום תיקים", 1, max_cases, 30, step=5, key="tr_min2")
            x_label = st.selectbox("ציר X", list(X_OPTIONS.keys()), key="tr_x")
            color_label = st.selectbox("צבע לפי", list(COLOR_OPTIONS.keys()), key="tr_color")
        x_axis = X_OPTIONS[x_label]
        color_by = COLOR_OPTIONS[color_label]
        dn2 = df_neemanim[df_neemanim["total_valid_cases"] >= min_cases2].copy()
        with main:
            if dn2.empty:
                st.caption("אין נאמנים לפי הסינון.")
            elif view == "chart":
                color_label_wrapped = wrap_text(color_label, 8)
                fig = px.scatter(
                    dn2, x=x_axis, y="dropout_rate_full",
                    color=color_by,
                    hover_name="full_name_neeman",
                    hover_data={"total_valid_cases": True,
                                "pct_150": ":.2f", "pct_siyua": ":.2f", "pct_arab": ":.2f"},
                    trendline="ols", trendline_color_override="#c94f4f",
                    color_continuous_scale="RdYlGn_r",
                    labels={x_axis: x_label, "dropout_rate_full": "שיעור ביטול",
                            color_by: color_label_wrapped},
                )
                fig.update_traces(marker=dict(size=8, opacity=0.85, line=dict(width=0)),
                                  selector=dict(mode="markers"))
                fig.update_layout(
                    height=400,
                    margin=dict(t=60, r=40, l=50, b=50),
                    coloraxis_colorbar=dict(
                        title=dict(text=color_label_wrapped, side="top"),
                        thickness=14, len=0.9,
                    ),
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                cols_for_table = ["full_name_neeman", "total_valid_cases",
                                  "dropout_rate_full", x_axis, color_by]
                cols_for_table = list(dict.fromkeys(cols_for_table))
                table = dn2[cols_for_table].copy()
                pct_cols = [c for c in ["dropout_rate_full", "pct_150", "pct_siyua", "pct_arab"]
                            if c in table.columns]
                for c in pct_cols:
                    table[c] = (table[c] * 100).round(1)
                st.dataframe(table.sort_values("dropout_rate_full", ascending=False),
                             use_container_width=True, hide_index=True, height=330)

    st.markdown("---")

    with section("המנבא החזק: % לקוחות ₪150 מול שיעור ביטול", key="tr_150") as (side, main, view):
        color_options_150 = {
            "שיעור ביטול": "dropout_rate_full",
            "% ערבים": "pct_arab",
            "% סיוע משפטי": "pct_siyua",
        }
        with side:
            min_cases3 = st.slider("מינימום תיקים", 1, max_cases, 30, step=5, key="tr_min3")
            color_label_150 = st.selectbox("צבע לפי",
                                           list(color_options_150.keys()), key="tr_color_150")
        color_by_150 = color_options_150[color_label_150]
        dn3 = df_neemanim[df_neemanim["total_valid_cases"] >= min_cases3].copy()
        with main:
            if dn3.empty:
                st.caption("אין נאמנים לפי הסינון.")
            elif view == "chart":
                fig = px.scatter(
                    dn3, x="pct_150", y="dropout_rate_full",
                    color=color_by_150,
                    hover_name="full_name_neeman",
                    hover_data={"total_valid_cases": True,
                                "pct_150": ":.2f", "pct_siyua": ":.2f", "pct_arab": ":.2f"},
                    trendline="ols", trendline_color_override="#c94f4f",
                    color_continuous_scale="RdYlGn_r",
                    labels={"pct_150": "% לקוחות ₪150",
                            "dropout_rate_full": "שיעור ביטול",
                            color_by_150: color_label_150},
                )
                fig.update_traces(marker=dict(size=7, opacity=0.8, line=dict(width=0)),
                                  selector=dict(mode="markers"))
                x_min, x_max = dn3["pct_150"].min(), dn3["pct_150"].max()
                y_min, y_max = dn3["dropout_rate_full"].min(), dn3["dropout_rate_full"].max()
                x_pad = (x_max - x_min) * 0.12 if x_max > x_min else 0.05
                y_pad = (y_max - y_min) * 0.15 if y_max > y_min else 0.05
                fig.update_xaxes(range=[max(0, x_min - x_pad), x_max + x_pad])
                fig.update_yaxes(range=[max(0, y_min - y_pad), y_max + y_pad])
                fig.update_layout(height=520, margin=dict(t=40, r=40, l=60, b=60))
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
            q4 = st.text_input("חיפוש שם", key="tr_search_full")
            min_cases4 = st.slider("מינימום תיקים", 1, max_cases, 1, step=5, key="tr_min4")
        dn4 = df_neemanim[df_neemanim["total_valid_cases"] >= min_cases4].copy()
        if q4:
            dn4 = dn4[dn4["full_name_neeman"].fillna("").str.contains(q4, na=False)]

        display_cols = [
            "full_name_neeman", "total_valid_cases", "dropout_rate_full",
            "dropout_rate_2020", "pct_150", "pct_siyua", "pct_arab",
            "mahoz_באר שבע", "mahoz_חיפה", "mahoz_ירושלים", "mahoz_תל אביב",
        ]
        show = dn4[display_cols].copy()
        for c in ["dropout_rate_full", "dropout_rate_2020", "pct_150", "pct_siyua", "pct_arab",
                  "mahoz_באר שבע", "mahoz_חיפה", "mahoz_ירושלים", "mahoz_תל אביב"]:
            show[c] = (show[c] * 100).round(1)
        show.columns = [
            "נאמן", "תיקים", "% ביטול כללי", "% ביטול 2020",
            "% תשלום 150", "% סיוע", "% ערבי",
            "% ב\"ש", "% חיפה", "% ירושלים", "% ת\"א",
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
                    show, use_container_width=True, hide_index=True, height=360,
                    column_config={
                        "% ביטול כללי": st.column_config.ProgressColumn(
                            "% ביטול כללי", format="%.1f%%", min_value=0, max_value=100),
                        "% ביטול 2020": st.column_config.ProgressColumn(
                            "% ביטול 2020", format="%.1f%%", min_value=0, max_value=100),
                        "תיקים": st.column_config.NumberColumn("תיקים", format="%d"),
                    })

