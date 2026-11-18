from pathlib import Path
import pandas as pd
import numpy as np
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent

# The dashboard reads ONLY the anonymized files produced by
# scripts/anonymize.py.  They contain no names, ID numbers, case numbers or
# dates of birth — trustees are P###, debtors H#####, cases T#####.
CLEAN_FILE = DATA_DIR / "df_flat_anon_211026.xlsx"
CLEAN_SHEET = "נתונים"
CLEAN_CACHE = DATA_DIR / ".df_flat_anon_211026.parquet"

# Pre-computed trustees table (optional). When present, we load it directly
# and skip the on-the-fly aggregation in load_neemanim(); otherwise we fall
# back to computing from the flat file.
NEEMANIM_FILE = DATA_DIR / "df_neemanim_anon_211026.xlsx"
NEEMANIM_CACHE = DATA_DIR / ".df_neemanim_anon_211026.parquet"

# app.py compares this to its own constant and re-imports this module (and
# the tabs) if a server process is still holding an older copy in memory.
DATA_VERSION = "211026-2"

CUTOFF_DATE = pd.Timestamp("2026-03-15")

GENDER_MAP = {"ז": "גבר", "נ": "אישה"}
SECTOR_MAP = {0: "יהודי", 1: "ערבי"}
SIYUA_MAP = {0: "ללא סיוע משפטי", 1: "עם סיוע משפטי"}
NECHUT_MAP = {0: "ללא נכות כללית", 1: "עם נכות כללית"}

CLOSED_STATUSES = {"סגור", "הפטר לאלתר", "הפטר", "ביטול"}

MAHOZ_COLS = ["mahoz_באר שבע", "mahoz_חיפה", "mahoz_ירושלים", "mahoz_תל אביב"]

# Defence in depth: raw identifier columns must never reach the UI, even if
# someone points CLEAN_FILE at a raw file by mistake.
_CLASSIFIED_COLS = ["num_tik", "id_hayav", "dob", "first_date", "last_date"]
_REQUIRED_ANON_COLS = ["tik_code", "hayav_code", "neeman_1"]

_OUTCOME_FROM_REASON = {
    "הפטר לאלתר": "הפטר לאלתר",
    "הפטר": "הפטר",
    "ביטול לאחר צו שיקום": "ביטול לאחר צו שיקום",
    "ביטול": "ביטול לפני צו שיקום",
    "ניתן צו שיקום כלכלי": "פתוח — צו שיקום",
    "ניתן צו פתיחת הליכים": "פתוח — שלב א'",
}
_OUTCOME_FROM_STATUS = {
    "ניתן צו שיקום כלכלי": "פתוח — צו שיקום",
    "ניתן צו פתיחת הליכים": "פתוח — שלב א'",
}


def _parquet_fresh(cache: Path, source: Path) -> bool:
    return (
        cache.exists()
        and source.exists()
        and cache.stat().st_mtime >= source.stat().st_mtime
    )


def _read_clean() -> pd.DataFrame:
    # Parquet reads ~10x faster than Excel.  We transparently cache a parquet
    # copy next to the source and rebuild whenever the source is newer.
    if _parquet_fresh(CLEAN_CACHE, CLEAN_FILE):
        return pd.read_parquet(CLEAN_CACHE)
    df = pd.read_excel(CLEAN_FILE, sheet_name=CLEAN_SHEET)
    missing = [c for c in _REQUIRED_ANON_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"{CLEAN_FILE.name} is not the anonymized file "
                         f"(missing {missing}) — run scripts/anonymize.py")
    df = df.drop(columns=[c for c in _CLASSIFIED_COLS if c in df.columns])
    try:
        df.to_parquet(CLEAN_CACHE, index=False)
    except Exception:
        pass
    return df


