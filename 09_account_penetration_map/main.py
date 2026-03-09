from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent / "data"
RESULTS_DIR = Path(__file__).parent / "results"


def load_data(filepath: Path) -> pd.DataFrame:
    df = pd.read_csv(filepath, encoding="utf-8-sig")
    for col in ["導入部署数", "対象部署数", "導入商材数", "接触人数", "売上"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def analyze(filepath: Path) -> pd.DataFrame:
    df = load_data(filepath).copy()
    df["浸透度"] = (df["導入部署数"] / df["対象部署数"] * 100).round(1).fillna(0)
    df["深耕余地スコア"] = ((100 - df["浸透度"]).clip(lower=0) * 0.5 + df["導入商材数"].rsub(5).clip(lower=0) * 8 + df["売上"] / 1000000).round(1)
    df["判定"] = df["深耕余地スコア"].apply(lambda s: "高" if s >= 45 else "中" if s >= 30 else "低")
    return df.sort_values(["判定", "深耕余地スコア"], ascending=[True, False]).reset_index(drop=True)


def save_results(df: pd.DataFrame) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / "account_growth_targets.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    return out


def default_data_path() -> Path:
    return DATA_DIR / "accounts.csv"
