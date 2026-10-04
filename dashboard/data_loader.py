from pathlib import Path
import pandas as pd
import numpy as np
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent
# Names of neemanim and debtors are classified — the CSV replaces them with
# anonymous identifiers (P001, P002, …). The full neemanim table is rebuilt
# from this file so no real names ever reach the dashboard.
FLAT_FILE = DATA_DIR / "df_flat_Anonymous.csv"

CUTOFF_DATE = pd.Timestamp("2026-03-15")

GENDER_MAP = {"ז": "גבר", "נ": "אישה"}
SECTOR_MAP = {0: "יהודי", 1: "ערבי"}
SIYUA_MAP = {0: "ללא סיוע משפטי", 1: "עם סיוע משפטי"}
NECHUT_MAP = {0: "ללא נכות כללית", 1: "עם נכות כללית"}

CLOSED_STATUSES = {"סגור", "הפטר לאלתר", "הפטר", "ביטול"}
DROPOUT_REASON = "ביטול לאחר צו שיקום"
IMMEDIATE_DISCHARGE = "הפטר לאלתר"

MAHOZ_COLS = ["mahoz_באר שבע", "mahoz_חיפה", "mahoz_ירושלים", "mahoz_תל אביב"]


def load_flat() -> pd.DataFrame:
    df = pd.read_csv(FLAT_FILE, encoding="utf-8-sig", low_memory=False)
    df["d_tzav_ptichat_halichim"] = pd.to_datetime(
        df["d_tzav_ptichat_halichim"], errors="coerce", dayfirst=True)
    df["d_tzav_shikum"] = pd.to_datetime(
        df["d_tzav_shikum"], errors="coerce", dayfirst=True)

    # Aliases so downstream code (which pre-dates anonymization) keeps working:
    # trustee display name = the anonymized P-code.
    df["neeman_2"] = df["name_clean_anonymous"]

    df["gender_label"] = df["gender"].map(GENDER_MAP).fillna("לא ידוע")
    df["sector_label"] = df["is_arab"].map(SECTOR_MAP).fillna("לא ידוע")
    df["siyua_label"] = df["is_siyua_bin"].map(SIYUA_MAP).fillna("לא ידוע")
    df["nechut_label"] = df["has_nechut_klalit"].map(NECHUT_MAP).fillna("לא ידוע")

    delta_days = (df["d_tzav_shikum"] - df["d_tzav_ptichat_halichim"]).dt.days
    df["duration_stage1_months"] = delta_days / 30.44

    time_to_cutoff_days = (CUTOFF_DATE - df["d_tzav_ptichat_halichim"]).dt.days
    df["months_since_opening"] = time_to_cutoff_days / 30.44

    df["is_closed"] = df["status_d_15032026"].isin(CLOSED_STATUSES)

    def outcome_bucket(row):
        s = row["status_d_15032026"]
        r = row["sibat_sgira_kidud_c"]
        if s == "סגור":
            if r == "הפטר לאלתר":
                return "הפטר לאלתר"
            if r == "ביטול לאחר צו שיקום":
                return "ביטול לאחר צו שיקום"
            if r == "ניתן צו שיקום כלכלי":
                return "הפטר"
            return "סגור (אחר)"
        if s == "הפטר לאלתר":
            return "הפטר לאלתר"
        if s == "הפטר":
            return "הפטר"
        if s == "ביטול":
            return "ביטול לאחר צו שיקום"
        if s == "ניתן צו שיקום כלכלי":
            return "פתוח — צו שיקום"
        if s == "ניתן צו פתיחת הליכים":
            return "פתוח — שלב א'"
        return s
    df["outcome"] = df.apply(outcome_bucket, axis=1)

    df["is_immediate_discharge"] = df["outcome"] == "הפטר לאלתר"
    df["is_dropout"] = df["outcome"] == "ביטול לאחר צו שיקום"
    df["is_hefter"] = df["outcome"] == "הפטר"

    return df


def load_neemanim() -> pd.DataFrame:
    # Rebuilt from the anonymized flat file — the original neemanim table
    # still contained real names, so we re-aggregate here so every metric is
    # keyed by the P-code alone.
    flat = load_flat()
    d = flat.dropna(subset=["name_clean_anonymous"]).copy()

    agg = d.groupby("name_clean_anonymous").agg(
        total_valid_cases=("num_tik", "count"),
        bitul_cases_full=("is_dropout", "sum"),
        pct_150=("first_payment", lambda s: (s == 150).mean()),
        pct_siyua=("is_siyua_bin", "mean"),
        pct_arab=("is_arab", "mean"),
    ).reset_index().rename(columns={"name_clean_anonymous": "full_name_neeman"})
    agg["dropout_rate_full"] = agg["bitul_cases_full"] / agg["total_valid_cases"]

    d2020 = d[d["year"] == 2020]
    r2020 = d2020.groupby("name_clean_anonymous").agg(
        cases_2020=("num_tik", "count"),
        bitul_2020=("is_dropout", "sum"),
    ).reset_index().rename(columns={"name_clean_anonymous": "full_name_neeman"})
    r2020["dropout_rate_2020"] = np.where(
        r2020["cases_2020"] > 0, r2020["bitul_2020"] / r2020["cases_2020"], np.nan)
    agg = agg.merge(
        r2020[["full_name_neeman", "dropout_rate_2020", "bitul_2020"]],
        on="full_name_neeman", how="left",
    )

    mahoz_share = pd.crosstab(
        d["name_clean_anonymous"], d["mahoz"], normalize="index"
    )
    mahoz_share.columns = [f"mahoz_{c}" for c in mahoz_share.columns]
    mahoz_share = mahoz_share.reset_index().rename(
        columns={"name_clean_anonymous": "full_name_neeman"})
    agg = agg.merge(mahoz_share, on="full_name_neeman", how="left")
    for m in MAHOZ_COLS:
        if m not in agg.columns:
            agg[m] = 0.0
        agg[m] = agg[m].fillna(0.0)

    return agg


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    out = df.copy()
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
