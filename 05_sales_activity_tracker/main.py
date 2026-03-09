from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent / "data"
RESULTS_DIR = Path(__file__).parent / "results"


def load_data(filepath: Path) -> pd.DataFrame:
    df = pd.read_csv(filepath, encoding="utf-8-sig")
    for col in ["架電", "メール", "訪問", "商談", "目標活動量"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def analyze(filepath: Path) -> pd.DataFrame:
    df = load_data(filepath).copy()
    df["総活動量"] = df[["架電", "メール", "訪問", "商談"]].sum(axis=1)
    df["達成率"] = (df["総活動量"] / df["目標活動量"] * 100).round(1).fillna(0)
    df["判定"] = df["達成率"].apply(lambda v: "未達" if v < 80 else "注意" if v < 100 else "達成")
    return df.sort_values(["判定", "達成率"], ascending=[True, True]).reset_index(drop=True)


def get_rep_totals(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("担当者", as_index=False)[["架電", "メール", "訪問", "商談", "総活動量"]].sum().sort_values("総活動量", ascending=False)


def save_results(df: pd.DataFrame) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / "activity_summary.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    return out


def default_data_path() -> Path:
    return DATA_DIR / "activities.csv"
