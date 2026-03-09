from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent / "data"
RESULTS_DIR = Path(__file__).parent / "results"


def load_data(filepath: Path) -> pd.DataFrame:
    df = pd.read_csv(filepath, encoding="utf-8-sig")
    df["金額"] = pd.to_numeric(df["金額"], errors="coerce").fillna(0)
    df["確度"] = pd.to_numeric(df["確度"], errors="coerce").fillna(0)
    return df


def analyze(filepath: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = load_data(filepath).copy()
    df["悲観"] = (df["金額"] * (df["確度"] - 15).clip(lower=0) / 100).round(0)
    df["標準"] = (df["金額"] * df["確度"] / 100).round(0)
    df["楽観"] = (df["金額"] * (df["確度"] + 10).clip(upper=100) / 100).round(0)

    monthly = df.groupby("受注予定月", as_index=False)[["悲観", "標準", "楽観"]].sum()
    monthly["標準上積み"] = (monthly["標準"] - monthly["悲観"]).clip(lower=0)
    monthly["楽観上積み"] = (monthly["楽観"] - monthly["標準"]).clip(lower=0)
    monthly["目標"] = (monthly["標準"] * 1.12).round(-3)
    return df.sort_values(["受注予定月", "標準"], ascending=[True, False]).reset_index(drop=True), monthly


def save_results(df: pd.DataFrame, monthly: pd.DataFrame) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / "forecast_scenarios.csv"
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        df.to_csv(f, index=False)
        f.write("\n")
        monthly.to_csv(f, index=False)
    return out


def default_data_path() -> Path:
    return DATA_DIR / "forecast.csv"
