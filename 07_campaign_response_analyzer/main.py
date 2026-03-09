from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent / "data"
RESULTS_DIR = Path(__file__).parent / "results"


def load_data(filepath: Path) -> pd.DataFrame:
    df = pd.read_csv(filepath, encoding="utf-8-sig")
    for col in ["送付数", "開封数", "クリック数", "商談化数"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def analyze(filepath: Path) -> pd.DataFrame:
    df = load_data(filepath).copy()
    df["開封率"] = (df["開封数"] / df["送付数"] * 100).round(1).fillna(0)
    df["クリック率"] = (df["クリック数"] / df["送付数"] * 100).round(1).fillna(0)
    df["商談化率"] = (df["商談化数"] / df["送付数"] * 100).round(1).fillna(0)
    return df.sort_values("商談化率", ascending=False).reset_index(drop=True)


def save_results(df: pd.DataFrame) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / "campaign_report.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    return out


def default_data_path() -> Path:
    return DATA_DIR / "campaigns.csv"
