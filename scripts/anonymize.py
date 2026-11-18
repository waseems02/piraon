"""Build the anonymized dataset and the anonymization key (טבלת התממה).

Input  : df_flat_clean_211026.xlsx            (raw — contains real identifiers)
Outputs: df_flat_anon_211026.xlsx             (safe to share / used by the dashboard)
         טבלת_התממה_211026.xlsx               (the KEY — private, never share/commit)

Codes
  P###    trustee (נאמן)  — same name always gets the same code; codes from the
                           previous dataset (P001…P244) are kept, new names continue.
  H#####  debtor  (חייב)  — one code per ID number (תעודת זהות), so a person who
                           appears in several cases keeps the same code. Numbers
                           continue the previous dataset's id_Anonymous numbering.
  T#####  case    (תיק)   — one code per case number.

Removed outright: dob (age columns remain), first_date, last_date.

Run from the project root:  py -3.13 scripts/anonymize.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "df_flat_clean_211026.xlsx"
OUT = ROOT / "df_flat_anon_211026.xlsx"
KEY = ROOT / "טבלת_התממה_211026.xlsx"

# Previous dataset — used only to keep existing codes stable.
OLD_RAW = ROOT / "df_flat_clean_121026.xlsx"
OLD_ANON = ROOT / "df_flat_Anonymous.csv"

DROP_COLS = ["dob", "first_date", "last_date"]
MIN_ID_DIGITS = 5


def _old_codes():
    """Return (trustee name -> P-code, id -> number) from the previous dataset."""
    if not (OLD_RAW.exists() and OLD_ANON.exists()):
        return {}, {}
    old = pd.read_excel(OLD_RAW, sheet_name="נתונים",
                        usecols=["num_tik", "neeman_1", "neeman_2", "id_hayav"])
    anon = pd.read_csv(OLD_ANON, encoding="utf-8-sig", low_memory=False,
                       usecols=["num_tik", "neeman1_anonymous",
                                "neeman2_anonymous", "id_Anonymous"])
    m = old.merge(anon, on="num_tik")
    pairs = pd.concat([
        m[["neeman_1", "neeman1_anonymous"]].set_axis(["name", "code"], axis=1),
        m[["neeman_2", "neeman2_anonymous"]].set_axis(["name", "code"], axis=1),
    ]).dropna().drop_duplicates()
    assert not pairs["name"].duplicated().any(), "old trustee codes inconsistent"
    trustee = dict(zip(pairs["name"], pairs["code"]))
    ids = m[["id_hayav", "id_Anonymous"]].dropna().drop_duplicates()
    assert not ids["id_hayav"].duplicated().any(), "old id codes inconsistent"
    id_num = dict(zip(ids["id_hayav"], ids["id_Anonymous"].str[1:].astype(int)))
    return trustee, id_num


def _salary_bin(s: pd.Series) -> pd.Series:
    bins = [-np.inf, 0, 1000, 2000, 5000, 7500, 10000, np.inf]
    labels = ["up to 0", "1-1000", "1001-2000", "2001-5000",
              "5001-7500", "7501-10000", "10000+"]
    return pd.cut(s, bins=bins, labels=labels).astype("string")


def main():
    df = pd.read_excel(RAW, sheet_name="Sheet1")
    legend = pd.read_excel(RAW, sheet_name="מקראה")
    old_trustee, old_id = _old_codes()

    # --- trustees -> P-codes (shared namespace for neeman_1 and neeman_2) ---
    names = pd.concat([df["neeman_1"], df["neeman_2"]]).dropna().unique()
    trustee = {n: old_trustee[n] for n in names if n in old_trustee}
    nxt = max([int(c[1:]) for c in old_trustee.values()], default=0) + 1
    for n in sorted(set(names) - set(trustee)):
        trustee[n] = f"P{nxt:03d}"
        nxt += 1

    # --- debtors (ID number) -> H-codes, stable per person ---
    # IDs shorter than MIN_ID_DIGITS are placeholders shared by unrelated
    # people (e.g. one 1-digit value covers 8 cases with different genders and
    # cities) — they get no person code, so they are never linked together.
    valid = df["id_hayav"].astype(str).str.len() >= MIN_ID_DIGITS
    ids = df[valid].sort_values("num_tik")["id_hayav"].drop_duplicates()
    id_code, nxt = {}, max(old_id.values(), default=0) + 1
    for i in ids:
        if i in old_id:
            id_code[i] = old_id[i]
        else:
            id_code[i] = nxt
            nxt += 1
    id_code = {i: f"H{n:05d}" for i, n in id_code.items()}

    # --- cases -> T-codes ---
    tik_code = {t: f"T{k:05d}" for k, t in
                enumerate(sorted(df["num_tik"].unique()), start=1)}

    # --- build anonymized frame ---
    anon = df.copy()
    anon.insert(0, "tik_code", anon.pop("num_tik").map(tik_code))
    anon.insert(1, "hayav_code", anon.pop("id_hayav").map(id_code))
    anon["neeman_1"] = anon["neeman_1"].map(trustee)
    anon["neeman_2"] = anon["neeman_2"].map(trustee)
    anon = anon.drop(columns=[c for c in DROP_COLS if c in anon.columns])
    anon["income_salery_bin"] = _salary_bin(anon["income_salery"])

    # Safety checks: no raw identifier survives.
    assert not anon.isin(list(names)).any().any(), "trustee name leaked"
    real_ids = list(df.loc[valid, "id_hayav"])
    num_cols = anon.select_dtypes("number").columns
    assert not anon[num_cols].isin(real_ids).any().any(), "ID number leaked"
    assert not anon.astype(str).isin([str(i) for i in real_ids]).any().any()
    assert anon["tik_code"].notna().all()
    assert anon["hayav_code"].isna().sum() == (~valid).sum()

    # --- legend: describe replaced / removed columns ---
    leg = legend.copy()
    first = leg.columns[0]
    notes = {
        "id_hayav": "הוחלף ב-hayav_code (H#####) — אותו אדם = אותו קוד",
        "neeman_1": "קוד נאמן אנונימי (P###)",
        "neeman_2": "קוד נאמן אנונימי (P###)",
        "dob": "הוסר (פרטי) — ראו age_ptichat_hlichim",
        "first_date": "הוסר",
        "last_date": "הוסר",
    }
    leg = leg[leg[first] != "num_tik"]
    for col, note in notes.items():
        leg.loc[leg[first] == col, leg.columns[1]] = note
    extra = pd.DataFrame({first: ["tik_code", "income_salery_bin"],
                          leg.columns[1]: ["קוד תיק אנונימי (T#####)",
                                           "קבוצת שכר (מחושב מ-income_salery)"]})
    leg = pd.concat([extra, leg], ignore_index=True)

    with pd.ExcelWriter(OUT, engine="openpyxl") as w:
        anon.to_excel(w, sheet_name="נתונים", index=False)
        leg.to_excel(w, sheet_name="מקראה", index=False)

    # --- the key (טבלת התממה) ---
    rev_t = pd.DataFrame(sorted(trustee.items(), key=lambda kv: kv[1]),
                         columns=["שם נאמן", "קוד"])
    n_cases = pd.concat([df["neeman_1"], df["neeman_2"]]).value_counts()
    rev_t["מספר הופעות"] = rev_t["שם נאמן"].map(n_cases).astype(int)
    rev_t["חדש בגרסה זו"] = ~rev_t["שם נאמן"].isin(list(old_trustee))
    rev_h = (df[valid].groupby("id_hayav").size().rename("מספר תיקים").reset_index()
             .assign(קוד=lambda d: d["id_hayav"].map(id_code))
             .rename(columns={"id_hayav": "תעודת זהות"})
             [["קוד", "תעודת זהות", "מספר תיקים"]].sort_values("קוד"))
    rev_k = (pd.DataFrame(sorted(tik_code.items()), columns=["מספר תיק", "קוד"])
             [["קוד", "מספר תיק"]])
    with pd.ExcelWriter(KEY, engine="openpyxl") as w:
        rev_t[["קוד", "שם נאמן", "מספר הופעות", "חדש בגרסה זו"]].to_excel(
            w, sheet_name="נאמנים", index=False)
        rev_h.to_excel(w, sheet_name="חייבים", index=False)
        rev_k.to_excel(w, sheet_name="תיקים", index=False)

    print(f"rows={len(anon)} cols={anon.shape[1]}")
    print(f"trustees={len(trustee)} (new={int(rev_t['חדש בגרסה זו'].sum())})")
    print(f"debtors={len(id_code)} (in >1 case={(rev_h['מספר תיקים'] > 1).sum()})")
    print(f"cases={len(tik_code)}  (no person code, placeholder ID: {(~valid).sum()})")
    print(f"wrote {OUT.name} and {KEY.name}")


if __name__ == "__main__":
    main()