@st.cache_data(show_spinner="טוען נתונים…")
def load_flat() -> pd.DataFrame:
    df = _read_clean()

    # Tabs count cases with "num_tik"; it now holds the anonymous T-code.
    df["num_tik"] = df["tik_code"]
    # The trustee a case is attributed to: the latest one assigned
    # (neeman_2 when the trustee was replaced, otherwise neeman_1).
    df["neeman"] = df["neeman_2"].fillna(df["neeman_1"])

    df["d_tzav_ptichat_halichim"] = pd.to_datetime(
        df["d_tzav_ptichat_halichim"], errors="coerce", dayfirst=True)
    df["d_tzav_shikum"] = pd.to_datetime(
        df["d_tzav_shikum"], errors="coerce", dayfirst=True)

    df["gender_label"] = df["gender"].map(GENDER_MAP).fillna("לא ידוע")
    df["sector_label"] = df["is_arab"].map(SECTOR_MAP).fillna("לא ידוע")
    df["siyua_label"] = df["is_siyua_bin"].map(SIYUA_MAP).fillna("לא ידוע")
    df["nechut_label"] = df["has_nechut_klalit"].map(NECHUT_MAP).fillna("לא ידוע")

    delta_days = (df["d_tzav_shikum"] - df["d_tzav_ptichat_halichim"]).dt.days
    df["duration_stage1_months"] = delta_days / 30.44

    time_to_cutoff_days = (CUTOFF_DATE - df["d_tzav_ptichat_halichim"]).dt.days
    df["months_since_opening"] = time_to_cutoff_days / 30.44

    df["is_closed"] = df["status_d_15032026"].isin(CLOSED_STATUSES)

    outcome = df["sibat_sgira_kidud_c"].map(_OUTCOME_FROM_REASON)
    outcome = outcome.fillna(df["status_d_15032026"].map(_OUTCOME_FROM_STATUS))
    outcome = outcome.fillna(df["status_d_15032026"]).fillna("לא ידוע")
    df["outcome"] = outcome

    df["is_immediate_discharge"] = df["outcome"] == "הפטר לאלתר"
    df["is_hefter"] = df["outcome"] == "הפטר"
    # "נשירה" per the legend / presentation = did NOT reach the shikum order
    # (got_2shikum_bin == 0, equivalent to sibat_sgira_kidud_c == "ביטול").
    # This yields Haifa 40.6%, matching the deck.  The old post-shikum-only
    # definition gave 9.6% for Haifa and did not match the presentation.
    df["is_dropout"] = df["outcome"] == "ביטול לפני צו שיקום"
    df["is_post_shikum_cancel"] = df["outcome"] == "ביטול לאחר צו שיקום"
    df["is_any_bitul"] = df["is_dropout"] | df["is_post_shikum_cancel"]

    return df


def _read_neemanim_file() -> pd.DataFrame:
    if _parquet_fresh(NEEMANIM_CACHE, NEEMANIM_FILE):
        return pd.read_parquet(NEEMANIM_CACHE)
    df = pd.read_excel(NEEMANIM_FILE)
    # Defence in depth: the real-name column is "id_neeman_clean" in the raw
    # file; after anonymization it should be gone.  Drop it if it survived.
    df = df.drop(columns=[c for c in ("id_neeman_clean",) if c in df.columns])
    try:
        df.to_parquet(NEEMANIM_CACHE, index=False)
    except Exception:
        pass
    return df


@st.cache_data(show_spinner="מחשב נאמנים…")
def load_neemanim() -> pd.DataFrame:
    if NEEMANIM_FILE.exists():
        df = _read_neemanim_file()
        for m in MAHOZ_COLS:
            if m not in df.columns:
                df[m] = 0.0
            df[m] = df[m].fillna(0.0)
        return df

    # Fallback: compute aggregates from the flat file. load_flat() is cached,
    # so this call is near-instant after first load.
    flat = load_flat()
    d = flat.dropna(subset=["neeman"]).copy()

    agg = d.groupby("neeman").agg(
        total_valid_cases=("num_tik", "count"),
        bitul_cases_full=("is_dropout", "sum"),
        pct_150=("first_payment", lambda s: (s == 150).mean()),
        pct_siyua=("is_siyua_bin", "mean"),
        pct_arab=("is_arab", "mean"),
    ).reset_index().rename(columns={"neeman": "full_name_neeman"})
    agg["dropout_rate_full"] = agg["bitul_cases_full"] / agg["total_valid_cases"]

    d2020 = d[d["year"] == 2020]
    r2020 = d2020.groupby("neeman").agg(
        cases_2020=("num_tik", "count"),
        bitul_2020=("is_dropout", "sum"),
    ).reset_index().rename(columns={"neeman": "full_name_neeman"})
    r2020["dropout_rate_2020"] = np.where(
        r2020["cases_2020"] > 0, r2020["bitul_2020"] / r2020["cases_2020"], np.nan)
    agg = agg.merge(
        r2020[["full_name_neeman", "dropout_rate_2020", "bitul_2020"]],
        on="full_name_neeman", how="left",
    )

    mahoz_share = pd.crosstab(
        d["neeman"], d["mahoz"], normalize="index"
    )
    mahoz_share.columns = [f"mahoz_{c}" for c in mahoz_share.columns]
    mahoz_share = mahoz_share.reset_index().rename(
        columns={"neeman": "full_name_neeman"})
    agg = agg.merge(mahoz_share, on="full_name_neeman", how="left")
    for m in MAHOZ_COLS:
        if m not in agg.columns:
            agg[m] = 0.0
        agg[m] = agg[m].fillna(0.0)

    return agg


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    out = df
    if filters.get("years"):
        out = out[out["year"].isin(filters["years"])]
    if filters.get("mahoz"):
        out = out[out["mahoz"].isin(filters["mahoz"])]
    if filters.get("gender_labels"):
        out = out[out["gender_label"].isin(filters["gender_labels"])]
    if filters.get("statuses"):
        out = out[out["status_d_15032026"].isin(filters["statuses"])]
    if filters.get("sectors"):
        out = out[out["sector_label"].isin(filters["sectors"])]
    if filters.get("siyua"):
        out = out[out["siyua_label"].isin(filters["siyua"])]
    if filters.get("age_bins"):
        out = out[out["age_bin"].isin(filters["age_bins"])]
    return out


def empty_state(msg: str = "אין נתונים לפילטרים שנבחרו"):
    st.info(msg)
