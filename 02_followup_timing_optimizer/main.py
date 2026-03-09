from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent / "data"
RESULTS_DIR = Path(__file__).parent / "results"
INTERVALS = {"初回接触": 2, "提案中": 4, "見積提出": 3, "稟議中": 5, "保留": 10}


def load_data(filepath: Path) -> pd.DataFrame:
    df = pd.read_csv(filepath, encoding="utf-8-sig")
    df["最終接触日"] = pd.to_datetime(df["最終接触日"], errors="coerce")
    return df


def analyze(filepath: Path, reference_date: pd.Timestamp | None = None) -> pd.DataFrame:
    ref = pd.Timestamp(reference_date).normalize() if reference_date is not None else pd.Timestamp.today().normalize()
    df = load_data(filepath).copy()
    df["推奨間隔"] = df["フェーズ"].map(INTERVALS).fillna(7)
    df["未接触日数"] = (ref - df["最終接触日"]).dt.days.clip(lower=0)
    df["超過日数"] = df["未接触日数"] - df["推奨間隔"]
    df["判定"] = df["超過日数"].apply(lambda d: "即連絡" if d >= 2 else "今週中" if d >= 0 else "様子見")
    df["優先スコア"] = df["超過日数"].clip(lower=0) * 6 + df["温度感"].map({"高": 20, "中": 12, "低": 5}).fillna(8)
    return df.sort_values(["判定", "優先スコア"], ascending=[True, False]).reset_index(drop=True)


def get_summary(df: pd.DataFrame) -> dict:
    return {k: int((df["判定"] == k).sum()) for k in ["即連絡", "今週中", "様子見"]}


def save_results(df: pd.DataFrame) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / "followup_actions.csv"
    export = df.copy()
    export["最終接触日"] = export["最終接触日"].dt.strftime("%Y-%m-%d")
    export.to_csv(out, index=False, encoding="utf-8-sig")
    return out


def default_data_path() -> Path:
    return DATA_DIR / "followups.csv"
