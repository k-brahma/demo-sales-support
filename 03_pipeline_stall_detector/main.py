from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent / "data"
RESULTS_DIR = Path(__file__).parent / "results"
THRESHOLDS = {"初回商談": 7, "提案": 10, "見積": 7, "稟議": 14, "契約調整": 10}


def load_data(filepath: Path) -> pd.DataFrame:
    df = pd.read_csv(filepath, encoding="utf-8-sig")
    df["フェーズ開始日"] = pd.to_datetime(df["フェーズ開始日"], errors="coerce")
    df["金額"] = pd.to_numeric(df["金額"], errors="coerce").fillna(0)
    return df


def analyze(filepath: Path, reference_date: pd.Timestamp | None = None) -> pd.DataFrame:
    ref = pd.Timestamp(reference_date).normalize() if reference_date is not None else pd.Timestamp.today().normalize()
    df = load_data(filepath).copy()
    df["滞留日数"] = (ref - df["フェーズ開始日"]).dt.days.clip(lower=0)
    df["基準日数"] = df["フェーズ"].map(THRESHOLDS).fillna(10)
    df["超過日数"] = df["滞留日数"] - df["基準日数"]
    df["停滞判定"] = df["超過日数"].apply(lambda d: "重度停滞" if d >= 7 else "停滞" if d >= 1 else "正常")
    df["リスクスコア"] = df["超過日数"].clip(lower=0) * 4 + (100 - df["確度"]).clip(lower=0) / 5
    return df.sort_values(["停滞判定", "リスクスコア", "金額"], ascending=[True, False, False]).reset_index(drop=True)


def get_phase_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary = df.groupby("フェーズ", as_index=False)["滞留日数"].mean()
    summary["滞留日数"] = summary["滞留日数"].round(1)
    return summary.sort_values("滞留日数", ascending=False)


def save_results(df: pd.DataFrame) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / "pipeline_stall_report.csv"
    export = df.copy()
    export["フェーズ開始日"] = export["フェーズ開始日"].dt.strftime("%Y-%m-%d")
    export.to_csv(out, index=False, encoding="utf-8-sig")
    return out


def default_data_path() -> Path:
    return DATA_DIR / "opportunities.csv"
