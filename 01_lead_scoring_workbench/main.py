from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent / "data"
RESULTS_DIR = Path(__file__).parent / "results"

INDUSTRY_SCORES = {"SaaS": 18, "情報通信": 16, "製造": 14, "物流": 13, "小売": 11, "医療": 12, "人材": 12, "金融": 10}
SIZE_SCORES = {"1-49": 5, "50-99": 8, "100-299": 12, "300-999": 16, "1000+": 20}


def load_leads(filepath: Path) -> pd.DataFrame:
    df = pd.read_csv(filepath, encoding="utf-8-sig")
    for col in ["問い合わせ回数", "資料DL数"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    df["最終接触日"] = pd.to_datetime(df["最終接触日"], errors="coerce")
    return df


def analyze(filepath: Path, reference_date: pd.Timestamp | None = None) -> pd.DataFrame:
    ref = pd.Timestamp(reference_date).normalize() if reference_date is not None else pd.Timestamp.today().normalize()
    df = load_leads(filepath).copy()
    df["未接触日数"] = (ref - df["最終接触日"]).dt.days.clip(lower=0)
    df["問い合わせ点"] = df["問い合わせ回数"].clip(upper=4) * 8
    df["資料DL点"] = df["資料DL数"].clip(upper=4) * 5
    df["業種点"] = df["業種"].map(INDUSTRY_SCORES).fillna(8)
    df["規模点"] = df["従業員規模"].map(SIZE_SCORES).fillna(6)
    df["接触鮮度点"] = df["未接触日数"].apply(lambda d: 20 if d <= 3 else 14 if d <= 7 else 8 if d <= 14 else 3 if d <= 30 else 0)
    df["合計スコア"] = df["問い合わせ点"] + df["資料DL点"] + df["業種点"] + df["規模点"] + df["接触鮮度点"]
    df["優先度"] = df["合計スコア"].apply(lambda s: "A" if s >= 75 else "B" if s >= 55 else "C")
    df["推奨アクション"] = df.apply(
        lambda r: "即日フォロー" if r["優先度"] == "A" and r["未接触日数"] >= 3 else "当日中に提案" if r["優先度"] == "A"
        else "今週中に再接触" if r["優先度"] == "B" and r["未接触日数"] >= 7 else "次回接触を予約" if r["優先度"] == "B"
        else "ナーチャリング継続",
        axis=1,
    )
    return df.sort_values(["優先度", "合計スコア"], ascending=[True, False]).reset_index(drop=True)


def get_summary(df: pd.DataFrame) -> dict:
    return {
        "総リード数": int(len(df)),
        "Aランク": int((df["優先度"] == "A").sum()),
        "Bランク": int((df["優先度"] == "B").sum()),
        "Cランク": int((df["優先度"] == "C").sum()),
        "平均スコア": float(round(df["合計スコア"].mean(), 1)) if len(df) else 0.0,
    }


def save_results(df: pd.DataFrame) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / "lead_priority.csv"
    export = df.copy()
    export["最終接触日"] = export["最終接触日"].dt.strftime("%Y-%m-%d")
    export.to_csv(out, index=False, encoding="utf-8-sig")
    return out


def default_data_path() -> Path:
    return DATA_DIR / "leads.csv"
