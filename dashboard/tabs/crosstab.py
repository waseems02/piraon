import streamlit as st
import pandas as pd
import plotly.express as px

from data_loader import empty_state
from ui import styled_dataframe, wrap_text


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

AGG_MODES = {
    "ספירה": "count",
    "% משורה": "row",
    "% מעמודה": "col",
    "% מסך הכל": "total",
}


def _build_crosstab(df: pd.DataFrame, row_col: str, col_col: str, mode: str,
                    show_margins: bool) -> pd.DataFrame:
    sub = df[[row_col, col_col]].dropna()
    if sub.empty:
        return pd.DataFrame()

    if mode == "count":
        ct = pd.crosstab(sub[row_col], sub[col_col], margins=show_margins,
                         margins_name="סה\"כ")
        return ct.astype(int)

    if mode == "row":
        ct = pd.crosstab(sub[row_col], sub[col_col], normalize="index") * 100
    elif mode == "col":
        ct = pd.crosstab(sub[row_col], sub[col_col], normalize="columns") * 100
    else:
        ct = pd.crosstab(sub[row_col], sub[col_col], normalize=True) * 100

    ct = ct.round(1)
    if show_margins:
        if mode == "row":
            ct["סה\"כ"] = 100.0
        elif mode == "col":
            ct.loc["סה\"כ"] = 100.0
        else:
            ct["סה\"כ"] = ct.sum(axis=1).round(1)
            ct.loc["סה\"כ"] = ct.sum(axis=0).round(1)
    return ct


def render(df: pd.DataFrame, df_neemanim: pd.DataFrame):
    st.subheader("טבלת הצלבה — בין שתי קטגוריות")
    st.caption(
        "בחר שני ממדים קטגוריאליים כדי לראות את ההתפלגות המשולבת (ספירה או אחוזים)."
    )

    if df.empty:
        empty_state()
        return

    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
    with c1:
        row_label = st.selectbox("שורה", list(DIMENSIONS.keys()), index=0, key="ct_row")
    with c2:
        col_options = [k for k in DIMENSIONS.keys() if k != row_label]
        col_label = st.selectbox("עמודה", col_options,
                                 index=min(2, len(col_options) - 1), key="ct_col")
    with c3:
        agg_label = st.selectbox("אגרגציה", list(AGG_MODES.keys()), key="ct_agg")
    with c4:
        show_margins = st.checkbox("הצג סיכומים", value=True, key="ct_margins")

    show_heatmap = st.checkbox("הצג גם מפת-חום", value=True, key="ct_heat")

    row_col = DIMENSIONS[row_label]
    col_col = DIMENSIONS[col_label]
    mode = AGG_MODES[agg_label]

    ct = _build_crosstab(df, row_col, col_col, mode, show_margins)
    if ct.empty:
        st.info("אין נתונים לשני הממדים שנבחרו (ייתכן שהעמודה לא קיימת או שהפילטרים ריקים).")
        return

    is_pct = mode != "count"
    display = ct.copy()
    if is_pct:
        display = display.applymap(lambda v: f"{v:.1f}%")

    display.index.name = row_label
    display.columns.name = col_label
    display_reset = display.reset_index()

    column_config = {}
    if is_pct:
        for c in display_reset.columns:
            if c != row_label:
                column_config[c] = st.column_config.TextColumn(c)
    styled_dataframe(display_reset, column_config=column_config)

    if show_heatmap:
        ct_numeric = ct.copy()
        if show_margins:
            ct_numeric = ct_numeric.drop(index=[i for i in ["סה\"כ"] if i in ct_numeric.index],
                                         errors="ignore")
            ct_numeric = ct_numeric.drop(columns=[c for c in ["סה\"כ"] if c in ct_numeric.columns],
                                         errors="ignore")
        if not ct_numeric.empty:
            ct_plot = ct_numeric.copy()
            ct_plot.columns = [wrap_text(str(c), 10) for c in ct_plot.columns]
            ct_plot.index = [wrap_text(str(i), 14) for i in ct_plot.index]
            fig = px.imshow(
                ct_plot,
                text_auto=".1f" if is_pct else True,
                aspect="auto",
                color_continuous_scale="Blues",
                labels=dict(x=col_label, y=row_label,
                            color="%" if is_pct else "תיקים"),
            )
            rows = len(ct_plot.index)
            cell_h = 60 if rows <= 6 else (50 if rows <= 10 else 42)
            chart_height = min(950, max(420, 180 + cell_h * rows))
            fig.update_layout(
                height=chart_height,
                margin=dict(t=100, r=40, l=70, b=40),
                font=dict(size=14),
                coloraxis_colorbar=dict(thickness=16, len=0.85, outlinewidth=0),
            )
            fig.update_xaxes(side="top", tickfont=dict(size=13))
            fig.update_yaxes(tickfont=dict(size=13))
            fig.update_traces(textfont=dict(size=15))
            st.plotly_chart(fig, use_container_width=True)
