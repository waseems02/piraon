from contextlib import contextmanager
import streamlit as st


VIEW_CHART = "chart"
VIEW_DATA = "data"


def view_toggle(key: str, default: str = VIEW_CHART) -> str:
    """Icon-only toggle between chart and data views. Returns 'chart' or 'data'."""
    options = [VIEW_CHART, VIEW_DATA]
    labels = {VIEW_CHART: ":material/bar_chart:", VIEW_DATA: ":material/table_view:"}
    selection = st.segmented_control(
        " ",
        options=options,
        format_func=lambda o: labels[o],
        default=default,
        key=f"view_{key}",
        label_visibility="collapsed",
    )
    return selection or default


@contextmanager
def section(title: str, key: str, side_ratio: int = 1, main_ratio: int = 3):
    """
    Yields (side_col, main_col, view) so the caller can:
      - put filters + the icon toggle in side_col
      - render either a chart or a table in main_col based on `view`

    Usage:
        with section("שיעור ביטול לפי מחוז", key="drop_by_mahoz") as (side, main, view):
            with side:
                # filters
                min_n = st.slider(...)
            with main:
                if view == "chart":
                    st.plotly_chart(...)
                else:
                    st.dataframe(...)
    """
    st.markdown(f"##### {title}")
    side, main = st.columns([side_ratio, main_ratio])
    with side:
        yield_view_placeholder = st.container()
    view = None
    with side:
        # rendered after the yield: caller places filters first, then we place toggle at the bottom
        pass
    # We need a two-pass approach: run the with-block, but caller might place widgets
    # before the toggle. Simplest: place the toggle at the top of side_col.
    with side:
        view = view_toggle(key)
        st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
    try:
        yield side, main, view
    finally:
        pass


def styled_dataframe(df, **kwargs):
    """Wrapper for st.dataframe with consistent defaults."""
    kwargs.setdefault("use_container_width", True)
    kwargs.setdefault("hide_index", True)
    return st.dataframe(df, **kwargs)


def download_button(df, filename: str, key: str = None):
    st.download_button(
        "הורדת CSV",
        df.to_csv(index=False).encode("utf-8-sig"),
        filename,
        "text/csv",
        key=key,
    )


def wrap_text(text, max_chars: int = 12) -> str:
    if not isinstance(text, str) or len(text) <= max_chars:
        return text
    words = text.split()
    if not words:
        return text
    lines, current = [], ""
    for w in words:
        candidate = f"{current} {w}".strip() if current else w
        if len(candidate) <= max_chars or not current:
            current = candidate
        else:
            lines.append(current)
            current = w
    if current:
        lines.append(current)
    return "<br>".join(lines)


def wrap_x_labels(fig, max_chars: int = 12):
    """Insert <br> into long string x-axis categories so labels stay horizontal."""
    seen, order = set(), []
    for tr in fig.data:
        xs = getattr(tr, "x", None)
        if xs is None:
            continue
        for v in xs:
            if isinstance(v, str) and v not in seen:
                seen.add(v)
                order.append(v)
    if not order:
        return fig
    fig.update_xaxes(
        tickmode="array",
        tickvals=order,
        ticktext=[wrap_text(v, max_chars) for v in order],
    )
    return fig
